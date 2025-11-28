"""Rules for DAG metadata validation (owner, tags, required params)."""

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

        return issues

    def _extract_owner_from_dict(self, node: ast.Dict) -> Optional[str]:
        """Extract owner value from a dictionary node."""
        for key, value in zip(node.keys, node.values):
            if isinstance(key, ast.Constant) and key.value == "owner":
                if isinstance(value, ast.Constant):
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

