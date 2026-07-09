"""Rule for validating DAG owner."""

import ast
from typing import List, Optional, Tuple

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
        valid_owners = self.config["valid_owners"]

        for node in self._find_default_args_dicts(tree):
            has_owner_key, owner_value = self._extract_owner_from_dict(node)
            if not has_owner_key:
                issues.append(
                    self.create_issue(
                        "DAG owner must be specified",
                        file_path,
                        node.lineno,
                        node.col_offset,
                    )
                )
            elif owner_value is None:
                # Owner is present but not a static string (e.g. a variable
                # or Variable.get(...)); cannot validate, so skip.
                continue
            elif not owner_value:
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

    def _extract_owner_from_dict(self, node: ast.Dict) -> Tuple[bool, Optional[str]]:
        """Extract the owner entry from a default_args dictionary node.

        Returns:
            Tuple of (owner key present, owner value). The value is None
            when the key is absent or its value is not a static string.
        """
        for key, value in zip(node.keys, node.values):
            if isinstance(key, ast.Constant) and key.value == "owner":
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    return True, value.value
                return True, None
        return False, None
