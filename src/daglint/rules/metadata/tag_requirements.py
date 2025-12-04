"""Rule for validating required DAG tags."""

import ast
from typing import List

from daglint.models import LintIssue
from daglint.rules.base import BaseRule


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

