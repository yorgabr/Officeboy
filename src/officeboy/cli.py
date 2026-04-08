"""
Rich CLI of Officeboy.
"""

import sys
from pathlib import Path
from typing import Optional

import click

from officeboy.core.disassembler import Disassembler
from officeboy.core.assembler import Assembler
from officeboy.generators.unit_tests import UnitTestGenerator
from officeboy.generators.functional_tests import FunctionalTestGenerator
from officeboy.lint.engine import LintEngine
from officeboy.lint.explain import explain_rule, explain_all_rules


class CLIContext:
    """Context object holding dependencies for CLI commands."""

    def __init__(
        self,
        disassembler_class=Disassembler,
        assembler_class=Assembler,
        unit_gen_class=UnitTestGenerator,
        functional_gen_class=FunctionalTestGenerator,
        lint_engine_class=LintEngine,
    ):
        self.disassembler_class = disassembler_class
        self.assembler_class = assembler_class
        self.unit_gen_class = unit_gen_class
        self.functional_gen_class = functional_gen_class
        self.lint_engine_class = lint_engine_class


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx: click.Context, verbose: bool):
    """Officeboy - MS Access Database Version Control Tool."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    if "context" not in ctx.obj:
        ctx.obj["context"] = CLIContext()


@cli.command(name="lint-explain-all")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
)
@click.option(
    "--enabled-only",
    is_flag=True,
    help="Show only rules enabled by configuration",
)
@click.pass_context
def lint_explain_all(
    ctx: click.Context,
    output_format: str,
    enabled_only: bool,
):
    """Explain all available lint rules."""
    explain_all_rules(
        output_format=output_format,
        enabled_only=enabled_only,
        root=Path.cwd(),
    )


@cli.command()
@click.argument("database", type=click.Path(exists=True, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path))
@click.option("--force", "-f", is_flag=True, help="Force disassembly of all objects")
@click.option("--index", type=click.Path(path_type=Path), help="Path to index file")
@click.pass_context
def disassemble(
    ctx: click.Context,
    database: Path,
    output: Path,
    force: bool,
    index: Optional[Path],
):
    """Break down Access database into source files."""
    context = ctx.obj["context"]
    verbose = ctx.obj["verbose"]

    from officeboy.core.index import IndexManager

    index_mgr = IndexManager(index) if index else None
    disassembler = context.disassembler_class(index_manager=index_mgr)

    try:
        result = disassembler.disassemble(
            database,
            output,
            force=force,
            progress_callback=(
                lambda name, cur, tot: click.echo(f"{cur}/{tot}: {name}")
                if verbose
                else None
            ),
        )
        click.echo(f"Disassembly completed: {result.total_disassembled} objects")
        click.echo(
            f" Forms: {result.forms}, Reports: {result.reports}, Modules: {result.modules}"
        )
        click.echo(f" Skipped: {result.skipped}")
        if result.errors:
            click.echo(f" Errors: {len(result.errors)}", err=True)
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    finally:
        disassembler.close()


@cli.command()
@click.argument("source", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument("database", type=click.Path(path_type=Path))
@click.option(
    "--template",
    "-t",
    type=click.Path(exists=True, path_type=Path),
    help="Template database",
)
@click.option("--overwrite", is_flag=True, help="Overwrite existing database")
@click.pass_context
def assemble(
    ctx: click.Context,
    source: Path,
    database: Path,
    template: Optional[Path],
    overwrite: bool,
):
    """Build Access database from source files."""
    context = ctx.obj["context"]

    if database.exists() and not overwrite:
        click.echo("Error: File exists. Use --overwrite to replace.", err=True)
        sys.exit(1)

    assembler = context.assembler_class()

    try:
        result = assembler.assemble(
            source, database, template=template, overwrite=overwrite
        )
        click.echo(f"Assembly completed: {result.total_assembled} objects imported")
        click.echo(
            f" Forms: {result.forms}, Reports: {result.reports}, Modules: {result.modules}"
        )
        if result.errors:
            click.echo(f" Errors: {len(result.errors)}", err=True)
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    finally:
        assembler.close()


@cli.command(name="lint")
@click.argument("source", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--fix", is_flag=True, help="Apply safe fixes")
@click.option("--unsafe-fixes", is_flag=True, help="Apply unsafe fixes")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
)
@click.option("--no-cache", is_flag=True, help="Disable lint cache")
@click.pass_context
def lint_command(
    ctx: click.Context,
    source: Path,
    fix: bool,
    unsafe_fixes: bool,
    output_format: str,
    no_cache: bool,
):
    """Lint disassembled Access source code."""
    context = ctx.obj["context"]
    engine = context.lint_engine_class(root=Path.cwd())

    diagnostics = engine.run(
        source,
        apply_fixes=fix,
        allow_unsafe=unsafe_fixes,
        use_cache=not no_cache,
        output_format=output_format,
    )

    if diagnostics.has_errors:
        sys.exit(1)


@cli.command(name="lint-explain")
@click.argument("rule_code")
def lint_explain(rule_code: str):
    """Explain a lint rule in detail."""
    explain_rule(rule_code)


@cli.command(name="lint-explain-all")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
)
def lint_explain_all(output_format: str):
    """Explain all available lint rules."""
    explain_all_rules(output_format)


@cli.command(name="lint-stats")
@click.argument("source", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.pass_context
def lint_stats(ctx: click.Context, source: Path):
    """Show lint statistics for source tree."""
    context = ctx.obj["context"]
    engine = context.lint_engine_class(root=Path.cwd())

    result = engine.run(
        source=source,
        apply_fixes=False,
        allow_unsafe=False,
        use_cache=True,
        output_format="text",
    )

    from officeboy.lint.stats import compute_stats

    stats = compute_stats(result)

    click.echo(f"Files analyzed : {stats['files']}")
    click.echo(f"Total issues   : {stats['total']}")
    click.echo("By severity:")
    for sev, count in stats["severity"].items():
        click.echo(f"  {sev}: {count}")

    click.echo("Top rules:")
    for rule, count in sorted(
        stats["rules"].items(), key=lambda x: x[1], reverse=True
    ):
        click.echo(f"  {rule}: {count}")


@cli.command()
def version():
    """Show version information."""
    from officeboy import __version__

    click.echo(f"Officeboy version {__version__}")


def main():
    """Main entry point."""
    if sys.platform != "win32":
        click.echo("Error: Officeboy requires Windows with MS Access", err=True)
        sys.exit(1)

    cli(obj={})


if __name__ == "__main__":
    main()