"""Rule for validating DAG owner."""

import ast
from typing import List, Optional

from daglint.models import LintIssue
from daglint.rules.base import BaseRule


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
                else:
                    # Owner key is missing
                    issues.append(
                        self.create_issue(
                            "DAG owner must be specified",
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
                    if isinstance(value.value, str):
                        return value.value
        return None
