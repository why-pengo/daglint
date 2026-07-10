"""Task-scoped rules must treat all task declaration spellings identically (#34)."""

import ast

import pytest

from daglint.rules import NoDuplicateTaskIDsRule, TaskIDConventionRule

# The same violating task — bad task ID — spelled six ways.
SPELLINGS = {
    "operator": "from airflow.operators.python import PythonOperator\nt = PythonOperator(task_id='BadTaskName')\n",
    "operator_attribute": "import airflow.operators.python as operators\nt = operators.PythonOperator(task_id='BadTaskName')\n",
    "taskflow_bare": "from airflow.decorators import task\n\n@task\ndef BadTaskName():\n    pass\n",
    "taskflow_call": "from airflow.decorators import task\n\n@task()\ndef BadTaskName():\n    pass\n",
    "taskflow_flavor": "from airflow.decorators import task\n\n@task.branch\ndef BadTaskName():\n    pass\n",
    "taskflow_explicit_id": "from airflow.decorators import task\n\n@task(task_id='BadTaskName')\ndef fine_name():\n    pass\n",
}


@pytest.mark.parametrize("spelling", sorted(SPELLINGS))
def test_task_id_convention_covers_all_spellings(spelling):
    """A violating task ID must be flagged regardless of declaration spelling."""
    code = SPELLINGS[spelling]
    tree = ast.parse(code)
    rule = TaskIDConventionRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1, f"{spelling} spelling not flagged"
    assert "Task ID 'BadTaskName' does not match pattern" in issues[0].message


def test_duplicate_ids_across_operator_and_taskflow():
    """Duplicate effective task IDs are caught across declaration styles."""
    code = """
from airflow.decorators import task
from airflow.operators.python import PythonOperator

@task
def load():
    pass

t = PythonOperator(task_id='load')
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1
    assert "Duplicate task_id 'load'" in issues[0].message


def test_duplicate_explicit_ids_on_taskflow_tasks():
    """Two @task functions sharing an explicit task_id are caught."""
    code = """
from airflow.decorators import task

@task(task_id='duplicate_id')
def first():
    pass

@task(task_id='duplicate_id')
def second():
    pass
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1
    assert "Duplicate task_id 'duplicate_id'" in issues[0].message


def test_distinct_taskflow_tasks_are_clean():
    """@task functions with distinct names produce no duplicate issues."""
    code = """
from airflow.decorators import task

@task
def extract():
    pass

@task
def load():
    pass
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 0


def test_dynamic_task_id_skipped():
    """A dynamic task_id= overrides the function name; neither is validated."""
    code = """
from airflow.decorators import task

@task(task_id=DYNAMIC_ID)
def BadTaskName():
    pass
"""
    tree = ast.parse(code)
    rule = TaskIDConventionRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 0


def test_task_group_decorator_is_not_a_task():
    """@task_group is excluded from task detection (#51 owns its semantics)."""
    code = """
from airflow.decorators import task_group

@task_group
def BadGroupName():
    pass
"""
    tree = ast.parse(code)
    for rule in (TaskIDConventionRule(), NoDuplicateTaskIDsRule()):
        assert rule.check(tree, "test.py", code) == []
