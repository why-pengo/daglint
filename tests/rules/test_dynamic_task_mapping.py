"""Tests for dynamic task mapping support (#52).

`<X>Operator.partial(task_id=...)` is the definition site of a mapped
classic operator and is subject to task rules; `.expand(...)`,
`.expand_kwargs(...)`, and TaskFlow `.partial()` calls are call sites
of an existing definition and must never count as a second one.
"""

import ast

from daglint.rules import NoDuplicateTaskIDsRule, TaskIDConventionRule


def test_partial_task_id_is_validated():
    """task_id passed to Operator.partial(...) gets naming validation."""
    code = """
t = PythonOperator.partial(task_id="BadMappedName", python_callable=f).expand(op_args=[[1]])
"""
    tree = ast.parse(code)
    rule = TaskIDConventionRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1
    assert "Task ID 'BadMappedName'" in issues[0].message


def test_mapped_task_collides_with_regular_task():
    """A mapped task and a regular task with the same id are duplicates."""
    code = """
t1 = PythonOperator.partial(task_id="copy_files", python_callable=f).expand(op_args=[[1]])
t2 = PythonOperator(task_id="copy_files", python_callable=f)
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1
    assert "Duplicate task_id 'copy_files'" in issues[0].message


def test_two_mapped_tasks_with_same_id_are_duplicates():
    """Two .partial() definitions with the same task_id are duplicates."""
    code = """
t1 = PythonOperator.partial(task_id="copy_files", python_callable=f).expand(op_args=[[1]])
t2 = PythonOperator.partial(task_id="copy_files", python_callable=g).expand(op_args=[[2]])
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1


def test_module_qualified_operator_partial_detected():
    """<module>.<X>Operator.partial(...) is detected like a direct call."""
    code = """
t = operators.PythonOperator.partial(task_id="BadMappedName").expand(op_args=[[1]])
"""
    tree = ast.parse(code)
    rule = TaskIDConventionRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1


def test_partial_inside_task_group_gets_group_prefix():
    """Mapped tasks inside a TaskGroup carry the group prefix (#51 semantics)."""
    code = """
with TaskGroup("extract") as tg:
    t1 = PythonOperator.partial(task_id="fetch", python_callable=f).expand(op_args=[[1]])
    t2 = PythonOperator(task_id="fetch", python_callable=f)

t3 = PythonOperator(task_id="fetch", python_callable=f)
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1
    assert "Duplicate task_id 'extract.fetch'" in issues[0].message


def test_partial_without_task_id_is_skipped():
    """A .partial() without a static task_id cannot be validated."""
    code = """
t1 = PythonOperator.partial(task_id=TASK_NAME, python_callable=f).expand(op_args=[[1]])
t2 = PythonOperator.partial(python_callable=f).expand(op_args=[[1]])
"""
    tree = ast.parse(code)
    for rule in (TaskIDConventionRule(), NoDuplicateTaskIDsRule()):
        assert rule.check(tree, "test.py", code) == []


def test_taskflow_expand_is_not_a_second_definition():
    """Calling .expand() on a @task function does not re-define the task."""
    code = """
from airflow.decorators import task

@task
def transform(x):
    return x

transform.expand(x=[1, 2, 3])
transform.expand(x=[4, 5, 6])
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    assert rule.check(tree, "test.py", code) == []


def test_taskflow_partial_expand_is_not_a_second_definition():
    """TaskFlow .partial(...).expand(...) chains are call sites, not definitions."""
    code = """
from airflow.decorators import task

@task
def BadName(x, y):
    return x

BadName.partial(y=1).expand(x=[1, 2])
BadName.partial(y=2).expand(x=[3, 4])
"""
    tree = ast.parse(code)
    convention_issues = TaskIDConventionRule().check(tree, "test.py", code)
    assert len(convention_issues) == 1
    assert NoDuplicateTaskIDsRule().check(tree, "test.py", code) == []


def test_taskflow_expand_kwargs_is_not_a_definition():
    """.expand_kwargs() call sites are not task definitions."""
    code = """
from airflow.decorators import task

@task
def transform(x):
    return x

transform.expand_kwargs([{"x": 1}, {"x": 2}])
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    assert rule.check(tree, "test.py", code) == []


def test_unrelated_partial_calls_not_matched():
    """functools.partial and other .partial() calls are not task definitions."""
    code = """
import functools

f = functools.partial(g, task_id="NotATask")
h = helper.partial(task_id="AlsoNotATask")
i = make_operator().partial(task_id="StillNotATask")
"""
    tree = ast.parse(code)
    for rule in (TaskIDConventionRule(), NoDuplicateTaskIDsRule()):
        assert rule.check(tree, "test.py", code) == []
