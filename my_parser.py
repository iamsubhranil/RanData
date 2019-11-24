from abc import ABC, abstractmethod
from scanner import Scanner, Token


class Ast:

    def accept(self, visitor):
        return visitor.visit(self)


class AssignmentStatement(Ast):

    def __init__(self, lhs, equal, rhs):
        self.lhs = lhs
        self.equal = equal
        self.rhs = rhs


class MethodCallExpression(Ast):

    def __init__(self, obj, func, args):
        self.obj = obj
        self.func = func
        self.args = tuple(args)


class LiteralExpression(Ast):

    def __init__(self, val):
        self.val = val

    def __repr__(self):
        return "LiteralExpression(" + str(self.val) + ")"


class VariableExpression(Ast):

    def __init__(self, val):
        self.val = val

    def __repr__(self):
        return "LiteralExpression(" + str(self.val) + ")"


class PrintStatement(Ast):

    def __init__(self, times, val):
        self.times = times
        self.val = val


class VisitorError(Exception):
    pass


class AstVisitor(ABC):

    VISITOR_METHODS = {}

    def __init__(self):
        self.VISITOR_METHODS = {LiteralExpression: self.visit_literal,
                                MethodCallExpression: self.visit_method_call,
                                AssignmentStatement: self.visit_assignment,
                                VariableExpression: self.visit_variable,
                                PrintStatement: self.visit_print,
                                Ast: self.visit_ast}

    def visit(self, ast):
        if ast.__class__ in self.VISITOR_METHODS:
            return self.VISITOR_METHODS[ast.__class__](ast)
        else:
            if len(self.VISITOR_METHODS) == 0:
                raise VisitorError(
                    "Initialize the inherited visitor with AstVisitor.__init__(self)!")
            else:
                raise VisitorError(
                    "Visitor not implemented for type '%s'" % ast.__class__)

    def visit_optional(self, ast, optional=None):  # allow to pass optional data
        if ast.__class__ in self.VISITOR_METHODS:
            return self.VISITOR_METHODS[ast.__class__](ast, optional)
        else:
            if len(self.VISITOR_METHODS) == 0:
                raise VisitorError(
                    "Initialize the inherited visitor with AstVisitor.__init__(self)!")
            else:
                raise VisitorError(
                    "Visitor not implemented for type '%s'" % ast.__class__)

    def visit_ast(self, ast):
        pass

    @abstractmethod
    def visit_assignment(self, ast):
        pass

    @abstractmethod
    def visit_literal(self, ast):
        pass

    @abstractmethod
    def visit_method_call(self, ast):
        pass

    @abstractmethod
    def visit_variable(self, ast):
        pass

    @abstractmethod
    def visit_print(self, ast):
        pass


class PrettyPrinter(AstVisitor):

    def __init__(self):
        AstVisitor.__init__(self)

    def visit_assignment(self, ast):
        print("%s = " % ast.lhs, end='')
        ast.rhs.accept(self)

    def visit_literal(self, ast):
        print(ast.val, end='')

    def visit_variable(self, ast):
        print(ast.val, end='')

    def visit_method_call(self, ast):
        ast.obj.accept(self)
        print("." + str(ast.func) + "(", end='')
        if len(ast.args) > 0:
            ast.args[0].accept(self)
            for arg in ast.args[1:]:
                print(", ", end='')
                arg.accept(self)
        print(")", end='')

    def visit_print(self, ast):
        print("print(", end='')
        ast.times.accept(self)
        print(",", end='')
        ast.val.accept(self)
        print(")", end='')


class ParseError(Exception):
    pass


class Parser:

    def __init__(self, scanner):
        self.scanner = scanner
        self.STATEMENT_RULES = {Token.IDENTIFIER: self.parse_assignment,
                                Token.KEYWORD_PRINT: self.parse_print}

    def consume(self, typ, errorstr):
        token = self.scanner.scan_next()
        if token.type != typ:
            error = errorstr
            if token.type == Token.EOF:
                error += "\nUnexpected end of file!"
            else:
                error += " Received : '%s'!" % token
            raise ParseError(error)
        return token

    def parse_all(self):
        statements = []
        while not self.scanner.is_at_end():
            statements.append(self.parse_next_statement())
        return statements

    def parse_next_statement(self):
        token = self.scanner.scan_next()
        if token.type == Token.EOF:
            return Ast()
        elif token.type in self.STATEMENT_RULES:
            return self.STATEMENT_RULES[token.type](token)
        else:
            raise ParseError("Invalid start of statement '%s'!" % token.val)

    def parse_print(self, token):
        self.consume(Token.BRACE_OPEN, "Expected '(' after print!")
        times = self.consume(
            Token.INTEGER, "Expected integer as first argument of print!")
        self.consume(Token.COMMA, "Expected ',' after first argument!")
        val = self.parse_expression()
        self.consume(Token.BRACE_CLOSE, "Expected ')' at the end of print!")
        return PrintStatement(times, val)

    def parse_assignment(self, token):
        equals = self.consume(Token.EQUALS, "Expected '=' after rule name!")
        expr = self.parse_expression()
        return AssignmentStatement(token, equals, expr)

    def parse_expression(self):
        return self.parse_method_call()

    def parse_primary(self):
        token = self.scanner.scan_next()
        if token.type == Token.INTEGER or token.type == Token.STRING:
            return LiteralExpression(token)
        elif token.type == Token.IDENTIFIER:
            return VariableExpression(token)
        else:
            raise ParseError("Invalid token '%s'", token)

    def parse_method_call(self):
        left = self.parse_primary()
        while self.scanner.match("."):
            name = self.consume(Token.IDENTIFIER, "Expected function name!")
            self.consume(Token.BRACE_OPEN,
                         "Expected brace open before function call!")
            args = []
            if not self.scanner.match(")"):

                args.append(self.parse_expression())

                while not self.scanner.match(")"):
                    self.consume(
                        Token.COMMA, "Expected ',' after argument!")
                    args.append(self.parse_expression())
            left = MethodCallExpression(left, name, args)
        return left
