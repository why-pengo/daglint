"""Tests for .override(task_id=...) re-identification (#53).

`my_task.override(task_id="other_id")(...)` instantiates a TaskFlow
task under a new ID at the call site, so task rules must treat the
override as a task definition with that ID. Overrides that do not
pass task_id keep the original identity and are ignored.
"""

import ast

from daglint.rules import NoDuplicateTaskIDsRule, TaskIDConventionRule


def test_override_task_id_is_validated():
    """task_id passed to .override(...) gets naming validation."""
    code = """
from airflow.decorators import task

@task
def process(x):
    return x

process.override(task_id="BadOverrideName")(1)
"""
    tree = ast.parse(code)
    rule = TaskIDConventionRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1
    assert "Task ID 'BadOverrideName'" in issues[0].message


def test_distinct_overrides_are_not_duplicates():
    """Reusing one @task under distinct override ids is legal."""
    code = """
from airflow.decorators import task

@task
def process(x):
    return x

process.override(task_id="process_a")(1)
process.override(task_id="process_b")(2)
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    assert rule.check(tree, "test.py", code) == []


def test_override_colliding_with_operator_id_is_a_duplicate():
    """An override id colliding with a classic operator's id is flagged."""
    code = """
process.override(task_id="fetch")(1)
t = PythonOperator(task_id="fetch", python_callable=f)
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1
    assert "Duplicate task_id 'fetch'" in issues[0].message


def test_same_override_id_twice_is_a_duplicate():
    """Two override call sites with the same explicit id are flagged."""
    code = """
process.override(task_id="copy")(1)
process.override(task_id="copy")(2)
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1


def test_override_inside_task_group_gets_group_prefix():
    """Override call sites carry the prefix of the group they run in (#51)."""
    code = """
with TaskGroup("extract") as tg:
    process.override(task_id="fetch")(1)

t = PythonOperator(task_id="fetch", python_callable=f)
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    assert rule.check(tree, "test.py", code) == []


def test_override_chained_with_expand_counts_once():
    """.override(task_id=...).expand(...) is one definition, not two."""
    code = """
process.override(task_id="mapped_copy").expand(x=[1, 2])
process.override(task_id="mapped_copy").expand(x=[3, 4])
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1


def test_dynamic_override_id_is_skipped():
    """A non-literal override id cannot be validated and is skipped."""
    code = """
process.override(task_id=TASK_NAME)(1)
process.override(task_id=f"copy_{env}")(2)
"""
    tree = ast.parse(code)
    for rule in (TaskIDConventionRule(), NoDuplicateTaskIDsRule()):
        assert rule.check(tree, "test.py", code) == []


def test_override_without_task_id_is_ignored():
    """.override(pool=...) does not change task identity."""
    code = """
process.override(pool="high_memory")(1)
process.override(pool="high_memory")(2)
"""
    tree = ast.parse(code)
    for rule in (TaskIDConventionRule(), NoDuplicateTaskIDsRule()):
        assert rule.check(tree, "test.py", code) == []


def test_override_on_call_result_is_ignored():
    """Chains on call results are not matched (conservative target scoping)."""
    code = """
make_task().override(task_id="BadName")(1)
"""
    tree = ast.parse(code)
    for rule in (TaskIDConventionRule(), NoDuplicateTaskIDsRule()):
        assert rule.check(tree, "test.py", code) == []


def test_module_qualified_target_is_matched():
    """Overrides on attribute targets like tasks.process are recognized."""
    code = """
tasks.process.override(task_id="BadOverrideName")(1)
"""
    tree = ast.parse(code)
    rule = TaskIDConventionRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1
