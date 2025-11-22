"""Data models for daglint."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class LintIssue:
    """Represents a linting issue found in a DAG file."""

    rule_id: str
    message: str
    file_path: str
    line: int
    severity: Literal["error", "warning", "info"] = "error"
    column: int = 0

    def __str__(self) -> str:
        """String representation of the issue."""
        return f"{self.file_path}:{self.line}:{self.column} - {self.severity.upper()} [{self.rule_id}] {self.message}"
