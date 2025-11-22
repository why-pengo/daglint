"""Linting rules for DAG files."""

import ast
import re
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


class DAGIDConventionRule(BaseRule):
    """Ensures DAG IDs follow naming conventions."""

    @property
    def rule_id(self) -> str:
        return "dag_id_convention"

    @property
    def description(self) -> str:
        return "DAG IDs must follow the specified naming pattern (default: snake_case)"

    def check(self, tree: ast.AST, file_path: str, source_code: str) -> List[LintIssue]:
        issues = []
        pattern = self.config.get("pattern", r"^[a-z][a-z0-9_]*$")

        for node in ast.walk(tree):
            # Look for DAG instantiation
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "DAG":
                    dag_id = self._extract_dag_id(node)
                    if dag_id and not re.match(pattern, dag_id):
                        issues.append(
                            self.create_issue(
                                f"DAG ID '{dag_id}' does not match pattern '{pattern}'",
                                file_path,
                                node.lineno,
                                node.col_offset,
                            )
                        )

                # Handle context manager (with DAG(...) as dag:)
                elif isinstance(node.func, ast.Attribute) and node.func.attr == "DAG":
                    dag_id = self._extract_dag_id(node)
                    if dag_id and not re.match(pattern, dag_id):
                        issues.append(
                            self.create_issue(
                                f"DAG ID '{dag_id}' does not match pattern '{pattern}'",
                                file_path,
                                node.lineno,
                                node.col_offset,
                            )
                        )

        return issues

    def _extract_dag_id(self, node: ast.Call) -> Optional[str]:
        """Extract DAG ID from a DAG() call."""
        # Check positional arguments
        if node.args and isinstance(node.args[0], ast.Constant):
            return node.args[0].value

        # Check keyword arguments
        for keyword in node.keywords:
            if keyword.arg == "dag_id":
                if isinstance(keyword.value, ast.Constant):
                    return keyword.value.value

        return None


class OwnerValidationRule(BaseRule):
    """Validates DAG owners are specified and valid."""

    @property
    def rule_id(self) -> str:
        return "owner_validation"

    @property
    def description(self) -> str:
        return "DAG owner must be specified and must be from the list of valid owners"

    def check(self, tree: ast.AST, file_path: str, source_code: str) -> List[LintIssue]:
        issues = []
        valid_owners = self.config.get("valid_owners", [])

        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                # Check if this is a default_args dictionary
                owner_value = self._extract_owner_from_dict(node)
                if owner_value is not None:
                    if not owner_value:
                        issues.append(
                            self.create_issue(
                                "DAG owner must be specified",
                                file_path,
                                node.lineno,
                                node.col_offset,
                            )
                        )
                    elif valid_owners and owner_value not in valid_owners:
                        issues.append(
                            self.create_issue(
                                f"Invalid owner '{owner_value}'. Must be one of: {', '.join(valid_owners)}",
                                file_path,
                                node.lineno,
                                node.col_offset,
                            )
                        )

        return issues

    def _extract_owner_from_dict(self, node: ast.Dict) -> Optional[str]:
        """Extract owner value from a dictionary node."""
        for key, value in zip(node.keys, node.values):
            if isinstance(key, ast.Constant) and key.value == "owner":
                if isinstance(value, ast.Constant):
                    return value.value
        return None


class TaskIDConventionRule(BaseRule):
    """Validates task IDs follow naming patterns."""

    @property
    def rule_id(self) -> str:
        return "task_id_convention"

    @property
    def description(self) -> str:
        return "Task IDs must follow the specified naming pattern (default: snake_case)"

    def check(self, tree: ast.AST, file_path: str, source_code: str) -> List[LintIssue]:
        issues = []
        pattern = self.config.get("pattern", r"^[a-z][a-z0-9_]*$")

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check if this is an operator instantiation
                if self._is_operator_call(node):
                    task_id = self._extract_task_id(node)
                    if task_id and not re.match(pattern, task_id):
                        issues.append(
                            self.create_issue(
                                f"Task ID '{task_id}' does not match pattern '{pattern}'",
                                file_path,
                                node.lineno,
                                node.col_offset,
                            )
                        )

        return issues

    def _is_operator_call(self, node: ast.Call) -> bool:
        """Check if a call is an operator instantiation."""
        if isinstance(node.func, ast.Name):
            return node.func.id.endswith("Operator")
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr.endswith("Operator")
        return False

    def _extract_task_id(self, node: ast.Call) -> Optional[str]:
        """Extract task_id from an operator call."""
        for keyword in node.keywords:
            if keyword.arg == "task_id":
                if isinstance(keyword.value, ast.Constant):
                    return keyword.value.value
        return None


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


class TagRequirementsRule(BaseRule):
    """Validates required tags are present."""

    @property
    def rule_id(self) -> str:
        return "tag_requirements"

    @property
    def description(self) -> str:
        return "DAGs must include all required tags"

    def check(self, tree: ast.AST, file_path: str, source_code: str) -> List[LintIssue]:
        issues = []
        required_tags = self.config.get("required_tags", [])

        if not required_tags:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "DAG":
                    tags = self._extract_tags(node)
                    missing_tags = set(required_tags) - set(tags)
                    if missing_tags:
                        issues.append(
                            self.create_issue(
                                f"Missing required tags: {', '.join(missing_tags)}",
                                file_path,
                                node.lineno,
                                node.col_offset,
                            )
                        )

        return issues

    def _extract_tags(self, node: ast.Call) -> List[str]:
        """Extract tags from a DAG() call."""
        for keyword in node.keywords:
            if keyword.arg == "tags":
                if isinstance(keyword.value, ast.List):
                    tags = []
                    for elt in keyword.value.elts:
                        if isinstance(elt, ast.Constant):
                            tags.append(elt.value)
                    return tags
        return []


class NoDuplicateTaskIDsRule(BaseRule):
    """Ensures no duplicate task IDs in a DAG."""

    @property
    def rule_id(self) -> str:
        return "no_duplicate_task_ids"

    @property
    def description(self) -> str:
        return "Task IDs must be unique within a DAG"

    def check(self, tree: ast.AST, file_path: str, source_code: str) -> List[LintIssue]:
        issues = []
        task_ids = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if self._is_operator_call(node):
                    task_id = self._extract_task_id(node)
                    if task_id:
                        if task_id in task_ids:
                            issues.append(
                                self.create_issue(
                                    f"Duplicate task_id '{task_id}' (first seen at line {task_ids[task_id]})",
                                    file_path,
                                    node.lineno,
                                    node.col_offset,
                                )
                            )
                        else:
                            task_ids[task_id] = node.lineno

        return issues

    def _is_operator_call(self, node: ast.Call) -> bool:
        """Check if a call is an operator instantiation."""
        if isinstance(node.func, ast.Name):
            return node.func.id.endswith("Operator")
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr.endswith("Operator")
        return False

    def _extract_task_id(self, node: ast.Call) -> Optional[str]:
        """Extract task_id from an operator call."""
        for keyword in node.keywords:
            if keyword.arg == "task_id":
                if isinstance(keyword.value, ast.Constant):
                    return keyword.value.value
        return None


class RequiredDAGParamsRule(BaseRule):
    """Ensures required DAG parameters are present."""

    @property
    def rule_id(self) -> str:
        return "required_dag_params"

    @property
    def description(self) -> str:
        return "DAGs must include all required parameters"

    def check(self, tree: ast.AST, file_path: str, source_code: str) -> List[LintIssue]:
        issues = []
        required_params = self.config.get("required_params", ["owner", "start_date", "description"])

        for node in ast.walk(tree):
            # Check default_args dict
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "default_args":
                        if isinstance(node.value, ast.Dict):
                            present_params = self._extract_dict_keys(node.value)
                            missing_params = set(required_params) - set(present_params)
                            if missing_params:
                                issues.append(
                                    self.create_issue(
                                        f"Missing required parameters in default_args: {', '.join(missing_params)}",
                                        file_path,
                                        node.lineno,
                                        node.col_offset,
                                    )
                                )

        return issues

    def _extract_dict_keys(self, node: ast.Dict) -> List[str]:
        """Extract string keys from a dictionary node."""
        keys = []
        for key in node.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                keys.append(key.value)
        return keys


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
                    return keyword.value.value
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


# Registry of all available rules
AVAILABLE_RULES = {
    "dag_id_convention": DAGIDConventionRule,
    "owner_validation": OwnerValidationRule,
    "task_id_convention": TaskIDConventionRule,
    "retry_configuration": RetryConfigurationRule,
    "tag_requirements": TagRequirementsRule,
    "no_duplicate_task_ids": NoDuplicateTaskIDsRule,
    "required_dag_params": RequiredDAGParamsRule,
    "catchup_validation": CatchupValidationRule,
    "schedule_validation": ScheduleValidationRule,
}
