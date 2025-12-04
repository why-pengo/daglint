"""Rule for validating required DAG parameters."""

import ast
from typing import List

from daglint.models import LintIssue
from daglint.rules.base import BaseRule


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

