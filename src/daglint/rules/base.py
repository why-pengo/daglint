"""Base class for all linting rules."""

import ast
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union

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

    def __init__(
        self,
        call: Optional[ast.Call],
        function_name: Optional[str] = None,
        position: Optional[ast.expr] = None,
        group_prefix: Tuple[str, ...] = (),
    ):
        """Initialize a task definition.

        Args:
            call: The instantiation call or decorator call; None for a
                bare decorator
            function_name: Name of the decorated function (decorator form only)
            position: Node to report issues at; defaults to the call
            group_prefix: Group ID segments of the enclosing task groups,
                outermost first; dynamic group IDs appear as unique
                placeholder segments
        """
        super().__init__(call, function_name, position)
        self.group_prefix = group_prefix

    @property
    def task_id(self) -> Optional[str]:
        """Leaf task ID: explicit task_id argument, else the decorated function name.

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

    @property
    def effective_task_id(self) -> Optional[str]:
        """Runtime task ID: the leaf task_id prefixed by enclosing group IDs.

        Mirrors Airflow's `group.subgroup.task` dotted paths, so two
        same-named tasks in different groups have distinct effective IDs.
        """
        task_id = self.task_id
        if task_id is None:
            return None
        return ".".join(self.group_prefix + (task_id,))


class TaskGroupDefinition(_AirflowDefinition):
    """A task group defined as a TaskGroup(...) call or an @task_group-decorated function.

    Normalizes the two forms so rules can read the group ID without
    caring how the group was declared.
    """

    @property
    def group_id(self) -> Optional[str]:
        """Group ID: explicit argument, else the decorated function name.

        Returns None when a group_id argument is present but not a
        static string — nothing can be validated.
        """
        if self.call is not None:
            value = self.get_kwarg("group_id")
            # Positional group_id exists only on TaskGroup(...) calls. In the
            # @task_group(...) decorator form the first positional binds to
            # python_callable and Airflow drops non-callables at runtime, so
            # the group ID stays the function name.
            if value is None and self.function_name is None and self.call.args:
                value = self.call.args[0]
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

    def _is_operator_partial_call(self, node: ast.Call) -> bool:
        """Check if a call is a dynamic-mapping Operator.partial(...) definition.

        In Airflow's dynamic task mapping, `<X>Operator.partial(task_id=...)`
        is the task definition site — it carries the constructor kwargs —
        while the chained `.expand(...)` only supplies mapped arguments (#52).
        TaskFlow `.partial()` calls (on decorated functions, not Operator
        classes) are call sites of an existing definition and do not match.

        Args:
            node: AST Call node to check

        Returns:
            True if the call is an Operator.partial(...) definition
        """
        if not (isinstance(node.func, ast.Attribute) and node.func.attr == "partial"):
            return False
        target = node.func.value
        if isinstance(target, ast.Name):
            return target.id.endswith("Operator")
        elif isinstance(target, ast.Attribute):
            return target.attr.endswith("Operator")
        return False

    def _is_task_override_call(self, node: ast.Call) -> bool:
        """Check if a call re-identifies a TaskFlow task via .override(task_id=...).

        `my_task.override(task_id="other_id")(...)` instantiates the task
        under a new ID at the call site (#53). Only calls that pass a
        task_id are re-identifications; .override(pool=...) and friends
        do not change task identity and are ignored, as are chains on
        call results (only Name/Attribute targets match).

        Args:
            node: AST Call node to check

        Returns:
            True if the call is a task_id-overriding .override(...) call
        """
        if not (isinstance(node.func, ast.Attribute) and node.func.attr == "override"):
            return False
        if not isinstance(node.func.value, (ast.Name, ast.Attribute)):
            return False
        return any(keyword.arg == "task_id" for keyword in node.keywords)

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

    def _is_task_group_call(self, node: ast.Call) -> bool:
        """Check if a call is a TaskGroup instantiation.

        Args:
            node: AST Call node to check

        Returns:
            True if the call is a TaskGroup instantiation
        """
        if isinstance(node.func, ast.Name):
            return node.func.id == "TaskGroup"
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr == "TaskGroup"
        return False

    def _is_task_group_decorator(self, node: ast.expr) -> bool:
        """Check if a decorator node is an @task_group decorator (bare or called).

        Args:
            node: Entry from a FunctionDef's decorator_list

        Returns:
            True if the decorator is @task_group, @task_group(...), or
            @<module>.task_group(...)
        """
        target = node.func if isinstance(node, ast.Call) else node
        if isinstance(target, ast.Name):
            return target.id == "task_group"
        elif isinstance(target, ast.Attribute):
            return target.attr == "task_group"
        return False

    def _group_segment(self, definition: TaskGroupDefinition) -> Optional[str]:
        """Segment a group contributes to the effective IDs of nested tasks.

        Returns None for groups that add no prefix (a literal
        prefix_group_id=False). A group whose ID — or prefix toggle —
        is not statically known yields a placeholder unique to its
        position, so its tasks can never collide with another group's.

        Args:
            definition: The group to compute a segment for

        Returns:
            The segment string, or None when the group adds no prefix
        """
        prefix_flag = definition.get_kwarg("prefix_group_id")
        if prefix_flag is not None:
            if isinstance(prefix_flag, ast.Constant) and prefix_flag.value is False:
                return None
            if not (isinstance(prefix_flag, ast.Constant) and prefix_flag.value is True):
                return f"<group:L{definition.lineno}:C{definition.col_offset}>"
        group_id = definition.group_id
        if group_id is not None:
            return group_id
        return f"<group:L{definition.lineno}:C{definition.col_offset}>"

    def _find_task_definitions(self, tree: ast.AST) -> List[TaskDefinition]:
        """Find every task definition in a file.

        Matches all declaration styles:
            *Operator(...) instantiation calls
            *Operator.partial(task_id=...) dynamic-mapping definitions (#52)
            @task / @task(...) / @task.<flavor> decorated functions (TaskFlow API)
            <task>.override(task_id=...) re-identification call sites (#53)

        `.expand(...)` / `.expand_kwargs(...)` calls and TaskFlow
        `.partial()` calls are call sites of an existing definition,
        never a second definition. An .override(...) without task_id
        does not change task identity and is likewise ignored.

        Tasks lexically nested in `with TaskGroup(...)` blocks or
        @task_group-decorated functions carry the enclosing group IDs
        as their group_prefix (#51).

        Args:
            tree: Abstract syntax tree of the file

        Returns:
            List of normalized task definitions
        """
        definitions: List[TaskDefinition] = []
        for node in ast.iter_child_nodes(tree):
            self._collect_task_definitions(node, (), definitions)
        return definitions

    def _collect_task_definitions(self, node: ast.AST, prefix: Tuple[str, ...], definitions: List[TaskDefinition]) -> None:
        """Recursively collect task definitions, tracking the group-prefix stack.

        Args:
            node: Node to visit
            prefix: Group ID segments of the enclosing task groups
            definitions: Accumulator for found task definitions
        """
        if isinstance(node, (ast.With, ast.AsyncWith)):
            self._collect_from_with(node, prefix, definitions)
            return
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._collect_from_function(node, prefix, definitions)
            return
        if isinstance(node, ast.Call) and (
            self._is_operator_call(node) or self._is_operator_partial_call(node) or self._is_task_override_call(node)
        ):
            definitions.append(TaskDefinition(call=node, group_prefix=prefix))
        for child in ast.iter_child_nodes(node):
            self._collect_task_definitions(child, prefix, definitions)

    def _collect_from_with(
        self, node: Union[ast.With, ast.AsyncWith], prefix: Tuple[str, ...], definitions: List[TaskDefinition]
    ) -> None:
        """Collect tasks from a with statement, entering TaskGroup scopes.

        Args:
            node: The With/AsyncWith node
            prefix: Group ID segments of the enclosing task groups
            definitions: Accumulator for found task definitions
        """
        body_prefix = prefix
        for item in node.items:
            context = item.context_expr
            if isinstance(context, ast.Call) and self._is_task_group_call(context):
                segment = self._group_segment(TaskGroupDefinition(call=context))
                if segment is not None:
                    body_prefix = body_prefix + (segment,)
            else:
                self._collect_task_definitions(context, prefix, definitions)
        for child in node.body:
            self._collect_task_definitions(child, body_prefix, definitions)

    def _collect_from_function(
        self,
        node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
        prefix: Tuple[str, ...],
        definitions: List[TaskDefinition],
    ) -> None:
        """Collect tasks from a function definition, entering @task_group scopes.

        Args:
            node: The FunctionDef/AsyncFunctionDef node
            prefix: Group ID segments of the enclosing task groups
            definitions: Accumulator for found task definitions
        """
        body_prefix = prefix
        for decorator in node.decorator_list:
            if self._is_task_group_decorator(decorator):
                call = decorator if isinstance(decorator, ast.Call) else None
                group = TaskGroupDefinition(call=call, function_name=node.name, position=decorator)
                segment = self._group_segment(group)
                if segment is not None:
                    body_prefix = body_prefix + (segment,)
                break
            if self._is_task_decorator(decorator):
                call = decorator if isinstance(decorator, ast.Call) else None
                definitions.append(TaskDefinition(call=call, function_name=node.name, position=decorator, group_prefix=prefix))
                break
        for child in ast.iter_child_nodes(node):
            child_prefix = body_prefix if child in node.body else prefix
            self._collect_task_definitions(child, child_prefix, definitions)

    def _find_task_group_definitions(self, tree: ast.AST) -> List[TaskGroupDefinition]:
        """Find every task group definition in a file.

        Matches both declaration styles:
            TaskGroup(...) / <module>.TaskGroup(...) instantiation calls
            @task_group / @task_group(...) decorated functions (TaskFlow API)

        Args:
            tree: Abstract syntax tree of the file

        Returns:
            List of normalized task group definitions
        """
        definitions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and self._is_task_group_call(node):
                definitions.append(TaskGroupDefinition(call=node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    if self._is_task_group_decorator(decorator):
                        call = decorator if isinstance(decorator, ast.Call) else None
                        definitions.append(TaskGroupDefinition(call=call, function_name=node.name, position=decorator))
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
