from src.ast import *
from src.lexer import tokenize


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, token_type):
        token = self.peek()

        if token and token[0] == token_type:
            self.pos += 1
            return token[1]

        raise SyntaxError(f"Expected {token_type}, got {token}")

    # parsing functions

    def parse_implies(self):
        left = self.parse_or()

        if self.peek() and self.peek()[0] == "IMPLIES":
            self.consume("IMPLIES")
            right = self.parse_implies()
            return Implies(left, right)

        return left

    def parse_or(self):
        left = self.parse_and()

        while self.peek() and self.peek()[0] == "OR":
            self.consume("OR")
            right = self.parse_and()
            left = Or(left, right)

        return left

    def parse_and(self):
        left = self.parse_not()

        while self.peek() and self.peek()[0] == "AND":
            self.consume("AND")
            right = self.parse_not()
            left = And(left, right)

        return left

    def parse_not(self):
        if self.peek() and self.peek()[0] == "NOT":
            self.consume("NOT")
            return Not(self.parse_not())

        return self.parse_atom()

    def parse_atom(self):
        token = self.peek()

        if token is None:
            raise SyntaxError("Unexpected end of formula")

        if token[0] == "LPAREN":
            self.consume("LPAREN")
            formula = self.parse_implies()
            self.consume("RPAREN")
            return formula

        if token[0] in ("FORALL", "EXISTS"):
            return self.parse_quantifier()

        if token[0] == "IDENT":
            return self.parse_predicate()

        raise SyntaxError(f"Invalid formula near token: {token}")

    def parse_quantifier(self):
        token = self.peek()

        if token[0] == "FORALL":
            self.consume("FORALL")
            var = self.consume("IDENT")
            self.consume("DOT")
            body = self.parse_not()

            return Forall(var, body)

        if token[0] == "EXISTS":
            self.consume("EXISTS")
            var = self.consume("IDENT")
            self.consume("DOT")
            body = self.parse_not()

            return Exists(var, body)

        raise SyntaxError(f"Expected quantifier, got {token}")

    def parse_predicate(self):
        name = self.consume("IDENT")

        self.consume("LPAREN")

        terms = []
        terms.append(self.parse_term())

        while self.peek() and self.peek()[0] == "COMMA":
            self.consume("COMMA")
            terms.append(self.parse_term())

        self.consume("RPAREN")

        return Predicate(name, tuple(terms))

    def parse_term(self):
        name = self.consume("IDENT")

        # Treat x, y, z as variables.
        # Everything else is treated as a constant.
        if name in ["x", "y", "z"]:
            return Var(name)

        return Const(name)

def parse(text: str):
    tokens = tokenize(text)
    parser = Parser(tokens)

    formula = parser.parse_implies()

    if parser.peek() is not None:
        raise SyntaxError(f"Unexpected token after formula: {parser.peek()}")

    return formula