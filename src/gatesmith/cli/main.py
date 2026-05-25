from __future__ import annotations

import typer
from pathlib import Path

from gatesmith.cli import renderer
from gatesmith.core.parser import ParseError
from gatesmith.core.pipeline import synthesize as run_pipeline
from gatesmith.io.reader import read_input
from gatesmith.io.writer import write_output

app = typer.Typer(help="Gatesmith")


@app.command()
def synthesize(
    input: str = typer.Argument(
        ..., help="Single Verilog assign statement or a file path"
    ),
    output: str | None = typer.Option(None, help="Destination Verilog file"),
    verbose: bool = typer.Option(False, help="Print synthesis diagnostics"),
    no_opt: bool = typer.Option(
        False,
        help="Disable logic minimization (no optimization)",
    ),
) -> None:
    # Read input file
    try:
        source = read_input(input)
        result = run_pipeline(source, no_opt=no_opt)
    except (ParseError, ValueError) as exc:
        renderer.render_error(str(exc))
        raise typer.Exit(code=1) from exc
    except Exception:
        renderer.render_error("Unexpected synthesis failure")
        raise typer.Exit(code=1)

    # Determine output file name
    if output is None:
        input_path = Path(input)

        if input_path.suffix == ".v":
            output = str(input_path.with_name(input_path.stem + "_out.v"))
        else:
            output = "out.v"

    # Render verbose output
    if verbose:
        vars_ = result.variables

        renderer.render_input_verilog(source)
        renderer.render_ast(result.assignment.expr)
        renderer.render_truth_table_rows(result.truth_table, vars_)
        renderer.render_minterms(result.minterms, vars_)
        if result.trace:
            renderer.render_qmc_rounds(result.trace.rounds, vars_)
            renderer.render_prime_implicants(result.trace.prime_implicants, vars_)
            if result.trace.prime_implicants:
                renderer.render_prime_coverage(
                    result.trace.prime_implicants, result.minterms, vars_
                )
        renderer.render_summary(result)
        renderer.render_verilog(result.verilog)

    # Write output file
    write_output(output, result.verilog)

    typer.echo(output)


if __name__ == "__main__":
    app()
