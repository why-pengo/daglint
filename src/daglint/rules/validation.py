"""Rules for validation of DAG structure and uniqueness."""

import ast
from typing import List, Optional

from daglint.models import LintIssue
from daglint.rules.base import BaseRule


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
