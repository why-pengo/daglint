"""Tests for DAG ID convention rule."""

import ast

from daglint.rules import DAGIDConventionRule


class TestDAGIDConventionRule:
    """Tests for DAG ID convention rule."""

    def test_valid_dag_id(self):
        """Test that valid DAG IDs pass."""
        code = """
from airflow import DAG

dag = DAG('my_valid_dag_id')
"""
        tree = ast.parse(code)
        rule = DAGIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_invalid_dag_id(self):
        """Test that invalid DAG IDs are caught."""
        code = """
from airflow import DAG

dag = DAG('MyInvalidDAGId')
"""
        tree = ast.parse(code)
        rule = DAGIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "does not match pattern" in issues[0].message

    def test_dag_id_with_keyword_arg(self):
        """Test DAG ID passed as keyword argument."""
        code = """
from airflow import DAG

dag = DAG(dag_id='valid_dag_id')
"""
        tree = ast.parse(code)
        rule = DAGIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_rule_has_metadata(self):
        """Test that rule has required metadata."""
        rule = DAGIDConventionRule()
        assert hasattr(rule, "rule_id")
        assert hasattr(rule, "description")
        assert rule.rule_id is not None
        assert rule.description is not None
        assert len(rule.rule_id) > 0
        assert len(rule.description) > 0
