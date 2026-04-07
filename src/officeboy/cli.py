"""
Rich CLI of Officeboy.
"""
import sys
from pathlib import Path
from typing import Optional

import click

from officeboy.core.disassembler import Disassembler, DisassemblyResult
from officeboy.core.assembler import Assembler, AssemblyResult
from officeboy.generators.unit_tests import UnitTestGenerator
from officeboy.generators.functional_tests import FunctionalTestGenerator


class CLIContext:
    """Context object holding dependencies for CLI commands."""
    
    def __init__(
        self,
        disassembler_class=Disassembler,
        assembler_class=Assembler,
        unit_gen_class=UnitTestGenerator,
        functional_gen_class=FunctionalTestGenerator
    ):
        self.disassembler_class = disassembler_class
        self.assembler_class = assembler_class
        self.unit_gen_class = unit_gen_class
        self.functional_gen_class = functional_gen_class


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    """Officeboy - MS Access Database Version Control Tool."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    if 'context' not in ctx.obj:
        ctx.obj['context'] = CLIContext()


@cli.command()
@click.argument('database', type=click.Path(exists=True, path_type=Path))
@click.argument('output', type=click.Path(path_type=Path))
@click.option('--force', '-f', is_flag=True, help='Force disassembly of all objects')
@click.option('--index', type=click.Path(path_type=Path), help='Path to index file')
@click.pass_context
def disassemble(ctx, database: Path, output: Path, force: bool, index: Optional[Path]):
    """Break down Access database into source files."""
    context = ctx.obj['context']
    verbose = ctx.obj['verbose']
    
    from officeboy.core.index import IndexManager
    index_mgr = IndexManager(index) if index else None
    
    disassembler = context.disassembler_class(index_manager=index_mgr)
    
    try:
        result = disassembler.disassemble(
            database, 
            output, 
            force=force,
            progress_callback=lambda name, cur, tot: click.echo(f"  {cur}/{tot}: {name}") if verbose else None
        )
        
        click.echo(f"Disassembly completed: {result.total_disassembled} objects")
        click.echo(f"  Forms: {result.forms}, Reports: {result.reports}, Modules: {result.modules}")
        click.echo(f"  Skipped: {result.skipped}")
        
        if result.errors:
            click.echo(f"  Errors: {len(result.errors)}", err=True)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        disassembler.close()


@cli.command()
@click.argument('source', type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument('database', type=click.Path(path_type=Path))
@click.option('--template', '-t', type=click.Path(exists=True, path_type=Path), help='Template database')
@click.option('--overwrite', is_flag=True, help='Overwrite existing database')
@click.pass_context
def assemble(ctx, source: Path, database: Path, template: Optional[Path], overwrite: bool):
    """Build Access database from source files."""
    context = ctx.obj['context']
    
    if database.exists() and not overwrite:
        click.echo(f"Error: File exists. Use --overwrite to replace.", err=True)
        sys.exit(1)
    
    assembler = context.assembler_class()
    
    try:
        result = assembler.assemble(
            source, 
            database, 
            template=template,
            overwrite=overwrite
        )
        
        click.echo(f"Assembly completed: {result.total_assembled} objects imported")
        click.echo(f"  Forms: {result.forms}, Reports: {result.reports}, Modules: {result.modules}")
        
        if result.errors:
            click.echo(f"  Errors: {len(result.errors)}", err=True)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        assembler.close()


@cli.command()
@click.argument('database', type=click.Path(exists=True, path_type=Path))
@click.option('--output', '-o', type=click.Path(path_type=Path), default='./tests', help='Output directory')
@click.option('--addin-name', default='TestAddin', help='Name of test add-in')
@click.pass_context
def make_unit_tests(ctx, database: Path, output: Path, addin_name: str):
    """Generate unit test add-in for database."""
    context = ctx.obj['context']
    generator = context.unit_gen_class()
    
    try:
        result = generator.generate(database, output, addin_name=addin_name)
        click.echo(f"Generated {result.test_count} tests in {result.module_count} modules")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('database', type=click.Path(exists=True, path_type=Path))
@click.option('--output', '-o', type=click.Path(path_type=Path), default='./robot_tests', help='Output directory')
@click.option('--library', '-l', default='FlaUILibrary', help='Robot Framework library')
@click.pass_context
def make_functional_tests(ctx, database: Path, output: Path, library: str):
    """Generate Robot Framework tests for database."""
    context = ctx.obj['context']
    generator = context.functional_gen_class()
    
    try:
        result = generator.generate(database, output, library=library)
        click.echo(f"Generated {result.test_case_count} test cases for {result.form_count} forms")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def version():
    """Show version information."""
    from officeboy import __version__
    click.echo(f"Officeboy version {__version__}")


# Backward compatibility aliases (optional - remove if not needed)
@cli.command(name='export', hidden=True)
@click.pass_context
def export_alias(ctx, **kwargs):
    """Alias for disassemble (deprecated)."""
    click.echo("Warning: 'export' is deprecated, use 'disassemble' instead.", err=True)
    ctx.forward(disassemble)


@cli.command(name='import', hidden=True)
@click.pass_context
def import_alias(ctx, **kwargs):
    """Alias for assemble (deprecated)."""
    click.echo("Warning: 'import' is deprecated, use 'assemble' instead.", err=True)
    ctx.forward(assemble)


def main():
    """Main entry point."""
    if sys.platform != 'win32':
        click.echo("Error: Officeboy requires Windows with MS Access", err=True)
        sys.exit(1)
    cli(obj={})


if __name__ == '__main__':
    main()