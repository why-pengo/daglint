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

    def test_taskflow_function_name_is_effective_dag_id(self):
        """A bare @dag uses the function name as the DAG ID and validates it (#34)."""
        code = """
from airflow.decorators import dag

@dag
def MyBadPipelineName():
    pass
"""
        tree = ast.parse(code)
        rule = DAGIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "MyBadPipelineName" in issues[0].message

    def test_taskflow_explicit_dag_id_overrides_function_name(self):
        """An explicit dag_id= on @dag(...) wins over the function name (#34)."""
        code = """
from airflow.decorators import dag

@dag(dag_id='good_dag_id')
def MyBadPipelineName():
    pass
"""
        tree = ast.parse(code)
        rule = DAGIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_taskflow_attribute_decorator_form(self):
        """@decorators.dag(...) attribute form is recognized (#34)."""
        code = """
from airflow import decorators

@decorators.dag(dag_id='BadDagId')
def my_pipeline():
    pass
"""
        tree = ast.parse(code)
        rule = DAGIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "BadDagId" in issues[0].message

    def test_taskflow_dynamic_dag_id_skips_function_name(self):
        """A dynamic dag_id= overrides the function name in Airflow, so
        neither can be validated (#34 review)."""
        code = """
from airflow.decorators import dag

@dag(dag_id=DYNAMIC_ID)
def MyBadPipelineName():
    pass
"""
        tree = ast.parse(code)
        rule = DAGIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_dynamic_positional_dag_id_skipped(self):
        """A dynamic positional DAG ID cannot be validated."""
        code = """
from airflow import DAG

dag = DAG(f"team_{suffix}")
"""
        tree = ast.parse(code)
        rule = DAGIDConventionRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_unrelated_decorator_not_matched(self):
        """Decorators that are not @dag do not create DAG definitions (#34)."""
        code = """
import functools

@functools.cache
def MyHelperFunction():
    pass
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
