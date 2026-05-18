# gatesmith

A a minimal CLI tool that converts a single Verilog `assign` statement into an optimized structural (gate-level) Verilog module.

It parses Boolean expressions, builds an AST, evaluates truth tables, minimizes logic using Quine-McCluskey, and emits simplified Sum-of-Products (SOP) and structural Verilog.

## Features

- Parses a single `assign <out> = <expr>;` statement
  - Supports operators: `~` (NOT), `&` (AND), `|` (OR), `^` (XOR)
- Builds an AST and evaluates truth tables
- Extracts minterms and applies Quine-McCluskey minimization
- Generates:
  - Simplified SOP expression
  - Structural Verilog

## Usage

### CLI

```bash
gatesmith "assign y = a & b | ~c;" --verbose
gatesmith input.v --verbose
```

### Input Format

Only single continuous assignment statements are supported:

```verilog
assign <output> = <expression>;
```

Supported operators:

- `~` : NOT
- `&` : AND
- `|` : OR
- `^` : XOR

Parentheses are supported for grouping.

### Output

Depending on flags (e.g. `--verbose`), the tool may output:

- Parsed AST
- Truth table
- Minterm list
- Minimized expression (SOP form)
- Structural Verilog module

## Development

### Requirements

- Python 3.11+
- uv

### Run tests

```bash
uv run pytest
```

## Project Structure

```
src/gatesmith/
├── core/        # Parsing, AST, evaluation, minimization, Verilog generation
├── cli/         # Typer-based CLI interface
tests/           # Unit tests
```
