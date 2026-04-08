from officeboy.lint.model import LintMessage, Severity


class DummyRule:
    def check(self, path, lines):
        yield LintMessage(
            rule_id="TEST001",
            message="Dummy rule triggered",
            file_path=path,
            line=1,
            severity=Severity.WARNING,
        )
