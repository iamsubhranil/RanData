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

    def is_str(self):
        return isinstance(self.val, str)

    def normalize(self):
        if self.is_str():
            self.val.replace("'", "''")

    def append(self, y):
        ret = str(self.val)
        for i in y:
            ret += str(i)
        return Value(ret)

    def constant(self, x):
        return Value(x[0], True)

    def one_of(self, l):
        idx = random.randint(0, len(l) - 1)
        return Value(l[idx])

    def lower(self, l):
        return Value(str(self.val).lower())

    def one_of_unique(self, l):
        origlist = l
        while len(origlist) == 1 and isinstance(origlist[0], Value):
            origlist = origlist[0].val
        l = origlist
        tup = tuple(l)
        if tup in self.UNIQUE_DICTIONARY:
            if len(self.UNIQUE_DICTIONARY[tup]) == len(tup):
                raise EngineError("No more unique values to generate!")
            v = self.one_of(l)
            while v in self.UNIQUE_DICTIONARY[tup]:
                v = self.one_of(l)
            self.UNIQUE_DICTIONARY[tup].append(v)
            return v
        else:
            v = self.one_of(l)
            self.UNIQUE_DICTIONARY[tup] = [v]
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

    def between(self, x):
        if len(x) < 2:
            raise EngineError(
                "number.between takes two arguments, 1 were given")
        return Value(random.randint(x[0].val, x[1].val))

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
        for arg in ast.args:
            temp = self.visit(arg)
            args.append(temp)

        res = []
        argsorted = zip(*args)
        if obj[0].is_constant:
            for a in argsorted:
                res.append(func(a))
        else:
            for o, a in zip(obj, argsorted):
                res.append(getattr(o, ast.func.val)(a))
        return res
