# DAGLint

A linting tool for Apache Airflow DAG files. Uses Python's AST to enforce standardisation and best practices across your DAG codebase.

> Inspired by ["Mastering Airflow DAG Standardization with Python's AST"](https://medium.com/apache-airflow/mastering-airflow-dag-standardization-with-pythons-ast-a-deep-dive-into-linting-at-scale-1396771a9b90)

## Features

| Rule | Description |
|------|-------------|
| `dag_id_convention` | Enforces snake_case naming for DAG IDs |
| `task_id_convention` | Enforces snake_case naming for task IDs |
| `group_id_convention` | Enforces snake_case naming for task group IDs |
| `owner_validation` | Validates DAG owners against an approved list |
| `tag_requirements` | Validates required tags are present |
| `required_dag_params` | Ensures required `default_args` keys are set |
| `retry_configuration` | Checks retry values are within configured limits |
| `no_duplicate_task_ids` | Prevents duplicate task IDs within a DAG (task-group aware: `group.task` paths) |
| `max_active_runs_validation` | Ensures `max_active_runs` is explicitly set |
| `catchup_validation` | Checks `catchup` is explicitly set |
| `schedule_validation` | Ensures `schedule_interval` / `schedule` is set |
| `doc_md_validation` | Warns when a DAG has no `doc_md` documentation |
| `unresolved_airflow_symbol` | Flags Airflow-looking names not traceable to any import |

Detection is import-aware: a name only counts as a DAG, task, or task group when it
is traceable to its Airflow origin, so aliased imports (`from airflow import DAG as Dag`)
are detected and same-named symbols from other libraries are not. Names that look like
Airflow constructs but have no binding at all (star imports from non-airflow modules,
generated fragments) are reported by `unresolved_airflow_symbol` at `info` severity
instead of being silently skipped.

## Installation

```bash
# From PyPI
pip install daglint

# From source
pip install -e .
```

## Usage

```bash
# Lint a single file or directory
daglint check dags/my_dag.py
daglint check dags/

# Run specific rules only
daglint check dags/ --rules dag_id_convention,owner_validation

# Machine-readable output for CI and editors
daglint check dags/ --format json

# GitHub Actions annotations (issues appear inline on PRs)
daglint check dags/ --format github

# Fail on warnings too, not just errors
daglint check dags/ --strict

# Skip extra directories when scanning (adds to the built-in defaults)
daglint check . --exclude generated --exclude fixtures

# List all available rules
daglint rules

# Generate a default configuration file
daglint init
```

### Example output

```
$ daglint check examples/invalid_dag.py
✗ examples/invalid_dag.py
  ERROR   [owner_validation]           Line  8: Invalid owner 'invalid-team'. Must be one of: data-team, analytics-team, airflow
  ERROR   [required_dag_params]        Line  8: Missing required parameters in default_args: retries, start_date
  ERROR   [dag_id_convention]          Line 19: DAG ID 'InvalidDAGID' does not match pattern '^[a-z][a-z0-9_]*$'
  WARNING [doc_md_validation]          Line 19: DAG is missing doc_md documentation
  WARNING [tag_requirements]           Line 19: Missing required tags: team, environment
  WARNING [max_active_runs_validation] Line 19: max_active_runs must be explicitly set to 1
  WARNING [catchup_validation]         Line 19: Catchup parameter not set. Consider setting it explicitly to False
  WARNING [schedule_validation]        Line 19: schedule must be explicitly set
  ERROR   [task_id_convention]         Line 30: Task ID 'InvalidTaskID' does not match pattern '^[a-z][a-z0-9_]*$'
  ERROR   [task_id_convention]         Line 36: Task ID 'InvalidTaskID' does not match pattern '^[a-z][a-z0-9_]*$'
  ERROR   [no_duplicate_task_ids]      Line 36: Duplicate task_id 'InvalidTaskID' (first seen at line 30)

--------------------------------------------------
Found 11 issue(s) (6 error(s), 5 warning(s)) in 1 file(s).

$ daglint check examples/valid_dag.py
✓ examples/valid_dag.py

--------------------------------------------------
All checks passed!
```

### Output formats

`--format` selects how issues are reported (default `text`):

- `text` — colorized human-readable output, as above.
- `json` — a machine-readable envelope for CI systems, editors, and wrappers:

  ```json
  {
    "issues": [
      {
        "rule_id": "owner_validation",
        "severity": "warning",
        "file": "dags/etl.py",
        "line": 12,
        "column": 0,
        "message": "DAG must have an owner"
      }
    ],
    "summary": {"files_checked": 8, "errors": 0, "warnings": 1, "infos": 0}
  }
  ```

- `github` — GitHub Actions [workflow commands](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions) (`::error file=...,line=...::message`), so issues show up as inline annotations on pull requests.

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | No issues found, or only warning/info issues without `--strict` |
| 1 | At least one error-severity issue (with `--strict`: any issue at all) |
| 2 | Usage error (unknown rule, bad flag, missing path) |

Warning-severity issues are advisory and do not fail the build by default; pass `--strict` to make them fail CI.

## Configuration

Generate a starter config with `daglint init`, or create `.daglint.yaml` manually:

```yaml
rules:
  dag_id_convention:
    enabled: true
    pattern: "^[a-z][a-z0-9_]*$"
    severity: error

  owner_validation:
    enabled: true
    valid_owners:
      - data-team
      - analytics-team
    severity: error

  tag_requirements:
    enabled: true
    required_tags:
      - environment
      - team
    severity: warning

  retry_configuration:
    enabled: true
    min_retries: 1
    max_retries: 5
    severity: warning

  max_active_runs_validation:
    enabled: true
    max_active_runs: 1
    severity: warning
```

`severity` must be one of `error`, `warning`, or `info`; any other value fails at startup with exit code 2.

### Excluding directories

Directory scans always skip hidden directories (`.venv/`, `.tox/`, `.git/`, …) and these defaults: `venv/`, `env/`, `build/`, `dist/`, `site-packages/`. Add your own directory-name patterns on top — they are matched with shell-style globs against each directory name, anywhere in the tree:

```yaml
exclude:
  - generated
  - "*_fixtures"
```

The repeatable `--exclude` CLI flag is additive with both the defaults and the config list. A file named explicitly on the command line is always linted, regardless of excludes.

## Development

```bash
make install-dev   # Install with dev dependencies
make test          # Run tests
make test-cov      # Run tests with coverage report
make format        # Format code (black + isort)
make lint          # Run all linters
make check         # lint + test
make help          # List all targets
```

## Project structure

```
src/daglint/
  cli.py              # Click CLI: check, rules, init commands
  linter.py           # DAGLinter: orchestrates rule execution
  config.py           # Config: loads .daglint.yaml or uses defaults
  models.py           # LintIssue dataclass
  rules/
    base.py           # BaseRule ABC
    __init__.py       # AVAILABLE_RULES registry
    naming.py         # dag_id_convention, task_id_convention, group_id_convention
    configuration.py  # retry_configuration, schedule_validation, catchup_validation
    validation.py     # no_duplicate_task_ids
    resolution.py     # unresolved_airflow_symbol
    symbols.py        # SymbolTable: import-alias resolution for detection
    metadata/         # owner_validation, tag_requirements, required_dag_params,
                      # max_active_runs_validation, doc_md_validation
tests/
examples/
  valid_dag.py        # Compliant DAG example
  invalid_dag.py      # DAG with multiple violations
```

## Further reading

- [CONTRIBUTING.md](CONTRIBUTING.md) — development setup, git workflow, adding rules
- [DEPLOYMENT.md](DEPLOYMENT.md) — CI/CD pipeline, Airflow integration, publishing to PyPI
- [VERSION_MANAGEMENT.md](VERSION_MANAGEMENT.md) — version bumping with bumpver
- [CHANGELOG.md](CHANGELOG.md) — version history

## License

MIT

