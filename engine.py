from my_parser import AstVisitor, FunctionCallExpression, PrintStatement, VariableExpression
from scanner import Token
import random
from itertools import repeat, chain
from contextlib import nullcontext

def append(y, r, rule=None):
    return ([''.join([str(z) for z in x]) for x in y], False)


def append_times(x, y, rule=None):
    # unpack the raw value, and mark the
    # returning one as constant
    return (repeat(append(x, y[1])[0][0], y[0]), True)


def one_of(l, r, rule=None):
    return ([r.choice(k) for k in l], False)


def one_of_times(l, y, rule=None):
    return (y[1].choices(l, k=y[0]), False)


def lower(w, r, rule=None):
    return ([str(x[0]).lower() for x in w], False)


def lower_times(x, y, rule=None):
    return (repeat(str(x[0]).lower(), y[0]), True)


def one_of_unique(k, r, rules):
    global UNIQUE_DICTIONARY
    global UNIQUE_DICTIONARY_LOCK

    res = []
    for expand in zip(k, rules):
        l = expand[0]
        rule = expand[1]
        with UNIQUE_DICTIONARY_LOCK:
            if rule not in UNIQUE_DICTIONARY:
                UNIQUE_DICTIONARY[rule] = set(l)

            dictionary = UNIQUE_DICTIONARY[rule]
            if len(dictionary) == 0:
                raise EngineError("No more unique values to generate!")

            # Value() marks this copy of the value as not constant
            v = r.sample(dictionary, 1)
            dictionary.remove(v[0])
            res.append(v[0])
            UNIQUE_DICTIONARY[rule] = dictionary
    return (res, False)


def one_of_unique_times(l, number, rule):
    global UNIQUE_DICTIONARY
    global UNIQUE_DICTIONARY_LOCK

    with UNIQUE_DICTIONARY_LOCK:
        if rule not in UNIQUE_DICTIONARY:
            UNIQUE_DICTIONARY[rule] = set(l)

        dictionary = UNIQUE_DICTIONARY[rule]
        if len(dictionary) < number[0]:
            raise EngineError(
                "Required %d unique values cannot be generated!" % number[0])
        v = number[1].sample(dictionary, number[0])
        dictionary.difference_update(v)

        UNIQUE_DICTIONARY[rule] = dictionary
    return (v, False)


def between_times(x, y, rule=None):
    lower = int(x[0])
    upper = int(x[1])
    return (y[1].choices(range(lower, upper + 1), k=y[0]), False)


def between(y, r, rule=None):
    return ([(x[0] + int((x[1] - x[0])*r.random())) for x in y], False)


def upto_times(x, y, rule=None):
    upper = int(x[0])
    return (y[1].choices(range(0, upper + 1), k=y[0]), False)


def upto(y, r, rule=None):
    return ([int(r.random() * (x + 1)) for x in y], False)


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


class Engine(AstVisitor):

    def __init__(self, generate_only=False, processes=-1):
        AstVisitor.__init__(self, debug=False)
        self.defaultrules = {}
        self.grammars = {}
        self.num_process = processes
        self.generate_only = generate_only
        self.function_dictionary = {"one_of": one_of, "one_of_unique": one_of_unique,
                                    "append": append, "lower": lower,
                                    "number_upto": upto, "number_between": between}
        self.vector_function_dictionary = {"one_of": one_of_times, "one_of_unique": one_of_unique_times,
                                           "append": append_times, "lower": lower_times,
                                           "number_upto": upto_times,
                                           "number_between": between_times}
        self.argcount = {"one_of": -1, "one_of_unique": -1,
                         "append": -1, "lower": 1,
                         "number_upto": 1, "number_between": 2}
        self.results = {}

    def visit_assignment(self, ast):
        if isinstance(ast.rhs, VariableExpression):
            if not ast.rhs.val.val in self.grammars:
                raise EngineError("Rule not found '%s'!" % ast.rhs.val)
            self.grammars[ast.lhs.val] = self.grammars[ast.rhs.val.val]
        else:
            self.grammars[ast.lhs.val] = ast.rhs
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
        randomer = [random.Random() for _ in work_times]
        optional_arg = [(w, r) for w, r in zip(work_times, randomer)]
        manager = Manager()
        l = manager.RLock()
        u = manager.dict()
        pool = Pool(processes=workers, initializer=init_child, initargs=(u,
                                                                         l))

        ret = pool.starmap(self.visit_optional, zip(ast_list, optional_arg))
        pool.close()
        if not self.generate_only:
            result = []
            for y in ret:
                result.extend(y[0])
            return result

    def visit_print(self, ast):
        times = int(ast.times.val)
        if (times > 10000 or self.num_process != -1) and self.num_process != 1:
            try:
                return self.evaluate_parallel(ast)
            except ImportError:
                if self.num_process != -1:
                    print("[Info] Python in this system does not support multiprocessing!\n"
                          "[Info] Falling back to single process!")
                pass
        # either times < 10000 or import failed
        init_child({}, nullcontext())
        random.seed()
        times = (times, random)
        ret = self.visit_optional(ast.val, times)[0]
        # print(ret)
        return ret

    def visit_literal(self, ast, times):
        times = times[0]
        if ast.val.type == Token.INTEGER:
            return (repeat(int(ast.val.val), times), True)
        else:
            return (repeat(str(ast.val.val.replace("\"", "")), times), True)

    def visit_variable(self, ast, times):
        name = ast.val.val
        if name in self.results:
            return self.results[name]
        elif name in self.grammars:
            res = self.visit_optional(self.grammars[name], (*times, name))
            self.results[name] = res
            return res
        elif name in self.defaultrules:
            return (repeat(self.defaultrules[name], times[0]), True)
        else:
            raise EngineError("No such rule found '%s'!" % name)

    def visit_function_call(self, ast, times):
        if ast.func.val not in self.function_dictionary:
            raise EngineError("Invalid function name '%s'!" % (ast.func))
        func = self.function_dictionary[ast.func.val]
        argc = self.argcount[ast.func.val]
        if argc != -1 and len(ast.args) != argc:
            raise EngineError("Function '%s' takes %d arguments, %d given!"
                              % (ast.func.val, argc, len(ast.args)))

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
            argsorted = repeat([next(y) for y in args], times[0])
        else:
            argsorted = zip(*args)

        res = []
        if arg_is_constant:
            func = self.vector_function_dictionary[ast.func.val]
            return func(next(argsorted), times, times[-1])
        else:
            # send the Random object
            res.extend(func(argsorted, times[1], times[-1])[0])
            # Finally, wrap the result on a tuple
            # and mark it as not constant
            return (res, False)
