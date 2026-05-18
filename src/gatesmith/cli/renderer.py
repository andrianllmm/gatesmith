from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.tree import Tree

from gatesmith.core.implicants import implicant_to_literal

console = Console()


def render_input_verilog(source: str) -> None:
    console.rule("Input Verilog")
    console.print(Syntax(source, "verilog", line_numbers=False))


def render_ast(expr) -> None:
    console.rule("Parsed AST")

    def _add(tree: Tree, n) -> None:
        if n is None:
            return
        tname = type(n).__name__
        if tname == "Var":
            tree.add(f"Var: {n.name}")
        elif tname == "Const":
            tree.add(f"Const: {int(n.value)}")
        elif tname == "Not":
            child = tree.add("Not")
            _add(child, n.node)
        elif tname in {"And", "Or", "Xor"}:
            child = tree.add(tname)
            for child_node in n.nodes:
                _add(child, child_node)
        else:
            tree.add(repr(n))

    ast_tree = Tree("AST")
    _add(ast_tree, expr)
    console.print(ast_tree)


def render_truth_table_rows(rows, variables: list[str]) -> None:
    console.rule("Truth Table")
    var_count = len(variables)
    tt = Table(title="Truth Table")
    tt.add_column("Index", justify="right")
    tt.add_column("Binary")
    for v in variables:
        tt.add_column(v)
    tt.add_column("Out")
    for row in rows:
        binary = format(row.index, f"0{var_count}b") if var_count else ""
        bits = (
            [str(int(row.assignment.get(v, False))) for v in variables]
            if var_count
            else []
        )
        tt.add_row(str(row.index), binary, *bits, str(int(row.output)))
    console.print(tt)


def render_minterms(minterms: list[int], variables: list[str]) -> None:
    console.rule("Minterms")
    var_count = len(variables)
    mt = Table(title="Minterms identified")
    mt.add_column("Minterm", justify="right")
    mt.add_column("Binary")
    for v in variables:
        mt.add_column(v)
    for m in minterms:
        binary = format(m, f"0{var_count}b") if var_count else ""
        bits = [binary[i] for i in range(var_count)] if var_count else []
        mt.add_row(str(m), binary, *bits)
    console.print(mt)


def render_qmc_rounds(rounds, variables: list[str]) -> None:
    console.rule("Quine-McCluskey Rounds")
    for round_idx, qround in enumerate(rounds):
        # `qround` is a QMCRound NamedTuple with an `implicants` field
        patterns = getattr(qround, "implicants", qround)
        t = Table(title=f"Round {round_idx}")
        t.add_column("Group", justify="right")
        t.add_column("Minterms")
        for v in variables:
            t.add_column(v)
        # `patterns` is an iterable of ImplicantSnapshot(pattern, covers)
        sorted_patterns = sorted(
            patterns, key=lambda pc: (pc.pattern.count("1") if pc.pattern else 0)
        )
        for snapshot in sorted_patterns:
            pattern = snapshot.pattern
            covers = snapshot.covers
            group = pattern.count("1") if pattern else 0
            bits = [ch for ch in pattern] if pattern else []
            t.add_row(str(group), ",".join(str(x) for x in covers), *bits)
        console.print(t)


def render_prime_implicants(prime_implicants, variables: list[str]) -> None:
    console.rule("Prime Implicants")
    pi = Table(title="Prime Implicants")
    pi.add_column("Prime Implicant")
    pi.add_column("Minterms")
    for v in variables:
        pi.add_column(v)
    for implicant in prime_implicants:
        literal = implicant_to_literal(implicant, variables)
        bits = [ch for ch in (implicant.pattern or "")]
        pi.add_row(literal, ",".join(str(x) for x in sorted(implicant.covers)), *bits)
    console.print(pi)


def render_prime_coverage(
    prime_implicants, minterms: list[int], variables: list[str]
) -> None:
    console.rule("Prime Implicant Coverage")
    headers = [implicant_to_literal(imp, variables) for imp in prime_implicants]
    pc = Table(title="Prime Implicant Coverage")
    pc.add_column("Minterm")
    for h in headers:
        pc.add_column(h)
    for m in sorted(minterms):
        row = [str(m)]
        for implicant in prime_implicants:
            row.append("X" if m in implicant.covers else "")
        pc.add_row(*row)
    console.print(pc)


def render_summary(result) -> None:
    console.rule("Result Summary")
    total_literals = sum(imp.literals for imp in result.implicants)
    num_terms = len(result.implicants)
    console.print(f"Simplified expression:\n{result.assignment.target} = {result.sop}")
    console.print(f"Total literals: {total_literals}")
    console.print(f"Number of terms: {num_terms}")


def render_verilog(verilog: str) -> None:
    console.rule("Generated Verilog")
    syntax = Syntax(verilog, "verilog", line_numbers=False)
    console.print(syntax)


def render_error(message: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {message}", style="red")
