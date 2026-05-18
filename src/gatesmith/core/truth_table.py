"""Truth table construction."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from gatesmith.core.ast import Expression
from gatesmith.core.evaluator import evaluate


@dataclass(frozen=True)
class TruthTableRow:
    """A single row in the truth table.

    - `index` is the integer index (minterm number)
    - `assignment` is a mapping of variable -> bool
    - `output` is the evaluated function value for that assignment
    """

    index: int
    assignment: dict[str, bool]
    output: bool


def build_truth_table(expr: Expression, variables: list[str]) -> list[TruthTableRow]:
    """Enumerate all input combinations and evaluate `expr`.

    The returned list is ordered by minterm index (binary counting order)
    so it can be directly consumed by minimization and display code.
    """

    rows: list[TruthTableRow] = []
    for index, bits in enumerate(product([False, True], repeat=len(variables))):
        assignment = {
            variable: bit for variable, bit in zip(variables, bits, strict=True)
        }
        rows.append(
            TruthTableRow(
                index=index, assignment=assignment, output=evaluate(expr, assignment)
            )
        )
    return rows


def minterms_from_truth_table(rows: list[TruthTableRow]) -> list[int]:
    """Return the list of minterm indices where the function output is true."""

    return [row.index for row in rows if row.output]


def minterms_from_expression(expr: Expression, variables: list[str]) -> list[int]:
    """Convenience: build truth table and extract minterms in one call."""

    return minterms_from_truth_table(build_truth_table(expr, variables))
