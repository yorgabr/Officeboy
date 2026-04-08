from pathlib import Path
from officeboy.lint.explain import explain_all_rules


def test_explain_all_text(capsys):
    explain_all_rules()
    out = capsys.readouterr().out
    assert "OB001" in out


def test_explain_all_json(capsys):
    explain_all_rules(output_format="json")
    out = capsys.readouterr().out
    assert "\"rule\"" in out


def test_explain_all_enabled_only(tmp_path, capsys):
    config = tmp_path / ".officeboy.toml"
    config.write_text(
        """
[lint]
select = ["OB001"]
""",
        encoding="utf-8",
    )

    explain_all_rules(enabled_only=True, root=tmp_path)
    out = capsys.readouterr().out
    assert "OB001" in out
    assert "F841" not in out