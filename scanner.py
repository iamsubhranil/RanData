class Token:
    # types
    IDENTIFIER = 0
    STRING = 1
    EQUALS = 2
    INTEGER = 3
    DOT = 4
    BRACE_OPEN = 5
    BRACE_CLOSE = 6
    KEYWORD_PRINT = 7
    COMMA = 8
    EOF = 9
    ERROR = 10
    KEYWORDS = {"print": KEYWORD_PRINT}

    def __init__(self, t, v):
        self.type = t
        self.val = v

    def __repr__(self):
        return str(self.val)


class ScanError(Exception):
    pass


class Scanner:

    SYMBOLS = {'.': Token.DOT,
               '(': Token.BRACE_OPEN,
               ')': Token.BRACE_CLOSE,
               '=': Token.EQUALS,
               ',': Token.COMMA}

    def __init__(self, source):
        self.pos = -1
        self.start = 0
        self.length = len(source)
        self.source = source

    def advance(self):
        self.pos += 1

    def match(self, c):
        if self.peek() == c:
            self.advance()
            return True
        return False

    def is_at_end(self):
        return self.pos >= (self.length - 1)

    def make_token(self, typ):
        part = self.source[self.start:self.pos + 1]
        if typ == Token.IDENTIFIER and part in Token.KEYWORDS:
            typ = Token.KEYWORDS[part]
        return Token(typ, part)

    def peek(self):
        if self.pos < self.length - 1:
            return self.source[self.pos + 1]
        return self.source[self.pos]

    def number(self):
        while(self.peek().isdigit()):
            self.advance()
        return self.make_token(Token.INTEGER)

    def identifier(self):
        while(self.peek().isalpha() or self.peek() == '_'):
            self.advance()
        return self.make_token(Token.IDENTIFIER)

    def string(self):
        while(self.peek() != '"' and not self.is_at_end()):
            self.advance()
        if not self.is_at_end():
            self.advance()
        else:
            raise ScanError("String not terminated properly!")
        return self.make_token(Token.STRING)

    def scan_next(self):
        self.advance()
        if self.pos == self.length:
            return self.make_token(Token.EOF)
        self.start = self.pos
        c = self.source[self.start]
        if(c.isalpha()):
            return self.identifier()
        elif(c.isdigit()):
            return self.number()
        elif(c == '"'):
            return self.string()
        elif(c in self.SYMBOLS):
            return self.make_token(self.SYMBOLS[c])
        elif(c == ' ' or c == '\n' or c == '\r' or c == '\t'):
            return self.scan_next()
        else:
            raise ScanError("Undefined symbol '%s'" % c)

    def scan_all(self):
        tokens = []
        while(self.pos != self.length):
            tokens.append(self.scan_next())
        return tokens
