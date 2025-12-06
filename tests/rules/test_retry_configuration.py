"""Tests for retry configuration rule."""

import ast

from daglint.rules import RetryConfigurationRule


class TestRetryConfigurationRule:
    """Tests for retry configuration rule."""

    def test_valid_retries(self):
        """Test that valid retry values pass."""
        code = """
default_args = {
    'retries': 3
}
"""
        tree = ast.parse(code)
        rule = RetryConfigurationRule({"min_retries": 1, "max_retries": 5})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_retries_below_minimum(self):
        """Test that retries below minimum are caught."""
        code = """
default_args = {
    'retries': 0
}
"""
        tree = ast.parse(code)
        rule = RetryConfigurationRule({"min_retries": 1, "max_retries": 5})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "below minimum" in issues[0].message

    def test_retries_above_maximum(self):
        """Test that retries above maximum are caught."""
        code = """
default_args = {
    'retries': 10
}
"""
        tree = ast.parse(code)
        rule = RetryConfigurationRule({"min_retries": 1, "max_retries": 5})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "exceeds maximum" in issues[0].message

    def test_rule_has_metadata(self):
        """Test that rule has required metadata."""
        rule = RetryConfigurationRule()
        assert hasattr(rule, 'rule_id')
        assert hasattr(rule, 'description')
        assert rule.rule_id is not None
        assert rule.description is not None
        assert len(rule.rule_id) > 0
        assert len(rule.description) > 0

