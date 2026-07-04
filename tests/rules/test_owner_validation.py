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

    def test_non_default_args_dicts_ignored(self):
        """Test that dicts other than default_args are not inspected at all."""
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
        assert len(issues) == 0

    def test_op_kwargs_dict_not_flagged(self):
        """Regression test: op_kwargs dicts must not trigger owner errors (#31)."""
        code = """
default_args = {
    'owner': 'data-team'
}

t1 = PythonOperator(
    task_id="do_thing",
    python_callable=my_func,
    op_kwargs={"foo": 1, "bar": 2},
)
"""
        tree = ast.parse(code)
        rule = OwnerValidationRule({"valid_owners": ["data-team", "analytics-team"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_params_dict_not_flagged(self):
        """Regression test: params dicts must not trigger owner errors (#31)."""
        code = """
default_args = {
    'owner': 'data-team'
}

dag = DAG(
    dag_id="my_dag",
    default_args=default_args,
    params={"env": "prod", "retries": 3},
)
"""
        tree = ast.parse(code)
        rule = OwnerValidationRule({"valid_owners": ["data-team", "analytics-team"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_inline_default_args_valid_owner(self):
        """Test that default_args passed inline to DAG() is validated."""
        code = """
dag = DAG(
    dag_id="my_dag",
    default_args={'owner': 'data-team'},
)
"""
        tree = ast.parse(code)
        rule = OwnerValidationRule({"valid_owners": ["data-team", "analytics-team"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_inline_default_args_invalid_owner(self):
        """Test that invalid owners in inline default_args are caught."""
        code = """
dag = DAG(
    dag_id="my_dag",
    default_args={'owner': 'invalid-team'},
)
"""
        tree = ast.parse(code)
        rule = OwnerValidationRule({"valid_owners": ["data-team", "analytics-team"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Invalid owner 'invalid-team'" in issues[0].message

    def test_inline_default_args_missing_owner(self):
        """Test that a missing owner key in inline default_args is caught."""
        code = """
dag = DAG(
    dag_id="my_dag",
    default_args={'retries': 2},
)
"""
        tree = ast.parse(code)
        rule = OwnerValidationRule({"valid_owners": ["data-team", "analytics-team"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "DAG owner must be specified" in issues[0].message

    def test_non_dag_call_with_default_args_kwarg_ignored(self):
        """Regression test: default_args kwargs on non-DAG calls are not inspected."""
        code = """
default_args = {
    'owner': 'data-team'
}

with TaskGroup("group", default_args={'retries': 1}):
    pass
"""
        tree = ast.parse(code)
        rule = OwnerValidationRule({"valid_owners": ["data-team", "analytics-team"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_attribute_dag_call_inline_default_args_validated(self):
        """Test that models.DAG(default_args={...}) is still validated."""
        code = """
dag = models.DAG(
    dag_id="my_dag",
    default_args={'retries': 2},
)
"""
        tree = ast.parse(code)
        rule = OwnerValidationRule({"valid_owners": ["data-team", "analytics-team"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "DAG owner must be specified" in issues[0].message

    def test_taskflow_decorator_default_args_validated(self):
        """default_args passed to @dag(...) is validated like DAG(...) (#34)."""
        code = """
from airflow.decorators import dag

@dag(default_args={'retries': 2})
def my_pipeline():
    pass
"""
        tree = ast.parse(code)
        rule = OwnerValidationRule({"valid_owners": ["data-team", "analytics-team"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "DAG owner must be specified" in issues[0].message

    def test_dynamic_owner_value_skipped(self):
        """Test that a non-literal owner value is skipped, not flagged."""
        code = """
default_args = {
    'owner': OWNER_CONST
}
"""
        tree = ast.parse(code)
        rule = OwnerValidationRule({"valid_owners": ["data-team", "analytics-team"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_no_default_args_no_issues(self):
        """Test that a file without default_args produces no owner issues."""
        code = """
dag = DAG(dag_id="my_dag")

t1 = PythonOperator(
    task_id="do_thing",
    python_callable=my_func,
    op_kwargs={"foo": 1},
)
"""
        tree = ast.parse(code)
        rule = OwnerValidationRule({"valid_owners": ["data-team", "analytics-team"]})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_rule_has_metadata(self):
        """Test that rule has required metadata."""
        rule = OwnerValidationRule()
        assert hasattr(rule, "rule_id")
        assert hasattr(rule, "description")
        assert rule.rule_id is not None
        assert rule.description is not None
        assert len(rule.rule_id) > 0
        assert len(rule.description) > 0
