# Copilot Instructions for daglint

`daglint` is a static analysis / linting tool for Apache Airflow DAG files. It parses Python files using the `ast` module and runs configurable rules against the AST.

## Commands

```bash
# Install with dev dependencies
make install-dev
# or: pip install -e ".[dev]"

# Run all tests
pytest
# or: make test

# Run a single test file
pytest tests/rules/test_dag_id_convention.py -v

# Run a single test by name
pytest tests/rules/test_dag_id_convention.py::TestDAGIDConventionRule::test_invalid_dag_id -v

# Format code (black + isort)
make format

# Lint (flake8 + black check + isort check + mypy)
make lint

# Run all checks (lint + test)
make check
```

Line length is **127** (configured in `pyproject.toml` and `.flake8`).

## Architecture

```
src/daglint/
  cli.py        # Click CLI: check, rules, init commands
  linter.py     # DAGLinter: loads rules, calls rule.check() per file
  config.py     # Config: loads .daglint.yaml or uses defaults
  models.py     # LintIssue dataclass
  rules/
    base.py     # BaseRule ABC — all rules extend this
    __init__.py # AVAILABLE_RULES dict registry
    naming.py         # dag_id_convention, task_id_convention
    configuration.py  # retry_configuration, schedule_validation, catchup_validation
    metadata/         # owner_validation, tag_requirements, required_dag_params
    validation.py     # no_duplicate_task_ids
```

**Data flow**: `cli.py` → `DAGLinter._load_rules()` (reads `AVAILABLE_RULES`, filters by config) → for each `.py` file: `ast.parse()` → `rule.check(tree, file_path, source_code)` → `LintIssue` list → sorted by line number.

Config is loaded from `.daglint.yaml` in the working directory, or falls back to `Config.default()`. Each rule entry has `enabled`, `severity`, and rule-specific keys (e.g., `pattern`, `min_retries`).

## Adding a New Rule

1. Add the rule class to the appropriate module in `src/daglint/rules/` (or create a new one):
   - `naming.py` — naming conventions
   - `configuration.py` — DAG/task configuration
   - `metadata/` — metadata, ownership, tags
   - `validation.py` — structural validation

2. Inherit from `BaseRule` and implement three things:
   ```python
   @property
   def rule_id(self) -> str: ...       # snake_case string, unique
   @property
   def description(self) -> str: ...   # human-readable
   def check(self, tree: ast.AST, file_path: str, source_code: str) -> List[LintIssue]: ...
   ```
   Use `self.create_issue(message, file_path, line, column)` to produce issues (picks up `self.severity`).
   Use helpers from `BaseRule`: `_is_operator_call(node)`, `_extract_task_id(node)`, `_extract_dag_id(node)`.

3. Register in `src/daglint/rules/__init__.py`:
   - Import the class
   - Add to `AVAILABLE_RULES` dict and `__all__`

4. Add default config entry in `Config._default_config()` in `src/daglint/config.py`.

5. Add a test file `tests/rules/test_<rule_id>.py`. Tests construct ASTs directly — no file I/O:
   ```python
   tree = ast.parse(code)
   rule = MyRule()
   issues = rule.check(tree, "test.py", code)
   ```

## Git Workflow

The branching model is: `issue-<number>` → `develop` → `main` (releases only).

### Feature work
- All work must be done on a branch named after the GitHub issue (e.g., `issue-42`).
- Always start from a fresh pull of the `develop` branch:
  ```bash
  git checkout develop && git pull origin develop
  git checkout -b issue-<number>
  ```
- Pull requests must target `develop` (not `main`).
- CI must pass and all review comments must be resolved before merge.

### Releasing
1. On `develop`, run `bumpver` to bump the version (creates a commit + tag locally):
   ```bash
   bumpver update --minor --no-fetch   # or --patch / --major
   ```
2. Open a PR from `develop` → `main`. This is the release PR — include CHANGELOG updates.
3. After the PR merges, push the tag and publish manually:
   ```bash
   git push origin --tags
   python -m build && python -m twine upload dist/*
   ```

## Key Conventions

- Rules are detected as abstract if `inspect.isabstract()` returns `True` — `BaseRule` is skipped automatically.
- `severity` defaults to `"error"` unless overridden in rule config (passed as `config` dict to `__init__`).
- Operator detection: `_is_operator_call` matches any class name ending in `"Operator"` (both `ast.Name` and `ast.Attribute`).
- `DAGLinter.lint_file` catches `SyntaxError` into a `syntax_error` issue; other exceptions are only surfaced when `verbose=True`.
- Version is managed with `bumpver`; version string lives in `pyproject.toml` and `src/daglint/__init__.py`.
