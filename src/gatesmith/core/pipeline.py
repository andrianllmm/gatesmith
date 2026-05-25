"""High-level synthesis pipeline orchestration."""

from __future__ import annotations

from dataclasses import dataclass

from gatesmith.core.ast import Assignment, collect_variables
from gatesmith.core.implicants import Implicant, minterms_to_implicants
from gatesmith.core.minimizer import MinimizationTrace, minimize_with_trace
from gatesmith.core.parser import parse_assign
from gatesmith.core.truth_table import (
    TruthTableRow,
    build_truth_table,
    minterms_from_truth_table,
)
from gatesmith.core.netlist import Netlist, build_netlist
from gatesmith.core.implicants import implicants_to_sop
from gatesmith.core.verilog import render_verilog


@dataclass(frozen=True)
class SynthesisResult:
    """Container for synthesis outputs and intermediate artifacts.

    Consumers (CLI, tests) can inspect `variables`, `truth_table`,
    `minterms`, `trace`, `implicants`, `sop` and `verilog`.
    """

    assignment: Assignment
    variables: list[str]
    truth_table: list[TruthTableRow]
    minterms: list[int]
    trace: MinimizationTrace | None
    implicants: list[Implicant]
    sop: str
    netlist: Netlist
    verilog: str


def synthesize(source: str, no_opt: bool = False) -> SynthesisResult:
    """Run the full synthesis pipeline for a single `assign` statement.

    Steps:
    1. Parse source into an AST
    2. Collect variables and build the truth table
    3. Extract minterms and minimize with QMC
    4. Convert implicants to SOP and netlist
    5. Render structural Verilog
    """

    assignment = parse_assign(source)

    variables = collect_variables(assignment.expr)

    truth_table = build_truth_table(assignment.expr, variables)

    minterms = minterms_from_truth_table(truth_table)

    implicants: list[Implicant] = []
    trace: MinimizationTrace | None = None
    if no_opt:
        implicants = minterms_to_implicants(minterms, len(variables))
    else:
        implicants, trace = minimize_with_trace(minterms, len(variables))

    sop = implicants_to_sop(implicants, variables)

    netlist = build_netlist(
        module_name=assignment.target,
        output_name=assignment.target,
        variables=variables,
        implicants=implicants,
    )

    verilog = render_verilog(netlist)

    return SynthesisResult(
        assignment=assignment,
        variables=variables,
        truth_table=truth_table,
        minterms=minterms,
        trace=trace,
        implicants=implicants,
        sop=sop,
        netlist=netlist,
        verilog=verilog,
    )
