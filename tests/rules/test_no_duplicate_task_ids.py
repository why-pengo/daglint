"""Tests for no duplicate task IDs rule."""

import ast

from daglint.rules import NoDuplicateTaskIDsRule


class TestNoDuplicateTaskIDsRule:
    """Tests for no duplicate task IDs rule."""

    def test_unique_task_ids(self):
        """Test that unique task IDs pass."""
        code = """
from airflow.operators.python import PythonOperator

task1 = PythonOperator(task_id='task_one')
task2 = PythonOperator(task_id='task_two')
"""
        tree = ast.parse(code)
        rule = NoDuplicateTaskIDsRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_duplicate_task_ids(self):
        """Test that duplicate task IDs are caught."""
        code = """
from airflow.operators.python import PythonOperator

task1 = PythonOperator(task_id='duplicate_task')
task2 = PythonOperator(task_id='duplicate_task')
"""
        tree = ast.parse(code)
        rule = NoDuplicateTaskIDsRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Duplicate task_id" in issues[0].message

    def test_rule_has_metadata(self):
        """Test that rule has required metadata."""
        rule = NoDuplicateTaskIDsRule()
        assert hasattr(rule, 'rule_id')
        assert hasattr(rule, 'description')
        assert rule.rule_id is not None
        assert rule.description is not None
        assert len(rule.rule_id) > 0
        assert len(rule.description) > 0

