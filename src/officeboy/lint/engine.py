from pathlib import Path
import json

from officeboy.lint.cache import LintCache
from officeboy.lint.registry import get_active_rules
from officeboy.lint.result import LintResult


class LintEngine:
    """Main linting engine."""

    def __init__(self, root: Path):
        self.root = root
        self.cache = LintCache(root)

    def run(
        self,
        source: Path,
        apply_fixes: bool,
        allow_unsafe: bool,
        use_cache: bool,
        output_format: str,
    ) -> LintResult:
        rules = get_active_rules()
        result = LintResult()

        for path in source.rglob("*.bas"):
            content = path.read_text(encoding="utf-8", errors="ignore")

            if use_cache and not self.cache.is_dirty(path, content):
                continue

            lines = content.splitlines()
            diagnostics = []

            for rule in rules:
                diagnostics.extend(rule.check(path, lines))

            result.add(path, diagnostics)

            if apply_fixes:
                new_lines = result.apply_fixes(
                    path, lines, allow_unsafe=allow_unsafe
                )
                if new_lines != lines:
                    path.write_text("\n".join(new_lines), encoding="utf-8")

            if use_cache:
                self.cache.update(path, content)

        if use_cache:
            self.cache.flush()

        result.print(output_format)
        return result