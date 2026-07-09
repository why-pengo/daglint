"""Rules for naming conventions (DAG IDs, Task IDs, Task Group IDs)."""

import ast
import re
from typing import List

from daglint.models import LintIssue
from daglint.rules.base import BaseRule


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
        pattern = self.config["pattern"]

        for definition in self._find_dag_definitions(tree):
            dag_id = definition.dag_id
            if dag_id and not re.match(pattern, dag_id):
                issues.append(
                    self.create_issue(
                        f"DAG ID '{dag_id}' does not match pattern '{pattern}'",
                        file_path,
                        definition.lineno,
                        definition.col_offset,
                    )
                )

        return issues


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
        pattern = self.config["pattern"]

        for definition in self._find_task_definitions(tree):
            task_id = definition.task_id
            if task_id and not re.match(pattern, task_id):
                issues.append(
                    self.create_issue(
                        f"Task ID '{task_id}' does not match pattern '{pattern}'",
                        file_path,
                        definition.lineno,
                        definition.col_offset,
                    )
                )

        return issues


class GroupIDConventionRule(BaseRule):
    """Ensures task group IDs follow naming conventions."""

    @property
    def rule_id(self) -> str:
        return "group_id_convention"

    @property
    def description(self) -> str:
        return "Task group IDs must follow the specified naming pattern (default: snake_case)"

    def check(self, tree: ast.AST, file_path: str, source_code: str) -> List[LintIssue]:
        issues = []
        pattern = self.config["pattern"]

        for definition in self._find_task_group_definitions(tree):
            group_id = definition.group_id
            if group_id and not re.match(pattern, group_id):
                issues.append(
                    self.create_issue(
                        f"Task group ID '{group_id}' does not match pattern '{pattern}'",
                        file_path,
                        definition.lineno,
                        definition.col_offset,
                    )
                )

        return issues
