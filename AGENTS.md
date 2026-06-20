# DAGLint — Agent Instructions

## Quick commands
- `make check` — run the full pipeline: **format → lint → test** (order matters!)
  - Format with **black** (line-length 127) + **isort** (`profile = black`, line-length 127)
  - Lint with **flake8** (src/daglint), **black --check**, **isort --check-only**, and **mypy** — all on `src/daglint` and `tests`
  - Test with **pytest tests/ -v**
    - Tests run from the repo root; config is in `pyproject.toml` under `[tool.pytest.ini_options]`
- Direct commands: `black src/daglint tests`, `isort src/daglint tests`, `flake8 src/daglint`, `mypy src/daglint --ignore-missing-imports`, `pytest tests/ -v`

## Architecture
- **src/daglint/** — the package
  - `cli.py` — Click CLI entry: `daglint check`, `daglint rules`, `daglint init`
  - `linter.py` — DAGLinter: orchestrates rule execution
  - `config.py` — config loader (`.daglint.yaml`) + defaults
  - `models.py` — LintIssue dataclass
  - `rules/base.py` — BaseRule ABC
  - `rules/__init__.py` — AVAILABLE_RULES registry
  - `rules/naming.py` — dag_id_convention, task_id_convention
  - `rules/configuration.py` — retry_configuration, schedule_validation, catchup_validation
  - `rules/validation.py` — no_duplicate_task_ids
  - `rules/metadata/` — owner_validation, tag_requirements, required_dag_params, max_active_runs_validation, doc_md_validation

## Adding a new rule
1. Create rule class in the appropriate module under `src/daglint/rules/` (or `rules/metadata/`)
2. Inherit from `BaseRule`, implement `rule_id`, `description`, `check`
3. Export in `src/daglint/rules/__init__.py` and add to `AVAILABLE_RULES`
4. Add defaults in `src/daglint/config.py`
5. Write tests in `tests/rules/test_<rule_id>.py`

## Branching / PRs
- Branch from `develop`: `git checkout develop && git pull origin develop`
- Name branch `issue-<number>`, target `develop` (not main)
- Run `make check` before opening a PR
