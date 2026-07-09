"""Rules for DAG configuration validation (retries, catchup, schedule)."""

import ast
from typing import List, Optional

from daglint.models import LintIssue
from daglint.rules.base import BaseRule


class RetryConfigurationRule(BaseRule):
    """Ensures retry settings are properly configured."""

    @property
    def rule_id(self) -> str:
        return "retry_configuration"

    @property
    def description(self) -> str:
        return "Retries must be configured within specified limits"

    def check(self, tree: ast.AST, file_path: str, source_code: str) -> List[LintIssue]:
        issues = []
        min_retries = self.config["min_retries"]
        max_retries = self.config["max_retries"]

        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                retry_value = self._extract_retries_from_dict(node)
                if retry_value is not None:
                    if retry_value < min_retries:
                        issues.append(
                            self.create_issue(
                                f"Retries value {retry_value} is below minimum {min_retries}",
                                file_path,
                                node.lineno,
                                node.col_offset,
                            )
                        )
                    elif retry_value > max_retries:
                        issues.append(
                            self.create_issue(
                                f"Retries value {retry_value} exceeds maximum {max_retries}",
                                file_path,
                                node.lineno,
                                node.col_offset,
                            )
                        )

        return issues

    def _extract_retries_from_dict(self, node: ast.Dict) -> Optional[int]:
        """Extract retries value from a dictionary node."""
        for key, value in zip(node.keys, node.values):
            if isinstance(key, ast.Constant) and key.value == "retries":
                if isinstance(value, ast.Constant) and isinstance(value.value, int):
                    return value.value
        return None


class CatchupValidationRule(BaseRule):
    """Validates catchup parameter is properly set."""

    @property
    def rule_id(self) -> str:
        return "catchup_validation"

    @property
    def description(self) -> str:
        return "Catchup parameter should be explicitly set to avoid unexpected behavior"

    def check(self, tree: ast.AST, file_path: str, source_code: str) -> List[LintIssue]:
        issues = []
        default_catchup = self.config["default_catchup"]

        for definition in self._find_dag_definitions(tree):
            catchup_value = self._extract_catchup(definition.get_kwarg("catchup"))
            if catchup_value is None:
                issues.append(
                    self.create_issue(
                        f"Catchup parameter not set. Consider setting it explicitly to {default_catchup}",
                        file_path,
                        definition.lineno,
                        definition.col_offset,
                    )
                )

        return issues

    def _extract_catchup(self, value: Optional[ast.expr]) -> Optional[bool]:
        """Extract a boolean from a catchup argument value node."""
        if isinstance(value, ast.Constant) and isinstance(value.value, bool):
            return value.value
        return None


class ScheduleValidationRule(BaseRule):
    """Validates schedule is properly set."""

    @property
    def rule_id(self) -> str:
        return "schedule_validation"

    @property
    def description(self) -> str:
        return "Schedule must be properly configured"

    def check(self, tree: ast.AST, file_path: str, source_code: str) -> List[LintIssue]:
        issues = []
        allow_none = self.config["allow_none"]

        for definition in self._find_dag_definitions(tree):
            schedule_value = definition.get_kwarg("schedule_interval") or definition.get_kwarg("schedule")
            if schedule_value is None and not allow_none:
                issues.append(
                    self.create_issue(
                        "schedule must be explicitly set",
                        file_path,
                        definition.lineno,
                        definition.col_offset,
                    )
                )

        return issues
