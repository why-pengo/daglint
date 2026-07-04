"""Rule for validating required DAG tags."""

import ast
from typing import List, Optional

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
        issues: list[LintIssue] = []
        required_tags = self.config.get("required_tags", [])

        if not required_tags:
            return issues

        for definition in self._find_dag_definitions(tree):
            tags = self._extract_tags(definition.get_kwarg("tags"))
            missing_tags = set(required_tags) - set(tags)
            if missing_tags:
                issues.append(
                    self.create_issue(
                        f"Missing required tags: {', '.join(sorted(missing_tags))}",
                        file_path,
                        definition.lineno,
                        definition.col_offset,
                    )
                )

        return issues

    def _extract_tags(self, value: Optional[ast.expr]) -> List[str]:
        """Extract string tags from a tags argument value node."""
        tags = []
        if isinstance(value, ast.List):
            for elt in value.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    tags.append(elt.value)
        return tags
