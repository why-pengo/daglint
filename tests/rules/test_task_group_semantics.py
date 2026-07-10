"""Tests for group-aware task_id semantics (#51).

Tasks inside task groups have effective IDs prefixed with the group ID
(`group.task`), so duplicate detection must compare full dotted paths
while naming rules keep validating the leaf name.
"""

import ast

from daglint.rules import NoDuplicateTaskIDsRule, TaskIDConventionRule

# Realistic import header for fixtures: strict detection (#55) only
# recognizes names traceable to their airflow origins.
IMPORTS = """\
from airflow.decorators import task, task_group
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
"""


def test_same_leaf_id_in_different_groups_is_not_a_duplicate():
    """Same-named tasks in different groups have distinct effective IDs."""
    code = IMPORTS + """
with TaskGroup("extract_a") as g1:
    t1 = PythonOperator(task_id="fetch")

with TaskGroup("extract_b") as g2:
    t2 = PythonOperator(task_id="fetch")
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    assert rule.check(tree, "test.py", code) == []


def test_duplicate_within_a_group_reports_dotted_path():
    """Duplicates inside one group are caught, reported as group.task."""
    code = IMPORTS + """
with TaskGroup("extract") as tg:
    t1 = PythonOperator(task_id="fetch")
    t2 = PythonOperator(task_id="fetch")
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1
    assert "Duplicate task_id 'extract.fetch'" in issues[0].message


def test_grouped_task_does_not_collide_with_top_level_task():
    """group.task and a bare top-level task are distinct."""
    code = IMPORTS + """
t0 = PythonOperator(task_id="fetch")

with TaskGroup("extract") as tg:
    t1 = PythonOperator(task_id="fetch")
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    assert rule.check(tree, "test.py", code) == []


def test_nested_groups_compose_dotted_path():
    """Nested groups prefix in order: outer.inner.task."""
    code = IMPORTS + """
with TaskGroup("outer") as o:
    with TaskGroup("inner") as i:
        t1 = PythonOperator(task_id="fetch")
        t2 = PythonOperator(task_id="fetch")
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1
    assert "'outer.inner.fetch'" in issues[0].message


def test_multiple_with_items_compose_in_order():
    """`with TaskGroup("a"), TaskGroup("b"):` prefixes as a.b."""
    code = IMPORTS + """
with TaskGroup("a"), TaskGroup("b"):
    t1 = PythonOperator(task_id="fetch")
    t2 = PythonOperator(task_id="fetch")
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1
    assert "'a.b.fetch'" in issues[0].message


def test_prefix_group_id_false_adds_no_prefix():
    """A literal prefix_group_id=False means the group does not prefix its tasks.

    Same-named tasks in two unprefixed sibling groups collide at
    runtime, and the linter must catch that.
    """
    code = IMPORTS + """
with TaskGroup("extract_a", prefix_group_id=False) as g1:
    t1 = PythonOperator(task_id="fetch")

with TaskGroup("extract_b", prefix_group_id=False) as g2:
    t2 = PythonOperator(task_id="fetch")
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1
    assert "Duplicate task_id 'fetch'" in issues[0].message


def test_prefix_group_id_true_prefixes_normally():
    """An explicit prefix_group_id=True behaves like the default."""
    code = IMPORTS + """
with TaskGroup("extract_a", prefix_group_id=True) as g1:
    t1 = PythonOperator(task_id="fetch")

with TaskGroup("extract_b", prefix_group_id=True) as g2:
    t2 = PythonOperator(task_id="fetch")
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    assert rule.check(tree, "test.py", code) == []


def test_dynamic_group_id_still_catches_duplicates_within_the_group():
    """A group with a non-literal ID gets a unique placeholder prefix."""
    code = IMPORTS + """
with TaskGroup(GROUP_NAME) as tg:
    t1 = PythonOperator(task_id="fetch")
    t2 = PythonOperator(task_id="fetch")
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1


def test_dynamic_group_ids_never_collide_across_groups():
    """Two groups with unknown IDs cannot produce cross-group duplicates."""
    code = IMPORTS + """
with TaskGroup(NAME_A) as g1:
    t1 = PythonOperator(task_id="fetch")

with TaskGroup(NAME_B) as g2:
    t2 = PythonOperator(task_id="fetch")
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    assert rule.check(tree, "test.py", code) == []


def test_task_group_decorator_prefixes_body_tasks():
    """Tasks in an @task_group function are prefixed by the function name."""
    code = IMPORTS + """
from airflow.decorators import task, task_group

@task_group
def extract():
    @task
    def fetch():
        pass

t0 = PythonOperator(task_id="fetch")
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    assert rule.check(tree, "test.py", code) == []


def test_task_group_decorator_explicit_group_id_prefixes_body_tasks():
    """An explicit group_id on @task_group(...) is the prefix for body tasks."""
    code = IMPORTS + """
@task_group(group_id="extract")
def some_group():
    @task
    def fetch():
        pass

    t2 = PythonOperator(task_id="fetch")
"""
    tree = ast.parse(code)
    rule = NoDuplicateTaskIDsRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1
    assert "'extract.fetch'" in issues[0].message


def test_task_id_convention_validates_leaf_name_inside_groups():
    """The naming rule checks the leaf task_id, not the dotted path."""
    code = IMPORTS + """
with TaskGroup("extract") as tg:
    t1 = PythonOperator(task_id="good_name")
    t2 = PythonOperator(task_id="BadName")
"""
    tree = ast.parse(code)
    rule = TaskIDConventionRule()
    issues = rule.check(tree, "test.py", code)
    assert len(issues) == 1
    assert "Task ID 'BadName'" in issues[0].message


def test_task_id_convention_ignores_group_naming():
    """A badly named group does not make its well-named tasks fail."""
    code = IMPORTS + """
with TaskGroup("BadGroupName") as tg:
    t1 = PythonOperator(task_id="good_name")
"""
    tree = ast.parse(code)
    rule = TaskIDConventionRule()
    assert rule.check(tree, "test.py", code) == []
