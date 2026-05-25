"""Utilities and lightweight model for implicants used by QMC."""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet


@dataclass(frozen=True)
class Implicant:
    """Immutable representation of a product term (implicant).

    - `pattern`: bitstring with '-' for don't-cares
    - `covers`: set of minterm indices covered
    - `literals`: number of asserted literals (used to prefer simpler terms)
    """

    pattern: str
    covers: FrozenSet[int]
    literals: int


def minterms_to_implicants(minterms: list[int], variable_count: int) -> list[Implicant]:
    """Convert a list of minterms into a list of `Implicant` objects."""
    return [
        minterm_to_implicant(minterm, variable_count)
        for minterm in sorted(set(minterms))
    ]


def minterm_to_implicant(minterm: int, variable_count: int) -> Implicant:
    """Convert a minterm index into its binary implicant form.

    Example: minterm=3, vars=4 -> "0011"
    """

    pattern = "" if variable_count == 0 else format(minterm, f"0{variable_count}b")

    return Implicant(
        pattern=pattern,
        covers=frozenset({minterm}),
        literals=literal_count(pattern),
    )


def bitcount(pattern: str) -> int:
    """Count the number of '1' bits in `pattern`.

    Used to group implicants by the number of set bits during QMC.
    """

    return sum(1 for char in pattern if char == "1")


def literal_count(pattern: str) -> int:
    """Return the count of non-don't-care characters (literals) in `pattern`.

    '-' counts as a don't-care and is not considered a literal.
    """

    return sum(1 for char in pattern if char != "-")


def implicants_to_sop(implicants: list[Implicant], variables: list[str]) -> str:
    """Render a list of implicants as a Sum-Of-Products expression string.

    Returns a Verilog-like textual expression using `~` for negation and
    `&`/`|` for conjunction/disjunction.
    Special-case: empty implicant
    list -> `1'b0`.
    """

    if not implicants:
        return "1'b0"

    terms: list[str] = []
    for implicant in implicants:
        literals: list[str] = []
        for variable, bit in zip(variables, implicant.pattern, strict=True):
            if bit == "1":
                literals.append(variable)
            elif bit == "0":
                literals.append(f"~{variable}")
        if not literals:
            terms.append("1'b1")
        elif len(literals) == 1:
            terms.append(literals[0])
        else:
            terms.append("(" + " & ".join(literals) + ")")
    if len(terms) == 1:
        return terms[0]
    return " | ".join(terms)


def implicant_to_literal(implicant: Implicant, variables: list[str]) -> str:
    """Convert a single implicant pattern to a human-readable literal.

    Example: pattern "--01" with variables [A,B,C,D] -> "~C & D".

    Returns `1'b1` for an implicant that has no literals.
    """

    pattern = implicant.pattern
    if not pattern:
        return "1'b1"
    parts: list[str] = []
    for var, ch in zip(variables, pattern, strict=True):
        if ch == "1":
            parts.append(var)
        elif ch == "0":
            parts.append(f"~{var}")
        else:
            # don't include '-' (don't care)
            continue
    if not parts:
        return "1'b1"
    return " & ".join(parts)
