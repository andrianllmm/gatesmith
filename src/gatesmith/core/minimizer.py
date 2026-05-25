"""Quine–McCluskey minimization implementation with trace support.

This module performs boolean minimization for small numbers of
variables. It provides two public entry points:

- `minimize(minterms, variable_count)` — returns minimized implicants
- `minimize_with_trace(minterms, variable_count)` — also returns a
  `MinimizationTrace` containing intermediate rounds useful for
  rendering detailed diagnostics in the CLI.

The implementation is intentionally straightforward and documented to
make the algorithm steps clear for future contributors.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
from typing import NamedTuple

from gatesmith.core.implicants import (
    Implicant,
    minterms_to_implicants,
    bitcount,
    literal_count,
)


class ImplicantSnapshot(NamedTuple):
    """Represents a single implicant state captured during a QMC iteration.

    Stored in `QMCRound` for trace/debug output.
    """

    pattern: str  # Bit pattern (e.g. "10-1")
    covers: tuple[int, ...]  # Minterms covered by this implicant


class QMCRound(NamedTuple):
    """Represents one full iteration of Quine-McCluskey grouping and merging.

    Each round stores all implicants before merging for trace/debugging.
    """

    implicants: tuple[ImplicantSnapshot, ...]


@dataclass(frozen=True)
class MinimizationTrace:
    """Complete trace of the QMC minimization process.

    Includes:
    - all intermediate rounds (for visualization/debugging)
    - final prime implicants (cannot be merged further)
    - selected implicants (final minimized cover solution)
    """

    rounds: tuple[QMCRound, ...]
    prime_implicants: tuple[Implicant, ...]
    selected_implicants: tuple[Implicant, ...]


def minimize(minterms: list[int], variable_count: int) -> list[Implicant]:
    """Run QMC and return final minimized implicants (no trace)."""

    implicants, _trace = minimize_with_trace(minterms, variable_count)
    return implicants


def minimize_with_trace(
    minterms: list[int], variable_count: int
) -> tuple[list[Implicant], MinimizationTrace]:
    """Performs Boolean minimization using Quine-McCluskey.

    Returns:
    - minimized implicants
    - full trace of intermediate steps for debugging/inspection
    """

    # Edge case: no minterms means constant function = 0
    if not minterms:
        return [], MinimizationTrace(
            rounds=tuple(),
            prime_implicants=tuple(),
            selected_implicants=tuple(),
        )

    # Initial implicants are direct binary representations of minterms
    current_implicants = minterms_to_implicants(minterms, variable_count)

    # Stores implicants that can no longer be merged (final candidates before selection)
    prime_implicants: list[Implicant] = []

    # Stores full history of QMC iterations
    rounds: list[QMCRound] = []

    while current_implicants:
        # Group implicants by number of 1s in their pattern.
        # This enables QMC rule: only adjacent groups can be merged.
        groups: dict[int, list[Implicant]] = defaultdict(list)
        for implicant in current_implicants:
            groups[bitcount(implicant.pattern)].append(implicant)

        # Snapshot current state before merging (for trace/debug output)
        rounds.append(
            QMCRound(
                tuple(
                    ImplicantSnapshot(
                        imp.pattern,
                        tuple(sorted(imp.covers)),
                    )
                    for imp in current_implicants
                )
            )
        )

        # Stores results of merging for the next iteration
        # pattern -> set of minterms covered by merged implicant
        next_round: dict[str, set[int]] = {}

        # Tracks which implicants participated in a successful merge
        # Anything not used here becomes a prime implicant candidate
        used_patterns: set[str] = set()

        # Ordered group keys (number of 1s)
        # Ensures only adjacent groups are compared (QMC rule)
        ordered_counts = sorted(groups)

        # Attempt merges between adjacent groups
        for count in ordered_counts:
            left_group = groups[count]
            right_group = groups.get(count + 1, [])

            for left in left_group:
                for right in right_group:
                    # Try merging two implicants that differ by exactly one bit
                    merged = merge_implicants(left.pattern, right.pattern)
                    if merged is None:
                        continue

                    # Mark both implicants as merged participants
                    used_patterns.add(left.pattern)
                    used_patterns.add(right.pattern)

                    # Union of all minterms covered by both implicants
                    covers = set(left.covers) | set(right.covers)

                    # Store merged implicant for next iteration
                    next_round.setdefault(merged, set()).update(covers)

        # Any implicant not merged becomes a prime implicant
        for implicant in current_implicants:
            if implicant.pattern not in used_patterns:
                prime_implicants.append(implicant)

        # Prepare next iteration from merged implicants
        current_implicants = [
            Implicant(
                pattern=pattern,
                covers=frozenset(covers),
                literals=literal_count(pattern),
            )
            for pattern, covers in sorted(next_round.items())
        ]

    # Select final minimal set of prime implicants that cover all minterms
    selected = select_implicants(prime_implicants, set(minterms))

    # Build final trace object for debugging/CLI visualization
    trace = MinimizationTrace(
        rounds=tuple(rounds),
        prime_implicants=tuple(
            sorted(
                prime_implicants,
                key=lambda item: (item.pattern, sorted(item.covers)),
            )
        ),
        selected_implicants=tuple(selected),
    )

    return selected, trace


def merge_implicants(left: str, right: str) -> str | None:
    """Attempt to merge two implicant patterns.

    If the patterns differ by exactly one non-wildcard bit, return the
    merged pattern replacing that bit with '-' (don't-care). Otherwise
    return None.
    """

    differences = 0
    pattern: list[str] = []

    for left_char, right_char in zip(left, right, strict=True):
        # Same bit -> keep it
        if left_char == right_char:
            pattern.append(left_char)
            continue

        # If wildcard already exists, cannot safely merge
        if left_char == "-" or right_char == "-":
            return None

        differences += 1

        # More than one difference breaks QMC merge rule
        if differences > 1:
            return None

        # Replace differing bit with wildcard
        pattern.append("-")

    return "".join(pattern) if differences == 1 else None


def select_implicants(
    prime_implicants: list[Implicant],
    minterms: set[int],
) -> list[Implicant]:
    """Select a small covering set of prime implicants.

    Strategy:
    1. Choose essential implicants first (those that uniquely cover a minterm)
    2. Use a deterministic greedy heuristic for remaining uncovered minterms
    """

    remaining = set(minterms)
    selected: list[Implicant] = []

    # Map: minterm -> list of implicants that cover it
    coverage_map: dict[int, list[Implicant]] = defaultdict(list)
    for implicant in prime_implicants:
        for minterm in implicant.covers:
            coverage_map[minterm].append(implicant)

    # Identify essential implicants (only one coverer per minterm)
    essential: list[Implicant] = []

    for minterm in sorted(remaining):
        covering = coverage_map.get(minterm, [])
        if len(covering) == 1:
            implicant = covering[0]
            if implicant not in essential:
                essential.append(implicant)

    # Add all essential implicants first
    for implicant in sorted(essential, key=implicant_selection_key):
        if implicant not in selected:
            selected.append(implicant)
            remaining -= set(implicant.covers)

    # Greedy selection for remaining minterms
    while remaining:
        # Candidate implicants must cover at least one remaining minterm
        candidates = [
            implicant
            for implicant in prime_implicants
            if set(implicant.covers) & remaining
        ]

        if not candidates:
            break

        # Choose best candidate:
        # - maximize coverage of remaining minterms
        # - minimize literal count
        # - keep deterministic ordering
        candidate = min(
            candidates,
            key=lambda item: (
                -len(set(item.covers) & remaining),
                item.literals,
                item.pattern,
            ),
        )

        selected.append(candidate)
        remaining -= set(candidate.covers)

    return sorted(deduplicate_implicants(selected), key=implicant_selection_key)


def deduplicate_implicants(implicants: list[Implicant]) -> list[Implicant]:
    """Remove duplicate implicants while preserving first-seen order."""

    seen: set[tuple[str, tuple[int, ...]]] = set()
    result: list[Implicant] = []

    for implicant in implicants:
        key = (implicant.pattern, tuple(sorted(implicant.covers)))

        if key in seen:
            continue

        seen.add(key)
        result.append(implicant)

    return result


def implicant_selection_key(implicant: Implicant) -> tuple[int, str, tuple[int, ...]]:
    """Deterministic ordering key for implicants used in selection steps."""

    return (
        implicant.literals,
        implicant.pattern,
        tuple(sorted(implicant.covers)),
    )
