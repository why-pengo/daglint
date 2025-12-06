"""Tests for required DAG params rule."""

import ast

from daglint.rules.metadata import RequiredDAGParamsRule


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
        assert "description" in issues[0].message

    def test_missing_owner(self):
        """Test that missing owner is caught."""
        code = """
default_args = {
    'start_date': '2023-01-01',
    'description': 'Test DAG'
}
"""
        tree = ast.parse(code)
        rule = RequiredDAGParamsRule({"required_params": ["owner", "start_date", "description"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Missing required parameters" in issues[0].message
        assert "owner" in issues[0].message

    def test_missing_start_date(self):
        """Test that missing start_date is caught."""
        code = """
default_args = {
    'owner': 'airflow',
    'description': 'Test DAG'
}
"""
        tree = ast.parse(code)
        rule = RequiredDAGParamsRule({"required_params": ["owner", "start_date", "description"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Missing required parameters" in issues[0].message
        assert "start_date" in issues[0].message

    def test_no_default_args(self):
        """Test that no issues are raised when default_args is not present."""
        code = """
from airflow import DAG

dag = DAG('my_dag')
"""
        tree = ast.parse(code)
        rule = RequiredDAGParamsRule({"required_params": ["owner", "start_date", "description"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_extra_params_allowed(self):
        """Test that extra params beyond required ones are allowed."""
        code = """
default_args = {
    'owner': 'airflow',
    'start_date': '2023-01-01',
    'description': 'Test DAG',
    'retries': 3,
    'retry_delay': 300
}
"""
        tree = ast.parse(code)
        rule = RequiredDAGParamsRule({"required_params": ["owner", "start_date", "description"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_default_required_params(self):
        """Test that default required params are used when none configured."""
        code = """
default_args = {
    'retries': 3
}
"""
        tree = ast.parse(code)
        rule = RequiredDAGParamsRule({})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Missing required parameters" in issues[0].message
        # Default params include owner, start_date, description
        assert any(param in issues[0].message for param in ["owner", "start_date", "description"])

    def test_multiple_default_args(self):
        """Test that only the variable named 'default_args' is validated."""
        code = """
default_args = {
    'owner': 'airflow',
    'start_date': '2023-01-01'
}

other_default_args = {
    'owner': 'airflow'
}
"""
        tree = ast.parse(code)
        rule = RequiredDAGParamsRule({"required_params": ["owner", "start_date"]})
        issues = rule.check(tree, "test.py", code)
        # Only default_args should be validated, not other_default_args
        assert len(issues) == 0

    def test_incomplete_default_args(self):
        """Test that default_args missing required params is caught."""
        code = """
default_args = {
    'owner': 'airflow'
}
"""
        tree = ast.parse(code)
        rule = RequiredDAGParamsRule({"required_params": ["owner", "start_date"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "start_date" in issues[0].message
