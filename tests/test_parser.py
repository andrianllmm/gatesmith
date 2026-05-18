from __future__ import annotations

import pytest

from gatesmith.core.ast import And, Assignment, Const, Not, Or, Var, Xor
from gatesmith.core.parser import ParseError, parse_assign


def test_parse_assign_respects_precedence() -> None:
    assignment = parse_assign("assign y = ~a & b ^ c | d;")

    assert assignment == Assignment(
        target="y",
        expr=Or(
            (
                Xor(
                    (
                        And((Not(Var("a")), Var("b"))),
                        Var("c"),
                    )
                ),
                Var("d"),
            )
        ),
    )


def test_parse_assign_with_mixed_whitespace() -> None:
    assignment = parse_assign("assign\tout = ( 1'b1&a ) ^   0 ;")

    assert assignment == Assignment(
        target="out",
        expr=Xor((And((Const(True), Var("a"))), Const(False))),
    )


def test_parse_assign_constants() -> None:
    assignment = parse_assign("assign out = 1'b1 & 0;")

    assert assignment == Assignment(
        target="out",
        expr=And((Const(True), Const(False))),
    )


def test_parse_assign_parentheses_override_precedence() -> None:
    assignment = parse_assign("assign out = (a & b) ^ c;")

    assert assignment == Assignment(
        target="out",
        expr=Xor((And((Var("a"), Var("b"))), Var("c"))),
    )


def test_parse_assign_rejects_invalid_input() -> None:
    with pytest.raises(ParseError):
        parse_assign("assign y = ;")
