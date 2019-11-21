from my_parser import AstVisitor
from scanner import Token
import random


class Value:

    UNIQUE_DICTIONARY = {}

    def __init__(self, v=''):
        if isinstance(v, Value):
            self.val = v.val
        else:
            self.val = v

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
        return Value(x[0])

    def one_of(self, l):
        idx = random.randrange(0, len(l), 1)
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
        return Value(random.randrange(x[0].val, x[1].val, 1))

    def upto(self, x):
        return Value(random.randrange(0, x[0].val, 1))


class EngineError(Exception):
    pass


class Engine(AstVisitor):

    def __init__(self):
        self.defaultrules = {"value": Value(), "number": Number()}
        self.grammars = {}
        self.objectstack = []

    def visit_assignment(self, ast):
        self.grammars[ast.lhs.val] = ast.rhs
        return None
        # return ast.rhs.accept(self)
        # assignment no longer explicitly evaluates

    def visit_print(self, ast):
        times = int(ast.times.val)
        ret = []
        for _ in range(times):
            ret.append(str(ast.val.accept(self)))
        return ret

    def visit_literal(self, ast):
        if ast.val.type == Token.INTEGER:
            return Value(int(ast.val.val))
        else:
            return Value(str(ast.val.val.replace("\"", "")))

    def visit_variable(self, ast):
        if ast.val.val in self.defaultrules:
            return self.defaultrules[ast.val.val]
        elif ast.val.val in self.grammars:
            return self.grammars[ast.val.val].accept(self)
        else:
            raise EngineError("No such rule found '%s'!" % ast.val.val)

    def visit_member_access(self, ast):
        obj = ast.object.accept(self)
        self.objectstack.append(obj)
        ret = ast.member.accept(self)
        self.objectstack.pop()
        return ret

    def visit_function_call(self, ast):
        args = []
        for arg in ast.args:
            args.append(arg.accept(self))
        obj = self.objectstack[-1]
        func = getattr(obj, ast.func.val, None)
        if callable(func):
            return func(args)
        else:
            raise EngineError("Invalid method name '%s'!" % ast.func)
