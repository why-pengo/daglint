"""Per-file symbol resolution for import-aware detection (#55).

Detection used to be purely name-based, so aliased imports
(`from airflow import DAG as Dag`) were invisible and unrelated
same-named symbols (`from mylib import DAG`) false-positived. A
SymbolTable maps each local name to its origin so detection can be
strict: import-bound names are authoritative, and names with no
binding at all are surfaced by the unresolved_airflow_symbol rule
instead of being matched or silently skipped.
"""

import ast
from typing import Dict, List, Optional

# Classification of a call/decorator target against a detection pattern.
MATCH = "match"
NO_MATCH = "no_match"
UNRESOLVED = "unresolved"

_LOCAL_ORIGIN = "<local>"


def _is_airflow_module(module: str) -> bool:
    """Check whether a dotted module path belongs to Airflow.

    Any `airflow.*` module counts — enumerating public paths would
    break across Airflow versions (2.x `airflow.models.dag` vs 3.x
    `airflow.sdk`), and a non-detection symbol imported from airflow
    can never satisfy a leaf-name check anyway.
    """
    return module == "airflow" or module.startswith("airflow.")


def leaf_name(node: ast.expr) -> Optional[str]:
    """Rightmost name of a Name/Attribute target, as written in source."""
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


class SymbolTable:
    """Maps a file's local names to their import origins.

    Imports bind names to dotted origin paths (`from airflow import
    DAG as Dag` binds `Dag` to `airflow.DAG`; `import airflow.decorators
    as ad` binds `ad` to `airflow.decorators`). Class and function
    definitions bind their name to a local origin, so in-file custom
    operators are recognized and a local `def dag` shadows the airflow
    decorator. Imports win over local definitions when both bind the
    same name. A `from <airflow module> import *` makes name-matching
    unbound symbols resolve to airflow instead of unresolved.
    """

    def __init__(self, tree: ast.AST):
        """Build the table from a file's AST.

        Args:
            tree: Abstract syntax tree of the file
        """
        self._bindings: Dict[str, str] = {}
        self._airflow_star = False
        local_names: List[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self._bind_import(node)
            elif isinstance(node, ast.ImportFrom):
                self._bind_import_from(node)
            elif isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                local_names.append(node.name)
        # setdefault so imports win over local definitions of the same name
        for name in local_names:
            self._bindings.setdefault(name, f"{_LOCAL_ORIGIN}.{name}")

    def _bind_import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.asname:
                self._bindings[alias.asname] = alias.name
            else:
                # `import airflow.decorators` binds only `airflow`
                top_level = alias.name.split(".", 1)[0]
                self._bindings[top_level] = top_level

    def _bind_import_from(self, node: ast.ImportFrom) -> None:
        module = "." * node.level + (node.module or "")
        for alias in node.names:
            if alias.name == "*":
                if _is_airflow_module(module):
                    self._airflow_star = True
                continue
            local = alias.asname or alias.name
            self._bindings[local] = f"{module}.{alias.name}"

    def resolve_target(self, node: ast.expr) -> Optional[str]:
        """Resolve a Name/Attribute chain to its full dotted origin path.

        `ad.dag` resolves to `airflow.decorators.dag` when `ad` is bound
        to `airflow.decorators`.

        Args:
            node: Call func or decorator target

        Returns:
            The dotted origin path, or None when the base of the chain
            is not a bound name
        """
        attrs: List[str] = []
        while isinstance(node, ast.Attribute):
            attrs.append(node.attr)
            node = node.value
        if not isinstance(node, ast.Name):
            return None
        origin = self._bindings.get(node.id)
        if origin is None:
            return None
        return ".".join([origin] + attrs[::-1])

    def classify(self, node: ast.expr, expected: str) -> str:
        """Classify a target against an airflow-owned symbol name.

        Args:
            node: Call func or decorator target
            expected: The airflow symbol name (e.g. "DAG", "dag", "task")

        Returns:
            MATCH when the target resolves to the symbol in an airflow
            module (or matches it by name under an airflow star import),
            UNRESOLVED when it matches by name but nothing binds it,
            NO_MATCH otherwise
        """
        origin = self.resolve_target(node)
        if origin is not None:
            module, _, leaf = origin.rpartition(".")
            if leaf == expected and _is_airflow_module(module):
                return MATCH
            return NO_MATCH
        if leaf_name(node) != expected:
            return NO_MATCH
        return MATCH if self._airflow_star else UNRESOLVED

    def classify_chain(self, node: ast.expr, expected: str) -> str:
        """Classify a dotted chain that may carry flavor attributes.

        `@task.branch` and `@ad.task.branch` declare tasks even though
        the chain does not end in `task`; each prefix of the chain is
        tried against the expected symbol.

        Args:
            node: Decorator target (already unwrapped from a Call)
            expected: The airflow symbol name (e.g. "task")

        Returns:
            The first non-NO_MATCH classification of any chain prefix,
            or NO_MATCH
        """
        while True:
            status = self.classify(node, expected)
            if status != NO_MATCH:
                return status
            if not isinstance(node, ast.Attribute):
                return NO_MATCH
            node = node.value

    def classify_operator(self, node: ast.expr) -> str:
        """Classify a call target as an Operator by resolved-name suffix.

        Custom operators live in user modules, so the origin is not
        restricted to airflow — the *Operator suffix check applies to
        the resolved origin name instead of the local alias. Locally
        defined operator classes resolve to themselves and match.

        Args:
            node: Call func (or the target of a .partial(...) chain)

        Returns:
            MATCH, UNRESOLVED, or NO_MATCH
        """
        origin = self.resolve_target(node)
        if origin is not None:
            leaf = origin.rpartition(".")[2]
            return MATCH if leaf.endswith("Operator") else NO_MATCH
        written = leaf_name(node)
        if written is None or not written.endswith("Operator"):
            return NO_MATCH
        return MATCH if self._airflow_star else UNRESOLVED
