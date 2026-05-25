"""Equivalence verification between AST, truth table, and netlist."""

from __future__ import annotations

from itertools import product

from gatesmith.core.ast import Expression
from gatesmith.core.pipeline import SynthesisResult
from gatesmith.core.truth_table import TruthTableRow
from gatesmith.core.netlist import Netlist
from gatesmith.core.evaluator import evaluate_ast, evaluate_netlist


def _all_input_vectors(variables: list[str]):
    """Generate all boolean assignments in lexicographic order."""
    return list(product([False, True], repeat=len(variables)))


def verify_ast_vs_netlist(
    expr: Expression,
    netlist: Netlist,
    variables: list[str],
) -> bool:
    """Check functional equivalence between AST and netlist."""

    for bits in _all_input_vectors(variables):
        assignment = dict(zip(variables, bits))

        ast_out = evaluate_ast(expr, assignment)
        net_out = evaluate_netlist(netlist, assignment)

        if ast_out != net_out:
            return False

    return True


def verify_truth_table_vs_netlist(
    truth_table: list[TruthTableRow],
    netlist: Netlist,
) -> bool:
    """Check netlist output matches precomputed truth table."""

    for row in truth_table:
        net_out = evaluate_netlist(netlist, row.assignment)

        if bool(row.output) != bool(net_out):
            return False

    return True


def verify_synthesis_result(result: SynthesisResult) -> bool:
    """Verify full pipeline correctness.

    Expects:
    - result.assignment.expr
    - result.variables
    - result.truth_table
    - result.netlist (must exist for verification)
    """

    expr = result.assignment.expr
    variables = result.variables

    # AST vs Netlist (primary check)
    ast_ok = verify_ast_vs_netlist(expr, result.netlist, variables)

    # Truth table vs Netlist (secondary consistency check)
    tt_ok = verify_truth_table_vs_netlist(result.truth_table, result.netlist)

    return ast_ok and tt_ok
