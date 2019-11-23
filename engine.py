from my_parser import AstVisitor
from scanner import Token
import random


class Value:

    UNIQUE_DICTIONARY = {}

    def __init__(self, v='', const=False):
        if isinstance(v, Value):
            self.val = v.val
            self.is_constant = const
        else:
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
        return [self.append(x)] * y

    def constant(self, x):
        return Value(x[0], True)

    def constant_times(self, x, y):
        return [Value(x[0], True)] * y

    def one_of(self, l):
        return Value(random.choice(l))

    def one_of_times(self, l, y):
        res = []
        for _ in range(y):
            res.append(Value(random.choice(l)))
        return res

    def lower(self):
        return Value(str(self.val).lower(), self.is_constant)

    def lower_times(self, x):
        return [self.lower()] * x

    def one_of_unique(self, l):
        origlist = l
        while len(origlist) == 1 and isinstance(origlist[0], Value):
            origlist = origlist[0].val
        l = origlist
        tup = frozenset(l)
        if tup in self.UNIQUE_DICTIONARY:
            dictionary = self.UNIQUE_DICTIONARY[tup]
            if len(dictionary) == len(tup):
                raise EngineError("No more unique values to generate!")
        else:
            self.UNIQUE_DICTIONARY[tup] = set()
            dictionary = self.UNIQUE_DICTIONARY[tup]

        v = random.sample(tup - dictionary, 1)
        dictionary.add(v)
        return v

    def one_of_unique_times(self, l, number):
        origlist = l
        while len(origlist) == 1 and isinstance(origlist[0], Value):
            origlist = origlist[0].val
        l = origlist
        tup = frozenset(l)
        if tup in self.UNIQUE_DICTIONARY:
            dictionary = self.UNIQUE_DICTIONARY[tup]
            if len(dictionary) <= (len(tup) + number):
                raise EngineError("Required %d unique values cannot be generated!" % number)
        else:
            self.UNIQUE_DICTIONARY[tup] = set()
            dictionary = self.UNIQUE_DICTIONARY[tup]
        v = random.sample(tup - dictionary, number)
        dictionary.update(v)
        return v

    def __hash__(self):
        if isinstance(self.val, Value):
            return self.val.__hash__()
        return hash(self.val)

    def __eq__(self, y):
        if isinstance(self.val, Value):
            return self.val.__eq__(y)
        return self.val == y.val


class Number(Value):

    def between_times(self, x, y):
        if len(x) != 2:
            raise EngineError(
                "number.between takes two arguments, %d were given" % len(x))
        res = []
        lower = int(x[0].val)
        upper = int(x[1].val)
        ran = random.randint
        for _ in range(y):
            res.append(Value(ran(lower, upper)))
        return res

    def between(self, x):
        if len(x) < 2:
            raise EngineError(
                "number.between takes two arguments, 1 were given")
        return Value(random.randint(x[0].val, x[1].val))

    def upto_times(self, x, y):
        if len(x) != 2:
            raise EngineError("upto takes one argument, %d were given" % len(x))
        res = []
        upper = int(x[0].val)
        ran = random.randint
        for _ in range(y):
            res.append(Value(ran(0, upper)))
        return res

    def upto(self, x):
        return Value(random.randint(0, x[0].val))


class EngineError(Exception):
    pass


class Engine(AstVisitor):

    def __init__(self):
        AstVisitor.__init__(self)
        self.defaultrules = {"value": Value('', True), "number": Number()}
        self.grammars = {}
        self.times = 0
        random.seed()

    def visit_assignment(self, ast):
        self.grammars[ast.lhs.val] = ast.rhs
        return None
        # return ast.rhs.accept(self)
        # assignment no longer explicitly evaluates

    def visit_print(self, ast):
        times = int(ast.times.val)
        self.times = times
        ret = self.visit(ast.val)
        return ret

    def visit_literal(self, ast):
        if ast.val.type == Token.INTEGER:
            return [Value(int(ast.val.val), True)] * self.times
        else:
            return [Value(str(ast.val.val.replace("\"", "")), True)] * self.times

    def visit_variable(self, ast):
        if ast.val.val in self.defaultrules:
            return [self.defaultrules[ast.val.val]] * self.times
        elif ast.val.val in self.grammars:
            return self.visit(self.grammars[ast.val.val])
        else:
            raise EngineError("No such rule found '%s'!" % ast.val.val)

    def visit_method_call(self, ast):
        obj = self.visit(ast.obj)
        func = getattr(obj[0], ast.func.val, None)
        if not callable(func):
            raise EngineError("Invalid method name '%s'!" % ast.func)
        args = []
        arg_is_constant = True
        for arg in ast.args:
            temp = self.visit(arg)
            arg_is_constant = arg_is_constant and temp[0].is_constant
            args.append(temp)

        res = []
        argsorted = zip(*args)
        if obj[0].is_constant:
            if arg_is_constant:
                bakfunc = func
                func = getattr(obj[0], str(ast.func.val) + "_times", None)
                if not callable(func):
                    print("[Warning] Should've implemented '%s' on '%s'!"
                          % (str(ast.func.val) + "_times", obj[0].__class__))
                    func = bakfunc
                else:
                    return func(next(argsorted), self.times)
            for a in argsorted:
                res.append(func(a))
        else:
            for o, a in zip(obj, argsorted):
                res.append(getattr(o, ast.func.val)(a))
        return res
