"""Base class for all linting rules."""

import ast
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from daglint.models import LintIssue


class BaseRule(ABC):
    """Base class for all linting rules."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the rule.

        Args:
            config: Rule-specific configuration
        """
        self.config = config or {}
        self.severity = self.config.get("severity", "error")

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique identifier for the rule."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of the rule."""
        pass

    @abstractmethod
    def check(self, tree: ast.AST, file_path: str, source_code: str) -> List[LintIssue]:
        """Check the AST for violations of this rule.

        Args:
            tree: Abstract syntax tree of the file
            file_path: Path to the file being checked
            source_code: Source code of the file

        Returns:
            List of linting issues found
        """
        pass

    def create_issue(self, message: str, file_path: str, line: int, column: int = 0) -> LintIssue:
        """Create a linting issue.

        Args:
            message: Issue message
            file_path: Path to the file
            line: Line number
            column: Column number

        Returns:
            LintIssue instance
        """
        return LintIssue(
            rule_id=self.rule_id,
            message=message,
            file_path=file_path,
            line=line,
            column=column,
            severity=self.severity,
        )
