from my_parser import AstVisitor
from scanner import Token
import random
from itertools import repeat, chain
from contextlib import nullcontext

class Value:

    def __init__(self, v='', const=False):
        self.val = v
        self.is_constant = const

    def __str__(self):
        return str(self.val)

    def append(self, y):
        ret = str(self.val)
        for i in y:
            ret += str(i)
        return Value(ret)

    def append_times(self, x, y):
        return repeat(self.append(x), y)

    def constant(self, x):
        return Value(x[0].val, True)

    def constant_times(self, x, y):
        return repeat(Value(x[0].val, True), y)

    def one_of(self, l):
        return Value(random.choice(l))

    def one_of_times(self, l, y):
        res = [Value(val.val) for val in random.choices(l, k=y)]
        return res

    def lower(self):
        return Value(str(self.val).lower(), self.is_constant)

    def lower_times(self, x):
        return repeat(self.lower(), x)

    def one_of_unique(self, l):
        global UNIQUE_DICTIONARY
        global UNIQUE_DICTIONARY_LOCK
        global INDIVIDUAL_DICTIONARY_LOCKS

        tup = frozenset(l)
        with UNIQUE_DICTIONARY_LOCK:
            if tup not in UNIQUE_DICTIONARY:
                UNIQUE_DICTIONARY[tup] = set(l)
                INDIVIDUAL_DICTIONARY_LOCKS[tup] = MANAGER.Lock()

        with INDIVIDUAL_DICTIONARY_LOCKS[tup]:
            dictionary = UNIQUE_DICTIONARY[tup]
            if len(dictionary) == 0:
                raise EngineError("No more unique values to generate!")

            # Value() marks this copy of the value as not constant
            v = random.sample(dictionary, 1)
        return Value(v.val)

    def one_of_unique_times(self, l, number):
        global UNIQUE_DICTIONARY
        global UNIQUE_DICTIONARY_LOCK
        global INDIVIDUAL_DICTIONARY_LOCKS

        tup = frozenset(l)
        with UNIQUE_DICTIONARY_LOCK:
            if tup not in UNIQUE_DICTIONARY:
                UNIQUE_DICTIONARY[tup] = set(l)
                INDIVIDUAL_DICTIONARY_LOCKS[tup] = MANAGER.Lock()

        with INDIVIDUAL_DICTIONARY_LOCKS[tup]:
            dictionary = UNIQUE_DICTIONARY[tup]
            if len(dictionary) < number:
                raise EngineError("Required %d unique values cannot be generated!" % number)
            v = []
            for y in random.sample(dictionary, number):
                v.append(Value(y.val))
                dictionary.remove(y)
            UNIQUE_DICTIONARY[tup] = dictionary
        return v

    def __hash__(self):
        return hash(self.val)

    def __eq__(self, y):
        return self.val == y.val

    def __repr__(self):
        return str(self.val)


class Number(Value):

    def __init__(self):
        Value.__init__(self, '', True)

    def between_times(self, x, y):
        if len(x) != 2:
            raise EngineError(
                "number.between takes two arguments, %d were given" % len(x))
        lower = int(x[0].val)
        upper = int(x[1].val)
        collection = random.choices(range(lower, upper + 1), k=y)
        res = [Value(val) for val in collection]
        return res

    def between(self, x):
        if len(x) != 2:
            raise EngineError(
                "number.between takes two arguments, %d were given" % len(x))
        return Value(random.randint(x[0].val, x[1].val))

    def upto_times(self, x, y):
        if len(x) != 1:
            raise EngineError("upto takes one argument, %d were given" % len(x))
        upper = int(x[0].val)
        collection = random.choices(range(0, upper + 1), k=y)
        res = [Value(val) for val in collection]
        return res

    def upto(self, x):
        return Value(random.randint(0, x[0].val))


class EngineError(Exception):
    pass

def init_child(u, l, i, m):
    global UNIQUE_DICTIONARY
    global UNIQUE_DICTIONARY_LOCK
    global INDIVIDUAL_DICTIONARY_LOCKS
    global MANAGER

    UNIQUE_DICTIONARY = u
    UNIQUE_DICTIONARY_LOCK = l
    INDIVIDUAL_DICTIONARY_LOCKS = i
    MANAGER = m

class NullManager:

    def Lock(self):
        return nullcontext()

class Engine(AstVisitor):

    def __init__(self, parallel=True):
        AstVisitor.__init__(self)
        self.defaultrules = {"value": Value('', True), "number": Number()}
        self.grammars = {}
        self.on_parallel = parallel
        self.method_dictionary = {Value: {"one_of": Value.one_of, "one_of_unique": Value.one_of_unique,
                                          "append": Value.append, "lower": Value.lower,
                                          "constant": Value.constant},
                                  Number: {"upto": Number.upto, "between": Number.between}}
        random.seed()

    def visit_assignment(self, ast):
        self.grammars[ast.lhs.val] = ast.rhs
        return None
        # return ast.rhs.accept(self)
        # assignment no longer explicitly evaluates

    def evaluate_parallel(self, ast):
        from multiprocessing import Pool, cpu_count, Lock, Manager
        workers = cpu_count()
        times = int(ast.times.val)
        each_time = int(times / workers)
        # equally divide work between count - 1 threads
        work_times = [int(each_time)] * (workers - 1)
        # dump all the extra work on last thread
        work_times.append(times - (each_time * (workers - 1)))
        ast_list = [ast.val] * len(work_times)
        manager = Manager()
        pool = Pool(workers, init_child, (manager.dict(), manager.Lock(), manager.dict(), manager))
        ret = pool.starmap(self.visit_optional, zip(ast_list, work_times))
        pool.close()
        result = []
        for y in ret:
            result.extend(y)
        return result

    def visit_print(self, ast):
        if self.on_parallel:
            try:
                return self.evaluate_parallel(ast)
            except ImportError:
                pass
        # either on_parallel is off or import failed
        times = int(ast.times.val)
        init_child({}, nullcontext(), {}, NullManager())
        return self.visit_optional(ast.val, times)

    def visit_literal(self, ast, times):
        if ast.val.type == Token.INTEGER:
            return repeat(Value(int(ast.val.val), True), times)
        else:
            return repeat(Value(str(ast.val.val.replace("\"", "")), True), times)

    def visit_variable(self, ast, times):
        if ast.val.val in self.defaultrules:
            return repeat(self.defaultrules[ast.val.val], times)
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
        obj0, obj = self.peek_one(obj)
        if obj0.__class__ not in self.method_dictionary:
            raise EngineError("Invalid object type '%s'!" % str(obj0.__class__))
        if ast.func.val not in self.method_dictionary[obj0.__class__]:
            raise EngineError("Invalid method name '%s'!" % (ast.func))
        func = self.method_dictionary[obj0.__class__][ast.func.val]

        args = []
        arg_is_constant = True
        for arg in ast.args:
            temp = self.visit_optional(arg, times)
            val, temp = self.peek_one(temp)
            arg_is_constant = arg_is_constant and val.is_constant
            args.append(temp)

        if arg_is_constant:
            argsorted = repeat([next(y) for y in args], times)
        else:
            argsorted = zip(*args)

        res = []
        if obj0.is_constant:
            if arg_is_constant:
                bakfunc = func
                func = getattr(obj0, str(ast.func.val) + "_times", None)
                if not callable(func):
                    print("[Warning] Should've implemented '%s' on '%s'!"
                          % (str(ast.func.val) + "_times", obj0.__class__))
                    func = bakfunc
                else:
                    res = func(next(argsorted), times)
                    return res
            for a in argsorted:
                res.append(func(obj0, a))
        else:
            for o, a in zip(obj, argsorted):
                res.append(func(o, a))
        return res
