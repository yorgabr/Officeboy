#!/usr/bin/env python3
"""Command Line Interface for Officeboy.

This module provides the main CLI entry point for the Officeboy tool,
which handles MS Access database version control operations.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Optional

import click
from colorama import init as colorama_init

from officeboy import __version__
from officeboy.core.exporter import AccessExporter
from officeboy.core.importer import AccessImporter
from officeboy.generators.functional_tests import FunctionalTestGenerator
from officeboy.generators.unit_tests import UnitTestGenerator
from officeboy.i18n import get_text as _

# Initialize colorama for Windows color support
colorama_init(autoreset=True)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application.
    
    Args:
        verbose: Enable verbose logging if True.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@click.group(invoke_without_command=True)
@click.option(
    "--version",
    is_flag=True,
    help=_("Show the version and exit."),
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help=_("Enable verbose output."),
)
@click.pass_context
def cli(ctx: click.Context, version: bool, verbose: bool) -> None:
    """Officeboy - MS Access Version Control and Automation Tool.
    
    Export, import, and generate tests for MS Access databases
    with Git-friendly source control integration.
    """
    setup_logging(verbose)
    
    if version:
        click.echo(f"Officeboy version {__version__}")
        ctx.exit(0)
    
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(0)


@cli.command(name="disassembly")
@click.argument(
    "access_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "source_dir",
    type=click.Path(file_okay=False, path_type=Path),
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help=_("Force export even if hashes match."),
)
@click.option(
    "--encoding",
    default="utf-8",
    help=_("Output encoding for exported files."),
)
@click.pass_context
def disassembly(
    ctx: click.Context,
    access_file: Path,
    source_dir: Path,
    force: bool,
    encoding: str,
) -> None:
    """Export MS Access objects to source directory.
    
    Exports all objects (forms, reports, modules, queries, macros, tables)
    from the specified Access database to the source directory.
    Uses SHA-256 hashing to skip unchanged objects unless --force is used.
    
    \b
    ACCESS_FILE: Path to the .accdb or .mdb file
    SOURCE_DIR: Directory where source files will be exported
    """
    logger = logging.getLogger(__name__)
    logger.info(_("Starting disassembly of {file}").format(file=access_file))
    
    try:
        exporter = AccessExporter(
            access_file=access_file,
            source_dir=source_dir,
            encoding=encoding,
            force_export=force,
        )
        stats = exporter.export_all()
        
        click.echo(
            click.style(
                _("Export completed successfully!"),
                fg="green",
                bold=True,
            )
        )
        click.echo(_("Exported {count} objects:").format(count=stats.total_exported))
        click.echo(_("  - Forms: {forms}").format(forms=stats.forms))
        click.echo(_("  - Reports: {reports}").format(reports=stats.reports))
        click.echo(_("  - Modules: {modules}").format(modules=stats.modules))
        click.echo(_("  - Queries: {queries}").format(queries=stats.queries))
        click.echo(_("  - Macros: {macros}").format(macros=stats.macros))
        click.echo(_("  - Tables: {tables}").format(tables=stats.tables))
        click.echo(_("  - Skipped (unchanged): {skipped}").format(skipped=stats.skipped))
        
    except Exception as e:
        logger.exception(_("Export failed"))
        click.echo(
            click.style(
                _("Error: {error}").format(error=str(e)),
                fg="red",
                bold=True,
            ),
            err=True,
        )
        ctx.exit(1)


@cli.command(name="assembly")
@click.argument(
    "source_dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.argument(
    "access_file",
    type=click.Path(dir_okay=False, path_type=Path),
)
@click.option(
    "--overwrite",
    "-o",
    is_flag=True,
    help=_("Overwrite existing database file."),
)
@click.option(
    "--template",
    "-t",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help=_("Template database to use as base."),
)
@click.pass_context
def assembly(
    ctx: click.Context,
    source_dir: Path,
    access_file: Path,
    overwrite: bool,
    template: Optional[Path],
) -> None:
    """Build MS Access database from source directory.
    
    Reconstructs an Access database from exported source files.
    Creates a new database or uses a template as base.
    
    \b
    SOURCE_DIR: Directory containing exported source files
    ACCESS_FILE: Path for the output .accdb or .mdb file
    """
    logger = logging.getLogger(__name__)
    logger.info(_("Starting assembly of {file}").format(file=access_file))
    
    if access_file.exists() and not overwrite:
        click.echo(
            click.style(
                _("Error: File exists. Use --overwrite to replace."),
                fg="red",
                bold=True,
            ),
            err=True,
        )
        ctx.exit(1)
    
    try:
        importer = AccessImporter(
            source_dir=source_dir,
            access_file=access_file,
            template=template,
        )
        stats = importer.import_all()
        
        click.echo(
            click.style(
                _("Assembly completed successfully!"),
                fg="green",
                bold=True,
            )
        )
        click.echo(_("Imported {count} objects:").format(count=stats.total_imported))
        click.echo(_("  - Forms: {forms}").format(forms=stats.forms))
        click.echo(_("  - Reports: {reports}").format(reports=stats.reports))
        click.echo(_("  - Modules: {modules}").format(modules=stats.modules))
        click.echo(_("  - Queries: {queries}").format(queries=stats.queries))
        click.echo(_("  - Macros: {macros}").format(macros=stats.macros))
        click.echo(_("  - Tables: {tables}").format(tables=stats.tables))
        
    except Exception as e:
        logger.exception(_("Assembly failed"))
        click.echo(
            click.style(
                _("Error: {error}").format(error=str(e)),
                fg="red",
                bold=True,
            ),
            err=True,
        )
        ctx.exit(1)


@cli.command(name="make-unit-tests")
@click.argument(
    "access_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=False, path_type=Path),
    default="./tests/unit",
    help=_("Output directory for test files."),
)
@click.option(
    "--addin-name",
    "-n",
    default="OfficeboyTests",
    help=_("Name for the generated Access Add-in."),
)
@click.pass_context
def make_unit_tests(
    ctx: click.Context,
    access_file: Path,
    output: Path,
    addin_name: str,
) -> None:
    """Generate unit test Add-in for MS Access database.
    
    Creates an MS Access Add-in containing test modules for each
    code module in the database. Each public function and sub
    gets at least one corresponding test method.
    
    \b
    ACCESS_FILE: Path to the .accdb or .mdb file to analyze
    """
    logger = logging.getLogger(__name__)
    logger.info(_("Generating unit tests for {file}").format(file=access_file))
    
    try:
        generator = UnitTestGenerator(
            access_file=access_file,
            output_dir=output,
            addin_name=addin_name,
        )
        stats = generator.generate()
        
        click.echo(
            click.style(
                _("Unit test Add-in generated successfully!"),
                fg="green",
                bold=True,
            )
        )
        click.echo(
            _("Created {modules} test modules with {tests} total tests").format(
                modules=stats.module_count,
                tests=stats.test_count,
            )
        )
        click.echo(_("Output: {path}").format(path=output))
        
    except Exception as e:
        logger.exception(_("Unit test generation failed"))
        click.echo(
            click.style(
                _("Error: {error}").format(error=str(e)),
                fg="red",
                bold=True,
            ),
            err=True,
        )
        ctx.exit(1)


@cli.command(name="make-functional-tests")
@click.argument(
    "access_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=False, path_type=Path),
    default="./tests/functional",
    help=_("Output directory for Robot Framework tests."),
)
@click.option(
    "--library",
    "-l",
    default="FlaUILibrary",
    help=_("Robot Framework library to use."),
)
@click.pass_context
def make_functional_tests(
    ctx: click.Context,
    access_file: Path,
    output: Path,
    library: str,
) -> None:
    """Generate functional tests for MS Access forms.
    
    Creates Robot Framework test specifications and Python scripts
    to test all forms in the database. Automatically detects form
    fields, buttons, and their Click event handlers.
    
    \b
    ACCESS_FILE: Path to the .accdb or .mdb file to analyze
    """
    logger = logging.getLogger(__name__)
    logger.info(_("Generating functional tests for {file}").format(file=access_file))
    
    try:
        generator = FunctionalTestGenerator(
            access_file=access_file,
            output_dir=output,
            library=library,
        )
        stats = generator.generate()
        
        click.echo(
            click.style(
                _("Functional tests generated successfully!"),
                fg="green",
                bold=True,
            )
        )
        click.echo(
            _("Created {specs} test specifications for {forms} forms").format(
                specs=stats.spec_count,
                forms=stats.form_count,
            )
        )
        click.echo(
            _("Total test cases: {cases}").format(cases=stats.test_case_count)
        )
        click.echo(_("Output: {path}").format(path=output))
        
    except Exception as e:
        logger.exception(_("Functional test generation failed"))
        click.echo(
            click.style(
                _("Error: {error}").format(error=str(e)),
                fg="red",
                bold=True,
            ),
            err=True,
        )
        ctx.exit(1)


def main() -> None:
    """Entry point for the CLI."""
    # Ensure we're on Windows
    if os.name != "nt":
        click.echo(
            click.style(
                _("Error: Officeboy requires Windows with MS Access."),
                fg="red",
                bold=True,
            ),
            err=True,
        )
        sys.exit(1)
    
    cli()


if __name__ == "__main__":
    main()
