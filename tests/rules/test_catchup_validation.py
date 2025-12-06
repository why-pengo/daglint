"""Tests for catchup validation rule."""

import ast

from daglint.rules import CatchupValidationRule


class TestCatchupValidationRule:
    """Tests for catchup validation rule."""

    def test_catchup_set(self):
        """Test that DAGs with catchup set pass."""
        code = """
from airflow import DAG

dag = DAG('my_dag', catchup=False)
"""
        tree = ast.parse(code)
        rule = CatchupValidationRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_catchup_not_set(self):
        """Test that DAGs without catchup are caught."""
        code = """
from airflow import DAG

dag = DAG('my_dag')
"""
        tree = ast.parse(code)
        rule = CatchupValidationRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Catchup parameter not set" in issues[0].message

    def test_rule_has_metadata(self):
        """Test that rule has required metadata."""
        rule = CatchupValidationRule()
        assert hasattr(rule, "rule_id")
        assert hasattr(rule, "description")
        assert rule.rule_id is not None
        assert rule.description is not None
        assert len(rule.rule_id) > 0
        assert len(rule.description) > 0
