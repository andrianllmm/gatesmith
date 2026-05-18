"""Simple recursive-descent parser for a restricted Verilog `assign`."""

from __future__ import annotations

from dataclasses import dataclass

from gatesmith.core.ast import And, Assignment, Const, Expression, Not, Or, Var, Xor


@dataclass(frozen=True)
class Token:
    """A token."""

    kind: str
    value: str


class ParseError(ValueError):
    """Raised when the input cannot be parsed."""


# Single-character tokens mapping
SINGLE_CHAR_TOKENS = {
    "=": "EQUALS",
    ";": "SEMICOLON",
    "(": "LPAREN",
    ")": "RPAREN",
    "~": "NOT",
    "!": "NOT",
    "&": "AND",
    "^": "XOR",
    "|": "OR",
}


def tokenize(source: str) -> list[Token]:
    """Convert the raw source string into a list of tokens.

    The tokenizer recognizes:
    - reserved word `assign`,
    - bit constants `1'b0` and `1'b1`
    - identifiers
    - digits 0/1
    - operators listed in `SINGLE_CHAR_TOKENS`.
    """

    tokens: list[Token] = []
    index = 0
    while index < len(source):
        char = source[index]

        # skip whitespace
        if char.isspace():
            index += 1
            continue

        # reserved word `assign` must be a standalone identifier
        if source.startswith("assign", index) and _is_boundary(source, index + 6):
            tokens.append(Token("ASSIGN", "assign"))
            index += 6
            continue

        # accept Verilog-style constants written as 1'b0 / 1'b1
        if source.startswith("1'b0", index):
            tokens.append(Token("CONST", "0"))
            index += 4
            continue
        if source.startswith("1'b1", index):
            tokens.append(Token("CONST", "1"))
            index += 4
            continue

        # single-character tokens
        if char in SINGLE_CHAR_TOKENS:
            tokens.append(Token(SINGLE_CHAR_TOKENS[char], char))
            index += 1
            continue

        # bare digit constants (0/1) are also accepted
        if char.isdigit():
            if char not in {"0", "1"}:
                raise ParseError(f"Unsupported constant near position {index}: {char}")
            tokens.append(Token("CONST", char))
            index += 1
            continue

        # identifiers: [A-Za-z_][A-Za-z0-9_]*
        if char.isalpha() or char == "_":
            end = index + 1
            while end < len(source) and (source[end].isalnum() or source[end] == "_"):
                end += 1
            value = source[index:end]
            tokens.append(Token("IDENT", value))
            index = end
            continue

        # any other character is unexpected (helps diagnose malformed files)
        raise ParseError(f"Unexpected character at position {index}: {char!r}")

    # End of input
    tokens.append(Token("EOF", ""))

    return tokens


def parse_assign(source: str) -> Assignment:
    """Parse `source` and return an `Assignment` AST.

    Raises `ParseError` on invalid input.
    """

    parser = Parser(tokenize(source))
    assignment = parser.parse_assignment()
    parser.expect("EOF")
    return assignment


def _is_boundary(source: str, index: int) -> bool:
    # Checks whether `index` is at an identifier boundary (end of word).
    return index >= len(source) or not (source[index].isalnum() or source[index] == "_")


class Parser:
    """Recursive-descent parser implementing operator precedence.

    Grammar (informal):
      assignment ::= 'assign' IDENT '=' expr ';'
      expr       ::= or
      or         ::= xor ('|' xor)*
      xor        ::= and ('^' and)*
      and        ::= not ('&' not)*
      not        ::= ('~' | '!') not | primary
      primary    ::= IDENT | CONST | '(' expr ')'
    """

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.index = 0

    def current(self) -> Token:
        return self.tokens[self.index]

    def advance(self) -> Token:
        token = self.current()
        self.index += 1
        return token

    def expect(self, kind: str) -> Token:
        token = self.current()
        if token.kind != kind:
            raise ParseError(f"Expected {kind}, found {token.kind or token.value!r}")
        return self.advance()

    def parse_assignment(self) -> Assignment:
        self.expect("ASSIGN")
        target = self.expect("IDENT").value
        self.expect("EQUALS")
        expr = self.parse_or()
        self.expect("SEMICOLON")
        return Assignment(target=target, expr=expr)

    def parse_or(self) -> Expression:
        nodes = [self.parse_xor()]
        while self.current().kind == "OR":
            self.advance()
            nodes.append(self.parse_xor())
        return nodes[0] if len(nodes) == 1 else Or(tuple(nodes))

    def parse_xor(self) -> Expression:
        nodes = [self.parse_and()]
        while self.current().kind == "XOR":
            self.advance()
            nodes.append(self.parse_and())
        return nodes[0] if len(nodes) == 1 else Xor(tuple(nodes))

    def parse_and(self) -> Expression:
        nodes = [self.parse_not()]
        while self.current().kind == "AND":
            self.advance()
            nodes.append(self.parse_not())
        return nodes[0] if len(nodes) == 1 else And(tuple(nodes))

    def parse_not(self) -> Expression:
        if self.current().kind == "NOT":
            self.advance()
            return Not(self.parse_not())
        return self.parse_primary()

    def parse_primary(self) -> Expression:
        token = self.current()
        if token.kind == "IDENT":
            self.advance()
            return Var(token.value)
        if token.kind == "CONST":
            self.advance()
            return Const(token.value == "1")
        if token.kind == "LPAREN":
            self.advance()
            expr = self.parse_or()
            self.expect("RPAREN")
            return expr
        raise ParseError(f"Unexpected token {token.kind!r}")
