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

    def _is_operator_call(self, node: ast.Call) -> bool:
        """Check if a call is an operator instantiation.

        Args:
            node: AST Call node to check

        Returns:
            True if the call is an Operator instantiation
        """
        if isinstance(node.func, ast.Name):
            return node.func.id.endswith("Operator")
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr.endswith("Operator")
        return False

    def _extract_task_id(self, node: ast.Call) -> Optional[str]:
        """Extract task_id from an operator call.

        Args:
            node: AST Call node representing an operator instantiation

        Returns:
            The task_id string if found, None otherwise
        """
        for keyword in node.keywords:
            if keyword.arg == "task_id":
                if isinstance(keyword.value, ast.Constant):
                    value = keyword.value.value
                    if isinstance(value, str):
                        return value
        return None

    def _extract_dag_id(self, node: ast.Call) -> Optional[str]:
        """Extract DAG ID from a DAG() call.

        Args:
            node: AST Call node representing a DAG instantiation

        Returns:
            The dag_id string if found, None otherwise
        """
        # Check positional arguments
        if node.args and isinstance(node.args[0], ast.Constant):
            value = node.args[0].value
            if isinstance(value, str):
                return value

        # Check keyword arguments
        for keyword in node.keywords:
            if keyword.arg == "dag_id":
                if isinstance(keyword.value, ast.Constant):
                    value = keyword.value.value
                    if isinstance(value, str):
                        return value

        return None

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
