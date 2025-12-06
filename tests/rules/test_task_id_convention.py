"""Tests for task ID convention rule."""

import ast

from daglint.rules import TaskIDConventionRule


class TestTaskIDConventionRule:
    """Tests for task ID convention rule."""

    def test_valid_task_id(self):
        """Test that valid task IDs pass."""
        code = """
from airflow.operators.python import PythonOperator

task = PythonOperator(task_id='my_valid_task')
"""
        tree = ast.parse(code)
        rule = TaskIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_invalid_task_id(self):
        """Test that invalid task IDs are caught."""
        code = """
from airflow.operators.python import PythonOperator

task = PythonOperator(task_id='MyInvalidTask')
"""
        tree = ast.parse(code)
        rule = TaskIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "does not match pattern" in issues[0].message

    def test_rule_has_metadata(self):
        """Test that rule has required metadata."""
        rule = TaskIDConventionRule()
        assert hasattr(rule, "rule_id")
        assert hasattr(rule, "description")
        assert rule.rule_id is not None
        assert rule.description is not None
        assert len(rule.rule_id) > 0
        assert len(rule.description) > 0
