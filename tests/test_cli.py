"""Tests for CLI commands."""

import tempfile
from pathlib import Path

from click.testing import CliRunner

from daglint.cli import cli


def test_cli_version():
    """Test --version flag."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0


def test_check_valid_file():
    """Test checking a valid DAG file."""
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

    runner = CliRunner()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        result = runner.invoke(cli, ["check", f.name])
        Path(f.name).unlink()

        assert result.exit_code == 0


def test_check_invalid_file():
    """Test checking an invalid DAG file."""
    code = """
from airflow import DAG

dag = DAG('InvalidDAGID')
"""

    runner = CliRunner()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        result = runner.invoke(cli, ["check", f.name])
        Path(f.name).unlink()

        assert result.exit_code == 1
        assert "does not match pattern" in result.output


def test_check_directory():
    """Test checking a directory."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test DAG file
        dag_file = Path(tmpdir) / "test_dag.py"
        dag_file.write_text("from airflow import DAG\ndag = DAG('InvalidDAG')")

        result = runner.invoke(cli, ["check", tmpdir])
        assert result.exit_code == 1


def test_check_with_specific_rules():
    """Test checking with specific rules."""
    code = """
from airflow import DAG

dag = DAG('InvalidDAGID')
"""

    runner = CliRunner()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        result = runner.invoke(cli, ["check", f.name, "--rules", "dag_id_convention"])
        Path(f.name).unlink()

        assert result.exit_code == 1


def test_check_verbose():
    """Test verbose output."""
    code = """
from airflow import DAG

dag = DAG('my_dag')
"""

    runner = CliRunner()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        result = runner.invoke(cli, ["check", f.name, "--verbose"])
        Path(f.name).unlink()

        assert "Checking:" in result.output


def test_rules_command():
    """Test rules command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["rules"])
    assert result.exit_code == 0
    assert "dag_id_convention" in result.output
    assert "owner_validation" in result.output


def test_init_command():
    """Test init command."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / ".daglint.yaml"
        result = runner.invoke(cli, ["init", "--output", str(config_path)])

        assert result.exit_code == 0
        assert config_path.exists()
        assert "Created configuration file" in result.output


def test_init_command_overwrite():
    """Test init command with existing file."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / ".daglint.yaml"
        config_path.write_text("existing content")

        # Decline overwrite
        result = runner.invoke(cli, ["init", "--output", str(config_path)], input="n\n")
        assert "Aborted" in result.output

        # Accept overwrite
        result = runner.invoke(cli, ["init", "--output", str(config_path)], input="y\n")
        assert result.exit_code == 0
