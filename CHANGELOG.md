# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

