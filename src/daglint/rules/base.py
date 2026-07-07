"""Base class for all linting rules."""

import ast
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from daglint.config import Config
from daglint.models import LintIssue


class _AirflowDefinition:
    """Base for normalized DAG/task definitions (call or decorator form)."""

    def __init__(
        self,
        call: Optional[ast.Call],
        function_name: Optional[str] = None,
        position: Optional[ast.expr] = None,
    ):
        """Initialize a definition.

        Args:
            call: The instantiation call or decorator call; None for a
                bare decorator
            function_name: Name of the decorated function (decorator form only)
            position: Node to report issues at; defaults to the call
        """
        self.call = call
        self.function_name = function_name
        anchor = position if position is not None else call
        self.lineno = anchor.lineno if anchor is not None else 0
        self.col_offset = anchor.col_offset if anchor is not None else 0

    def get_kwarg(self, name: str) -> Optional[ast.expr]:
        """Return the AST value node for a keyword argument, if present.

        Args:
            name: Keyword argument name

        Returns:
            The value node, or None if the argument is absent
        """
        if self.call is None:
            return None
        for keyword in self.call.keywords:
            if keyword.arg == name:
                return keyword.value
        return None


class DagDefinition(_AirflowDefinition):
    """A DAG defined either as a DAG(...) call or an @dag-decorated function.

    Normalizes the two forms so rules can read DAG arguments and the
    effective DAG ID without caring how the DAG was declared.
    """

    @property
    def dag_id(self) -> Optional[str]:
        """Effective DAG ID: explicit argument, else the decorated function name.

        Returns None when a dag_id argument is present but not a static
        string — a dynamic ID overrides the function-name default in
        Airflow, so nothing can be validated.
        """
        if self.call is not None:
            if self.call.args:
                first = self.call.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    return first.value
                return None
            value = self.get_kwarg("dag_id")
            if value is not None:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    return value.value
                return None
        return self.function_name


class TaskDefinition(_AirflowDefinition):
    """A task defined either as an *Operator(...) call or an @task-decorated function.

    Normalizes the two forms so rules can read the effective task ID
    without caring how the task was declared.
    """

    @property
    def task_id(self) -> Optional[str]:
        """Effective task ID: explicit task_id argument, else the decorated function name.

        Returns None when a task_id argument is present but not a static
        string — a dynamic ID overrides the function-name default in
        Airflow, so nothing can be validated.
        """
        if self.call is not None:
            value = self.get_kwarg("task_id")
            if value is not None:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    return value.value
                return None
        return self.function_name


class BaseRule(ABC):
    """Base class for all linting rules."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the rule.

        Args:
            config: Rule-specific configuration. Keys not provided fall
                back to the rule's entry in the default config, so the
                default config is the single source of truth for
                default values (#50).
        """
        self.config = {**Config.default_rule_config(self.rule_id), **(config or {})}
        self.severity = self.config.get("severity", "error")

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique identifier for the rule."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of the rule."""
        pass

    @abstractmethod
    def check(self, tree: ast.AST, file_path: str, source_code: str) -> List[LintIssue]:
        """Check the AST for violations of this rule.

        Args:
            tree: Abstract syntax tree of the file
            file_path: Path to the file being checked
            source_code: Source code of the file

        Returns:
            List of linting issues found
        """
        pass

    def _is_operator_call(self, node: ast.Call) -> bool:
        """Check if a call is an operator instantiation.

        Args:
            node: AST Call node to check

        Returns:
            True if the call is an Operator instantiation
        """
        if isinstance(node.func, ast.Name):
            return node.func.id.endswith("Operator")
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr.endswith("Operator")
        return False

    def _is_dag_call(self, node: ast.Call) -> bool:
        """Check if a call is a DAG instantiation.

        Args:
            node: AST Call node to check

        Returns:
            True if the call is a DAG instantiation
        """
        if isinstance(node.func, ast.Name):
            return node.func.id == "DAG"
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr == "DAG"
        return False

    def _is_dag_decorator(self, node: ast.expr) -> bool:
        """Check if a decorator node is an @dag decorator (bare or called).

        Args:
            node: Entry from a FunctionDef's decorator_list

        Returns:
            True if the decorator is @dag, @dag(...), or @<module>.dag(...)
        """
        target = node.func if isinstance(node, ast.Call) else node
        if isinstance(target, ast.Name):
            return target.id == "dag"
        elif isinstance(target, ast.Attribute):
            return target.attr == "dag"
        return False

    def _find_dag_definitions(self, tree: ast.AST) -> List[DagDefinition]:
        """Find every DAG definition in a file.

        Matches both declaration styles:
            DAG(...) / <module>.DAG(...) instantiation calls
            @dag / @dag(...) decorated functions (TaskFlow API)

        Args:
            tree: Abstract syntax tree of the file

        Returns:
            List of normalized DAG definitions
        """
        definitions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and self._is_dag_call(node):
                definitions.append(DagDefinition(call=node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    if self._is_dag_decorator(decorator):
                        call = decorator if isinstance(decorator, ast.Call) else None
                        definitions.append(DagDefinition(call=call, function_name=node.name, position=decorator))
                        break
        return definitions

    def _is_task_decorator(self, node: ast.expr) -> bool:
        """Check if a decorator node is an @task decorator (bare, called, or flavored).

        Matches @task, @task(...), flavors like @task.branch(...), and
        module-qualified forms like @decorators.task(...).

        Args:
            node: Entry from a FunctionDef's decorator_list

        Returns:
            True if the decorator declares a TaskFlow task
        """
        target = node.func if isinstance(node, ast.Call) else node
        while isinstance(target, ast.Attribute):
            if target.attr == "task":
                return True
            target = target.value
        return isinstance(target, ast.Name) and target.id == "task"

    def _find_task_definitions(self, tree: ast.AST) -> List[TaskDefinition]:
        """Find every task definition in a file.

        Matches both declaration styles:
            *Operator(...) instantiation calls
            @task / @task(...) / @task.<flavor> decorated functions (TaskFlow API)

        Args:
            tree: Abstract syntax tree of the file

        Returns:
            List of normalized task definitions
        """
        definitions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and self._is_operator_call(node):
                definitions.append(TaskDefinition(call=node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    if self._is_task_decorator(decorator):
                        call = decorator if isinstance(decorator, ast.Call) else None
                        definitions.append(TaskDefinition(call=call, function_name=node.name, position=decorator))
                        break
        return definitions

    def _find_default_args_dicts(self, tree: ast.AST) -> List[ast.Dict]:
        """Find dict literals bound to default_args.

        Matches all forms:
            default_args = {...}
            DAG(..., default_args={...})
            @dag(default_args={...})

        Args:
            tree: Abstract syntax tree of the file

        Returns:
            List of AST Dict nodes bound to default_args
        """
        dicts = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Dict) and any(
                    isinstance(target, ast.Name) and target.id == "default_args" for target in node.targets
                ):
                    dicts.append(node.value)
        for definition in self._find_dag_definitions(tree):
            value = definition.get_kwarg("default_args")
            if isinstance(value, ast.Dict):
                dicts.append(value)
        return dicts

    def create_issue(self, message: str, file_path: str, line: int, column: int = 0) -> LintIssue:
        """Create a linting issue.

        Args:
            message: Issue message
            file_path: Path to the file
            line: Line number
            column: Column number

        Returns:
            LintIssue instance
        """
        return LintIssue(
            rule_id=self.rule_id,
            message=message,
            file_path=file_path,
            line=line,
            column=column,
            severity=self.severity,
        )
