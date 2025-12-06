"""Tests for schedule validation rule."""

import ast

from daglint.rules import ScheduleValidationRule


class TestScheduleValidationRule:
    """Tests for schedule validation rule."""

    def test_schedule_set(self):
        """Test that DAGs with schedule set pass."""
        code = """
from airflow import DAG

dag = DAG('my_dag', schedule_interval='@daily')
"""
        tree = ast.parse(code)
        rule = ScheduleValidationRule({"allow_none": False})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_schedule_not_set(self):
        """Test that DAGs without schedule are caught."""
        code = """
from airflow import DAG

dag = DAG('my_dag')
"""
        tree = ast.parse(code)
        rule = ScheduleValidationRule({"allow_none": False})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "schedule_interval must be explicitly set" in issues[0].message

    def test_rule_has_metadata(self):
        """Test that rule has required metadata."""
        rule = ScheduleValidationRule()
        assert hasattr(rule, 'rule_id')
        assert hasattr(rule, 'description')
        assert rule.rule_id is not None
        assert rule.description is not None
        assert len(rule.rule_id) > 0
        assert len(rule.description) > 0

