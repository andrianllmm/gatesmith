"""Abstract syntax tree (AST) definitions for a small Verilog subset.

This module defines the minimal set of expression nodes used by the project:
variables, constants, and the boolean operators (NOT, AND, OR, XOR).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Var:
    """A named variable (signal) in the expression."""

    name: str


@dataclass(frozen=True)
class Const:
    """A boolean constant (True/False)."""

    value: bool


@dataclass(frozen=True)
class Not:
    """Logical NOT applied to a single child node."""

    node: "Expression"


@dataclass(frozen=True)
class And:
    """Logical AND over a tuple of child expressions."""

    nodes: tuple["Expression", ...]


@dataclass(frozen=True)
class Or:
    """Logical OR over a tuple of child expressions."""

    nodes: tuple["Expression", ...]


@dataclass(frozen=True)
class Xor:
    """Logical XOR over a tuple of child expressions."""

    nodes: tuple["Expression", ...]


Expression = Var | Const | Not | And | Or | Xor


@dataclass(frozen=True)
class Assignment:
    """Represents `assign <target> = <expr>;` parsed from source."""

    target: str
    expr: Expression


def collect_variables(node: Expression) -> list[str]:
    """Return a sorted list of unique variable names referenced in `node`.

    Traverses the expression tree and collects `Var.name`. The result is
    sorted to guarantee deterministic ordering for downstream steps
    (truth table construction, netlist, etc.).
    """

    names: set[str] = set()

    def walk(current: Expression) -> None:
        # Leaf: variable
        if isinstance(current, Var):
            names.add(current.name)
            return
        # Leaf: constant
        if isinstance(current, Const):
            return
        # Unary operator
        if isinstance(current, Not):
            walk(current.node)
            return
        # N-ary operators (And/Or/Xor) expose `.nodes`
        for child in current.nodes:
            walk(child)

    walk(node)
    return sorted(names)
