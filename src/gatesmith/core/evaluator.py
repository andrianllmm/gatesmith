"""Expression and netlist evaluator utilities."""

from __future__ import annotations

from gatesmith.core.ast import And, Const, Expression, Not, Or, Var, Xor
from gatesmith.core.netlist import Netlist


def evaluate_ast(node: Expression, assignment: dict[str, bool]) -> bool:
    """Recursively evaluate AST under a variable assignment."""

    if isinstance(node, Var):
        return bool(assignment[node.name])

    if isinstance(node, Const):
        return bool(node.value)

    if isinstance(node, Not):
        return not evaluate_ast(node.node, assignment)

    if isinstance(node, And):
        return all(evaluate_ast(child, assignment) for child in node.nodes)

    if isinstance(node, Or):
        return any(evaluate_ast(child, assignment) for child in node.nodes)

    if isinstance(node, Xor):
        result = False
        for child in node.nodes:
            result ^= evaluate_ast(child, assignment)
        return result

    raise TypeError(f"Unsupported expression node: {type(node)!r}")


def evaluate_netlist(netlist: Netlist, assignment: dict[str, bool]) -> bool:
    """Evaluate a structural netlist under a variable assignment.

    Assumptions:
    - Gates are already in topological order (true for build_netlist)
    - All inputs are either:
        - primary inputs
        - previously computed wires
    """

    values: dict[str, bool] = {k: bool(v) for k, v in assignment.items()}

    def read(sig: str) -> bool:
        if sig == "1'b1":
            return True
        if sig == "1'b0":
            return False
        return values[sig]

    def write(sig: str, val: bool) -> None:
        values[sig] = val

    # Evaluate gates sequentially
    for gate in netlist.gates:
        inputs = [read(i) for i in gate.inputs]

        if gate.kind == "and":
            result = inputs[0]
            for v in inputs[1:]:
                result = result and v

        elif gate.kind == "or":
            result = inputs[0]
            for v in inputs[1:]:
                result = result or v

        elif gate.kind == "not":
            if len(inputs) != 1:
                raise ValueError("NOT gate must have exactly one input")
            result = not inputs[0]

        else:
            raise TypeError(f"Unsupported gate type: {gate.kind!r}")

        write(gate.output, result)

    # Final output resolution
    return read(netlist.output_driver)
