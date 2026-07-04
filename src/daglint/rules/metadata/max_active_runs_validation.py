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

        for definition in self._find_dag_definitions(tree):
            max_active_runs = self._extract_max_active_runs(definition.get_kwarg("max_active_runs"))

            if max_active_runs is None:
                issues.append(
                    self.create_issue(
                        f"max_active_runs must be explicitly set to {expected_max_active_runs}",
                        file_path,
                        definition.lineno,
                        definition.col_offset,
                    )
                )
            elif max_active_runs != expected_max_active_runs:
                issues.append(
                    self.create_issue(
                        f"max_active_runs is set to {max_active_runs}. Expected {expected_max_active_runs}",
                        file_path,
                        definition.lineno,
                        definition.col_offset,
                    )
                )

        return issues

    def _extract_max_active_runs(self, value: Optional[ast.expr]) -> Optional[int]:
        """Extract an integer from a max_active_runs argument value node."""
        if isinstance(value, ast.Constant) and isinstance(value.value, int):
            return value.value
        return None
