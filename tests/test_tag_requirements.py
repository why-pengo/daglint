"""Tests for tag requirements rule."""

import ast

from daglint.rules.metadata import TagRequirementsRule


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
        assert "team" in issues[0].message

    def test_no_tags_provided(self):
        """Test that missing all tags are caught."""
        code = """
from airflow import DAG

dag = DAG('my_dag')
"""
        tree = ast.parse(code)
        rule = TagRequirementsRule({"required_tags": ["environment", "team"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Missing required tags" in issues[0].message

    def test_empty_tags_list(self):
        """Test that empty tags list is caught."""
        code = """
from airflow import DAG

dag = DAG('my_dag', tags=[])
"""
        tree = ast.parse(code)
        rule = TagRequirementsRule({"required_tags": ["environment", "team"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Missing required tags" in issues[0].message

    def test_no_required_tags_configured(self):
        """Test that no issues are raised when no required tags are configured."""
        code = """
from airflow import DAG

dag = DAG('my_dag')
"""
        tree = ast.parse(code)
        rule = TagRequirementsRule({})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_extra_tags_allowed(self):
        """Test that extra tags beyond required ones are allowed."""
        code = """
from airflow import DAG

dag = DAG('my_dag', tags=['environment', 'team', 'extra_tag'])
"""
        tree = ast.parse(code)
        rule = TagRequirementsRule({"required_tags": ["environment", "team"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_multiple_dags(self):
        """Test that multiple DAGs are validated."""
        code = """
from airflow import DAG

dag1 = DAG('dag1', tags=['environment', 'team'])
dag2 = DAG('dag2', tags=['environment'])
"""
        tree = ast.parse(code)
        rule = TagRequirementsRule({"required_tags": ["environment", "team"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Missing required tags" in issues[0].message
