"""Rule for validating DAG max_active_runs configuration."""

import ast
from typing import List, Optional

from daglint.models import LintIssue
from daglint.rules.base import BaseRule


class MaxActiveRunsValidationRule(BaseRule):
    """Ensures DAGs explicitly set max_active_runs to the configured value."""

    @property
    def rule_id(self) -> str:
        return "max_active_runs_validation"

    @property
    def description(self) -> str:
        return "DAGs must explicitly set max_active_runs to the configured value"

    def check(self, tree: ast.AST, file_path: str, source_code: str) -> List[LintIssue]:
        issues = []
        expected_max_active_runs = self.config.get("max_active_runs", 1)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and self._is_dag_call(node):
                max_active_runs = self._extract_max_active_runs(node)

                if max_active_runs is None:
                    issues.append(
                        self.create_issue(
                            f"max_active_runs must be explicitly set to {expected_max_active_runs}",
                            file_path,
                            node.lineno,
                            node.col_offset,
                        )
                    )
                elif max_active_runs != expected_max_active_runs:
                    issues.append(
                        self.create_issue(
                            f"max_active_runs is set to {max_active_runs}. Expected {expected_max_active_runs}",
                            file_path,
                            node.lineno,
                            node.col_offset,
                        )
                    )

        return issues

    def _is_dag_call(self, node: ast.Call) -> bool:
        """Check if a call is a DAG instantiation."""
        if isinstance(node.func, ast.Name):
            return node.func.id == "DAG"

        if isinstance(node.func, ast.Attribute):
            return node.func.attr == "DAG"

        return False

    def _extract_max_active_runs(self, node: ast.Call) -> Optional[int]:
        """Extract max_active_runs from a DAG() call."""
        for keyword in node.keywords:
            if keyword.arg == "max_active_runs":
                if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, int):
                    return keyword.value.value

        return None
