import pytest
from officeboy.lint.explain import explain_rule


def test_explain_rule_ok(capsys):
    explain_rule("OB001")
    out = capsys.readouterr().out
    assert "OB001" in out
    assert "Public procedure" in out


def test_explain_rule_unknown():
    with pytest.raises(Exception):
        explain_rule("ZZ999")
