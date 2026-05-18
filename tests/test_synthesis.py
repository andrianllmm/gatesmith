from __future__ import annotations

import pytest

from gatesmith.core.implicants import Implicant
from gatesmith.core.netlist import build_netlist
from gatesmith.core.implicants import implicants_to_sop
from gatesmith.core.verilog import render_verilog


def test_verilog_rendering_are_structural() -> None:
    implicants = [
        Implicant(pattern="--0", covers=frozenset({0, 2, 4, 6}), literals=1),
        Implicant(pattern="11-", covers=frozenset({6, 7}), literals=2),
    ]
    variables = ["a", "b", "c"]

    assert implicants_to_sop(implicants, variables) == "~c | (a & b)"

    netlist = build_netlist(
        module_name="y", output_name="y", variables=variables, implicants=implicants
    )
    verilog = render_verilog(netlist)

    assert "module y(input a, input b, input c, output y);" in verilog
    assert "not u0 (n0, c);" in verilog
    assert "and u1 (t0, a, b);" in verilog
    assert "or u2 (t1, n0, t0);" in verilog
    assert "assign y = t1;" in verilog


def test_netlist_caches_inverters() -> None:
    implicants = [
        Implicant(pattern="0-", covers=frozenset({0, 1}), literals=1),
        Implicant(pattern="01", covers=frozenset({1}), literals=2),
    ]
    netlist = build_netlist(
        module_name="y", output_name="y", variables=["a", "b"], implicants=implicants
    )
    assert sum(gate.kind == "not" for gate in netlist.gates) == 1
