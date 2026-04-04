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

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "DAG":
                    doc_md = self._extract_doc_md(node)
                    if doc_md is None:
                        issues.append(
                            self.create_issue(
                                "DAG is missing doc_md documentation",
                                file_path,
                                node.lineno,
                                node.col_offset,
                            )
                        )
                    elif doc_md.strip() == "":
                        issues.append(
                            self.create_issue(
                                "DAG doc_md must not be empty",
                                file_path,
                                node.lineno,
                                node.col_offset,
                            )
                        )

        return issues

    def _extract_doc_md(self, node: ast.Call) -> Optional[str]:
        """Extract doc_md value from a DAG() call.

        Returns None if doc_md is absent, the string value if it's a string literal,
        or a non-empty sentinel if it's any other expression (variable, call, etc.).
        """
        for keyword in node.keywords:
            if keyword.arg == "doc_md":
                if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                    return keyword.value.value
                # Variable or other expression — treat as non-empty
                return "<expression>"
        return None
