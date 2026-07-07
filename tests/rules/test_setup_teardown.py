"""Tests for @setup / @teardown decorator support (#54).

Both decorators turn a plain function into a TaskFlow task whose
task_id is the function name; neither accepts a task_id. They get
ordinary task treatment — naming validation, duplicate detection,
group prefixes — with no special-case rules.
"""

import ast

from daglint.rules import NoDuplicateTaskIDsRule, TaskIDConventionRule


def test_setup_function_name_is_validated():
    """@setup functions are tasks; their names get naming validation."""
    code = """
from airflow.decorators import setup

@setup
def CreateCluster():
    pass
"""
    tree = ast.parse(code)
    rule = TaskIDConventionRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1
    assert "Task ID 'CreateCluster'" in issues[0].message


def test_teardown_called_form_is_a_task():
    """@teardown(...) with kwargs is detected like the bare form."""
    code = """
from airflow.decorators import teardown

@teardown(on_failure_fail_dagrun=True)
def delete_cluster():
    pass

t = EmptyOperator(task_id="delete_cluster")
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1
    assert "Duplicate task_id 'delete_cluster'" in issues[0].message


def test_distinct_setup_and_teardown_tasks_are_clean():
    """Well-named, distinct setup/teardown tasks raise nothing."""
    code = """
from airflow.decorators import setup, teardown

@setup
def create_cluster():
    pass

@teardown
def delete_cluster():
    pass
"""
    tree = ast.parse(code)
    for rule in (TaskIDConventionRule(), NoDuplicateTaskIDsRule()):
        assert rule.check(tree, "test.py", code) == []


def test_stacked_task_decorator_provides_explicit_id():
    """@setup stacked over @task(task_id=...) uses the explicit id, once."""
    code = """
from airflow.decorators import setup, task

@setup
@task(task_id="explicit_id")
def create_cluster():
    pass

t = EmptyOperator(task_id="explicit_id")
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1
    assert "Duplicate task_id 'explicit_id'" in issues[0].message


def test_setup_inside_task_group_gets_group_prefix():
    """Setup/teardown tasks in a group carry the group prefix (#51)."""
    code = """
with TaskGroup("cluster") as tg:
    @setup
    def create():
        pass

t = EmptyOperator(task_id="create")
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    assert rule.check(tree, "test.py", code) == []


def test_module_qualified_decorator_form():
    """@decorators.setup is recognized like the bare form."""
    code = """
from airflow import decorators

@decorators.teardown
def BadTeardownName():
    pass
"""
    tree = ast.parse(code)
    rule = TaskIDConventionRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1


def test_as_setup_and_as_teardown_are_call_sites():
    """.as_setup()/.as_teardown() convert existing tasks; no new definition."""
    code = """
t1 = EmptyOperator(task_id="cleanup").as_teardown()
t2 = create_cluster().as_setup()
"""
    tree = ast.parse(code)
    convention_issues = TaskIDConventionRule().check(tree, "test.py", code)
    duplicate_issues = NoDuplicateTaskIDsRule().check(tree, "test.py", code)
    assert convention_issues == []
    assert duplicate_issues == []


def test_unrelated_decorators_not_matched():
    """Decorators merely containing 'setup' in the name are not tasks."""
    code = """
@setup_hook
def configure():
    pass

@pytest.fixture
def setup_db():
    pass
"""
    tree = ast.parse(code)
    for rule in (TaskIDConventionRule(), NoDuplicateTaskIDsRule()):
        assert rule.check(tree, "test.py", code) == []
