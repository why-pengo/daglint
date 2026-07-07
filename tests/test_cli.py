"""Tests for CLI commands."""

import json
import tempfile
from pathlib import Path

from click.testing import CliRunner

from daglint.cli import cli

# Passes every rule.
CLEAN_DAG = """
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
    max_active_runs=1,
    catchup=False,
    tags=['environment', 'team'],
    doc_md='A valid DAG for testing.',
) as dag:

    task1 = PythonOperator(
        task_id='my_task',
        python_callable=lambda: print('Hello')
    )
"""

# Same as CLEAN_DAG but without doc_md: trips only the warning-severity
# doc_md_validation rule, no error-severity issues.
WARNINGS_ONLY_DAG = CLEAN_DAG.replace("    doc_md='A valid DAG for testing.',\n", "")

# Bad dag_id: trips the error-severity dag_id_convention rule.
ERROR_DAG = """
from airflow import DAG

dag = DAG('InvalidDAGID')
"""


def _run_check(code, *args):
    """Lint a temp file containing `code` with the given extra CLI args."""
    runner = CliRunner()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
    try:
        return runner.invoke(cli, ["check", f.name, *args])
    finally:
        Path(f.name).unlink()


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
    max_active_runs=1,
    catchup=False,
    tags=['environment', 'team'],
    doc_md='A valid DAG for testing.',
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


def test_check_unknown_rule_is_usage_error():
    """An unknown rule name must abort with an error, not silently pass (#32)."""
    code = """
from airflow import DAG

dag = DAG('InvalidDAGID')
"""

    runner = CliRunner()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        result = runner.invoke(cli, ["check", f.name, "--rules", "bogus_rule_name"])
        Path(f.name).unlink()

        assert result.exit_code == 2
        assert "bogus_rule_name" in result.output
        assert "owner_validation" in result.output  # valid rules are listed
        assert "All checks passed" not in result.output


def test_check_multiple_unknown_rules_all_reported():
    """Every unknown rule name is reported in a single error, and nothing runs."""
    code = """
from airflow import DAG

dag = DAG('InvalidDAGID')
"""

    runner = CliRunner()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        result = runner.invoke(cli, ["check", f.name, "--rules", "typo_one,dag_id_convention,typo_two"])
        Path(f.name).unlink()

        assert result.exit_code == 2
        assert "typo_one" in result.output
        assert "typo_two" in result.output
        assert "does not match pattern" not in result.output  # no partial run


def test_check_rules_trailing_comma_accepted():
    """Trailing commas and whitespace in --rules are tolerated."""
    code = """
from airflow import DAG

dag = DAG('InvalidDAGID')
"""

    runner = CliRunner()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        result = runner.invoke(cli, ["check", f.name, "--rules", "dag_id_convention, "])
        Path(f.name).unlink()

        assert result.exit_code == 1
        assert "does not match pattern" in result.output


def test_check_rules_with_only_separators_is_usage_error():
    """--rules with no actual rule names must error, not lint with zero rules."""
    code = """
from airflow import DAG

dag = DAG('InvalidDAGID')
"""

    runner = CliRunner()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()

        for empty_value in (",", ""):
            result = runner.invoke(cli, ["check", f.name, "--rules", empty_value])
            assert result.exit_code == 2
            assert "All checks passed" not in result.output
        Path(f.name).unlink()


def test_check_rules_with_partial_config_disables_unlisted_rules():
    """--rules disables rules absent from a partial config file (#32)."""
    code = """
from airflow import DAG

default_args = {}

dag = DAG('my_dag', default_args=default_args)
"""

    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        dag_file = Path(tmpdir) / "my_dag.py"
        dag_file.write_text(code)
        config_file = Path(tmpdir) / "partial.yaml"
        config_file.write_text("rules:\n  dag_id_convention:\n    enabled: true\n")

        # owner_validation would flag the empty default_args, but it is not
        # in the requested rules, so it must stay disabled.
        result = runner.invoke(
            cli,
            ["check", str(dag_file), "--config", str(config_file), "--rules", "dag_id_convention"],
        )

        assert result.exit_code == 0
        assert "All checks passed" in result.output


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


def test_check_warnings_only_passes_by_default():
    """Warning-severity issues alone must not fail the build (#39)."""
    result = _run_check(WARNINGS_ONLY_DAG)
    assert result.exit_code == 0
    assert "warning(s)" in result.output
    assert "use --strict" in result.output


def test_check_warnings_only_fails_with_strict():
    """--strict promotes warnings to build failures (#39)."""
    result = _run_check(WARNINGS_ONLY_DAG, "--strict")
    assert result.exit_code == 1


def test_check_clean_passes_with_strict():
    """--strict on a clean file still exits 0."""
    result = _run_check(CLEAN_DAG, "--strict")
    assert result.exit_code == 0
    assert "All checks passed" in result.output


def test_check_errors_fail_without_strict():
    """Error-severity issues exit 1 regardless of --strict (#39)."""
    result = _run_check(ERROR_DAG)
    assert result.exit_code == 1
    assert "error(s)" in result.output


def test_check_format_json_clean():
    """JSON output for a clean file is a parseable envelope with empty issues."""
    result = _run_check(CLEAN_DAG, "--format", "json")
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["issues"] == []
    assert payload["summary"] == {"files_checked": 1, "errors": 0, "warnings": 0, "infos": 0}


def test_check_format_json_with_issues():
    """JSON output carries every issue field and drives the same exit codes."""
    result = _run_check(ERROR_DAG, "--format", "json")
    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["summary"]["errors"] >= 1
    issue = next(i for i in payload["issues"] if i["rule_id"] == "dag_id_convention")
    assert issue["severity"] == "error"
    assert set(issue) == {"rule_id", "severity", "file", "line", "column", "message"}
    assert issue["file"].endswith(".py")
    assert issue["line"] > 0


def test_check_format_json_warnings_only_exit_codes():
    """JSON format follows the same errors-only/--strict exit semantics."""
    assert _run_check(WARNINGS_ONLY_DAG, "--format", "json").exit_code == 0
    assert _run_check(WARNINGS_ONLY_DAG, "--format", "json", "--strict").exit_code == 1


def test_check_format_github():
    """GitHub format emits one workflow command per issue plus a summary."""
    result = _run_check(ERROR_DAG, "--format", "github")
    assert result.exit_code == 1
    assert "::error file=" in result.output
    assert ",line=" in result.output
    assert "[dag_id_convention]" in result.output
    assert "daglint checked 1 file(s)" in result.output


def test_check_format_github_warning_severity():
    """Warning-severity issues map to ::warning commands."""
    result = _run_check(WARNINGS_ONLY_DAG, "--format", "github")
    assert result.exit_code == 0
    assert "::warning file=" in result.output
    assert "::error" not in result.output


def test_check_format_rejects_unknown():
    """An unknown --format value is a usage error."""
    result = _run_check(CLEAN_DAG, "--format", "yaml")
    assert result.exit_code == 2


def test_check_format_json_empty_directory():
    """JSON on a directory with no Python files still emits a valid envelope."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(cli, ["check", tmpdir, "--format", "json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["issues"] == []
    assert payload["summary"]["files_checked"] == 0


def test_check_help_does_not_advertise_fix():
    """--fix is gone for good (autofix is out of scope); help must not mention it (#35)."""
    runner = CliRunner()
    result = runner.invoke(cli, ["check", "--help"])
    assert result.exit_code == 0
    assert "--fix" not in result.output


def test_check_fix_flag_rejected():
    """Passing the removed --fix flag is a usage error, not a silent no-op (#35)."""
    code = """
from airflow import DAG

dag = DAG('my_dag')
"""

    runner = CliRunner()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
    try:
        result = runner.invoke(cli, ["check", f.name, "--fix"])
    finally:
        Path(f.name).unlink()

    assert result.exit_code == 2
    assert "No such option" in result.output


def test_rules_command():
    """Test rules command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["rules"])
    assert result.exit_code == 0
    assert "dag_id_convention" in result.output
    assert "max_active_runs_validation" in result.output
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
