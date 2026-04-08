from pathlib import Path
import tomllib


class LintConfig:
    """Configuration for Officeboy lint."""

    def __init__(self, root: Path):
        self.select: list[str] = []
        self.ignore: list[str] = []

        config_file = root / ".officeboy.toml"
        if config_file.exists():
            data = tomllib.loads(config_file.read_text(encoding="utf-8"))
            lint = data.get("lint", {})
            self.select = lint.get("select", [])
            self.ignore = lint.get("ignore", [])


def rule_enabled(rule_code: str, config: LintConfig) -> bool:
    prefix = rule_code.rstrip("0123456789")

    if rule_code in config.ignore:
        return False

    if not config.select:
        return True

    return rule_code in config.select or prefix in config.select