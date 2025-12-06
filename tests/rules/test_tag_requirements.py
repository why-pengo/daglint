"""Tests for tag requirements rule."""

import ast

from daglint.rules import TagRequirementsRule


class TestTagRequirementsRule:
    """Tests for tag requirements rule."""

    def test_all_required_tags_present(self):
        """Test that DAGs with all required tags pass."""
        code = """
from airflow import DAG

dag = DAG('my_dag', tags=['environment', 'team'])
"""
        tree = ast.parse(code)
        rule = TagRequirementsRule({"required_tags": ["environment", "team"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_missing_required_tags(self):
        """Test that missing required tags are caught."""
        code = """
from airflow import DAG

dag = DAG('my_dag', tags=['environment'])
"""
        tree = ast.parse(code)
        rule = TagRequirementsRule({"required_tags": ["environment", "team"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Missing required tags" in issues[0].message

    def test_rule_has_metadata(self):
        """Test that rule has required metadata."""
        rule = TagRequirementsRule()
        assert hasattr(rule, "rule_id")
        assert hasattr(rule, "description")
        assert rule.rule_id is not None
        assert rule.description is not None
        assert len(rule.rule_id) > 0
        assert len(rule.description) > 0
