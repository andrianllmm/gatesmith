from __future__ import annotations

import pytest

from gatesmith.core.ast import And, Not, Or, Var
from gatesmith.core.truth_table import build_truth_table, minterms_from_expression


def test_truth_table_and_minterms_are_deterministic() -> None:
    expr = Or((And((Var("a"), Var("b"))), Not(Var("c"))))
    minterms = minterms_from_expression(expr, ["a", "b", "c"])
    assert minterms == [0, 2, 4, 6, 7]

    rows = build_truth_table(expr, ["a", "b", "c"])
    assert [row.index for row in rows] == list(range(8))
    assert rows[0].output is True
    assert rows[1].output is False
