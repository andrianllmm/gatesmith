"""Render a `Netlist` as structural Verilog source."""

from __future__ import annotations

from gatesmith.core.netlist import Netlist


def render_verilog(netlist: Netlist) -> str:
    """Return Verilog source text for `netlist`.

    Returns a small module with deterministic formatting
    that corresponds directly to the `Netlist` structure.

    The output uses primitive gate instantiations (`and`, `or`, `not`)
    and a final `assign` to drive the module output.
    """

    # Stores lines of code
    lines: list[str] = []

    # Header ports (input and output)
    header_ports = ", ".join(
        [
            *(f"input {name}" for name in netlist.input_ports),
            f"output {netlist.output_port}",
        ]
    )

    # Module declaration
    lines.append(f"module {netlist.module_name}({header_ports});")

    # Wire declarations
    if netlist.wire_names:
        lines.append(f"  wire {', '.join(netlist.wire_names)};")

    # Gate instantiations
    for gate in netlist.gates:
        joined_inputs = ", ".join((gate.output, *gate.inputs))
        lines.append(f"  {gate.kind} {gate.name} ({joined_inputs});")

    # Final assignment
    lines.append(f"  assign {netlist.output_port} = {netlist.output_driver};")

    # Module footer
    lines.append("endmodule")

    # Combine into a single string
    return "\n".join(lines) + "\n"
