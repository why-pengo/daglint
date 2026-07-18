"""Rules for import-resolution of Airflow symbols."""

import ast
from typing import List, Optional, Tuple

from daglint.models import LintIssue
from daglint.rules.base import BaseRule
from daglint.rules.symbols import UNRESOLVED, SymbolTable, leaf_name


class UnresolvedAirflowSymbolRule(BaseRule):
    """Flags Airflow-looking symbols that no import or local definition binds.

    Detection is strict (#55): a name only counts as a DAG, task, or
    task group when it is traceable to its Airflow origin. Silently
    skipping an untraceable name would make a file lint green without
    ever being examined, so this rule surfaces the skip instead — a
    star import, generated fragment, or dynamically bound name shows
    up as an info issue rather than an invisible false negative.
    """

    @property
    def rule_id(self) -> str:
        return "unresolved_airflow_symbol"

    @property
    def description(self) -> str:
        return "Airflow-looking symbols must be traceable to an import or local definition"

    def check(self, tree: ast.AST, file_path: str, source_code: str) -> List[LintIssue]:
        table = self._symbol_table(tree)
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                finding = self._classify_call(node, table)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    finding = self._classify_decorator(decorator, table)
                    if finding is not None:
                        name, kind = finding
                        issues.append(self._unresolved_issue(name, kind, file_path, decorator))
                continue
            else:
                continue
            if finding is not None:
                name, kind = finding
                issues.append(self._unresolved_issue(name, kind, file_path, node))
        return issues

    def _classify_call(self, node: ast.Call, table: SymbolTable) -> Optional[Tuple[str, str]]:
        """Return (name, kind) when a call matches detection by name but is unbound."""
        func = node.func
        if table.classify(func, "DAG") == UNRESOLVED:
            return "DAG", "a DAG"
        if table.classify(func, "TaskGroup") == UNRESOLVED:
            return "TaskGroup", "a task group"
        if table.classify_operator(func) == UNRESOLVED:
            return leaf_name(func) or "", "an operator task"
        if isinstance(func, ast.Attribute) and func.attr == "partial":
            if table.classify_operator(func.value) == UNRESOLVED:
                return leaf_name(func.value) or "", "an operator task"
        return None

    def _classify_decorator(self, node: ast.expr, table: SymbolTable) -> Optional[Tuple[str, str]]:
        """Return (name, kind) when a decorator matches detection by name but is unbound."""
        target = node.func if isinstance(node, ast.Call) else node
        for expected, kind in (
            ("dag", "the @dag decorator"),
            ("task_group", "the @task_group decorator"),
            ("setup", "the @setup decorator"),
            ("teardown", "the @teardown decorator"),
        ):
            if table.classify(target, expected) == UNRESOLVED:
                return expected, kind
        if table.classify_chain(target, "task") == UNRESOLVED:
            return "task", "the @task decorator"
        return None

    def _unresolved_issue(self, name: str, kind: str, file_path: str, node: ast.expr) -> LintIssue:
        return self.create_issue(
            f"'{name}' matches detection for {kind} by name but is not traceable to any "
            f"import or local definition; rules will not lint it",
            file_path,
            node.lineno,
            node.col_offset,
        )
