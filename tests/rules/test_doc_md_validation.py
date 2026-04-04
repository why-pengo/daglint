"""Tests for doc_md validation rule."""

import ast

from daglint.rules.metadata import DocMdValidationRule


class TestDocMdValidationRule:
    """Tests for doc_md validation rule."""

    def test_dag_with_doc_md_passes(self):
        """Test that a DAG with doc_md set passes."""
        code = """
from airflow import DAG

dag = DAG('my_dag', doc_md=\"\"\"This is my DAG documentation.\"\"\")
"""
        tree = ast.parse(code)
        rule = DocMdValidationRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_dag_without_doc_md_fails(self):
        """Test that a DAG without doc_md is flagged."""
        code = """
from airflow import DAG

dag = DAG('my_dag', schedule_interval='@daily')
"""
        tree = ast.parse(code)
        rule = DocMdValidationRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "missing doc_md" in issues[0].message

    def test_dag_with_empty_doc_md_fails(self):
        """Test that a DAG with an empty doc_md string is flagged."""
        code = """
from airflow import DAG

dag = DAG('my_dag', doc_md='')
"""
        tree = ast.parse(code)
        rule = DocMdValidationRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "must not be empty" in issues[0].message

    def test_dag_with_whitespace_doc_md_fails(self):
        """Test that a DAG with a whitespace-only doc_md is flagged."""
        code = """
from airflow import DAG

dag = DAG('my_dag', doc_md='   ')
"""
        tree = ast.parse(code)
        rule = DocMdValidationRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "must not be empty" in issues[0].message

    def test_dag_with_variable_doc_md_passes(self):
        """Test that doc_md assigned from a variable is accepted."""
        code = """
from airflow import DAG

DOC = "Some documentation"
dag = DAG('my_dag', doc_md=DOC)
"""
        tree = ast.parse(code)
        rule = DocMdValidationRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_multiple_dags_both_missing(self):
        """Test that multiple DAGs without doc_md each produce an issue."""
        code = """
from airflow import DAG

dag1 = DAG('dag1')
dag2 = DAG('dag2')
"""
        tree = ast.parse(code)
        rule = DocMdValidationRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 2

    def test_multiple_dags_one_missing(self):
        """Test that only the DAG without doc_md is flagged."""
        code = """
from airflow import DAG

dag1 = DAG('dag1', doc_md='Documented.')
dag2 = DAG('dag2')
"""
        tree = ast.parse(code)
        rule = DocMdValidationRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 1
        assert "missing doc_md" in issues[0].message

    def test_non_dag_call_ignored(self):
        """Test that non-DAG callable with doc_md kwarg is not flagged."""
        code = """
some_function(doc_md='irrelevant')
"""
        tree = ast.parse(code)
        rule = DocMdValidationRule()
        issues = rule.check(tree, "test.py", code)
        assert len(issues) == 0

    def test_rule_has_metadata(self):
        """Test that rule has required metadata."""
        rule = DocMdValidationRule()
        assert rule.rule_id == "doc_md_validation"
        assert len(rule.description) > 0
