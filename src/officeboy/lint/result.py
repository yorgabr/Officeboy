from collections import defaultdict
from officeboy.lint.model import FixSafety


class LintResult:
    def __init__(self):
        self.findings = defaultdict(list)
        self.has_errors = False

    def add(self, path, diagnostics):
        for diag in diagnostics:
            self.findings[path].append(diag)
            if diag.severity.value == "error":
                self.has_errors = True

    def apply_fixes(self, path, lines, allow_unsafe: bool):
        new_lines = list(lines)
        for diag in self.findings.get(path, []):
            if diag.fix is None:
                continue
            if diag.fix.safety == FixSafety.UNSAFE and not allow_unsafe:
                continue
            new_lines = diag.fix.apply(new_lines)
        return new_lines

    def print(self, output_format: str):
        if output_format == "json":
            data = []
            for path, diags in self.findings.items():
                for d in diags:
                    data.append(
                        {
                            "file": str(path),
                            "line": d.line,
                            "rule": d.rule_id,
                            "severity": d.severity.value,
                            "message": d.message,
                            "fixable": d.fix is not None,
                        }
                    )
            import json

            print(json.dumps(data, indent=2))
            return

        for path, diags in self.findings.items():
            for d in diags:
                print(
                    f"{path}:{d.line}: {d.rule_id} {d.message}"
                )