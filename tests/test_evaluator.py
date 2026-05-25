from gatesmith.core.ast import And, Const, Not, Or, Var, Xor
from gatesmith.core.evaluator import evaluate_ast


def test_evaluate_mixed_ast() -> None:
    # Expression: (~a & b) ^ (c | False)
    expr = Xor(
        (
            And(
                (
                    Not(Var("a")),
                    Var("b"),
                )
            ),
            Or(
                (
                    Var("c"),
                    Const(False),
                )
            ),
        )
    )

    assignment = {
        "a": True,
        "b": True,
        "c": False,
    }

    # Step-by-step:
    # ~a = False
    # (~a & b) = False & True = False
    # (c | False) = False | False = False
    # XOR = False ^ False = False

    assert evaluate_ast(expr, assignment) is False
