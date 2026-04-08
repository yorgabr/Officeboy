import json
import click
from pathlib import Path

from officeboy.lint.catalog.explanations import EXPLANATIONS
from officeboy.lint.config import LintConfig, rule_enabled


def explain_rule(rule_code: str) -> None:
    rule = EXPLANATIONS.get(rule_code.upper())
    if not rule:
        raise click.ClickException(f"Unknown rule '{rule_code}'")

    click.echo(f"{rule.code} – {rule.title}")
    click.echo("-" * 60)
    click.echo(rule.description)
    click.echo()
    click.echo(f"Severity      : {rule.severity.value}")
    click.echo(f"Applicability : {rule.applicability.value}")
    click.echo(f"Fixable       : {rule.fixable}")

    if rule.fixable:
        click.echo(f"Fix safety    : {rule.fix_safety.value}")

    click.echo("\nExample:")
    click.echo(rule.example.rstrip())


def explain_all_rules(
    output_format: str = "text",
    enabled_only: bool = False,
    root: Path | None = None,
) -> None:
    rules = sorted(EXPLANATIONS.values(), key=lambda r: r.code)

    if enabled_only:
        if root is None:
            root = Path.cwd()
        config = LintConfig(root)
        rules = [r for r in rules if rule_enabled(r.code, config)]

    if output_format == "json":
        click.echo(
            json.dumps(
                [
                    {
                        "rule": r.code,
                        "title": r.title,
                        "severity": r.severity.value,
                        "applicability": r.applicability.value,
                        "fixable": r.fixable,
                        "fix_safety": (
                            r.fix_safety.value if r.fix_safety else None
                        ),
                    }
                    for r in rules
                ],
                indent=2,
            )
        )
        return

    for r in rules:
        click.echo(f"{r.code} – {r.title}")
        click.echo(f"Severity      : {r.severity.value}")
        click.echo(f"Applicability : {r.applicability.value}")
        click.echo(f"Fixable       : {'yes' if r.fixable else 'no'}")
        click.echo()