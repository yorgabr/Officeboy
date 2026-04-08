from collections import Counter
from officeboy.lint.result import LintResult


def compute_stats(result: LintResult) -> dict:
    rule_counts = Counter()
    severity_counts = Counter()

    for diagnostics in result.findings.values():
        for diag in diagnostics:
            rule_counts[diag.rule_id] += 1
            severity_counts[diag.severity.value] += 1

    return {
        "rules": dict(rule_counts),
        "severity": dict(severity_counts),
        "files": len(result.findings),
        "total": sum(rule_counts.values()),
    }