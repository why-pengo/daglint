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
        """Test that the default config's required params are used when none configured (#50)."""
        code = """
default_args = {
    'retries': 3
}
"""
        tree = ast.parse(code)
        rule = RequiredDAGParamsRule({})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Missing required parameters in default_args: owner, start_date" in issues[0].message

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
        assert "Missing required parameters" in issues[0].message

    def test_inline_default_args_missing_params(self):
        """Test that inline DAG(default_args={...}) missing params is caught (#41)."""
        code = """
dag = DAG(
    dag_id='my_dag',
    default_args={'owner': 'airflow'},
)
"""
        tree = ast.parse(code)
        rule = RequiredDAGParamsRule({"required_params": ["owner", "start_date", "retries"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Missing required parameters in default_args: retries, start_date" in issues[0].message

    def test_inline_default_args_all_params_present(self):
        """Test that inline default_args with all required params passes (#41)."""
        code = """
dag = DAG(
    dag_id='my_dag',
    default_args={'owner': 'airflow', 'start_date': '2023-01-01', 'retries': 3},
)
"""
        tree = ast.parse(code)
        rule = RequiredDAGParamsRule({"required_params": ["owner", "start_date", "retries"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_assignment_and_inline_forms_both_checked(self):
        """Test that assignment and a separate inline default_args are each validated."""
        code = """
default_args = {
    'owner': 'airflow',
    'start_date': '2023-01-01'
}

dag = DAG(
    dag_id='my_dag',
    default_args={'owner': 'airflow'},
)
"""
        tree = ast.parse(code)
        rule = RequiredDAGParamsRule({"required_params": ["owner", "start_date"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "start_date" in issues[0].message

    def test_non_dag_call_default_args_ignored(self):
        """Test that default_args kwargs on non-DAG calls are not inspected."""
        code = """
default_args = {
    'owner': 'airflow',
    'start_date': '2023-01-01'
}

with TaskGroup('group', default_args={'retries': 1}):
    pass
"""
        tree = ast.parse(code)
        rule = RequiredDAGParamsRule({"required_params": ["owner", "start_date"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_taskflow_decorator_default_args_checked(self):
        """default_args passed to @dag(...) is checked for required params (#34)."""
        code = """
from airflow.decorators import dag

@dag(default_args={'owner': 'airflow'})
def my_pipeline():
    pass
"""
        tree = ast.parse(code)
        rule = RequiredDAGParamsRule({"required_params": ["owner", "start_date", "retries"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Missing required parameters in default_args: retries, start_date" in issues[0].message

    def test_missing_params_listed_in_sorted_order(self):
        """Missing params are reported in deterministic (sorted) order."""
        code = """
default_args = {}
"""
        tree = ast.parse(code)
        rule = RequiredDAGParamsRule({"required_params": ["start_date", "owner", "retries"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Missing required parameters in default_args: owner, retries, start_date" in issues[0].message

    def test_rule_has_metadata(self):
        """Test that rule has required metadata."""
        rule = RequiredDAGParamsRule()
        assert hasattr(rule, "rule_id")
        assert hasattr(rule, "description")
        assert rule.rule_id is not None
        assert rule.description is not None
        assert len(rule.rule_id) > 0
        assert len(rule.description) > 0
