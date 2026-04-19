import typer

app = typer.Typer(help="GateSmith")


@app.command()
def synthesize(
    input: str,
    output: str = "out.v",
):
    """
    Convert dataflow Verilog into optimized gate-level Verilog.
    """
    typer.echo(f"Input: {input}")
    typer.echo(f"Output: {output}")


if __name__ == "__main__":
    app()
