"""Rule for validating DAG doc_md documentation."""

import ast
from typing import List, Optional

from daglint.models import LintIssue
from daglint.rules.base import BaseRule


class DocMdValidationRule(BaseRule):
    """Validates that DAGs have doc_md set."""

    @property
    def rule_id(self) -> str:
        return "doc_md_validation"

    @property
    def description(self) -> str:
        return "DAGs must have doc_md set to provide documentation"

    def check(self, tree: ast.AST, file_path: str, source_code: str) -> List[LintIssue]:
        issues = []

        for definition in self._find_dag_definitions(tree):
            doc_md = self._extract_doc_md(definition.get_kwarg("doc_md"))
            if doc_md is None:
                issues.append(
                    self.create_issue(
                        "DAG is missing doc_md documentation",
                        file_path,
                        definition.lineno,
                        definition.col_offset,
                    )
                )
            elif doc_md.strip() == "":
                issues.append(
                    self.create_issue(
                        "DAG doc_md must not be empty",
                        file_path,
                        definition.lineno,
                        definition.col_offset,
                    )
                )

        return issues

    def _extract_doc_md(self, value: Optional[ast.expr]) -> Optional[str]:
        """Extract a doc_md string from its argument value node.

        Returns None if doc_md is absent, the string value if it's a string literal,
        or a non-empty sentinel if it's any other expression (variable, call, etc.).
        """
        if value is None:
            return None
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            return value.value
        # Variable or other expression — treat as non-empty
        return "<expression>"
