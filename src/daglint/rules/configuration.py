"""Rules for DAG configuration validation (retries, catchup, schedule)."""

import ast
from typing import Any, List, Optional

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
        min_retries = self.config.get("min_retries", 1)
        max_retries = self.config.get("max_retries", 5)

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
        default_catchup = self.config.get("default_catchup", False)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "DAG":
                    catchup_value = self._extract_catchup(node)
                    if catchup_value is None:
                        issues.append(
                            self.create_issue(
                                f"Catchup parameter not set. Consider setting it explicitly to {default_catchup}",
                                file_path,
                                node.lineno,
                                node.col_offset,
                            )
                        )

        return issues

    def _extract_catchup(self, node: ast.Call) -> Optional[bool]:
        """Extract catchup parameter from a DAG() call."""
        for keyword in node.keywords:
            if keyword.arg == "catchup":
                if isinstance(keyword.value, ast.Constant):
                    value = keyword.value.value
                    if isinstance(value, bool):
                        return value
        return None


class ScheduleValidationRule(BaseRule):
    """Validates schedule_interval is properly set."""

    @property
    def rule_id(self) -> str:
        return "schedule_validation"

    @property
    def description(self) -> str:
        return "Schedule interval must be properly configured"

    def check(self, tree: ast.AST, file_path: str, source_code: str) -> List[LintIssue]:
        issues = []
        allow_none = self.config.get("allow_none", False)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "DAG":
                    schedule_value = self._extract_schedule(node)
                    if schedule_value is None and not allow_none:
                        issues.append(
                            self.create_issue(
                                "schedule_interval must be explicitly set",
                                file_path,
                                node.lineno,
                                node.col_offset,
                            )
                        )

        return issues

    def _extract_schedule(self, node: ast.Call) -> Optional[Any]:
        """Extract schedule_interval parameter from a DAG() call."""
        for keyword in node.keywords:
            if keyword.arg in ("schedule_interval", "schedule"):
                return keyword.value
        return None
