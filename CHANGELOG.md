# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-07-08

### Added
- TaskFlow API support: `@dag`-decorated DAGs are detected via a shared `DagDefinition` layer, and `@task`-decorated tasks are visible to task-scoped rules (#34).
- `@task_group` support with group-aware `task_id` semantics (#62).
- Dynamic task mapping support: tasks created via `.expand()` / `.partial()` are recognized (#63).
- `.override(task_id=...)` re-identification is recognized (#64).
- `@setup` / `@teardown` decorator support (#65).
- `doc_md_validation` rule: warn when a DAG has no `doc_md` documentation (#19).
- `required_dag_params` now also checks inline `DAG(default_args={...})` dicts (#49).
- `--format [text|json|github]` option on `daglint check`: `json` emits a machine-readable envelope (`issues` list plus a `summary` block), `github` emits GitHub Actions workflow commands so issues appear as inline PR annotations (#39).
- `--strict` flag: exit non-zero on any issue, not just errors (#39).
- Directory scans now skip hidden directories and common non-source dirs (`venv/`, `env/`, `build/`, `dist/`, `site-packages/`) by default; extend with an `exclude:` list in `.daglint.yaml` or the repeatable `--exclude` flag (#40).
- Severity values in `.daglint.yaml` are validated on load; anything other than `error`/`warning`/`info` fails fast with a clear message (#40).
- Automated PyPI releases from CI via Trusted Publishing (OIDC): pushing a version tag builds, checks, and publishes the package after environment approval — no stored tokens (#38).

### Changed
- **Breaking for CI gating on warnings:** `daglint check` now exits 1 only when error-severity issues are found. Warning/info issues alone exit 0 unless `--strict` is passed. Exit code 2 means a usage error (#39).
- A file that crashes the linter now always reports a `lint_error` issue (error severity) instead of silently passing without `--verbose`; verbose mode adds the exception type to the message (#40).

### Fixed
- `owner_validation` only checks `owner` keys inside `default_args` dicts, not unrelated dicts (#42).
- Unknown rule names passed to `--rules` are rejected with a usage error instead of silently passing (#46).
- `schedule_validation` messages no longer reference the removed `schedule_interval` argument (#60).
- The default config is the single source of truth for rule defaults, so CLI and config-file behavior cannot drift (#61).

### Removed
- No-op `--fix` flag on `daglint check`; daglint is a pure linter (#47).
- Unused `DAGLinter.lint_directory` method; the CLI is the single collection path (#40).
- `requirements.txt`; runtime dependencies live in `pyproject.toml` only (#40).

### Security
- Hardened GitHub Actions workflows with least-privilege permissions, enabled CodeQL scanning and Dependabot updates, and added `SECURITY.md` with a private vulnerability reporting policy (#68).
- Bumped `urllib3` to 2.7.0 for CVE-2026-44431 / CVE-2026-44432 (#59).

## [0.6.1] - 2025-12-05

### Fixed

## 🎨 Fix Shell Colorization in dev.sh for zsh Compatibility

### Summary
Fixes shell colorization not working under zsh by replacing heredoc-based help text with `printf` statements that 
properly interpret ANSI escape sequences across both bash and zsh.

### Problem
The `dev.sh` script's colorization was not working in zsh shells. Color codes like `\033[0;34m` were being displayed 
as literal text instead of rendering as colors.

### Changes Made

#### `dev.sh`
- **Replaced heredoc with `printf` statements** in `show_help()` function
  - Converted help text from a single heredoc block to individual `printf` calls
  - Each line now explicitly uses `printf` which consistently interprets escape sequences in both bash and zsh
- **Maintained existing color scheme**:
  - 🔵 Blue arrows (`==>`) for status messages
  - ✅ Green checkmarks (`✓`) for success messages
  - ❌ Red X marks (`✗`) for error messages
  - ⚠️ Yellow exclamation marks (`!`) for warning messages

## [0.6.0] - 2025-11-29

### Added
- Add `twine` as the official PyPI upload tool and include it in packaging/dev dependencies.
- Ensure `DEPLOYMENT.md` is tracked by bumpver so release version bumps update the deployment notes.

### Changed
- Update packaging configuration in `pyproject.toml` to use `twine` for uploads and to fix TOML-related issues surfaced during packaging.
- Expand the `bumpver`/versioning configuration (the `bumpver` section in `pyproject.toml`) to include `DEPLOYMENT.md` in `file_patterns` so it is automatically updated on version bumps.
- Tidy CI / release workflow steps to integrate the corrected packaging and upload flow.

### Fixed
- Resolve packaging and TOML misconfiguration that prevented proper PyPI uploads from the release workflow.
- Fix workflow failures related to the upload step by aligning tooling and config (packaging scripts, `twine` invocation, and TOML keys).


## [0.1.0] - 2025-11-22

### Added
- Initial release of DAGLint
- Core linting functionality using Python AST
- CLI tool with `check`, `rules`, and `init` commands
- Nine linting rules:
  - DAG ID naming convention
  - Owner validation
  - Task ID naming convention
  - Retry configuration validation
  - Tag requirements
  - No duplicate task IDs
  - Required DAG parameters
  - Catchup validation
  - Schedule validation
- YAML-based configuration system
- Comprehensive test suite with pytest
- GitHub CI/CD workflows for automated testing
- Code quality checks (black, isort, flake8, mypy)
- Detailed documentation and examples
- Click-based command line interface

### Features
- AST-based linting for accurate code analysis
- Configurable rules with severity levels
- Colorized console output
- Support for linting individual files or directories
- Extensible rule system for custom rules

