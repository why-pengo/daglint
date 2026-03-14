"""Tests for max_active_runs validation rule."""

import ast

from daglint.rules.metadata import MaxActiveRunsValidationRule


class TestMaxActiveRunsValidationRule:
    """Tests for max_active_runs validation rule."""

    def test_valid_max_active_runs(self):
        """Test that DAGs with the default max_active_runs pass."""
        code = """
from airflow import DAG

dag = DAG(
    'my_dag',
    max_active_runs=1,
)
"""
        tree = ast.parse(code)
        rule = MaxActiveRunsValidationRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_missing_max_active_runs(self):
        """Test that DAGs missing max_active_runs are caught."""
        code = """
from airflow import DAG

dag = DAG('my_dag')
"""
        tree = ast.parse(code)
        rule = MaxActiveRunsValidationRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "must be explicitly set to 1" in issues[0].message

    def test_incorrect_max_active_runs(self):
        """Test that DAGs with the wrong max_active_runs are caught."""
        code = """
from airflow import DAG

dag = DAG(
    'my_dag',
    max_active_runs=3,
)
"""
        tree = ast.parse(code)
        rule = MaxActiveRunsValidationRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Expected 1" in issues[0].message

    def test_custom_configured_max_active_runs(self):
        """Test that the expected value can be changed via config."""
        code = """
from airflow import DAG

dag = DAG(
    'my_dag',
    max_active_runs=2,
)
"""
        tree = ast.parse(code)
        rule = MaxActiveRunsValidationRule({"max_active_runs": 2})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_attribute_based_dag_call(self):
        """Test that airflow.DAG style calls are supported."""
        code = """
import airflow

dag = airflow.DAG(
    'my_dag',
    max_active_runs=1,
)
"""
        tree = ast.parse(code)
        rule = MaxActiveRunsValidationRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_rule_has_metadata(self):
        """Test that rule has required metadata."""
        rule = MaxActiveRunsValidationRule()
        assert hasattr(rule, "rule_id")
        assert hasattr(rule, "description")
        assert rule.rule_id is not None
        assert rule.description is not None
        assert len(rule.rule_id) > 0
        assert len(rule.description) > 0
