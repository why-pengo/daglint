"""Tests for import-alias resolution in DAG/task detection (#55).

Detection is strict: import-bound names are authoritative, airflow-owned
symbols must trace to an airflow origin, and names that match detection
by name but have no binding raise unresolved_airflow_symbol instead of
matching or being silently skipped.
"""

import ast

from daglint.rules import (
    DAGIDConventionRule,
    GroupIDConventionRule,
    NoDuplicateTaskIDsRule,
    TaskIDConventionRule,
    UnresolvedAirflowSymbolRule,
)


def _issues(rule, code):
    return rule.check(ast.parse(code), "test.py", code)


class TestAliasedImportsAreDetected:
    def test_aliased_dag_import(self):
        """from airflow import DAG as Dag → Dag(...) is a DAG."""
        code = """
from airflow import DAG as Dag

dag = Dag(dag_id="InvalidDAGID")
"""
        issues = _issues(DAGIDConventionRule(), code)
        assert len(issues) == 1
        assert "InvalidDAGID" in issues[0].message

    def test_aliased_dag_decorator(self):
        """from airflow.decorators import dag as d → @d declares a DAG."""
        code = """
from airflow.decorators import dag as d

@d
def InvalidDAGID():
    pass
"""
        issues = _issues(DAGIDConventionRule(), code)
        assert len(issues) == 1

    def test_airflow_sdk_import(self):
        """Airflow 3's airflow.sdk is an airflow origin."""
        code = """
from airflow.sdk import DAG

dag = DAG(dag_id="InvalidDAGID")
"""
        assert len(_issues(DAGIDConventionRule(), code)) == 1

    def test_module_alias_task_flavor_decorator(self):
        """import airflow.decorators as ad → @ad.task.branch declares a task."""
        code = """
import airflow.decorators as ad

@ad.task.branch
def BadTaskName():
    pass
"""
        issues = _issues(TaskIDConventionRule(), code)
        assert len(issues) == 1
        assert "BadTaskName" in issues[0].message

    def test_aliased_operator_import(self):
        """The *Operator suffix applies to the resolved origin name."""
        code = """
from my_company.operators import FooOperator as fo

t = fo(task_id="BadTaskName")
"""
        assert len(_issues(TaskIDConventionRule(), code)) == 1

    def test_aliased_task_group_import(self):
        """from airflow.utils.task_group import TaskGroup as TG → TG(...) is a group."""
        code = """
from airflow.utils.task_group import TaskGroup as TG

with TG("BadGroupName") as tg:
    pass
"""
        assert len(_issues(GroupIDConventionRule(), code)) == 1


class TestImpostorsAreExcluded:
    def test_non_airflow_dag_import(self):
        """from mylib import DAG → DAG(...) is not Airflow's DAG."""
        code = """
from mylib import DAG

dag = DAG(dag_id="InvalidDAGID")
"""
        assert _issues(DAGIDConventionRule(), code) == []
        assert _issues(UnresolvedAirflowSymbolRule(), code) == []

    def test_alias_that_looks_like_an_operator(self):
        """from x import Foo as FooOperator → origin name decides, no match."""
        code = """
from x import Foo as FooOperator

t = FooOperator(task_id="BadTaskName")
"""
        assert _issues(TaskIDConventionRule(), code) == []
        assert _issues(UnresolvedAirflowSymbolRule(), code) == []

    def test_local_def_shadows_dag_decorator(self):
        """A local def dag makes @dag a non-airflow decorator."""
        code = """
def dag(fn):
    return fn

@dag
def InvalidDAGID():
    pass
"""
        assert _issues(DAGIDConventionRule(), code) == []
        assert _issues(UnresolvedAirflowSymbolRule(), code) == []

    def test_non_airflow_task_decorator(self):
        """@mylib.task is not a TaskFlow task."""
        code = """
import mylib

@mylib.task
def BadTaskName():
    pass
"""
        assert _issues(TaskIDConventionRule(), code) == []
        assert _issues(UnresolvedAirflowSymbolRule(), code) == []


class TestLocalDefinitionsBind:
    def test_local_operator_class_is_detected(self):
        """An operator class defined in-file is a task definition site."""
        code = """
from airflow.models import BaseOperator

class MyCustomOperator(BaseOperator):
    pass

t = MyCustomOperator(task_id="BadTaskName")
"""
        assert len(_issues(TaskIDConventionRule(), code)) == 1
        assert _issues(UnresolvedAirflowSymbolRule(), code) == []


class TestStarImports:
    def test_airflow_star_import_binds_matching_names(self):
        """from airflow.models import * → DAG(...) is detected, no warning."""
        code = """
from airflow.models import *

dag = DAG(dag_id="InvalidDAGID")
"""
        assert len(_issues(DAGIDConventionRule(), code)) == 1
        assert _issues(UnresolvedAirflowSymbolRule(), code) == []

    def test_non_airflow_star_import_leaves_names_unresolved(self):
        """from legacy_helpers import * → DAG(...) is unresolved and warned."""
        code = """
from legacy_helpers import *

dag = DAG(dag_id="InvalidDAGID")
"""
        assert _issues(DAGIDConventionRule(), code) == []
        assert len(_issues(UnresolvedAirflowSymbolRule(), code)) == 1


class TestUnresolvedAirflowSymbolRule:
    def test_unbound_dag_call_warns_once(self):
        """A no-import DAG(...) yields exactly one info issue and no DAG issues."""
        code = """
dag = DAG(dag_id="InvalidDAGID")
"""
        assert _issues(DAGIDConventionRule(), code) == []
        issues = _issues(UnresolvedAirflowSymbolRule(), code)
        assert len(issues) == 1
        assert issues[0].severity == "info"
        assert "'DAG'" in issues[0].message

    def test_unbound_operator_call_warns(self):
        code = """
t = PythonOperator(task_id="fetch")
"""
        assert _issues(TaskIDConventionRule(), code) == []
        issues = _issues(UnresolvedAirflowSymbolRule(), code)
        assert len(issues) == 1
        assert "'PythonOperator'" in issues[0].message

    def test_unbound_operator_partial_warns(self):
        code = """
t = PythonOperator.partial(task_id="fetch").expand(op_args=[[1]])
"""
        assert _issues(NoDuplicateTaskIDsRule(), code) == []
        assert len(_issues(UnresolvedAirflowSymbolRule(), code)) == 1

    def test_unbound_decorators_warn(self):
        code = """
@dag
def my_pipeline():
    @task
    def extract():
        pass

    @task.branch
    def fork():
        pass
"""
        issues = _issues(UnresolvedAirflowSymbolRule(), code)
        assert len(issues) == 3

    def test_unbound_task_group_warns(self):
        code = """
with TaskGroup("extract") as tg:
    pass
"""
        issues = _issues(UnresolvedAirflowSymbolRule(), code)
        assert len(issues) == 1
        assert "'TaskGroup'" in issues[0].message

    def test_fully_imported_file_is_clean(self):
        """A file with proper imports raises no unresolved issues."""
        code = """
from airflow import DAG
from airflow.decorators import task
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

with DAG(dag_id="my_dag") as dag:
    with TaskGroup("extract") as tg:
        t = PythonOperator(task_id="fetch")

@task
def transform():
    pass
"""
        assert _issues(UnresolvedAirflowSymbolRule(), code) == []

    def test_unrelated_calls_do_not_warn(self):
        """Ordinary unbound calls are not airflow-looking and stay silent."""
        code = """
result = process(data)
client = make_client(task_id="not_airflow")
"""
        assert _issues(UnresolvedAirflowSymbolRule(), code) == []

    def test_rule_has_metadata(self):
        rule = UnresolvedAirflowSymbolRule()
        assert rule.rule_id == "unresolved_airflow_symbol"
        assert rule.description
        assert rule.severity == "info"
