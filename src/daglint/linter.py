"""Core linting functionality."""

import ast
import inspect
from pathlib import Path
from typing import List

from daglint.config import Config
from daglint.models import LintIssue
from daglint.rules import AVAILABLE_RULES


class DAGLinter:
    """Main linter class for analyzing DAG files."""

    def __init__(self, config: Config, verbose: bool = False):
        """Initialize the linter.

        Args:
            config: Configuration object
            verbose: Enable verbose output
        """
        self.config = config
        self.verbose = verbose
        self.rules = self._load_rules()

    def _load_rules(self) -> List:
        """Load enabled rules based on configuration.

        Returns:
            List of enabled rule instances
        """
        enabled_rules = []
        for rule_id, rule_class in AVAILABLE_RULES.items():
            if inspect.isabstract(rule_class):
                continue  # Skip abstract base classes
            if self.config.is_rule_enabled(rule_id):
                rule_config = self.config.get_rule_config(rule_id)
                rule_instance = rule_class(rule_config)
                enabled_rules.append(rule_instance)
        return enabled_rules

    def lint_file(self, file_path: str) -> List[LintIssue]:
        """Lint a single DAG file.

        Args:
            file_path: Path to the DAG file

        Returns:
            List of linting issues found
        """
        issues = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()

            # Parse the file into an AST
            tree = ast.parse(source_code, filename=file_path)

            # Run each enabled rule
            for rule in self.rules:
                rule_issues = rule.check(tree, file_path, source_code)
                issues.extend(rule_issues)

        except SyntaxError as e:
            issues.append(
                LintIssue(
                    rule_id="syntax_error",
                    message=f"Syntax error: {e.msg}",
                    file_path=file_path,
                    line=e.lineno or 0,
                    severity="error",
                )
            )
        except Exception as e:
            if self.verbose:
                issues.append(
                    LintIssue(
                        rule_id="lint_error",
                        message=f"Error linting file: {str(e)}",
                        file_path=file_path,
                        line=0,
                        severity="error",
                    )
                )

        return sorted(issues, key=lambda x: x.line)

    def lint_directory(self, dir_path: str) -> dict:
        """Lint all Python files in a directory.

        Args:
            dir_path: Path to directory

        Returns:
            Dictionary mapping file paths to their issues
        """
        directory = Path(dir_path)
        results = {}

        for py_file in directory.rglob("*.py"):
            issues = self.lint_file(str(py_file))
            if issues:
                results[str(py_file)] = issues

        return results
