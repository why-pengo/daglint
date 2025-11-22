"""Tests for the linter."""

import tempfile
from pathlib import Path

import pytest

from daglint.config import Config
from daglint.linter import DAGLinter


def test_lint_valid_dag():
    """Test linting a valid DAG file."""
    code = """
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'data-team',
    'start_date': datetime(2023, 1, 1),
    'retries': 3,
}

with DAG(
    dag_id='my_valid_dag',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    tags=['environment', 'team'],
) as dag:
    
    task1 = PythonOperator(
        task_id='my_task',
        python_callable=lambda: print('Hello')
    )
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        config = Config.default()
        linter = DAGLinter(config)
        issues = linter.lint_file(f.name)

        Path(f.name).unlink()

        # Should have minimal issues (might have some warnings)
        assert all(issue.severity != "error" for issue in issues)


def test_lint_invalid_dag():
    """Test linting an invalid DAG file."""
    code = """
from airflow import DAG

dag = DAG('InvalidDAGID')
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        config = Config.default()
        linter = DAGLinter(config)
        issues = linter.lint_file(f.name)

        Path(f.name).unlink()

        assert len(issues) > 0
        assert any("does not match pattern" in issue.message for issue in issues)


def test_lint_syntax_error():
    """Test linting a file with syntax errors."""
    code = """
from airflow import DAG

dag = DAG('my_dag'
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        config = Config.default()
        linter = DAGLinter(config)
        issues = linter.lint_file(f.name)

        Path(f.name).unlink()

        assert len(issues) == 1
        assert issues[0].rule_id == "syntax_error"


def test_lint_directory():
    """Test linting a directory of DAG files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        file1 = Path(tmpdir) / "dag1.py"
        file1.write_text("from airflow import DAG\ndag = DAG('valid_dag')")

        file2 = Path(tmpdir) / "dag2.py"
        file2.write_text("from airflow import DAG\ndag = DAG('InvalidDAG')")

        config = Config.default()
        linter = DAGLinter(config)
        results = linter.lint_directory(tmpdir)

        # Should have issues for at least one file
        assert len(results) >= 1


def test_linter_with_custom_config():
    """Test linter with custom configuration."""
    code = """
from airflow import DAG

dag = DAG('test_my_dag')
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        # Custom config that requires 'test_' prefix
        config = Config(
            {
                "rules": {
                    "dag_id_convention": {
                        "enabled": True,
                        "pattern": r"^test_[a-z][a-z0-9_]*$",
                        "severity": "error",
                    }
                }
            }
        )

        linter = DAGLinter(config)
        issues = linter.lint_file(f.name)

        Path(f.name).unlink()

        # Should pass with custom pattern
        dag_id_issues = [i for i in issues if i.rule_id == "dag_id_convention"]
        assert len(dag_id_issues) == 0
