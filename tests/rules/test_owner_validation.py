"""Tests for owner validation rule."""

import ast

from daglint.rules.metadata import OwnerValidationRule


class TestOwnerValidationRule:
    """Tests for owner validation rule."""

    def test_valid_owner(self):
        """Test that valid owners pass."""
        code = """
default_args = {
    'owner': 'data-team'
}
"""
        tree = ast.parse(code)
        rule = OwnerValidationRule({"valid_owners": ["data-team", "analytics-team"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_invalid_owner(self):
        """Test that invalid owners are caught."""
        code = """
default_args = {
    'owner': 'invalid-team'
}
"""
        tree = ast.parse(code)
        rule = OwnerValidationRule({"valid_owners": ["data-team", "analytics-team"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Invalid owner" in issues[0].message

    def test_missing_owner(self):
        """Test that empty owner is caught when owner key is missing."""
        code = """
default_args = {
}
"""
        tree = ast.parse(code)
        rule = OwnerValidationRule({"valid_owners": ["data-team", "analytics-team"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "DAG owner must be specified" in issues[0].message

    def test_empty_owner(self):
        """Test that missing owner is caught when owner key is present but empty."""
        code = """
default_args = {
    'owner': ''
}
"""
        tree = ast.parse(code)
        rule = OwnerValidationRule({"valid_owners": ["data-team", "analytics-team"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "DAG owner must be specified" in issues[0].message

    def test_valid_owner_no_validation_list(self):
        """Test that any owner passes when no valid_owners list is provided."""
        code = """
default_args = {
    'owner': 'any-team'
}
"""
        tree = ast.parse(code)
        rule = OwnerValidationRule({})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_multiple_dicts_with_owners(self):
        """Test that multiple dictionaries with owner keys are validated."""
        code = """
default_args = {
    'owner': 'data-team'
}

other_args = {
    'owner': 'invalid-team'
}
"""
        tree = ast.parse(code)
        rule = OwnerValidationRule({"valid_owners": ["data-team", "analytics-team"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Invalid owner 'invalid-team'" in issues[0].message

    def test_rule_has_metadata(self):
        """Test that rule has required metadata."""
        rule = OwnerValidationRule()
        assert hasattr(rule, "rule_id")
        assert hasattr(rule, "description")
        assert rule.rule_id is not None
        assert rule.description is not None
        assert len(rule.rule_id) > 0
        assert len(rule.description) > 0
