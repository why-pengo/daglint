"""Rules for naming conventions (DAG IDs, Task IDs)."""

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
