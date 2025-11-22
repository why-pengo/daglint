"""Tests for linting rules."""

import ast

import pytest

from daglint.rules import (
    CatchupValidationRule,
    DAGIDConventionRule,
    NoDuplicateTaskIDsRule,
    OwnerValidationRule,
    RequiredDAGParamsRule,
    RetryConfigurationRule,
    ScheduleValidationRule,
    TagRequirementsRule,
    TaskIDConventionRule,
)


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


class TestTaskIDConventionRule:
    """Tests for task ID convention rule."""

    def test_valid_task_id(self):
        """Test that valid task IDs pass."""
        code = """
from airflow.operators.python import PythonOperator

task = PythonOperator(task_id='my_valid_task')
"""
        tree = ast.parse(code)
        rule = TaskIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_invalid_task_id(self):
        """Test that invalid task IDs are caught."""
        code = """
from airflow.operators.python import PythonOperator

task = PythonOperator(task_id='MyInvalidTask')
"""
        tree = ast.parse(code)
        rule = TaskIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "does not match pattern" in issues[0].message


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


class TestNoDuplicateTaskIDsRule:
    """Tests for no duplicate task IDs rule."""

    def test_unique_task_ids(self):
        """Test that unique task IDs pass."""
        code = """
from airflow.operators.python import PythonOperator

task1 = PythonOperator(task_id='task_one')
task2 = PythonOperator(task_id='task_two')
"""
        tree = ast.parse(code)
        rule = NoDuplicateTaskIDsRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_duplicate_task_ids(self):
        """Test that duplicate task IDs are caught."""
        code = """
from airflow.operators.python import PythonOperator

task1 = PythonOperator(task_id='duplicate_task')
task2 = PythonOperator(task_id='duplicate_task')
"""
        tree = ast.parse(code)
        rule = NoDuplicateTaskIDsRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Duplicate task_id" in issues[0].message


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

class TestCatchupValidationRule:
    """Tests for catchup validation rule."""

    def test_catchup_set(self):
        """Test that DAGs with catchup set pass."""
        code = """
from airflow import DAG

dag = DAG('my_dag', catchup=False)
"""
        tree = ast.parse(code)
        rule = CatchupValidationRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_catchup_not_set(self):
        """Test that DAGs without catchup are caught."""
        code = """
from airflow import DAG

dag = DAG('my_dag')
"""
        tree = ast.parse(code)
        rule = CatchupValidationRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "Catchup parameter not set" in issues[0].message


class TestScheduleValidationRule:
    """Tests for schedule validation rule."""

    def test_schedule_set(self):
        """Test that DAGs with schedule set pass."""
        code = """
from airflow import DAG

dag = DAG('my_dag', schedule_interval='@daily')
"""
        tree = ast.parse(code)
        rule = ScheduleValidationRule({"allow_none": False})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_schedule_not_set(self):
        """Test that DAGs without schedule are caught."""
        code = """
from airflow import DAG

dag = DAG('my_dag')
"""
        tree = ast.parse(code)
        rule = ScheduleValidationRule({"allow_none": False})
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "schedule_interval must be explicitly set" in issues[0].message
