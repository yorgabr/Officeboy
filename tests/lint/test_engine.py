from pathlib import Path

from officeboy.lint.engine import LintEngine
from tests.lint.helpers import DummyRule


def test_lint_engine_runs(tmp_path: Path, monkeypatch):
    source = tmp_path / "src"
    source.mkdir()

    file_path = source / "test.bas"
    file_path.write_text("Public Sub Test()\nEnd Sub", encoding="utf-8")

    monkeypatch.setattr(
        "officeboy.lint.registry.get_active_rules",
        lambda: [DummyRule()],
    )

    engine = LintEngine(root=tmp_path)
    result = engine.run(
        source=source,
        apply_fixes=False,
        allow_unsafe=False,
        use_cache=False,
        output_format="text",
    )

    assert not result.has_errors
    assert len(result.findings) == 1