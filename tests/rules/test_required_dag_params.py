"""Tests for required DAG params rule."""

import ast

from daglint.rules import RequiredDAGParamsRule


class TestRequiredDAGParamsRule:
    """Tests for required DAG params rule."""

    def test_all_required_params_present(self):
        """Test that default_args with all required params pass."""
        code = """
default_args = {
    'owner': 'airflow',
    'start_date': '2023-01-01',
    'retries': 3
}
"""
        tree = ast.parse(code)
        rule = RequiredDAGParamsRule({"required_params": ["owner", "start_date", "retries"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_missing_required_params(self):
        """Test that missing required params are caught."""
        code = """
default_args = {
    'owner': 'airflow'
}
"""
        tree = ast.parse(code)
        rule = RequiredDAGParamsRule({"required_params": ["owner", "start_date", "retries"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Missing required parameters" in issues[0].message

    def test_missing_required_description(self):
        """Test that missing required description is caught."""
        code = """
default_args = {
    'owner': 'airflow'
}
"""
        tree = ast.parse(code)
        rule = RequiredDAGParamsRule({"required_params": ["owner", "description"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Missing required parameters" in issues[0].message

    def test_rule_has_metadata(self):
        """Test that rule has required metadata."""
        rule = RequiredDAGParamsRule()
        assert hasattr(rule, 'rule_id')
        assert hasattr(rule, 'description')
        assert rule.rule_id is not None
        assert rule.description is not None
        assert len(rule.rule_id) > 0
        assert len(rule.description) > 0

