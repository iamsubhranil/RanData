from my_parser import AstVisitor, MethodCallExpression, PrintStatement
from scanner import Token
import random
from itertools import repeat, chain
from contextlib import nullcontext


class Value:

    def __init__(self, v=[], const=False):
        # val now contains a collection of
        # raw values of same type, and
        # is_constant marks the whole set
        # of values either constant or not
        self.val = v
        self.is_constant = const

    def __str__(self):
        return str(self.val)

    def __repr__(self):
        return "Value(" + str(self.val) + ")"


# append is called when either the
# collection stored here is not constant
# or the argument is not, so in either
# case, we just need to append one to one
def append(x, y):
    ret = str(x)
    for i in y:
        ret += str(i)
    return Value([ret])

def append_times(w, x, y):
    # unpack the raw value, and mark the
    # returning one as constant
    return Value(repeat(append(w, x).val[0], y), True)

# arguments are unpacked now
def constant(w, x):
    return Value([x], True)

def constant_times(w, x, y):
    return Value(repeat(x[0], y), True)

def one_of(w, l):
    return Value([random.choice(l)])

def one_of_times(w, l, y):
    res = random.choices(l, k=y)
    return Value(res)

def lower(w):
    return Value([str(w).lower()])

def lower_times(x, y):
    return Value(repeat(str(x).lower(), y), True)

def one_of_unique(x, l):
    global UNIQUE_DICTIONARY
    global UNIQUE_DICTIONARY_LOCK

    tup = frozenset(l)
    with UNIQUE_DICTIONARY_LOCK:
        if tup not in UNIQUE_DICTIONARY:
            UNIQUE_DICTIONARY[tup] = set(l)

        dictionary = UNIQUE_DICTIONARY[tup]
        if len(dictionary) == 0:
            raise EngineError("No more unique values to generate!")

        # Value() marks this copy of the value as not constant
        v = random.sample(dictionary, 1)
        dictionary.remove(v)

        UNIQUE_DICTIONARY[tup] = dictionary
    return Value([v])

def one_of_unique_times(x, l, number):
    global UNIQUE_DICTIONARY
    global UNIQUE_DICTIONARY_LOCK

    tup = frozenset(l)
    with UNIQUE_DICTIONARY_LOCK:
        if tup not in UNIQUE_DICTIONARY:
            UNIQUE_DICTIONARY[tup] = set(l)

        dictionary = UNIQUE_DICTIONARY[tup]
        if len(dictionary) < number:
            raise EngineError(
                "Required %d unique values cannot be generated!" % number)
        v = random.sample(dictionary, number)
        dictionary.difference_update(v)

        UNIQUE_DICTIONARY[tup] = dictionary
    return Value(v)

def between_times(w, x, y):
    if len(x) != 2:
        raise EngineError(
            "number.between takes two arguments, %d were given" % len(x))
    lower = int(x[0])
    upper = int(x[1])
    collection = random.choices(range(lower, upper + 1), k=y)
    return Value(collection)

def between(w, x):
    if len(x) != 2:
        raise EngineError(
            "number.between takes two arguments, %d were given" % len(x))
    return Value([random.randint(x[0], x[1])])

def upto_times(w, x, y):
    if len(x) != 1:
        raise EngineError(
            "upto takes one argument, %d were given" % len(x))
    upper = int(x[0])
    collection = random.choices(range(0, upper + 1), k=y)
    return Value(collection)

def upto(w, x):
    return Value([random.randint(0, x[0])])


class EngineError(Exception):
    pass


def init_child(u, l):
    global UNIQUE_DICTIONARY
    global UNIQUE_DICTIONARY_LOCK

    UNIQUE_DICTIONARY = u
    UNIQUE_DICTIONARY_LOCK = l


class NullManager:

    def Lock(self):
        return nullcontext()

class AstFlatter(AstVisitor):

    def __init__(self, grammars={}):
        AstVisitor.__init__(self, True)
        self.grammars = grammars

    def visit_assignment(self, ast):
        self.grammars[ast.lhs.val] = self.visit(ast.rhs)
        return self.grammars[ast.lhs.val]

    def visit_literal(self, ast):
        return ast

    def visit_variable(self, ast):
        if ast.val.val in self.grammars:
            return self.grammars[ast.val.val]
        return ast

    def visit_method_call(self, ast):
        obj = self.visit(ast.obj)
        func = ast.func
        args = []
        for a in ast.args:
            args.append(self.visit(a))
        return MethodCallExpression(obj, func, args)

    def visit_print(self, ast):
        val = self.visit(ast.val)
        return PrintStatement(ast.times, val)

class Engine(AstVisitor):

    def __init__(self, parallel=True):
        AstVisitor.__init__(self)
        self.defaultrules = {"value": '', "number": 0}
        self.grammars = {}
        self.flatter = AstFlatter()
        self.on_parallel = parallel
        self.method_dictionary = {str: {"one_of": one_of, "one_of_unique": one_of_unique,
                                          "append": append, "lower": lower,
                                          "constant": constant},
                                  int: {"upto": upto, "between": between}}
        self.vector_method_dictionary = {"one_of" : one_of_times, "one_of_unique": one_of_unique_times,
                                         "append": append_times, "lower": lower_times,
                                         "constant": constant_times, "upto": upto_times,
                                         "between": between_times}
        random.seed()

    def visit_assignment(self, ast):
        self.grammars[ast.lhs.val] = self.flatter.visit(ast)
        return None
        # return ast.rhs.accept(self)
        # assignment no longer explicitly evaluates

    def evaluate_parallel(self, ast):
        from multiprocessing import Pool, cpu_count, RLock, Manager
        workers = cpu_count()
        times = int(ast.times.val)
        each_time = int(times / workers)
        # equally divide work between count - 1 threads
        work_times = [int(each_time)] * (workers - 1)
        # dump all the extra work on last thread
        work_times.append(times - (each_time * (workers - 1)))
        ast_list = [ast.val] * len(work_times)
        manager = Manager()
        l = manager.RLock()
        u = manager.dict()
        pool = Pool(processes=workers, initializer=init_child, initargs=(u,
                                                                         l))

        ret = pool.starmap(self.visit_optional, zip(ast_list, work_times))
        pool.close()
        result = []
        for y in ret:
            result.extend(y.val)
        return result

    def visit_print(self, ast):
        ast = self.flatter.visit_print(ast)
        times = int(ast.times.val)
        if times > 10000 and self.on_parallel:
            try:
                return self.evaluate_parallel(ast)
            except ImportError:
                pass
        # either on_parallel is off or import failed
        init_child({}, nullcontext())
        ret = self.visit_optional(ast.val, times).val
        #print(ret)
        return ret

    def visit_literal(self, ast, times):
        if ast.val.type == Token.INTEGER:
            return Value(repeat(int(ast.val.val), times), True)
        else:
            return Value(repeat(str(ast.val.val.replace("\"", "")), times), True)

    def visit_variable(self, ast, times):
        if ast.val.val in self.defaultrules:
            return Value(repeat(self.defaultrules[ast.val.val], times), True)
        elif ast.val.val in self.grammars:
            return self.visit_optional(self.grammars[ast.val.val], times)
        else:
            raise EngineError("No such rule found '%s'!" % ast.val.val)

    def peek_one(self, iterable):
        gen = iter(iterable)
        peek = next(gen)
        iterator = chain([peek], gen)
        return (peek, iterator)

    def visit_method_call(self, ast, times):
        obj = self.visit_optional(ast.obj, times)
        obj0, obj.val = self.peek_one(obj.val)
        if obj0.__class__ not in self.method_dictionary:
            raise EngineError("Invalid object type '%s'!" %
                              str(obj0.__class__))
        if ast.func.val not in self.method_dictionary[obj0.__class__]:
            raise EngineError("Invalid method name '%s'!" % (ast.func))
        func = self.method_dictionary[obj0.__class__][ast.func.val]

        args = []
        arg_is_constant = True
        for arg in ast.args:
            # temp now contains a collection of similar values
            # which maybe marked as a constant
            temp = self.visit_optional(arg, times)
            arg_is_constant = arg_is_constant and temp.is_constant
            # extract the raw collection and store it as argument
            args.append(temp.val)

        if arg_is_constant:
            argsorted = repeat([next(y) for y in args], times)
        else:
            argsorted = zip(*args)

        res = []
        if obj.is_constant:
            if arg_is_constant:
                if ast.func.val not in self.vector_method_dictionary:
                    print("[Warning] Should've implemented '%s' on '%s'!"
                          % (str(ast.func.val) + "_times", obj0.__class__))
                else:
                    func = self.vector_method_dictionary[ast.func.val]
                    # returns a Value wrapper over the collection
                    res = func(obj0, next(argsorted), times)
                    return res
            for a in argsorted:
                # obj is constant but arg is not,
                # so we call the obj0 with one set
                # of arg each time, which should
                # return a Value wrapper containing
                # one child
                res.append(func(obj0, a).val[0])
        else:
            for o, a in zip(obj.val, argsorted):
                # None of obj and arg is constant,
                # so we call each obj with one arg
                # each time, which should also return
                # a Value wrapper containing one child
                res.append(func(o, a).val[0])
        # Finally, wrap the result on a Value
        # and mark it as not constant
        return Value(res, False)
