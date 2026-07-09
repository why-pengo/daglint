"""Tests for task group ID naming convention rule."""

import ast

from daglint.rules import GroupIDConventionRule


class TestGroupIDConventionRule:
    """Tests for task group ID naming convention rule."""

    def test_valid_group_id(self):
        """Test that snake_case group IDs pass."""
        code = """
from airflow.utils.task_group import TaskGroup

with TaskGroup("extract_tasks") as tg:
    pass
"""
        tree = ast.parse(code)
        rule = GroupIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_invalid_group_id(self):
        """Test that non-snake_case group IDs are caught."""
        code = """
from airflow.utils.task_group import TaskGroup

with TaskGroup("ExtractTasks") as tg:
    pass
"""
        tree = ast.parse(code)
        rule = GroupIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Task group ID 'ExtractTasks' does not match pattern" in issues[0].message

    def test_group_id_keyword_arg(self):
        """Test that group_id passed as a keyword argument is validated."""
        code = """
with TaskGroup(group_id="Extract-Tasks") as tg:
    pass
"""
        tree = ast.parse(code)
        rule = GroupIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "'Extract-Tasks'" in issues[0].message

    def test_assignment_form_validated(self):
        """Test that TaskGroup instantiations outside a with block are validated."""
        code = """
tg = TaskGroup("BadName", dag=dag)
"""
        tree = ast.parse(code)
        rule = GroupIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1

    def test_attribute_call_form_validated(self):
        """Test that <module>.TaskGroup(...) is validated."""
        code = """
with task_group.TaskGroup("BadName") as tg:
    pass
"""
        tree = ast.parse(code)
        rule = GroupIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1

    def test_taskflow_function_name_is_effective_group_id(self):
        """@task_group without group_id uses the function name as the group ID."""
        code = """
from airflow.decorators import task_group

@task_group
def BadGroupName():
    pass
"""
        tree = ast.parse(code)
        rule = GroupIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "'BadGroupName'" in issues[0].message

    def test_taskflow_explicit_group_id_overrides_function_name(self):
        """An explicit group_id on @task_group(...) overrides the function name."""
        code = """
from airflow.decorators import task_group

@task_group(group_id="good_name")
def BadGroupName():
    pass
"""
        tree = ast.parse(code)
        rule = GroupIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_taskflow_positional_argument_is_ignored(self):
        """A positional argument on @task_group(...) is NOT a group_id.

        Airflow's runtime binds the first positional to python_callable
        and silently drops non-callables (both 2.x and 3.x), so the
        effective group ID is the function name — only the type-stub
        overloads suggest otherwise.
        """
        code = """
from airflow.decorators import task_group

@task_group("IgnoredPositional")
def good_name():
    pass
"""
        tree = ast.parse(code)
        rule = GroupIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_dynamic_group_id_skipped(self):
        """A non-literal group ID cannot be validated and is skipped."""
        code = """
with TaskGroup(GROUP_NAME) as tg:
    pass

@task_group(group_id=f"group_{env}")
def my_group():
    pass
"""
        tree = ast.parse(code)
        rule = GroupIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_nested_groups_all_validated(self):
        """Every group in a nested structure is validated individually."""
        code = """
with TaskGroup("outer_group") as outer:
    with TaskGroup("InnerGroup") as inner:
        pass
"""
        tree = ast.parse(code)
        rule = GroupIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "'InnerGroup'" in issues[0].message

    def test_unrelated_calls_and_decorators_ignored(self):
        """Non-TaskGroup calls and non-task_group decorators are not matched."""
        code = """
tg = SomeGroup("BadName")

@task
def BadTaskName():
    pass
"""
        tree = ast.parse(code)
        rule = GroupIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_rule_has_metadata(self):
        """Test that rule has required metadata."""
        rule = GroupIDConventionRule()
        assert hasattr(rule, "rule_id")
        assert hasattr(rule, "description")
        assert rule.rule_id is not None
        assert rule.description is not None
        assert len(rule.rule_id) > 0
        assert len(rule.description) > 0
