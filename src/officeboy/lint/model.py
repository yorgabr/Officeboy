from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class FixSafety(str, Enum):
    SAFE = "safe"
    UNSAFE = "unsafe"


@dataclass(frozen=True)
class Fix:
    apply: Callable[[list[str]], list[str]]
    safety: FixSafety


@dataclass(frozen=True)
class LintMessage:
    rule_id: str
    message: str
    file_path: Path
    line: int
    severity: Severity
    fix: Optional[Fix] = None