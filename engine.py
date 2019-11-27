from my_parser import AstVisitor, FunctionCallExpression, PrintStatement
from scanner import Token
import random
from itertools import repeat, chain
from contextlib import nullcontext


def append(y):
    return ([''.join([str(z) for z in x]) for x in y], False)


def append_times(x, y):
    # unpack the raw value, and mark the
    # returning one as constant
    return (repeat(append(x)[0][0], y), True)


def one_of(l):
    return ([random.choice(l)], False)


def one_of_times(l, y):
    return (random.choices(l, k=y), False)


def lower(w):
    return ([str(w).lower()], False)


def lower_times(x, y):
    return (repeat(str(x).lower(), y), True)


def one_of_unique(l):
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
    return ([v], False)


def one_of_unique_times(l, number):
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
    return (v, False)


def between_times(x, y):
    if len(x) != 2:
        raise EngineError(
            "number.between takes two arguments, %d were given" % len(x))
    lower = int(x[0])
    upper = int(x[1])
    return (random.choices(range(lower, upper + 1), k=y), False)


def between(x):
    if len(x) != 2:
        raise EngineError(
            "number.between takes two arguments, %d were given" % len(x))
    return ([random.randint(x[0], x[1])], False)


def upto_times(x, y):
    if len(x) != 1:
        raise EngineError(
            "upto takes one argument, %d were given" % len(x))
    upper = int(x[0])
    return (random.choices(range(0, upper + 1), k=y), False)


def upto(x):
    return ([random.randint(0, x[0])], False)


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
        AstVisitor.__init__(self)
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

    def visit_function_call(self, ast):
        func = ast.func
        args = []
        for a in ast.args:
            args.append(self.visit(a))
        return FunctionCallExpression(func, args)

    def visit_print(self, ast):
        val = self.visit(ast.val)
        return PrintStatement(ast.times, val)


class Engine(AstVisitor):

    def __init__(self, generate_only=False, processes=-1):
        AstVisitor.__init__(self)
        self.defaultrules = {}
        self.grammars = {}
        self.flatter = AstFlatter()
        self.num_process = processes
        self.generate_only = generate_only
        self.function_dictionary = {"one_of": one_of, "one_of_unique": one_of_unique,
                                    "append": append, "lower": lower,
                                    "number_upto": upto, "number_between": between}
        self.vector_function_dictionary = {"one_of": one_of_times, "one_of_unique": one_of_unique_times,
                                           "append": append_times, "lower": lower_times,
                                           "number_upto": upto_times,
                                           "number_between": between_times}
        random.seed()

    def visit_assignment(self, ast):
        self.grammars[ast.lhs.val] = self.flatter.visit(ast)
        return None
        # return ast.rhs.accept(self)
        # assignment no longer explicitly evaluates

    def evaluate_parallel(self, ast):
        from multiprocessing import Pool, cpu_count, RLock, Manager
        workers = self.num_process
        if workers == -1:
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
        if not self.generate_only:
            result = []
            for y in ret:
                result.extend(y[0])
            return result

    def visit_print(self, ast):
        ast = self.flatter.visit_print(ast)
        times = int(ast.times.val)
        if times > 10000 and self.num_process != 1:
            try:
                return self.evaluate_parallel(ast)
            except ImportError:
                if self.num_process != -1:
                    print("[Info] Python in this system does not support multiprocessing!\n"
                          "Falling back to single process!")
                pass
        # either times < 10000 or import failed
        init_child({}, nullcontext())
        ret = self.visit_optional(ast.val, times)[0]
        # print(ret)
        return ret

    def visit_literal(self, ast, times):
        if ast.val.type == Token.INTEGER:
            return (repeat(int(ast.val.val), times), True)
        else:
            return (repeat(str(ast.val.val.replace("\"", "")), times), True)

    def visit_variable(self, ast, times):
        if ast.val.val in self.defaultrules:
            return (repeat(self.defaultrules[ast.val.val], times), True)
        elif ast.val.val in self.grammars:
            return self.visit_optional(self.grammars[ast.val.val], times)
        else:
            raise EngineError("No such rule found '%s'!" % ast.val.val)

    def peek_one(self, iterable):
        gen = iter(iterable)
        peek = next(gen)
        iterator = chain([peek], gen)
        return (peek, iterator)

    def visit_function_call(self, ast, times):
        if ast.func.val not in self.function_dictionary:
            raise EngineError("Invalid function name '%s'!" % (ast.func))
        func = self.function_dictionary[ast.func.val]

        args = []
        arg_is_constant = True
        for arg in ast.args:
            # temp now contains a collection of similar values
            # which maybe marked as a constant
            temp = self.visit_optional(arg, times)
            arg_is_constant = arg_is_constant and temp[1]
            # extract the raw collection and store it as argument
            args.append(temp[0])

        if arg_is_constant:
            argsorted = repeat([next(y) for y in args], times)
        else:
            argsorted = zip(*args)

        res = []
        if arg_is_constant:
            func = self.vector_function_dictionary[ast.func.val]
            res = func(next(argsorted), times)
            return res
        else:
            res.extend(func(argsorted)[0])
            # Finally, wrap the result on a tuple
            # and mark it as not constant
            return (res, False)
