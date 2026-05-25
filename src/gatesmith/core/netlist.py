"""Build a simple structural netlist from implicants.

This module translates a list of implicants (product terms) into a
flat netlist composed of `and`, `or`, and `not` gate instances.

The translation rules are:
 - Each implicant becomes a product (AND) of its literals.
 - Literals that are inverted (`0`) are implemented with a shared NOT
   gate per input signal (inversion cache).
 - Product terms are combined with OR gates to form the final output.
 - Special cases for constant functions (no implicants -> constant 0,
   implicant with no literals -> constant 1) are handled explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass

from gatesmith.core.implicants import Implicant


@dataclass(frozen=True)
class GateInstance:
    """Represents a single gate instance in the netlist.

    - `kind` is the gate type string (e.g. 'and', 'or', 'not')
    - `name` is a generated instance name (deterministic)
    - `output` is the output wire name
    - `inputs` is a tuple of input wire names
    """

    kind: str
    name: str
    output: str
    inputs: tuple[str, ...]


@dataclass(frozen=True)
class Netlist:
    """Immutable container holding the synthesized netlist.

    The `output_driver` is either a wire name or a Verilog constant
    like "1'b0" / "1'b1".
    """

    module_name: str
    input_ports: tuple[str, ...]
    output_port: str
    wire_names: tuple[str, ...]
    gates: tuple[GateInstance, ...]
    output_driver: str


def build_netlist(
    module_name: str,
    output_name: str,
    variables: list[str],
    implicants: list[Implicant],
) -> Netlist:
    """Construct a `Netlist` from input variable names and implicants.

    The function generates deterministic internal wire and gate names
    so the resulting Verilog is stable across runs.
    """

    gates: list[GateInstance] = []
    wire_names: list[str] = []
    inversion_cache: dict[str, str] = {}
    not_counter = 0
    temp_counter = 0
    gate_counter = 0

    def new_wire(prefix: str = "t") -> str:
        nonlocal not_counter, temp_counter
        if prefix == "n":
            wire = f"n{not_counter}"
            not_counter += 1
        else:
            wire = f"t{temp_counter}"
            temp_counter += 1
        wire_names.append(wire)
        return wire

    def new_gate_name() -> str:
        nonlocal gate_counter
        name = f"u{gate_counter}"
        gate_counter += 1
        return name

    def literal_wire(variable: str, bit: str) -> str:
        """Return the wire name that implements `variable` asserted as `bit`.

        If `bit` is '1' the original variable wire is used. If `bit` is
        '0' a shared inverter is created and cached.
        """

        # Use original wire if true form
        if bit == "1":
            return variable

        # Check for don't-care
        if bit != "0":
            raise ValueError(f"Unsupported implicant bit: {bit!r}")

        # Create a new wire and cache it if negated form
        if variable not in inversion_cache:
            output_wire = new_wire("n")
            inversion_cache[variable] = output_wire
            gates.append(
                GateInstance(
                    kind="not",
                    name=new_gate_name(),
                    output=output_wire,
                    inputs=(variable,),
                )
            )
        return inversion_cache[variable]

    # Case: No implicants
    # Constant 0 function (no implicants) -> drive with literal 0
    if not implicants:
        return Netlist(
            module_name=module_name,
            input_ports=tuple(variables),
            output_port=output_name,
            wire_names=tuple(),
            gates=tuple(),
            output_driver="1'b0",
        )

    # Stores product terms
    product_wires: list[str] = []
    for implicant in implicants:
        # Get literals
        literals: list[str] = []
        for variable, bit in zip(variables, implicant.pattern, strict=True):
            # Skip don't-cares
            if bit == "-":
                continue
            # Create a new wire for each literal
            literals.append(literal_wire(variable, bit))

        # Empty literals => product term is constant 1
        if not literals:
            product_wires.append("1'b1")
            continue

        # Single-literal term => use the literal directly
        if len(literals) == 1:
            product_wires.append(literals[0])
            continue

        # Build an AND tree for multi-literal terms
        current = literals[0]
        for literal in literals[1:]:
            combined = new_wire()
            gates.append(
                GateInstance(
                    kind="and",
                    name=new_gate_name(),
                    output=combined,
                    inputs=(current, literal),
                )
            )
            current = combined
        product_wires.append(current)

    # Combine product terms with OR gates
    output_driver = product_wires[0]
    if len(product_wires) > 1:
        current = product_wires[0]
        for term in product_wires[1:]:
            combined = new_wire()
            gates.append(
                GateInstance(
                    kind="or",
                    name=new_gate_name(),
                    output=combined,
                    inputs=(current, term),
                )
            )
            current = combined
        output_driver = current

    # Return the netlist
    return Netlist(
        module_name=module_name,
        input_ports=tuple(variables),
        output_port=output_name,
        wire_names=tuple(wire_names),
        gates=tuple(gates),
        output_driver=output_driver,
    )
