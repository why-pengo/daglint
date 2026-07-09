# Contributing to DAGLint

Thank you for your interest in contributing to DAGLint! This document provides guidelines for contributing to the project.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/daglint.git
cd daglint
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
make install-dev
```

## Running Tests

Run all tests:
```bash
make test
```

Run with coverage:
```bash
make test-cov
```

## Code Quality

Before submitting a PR, ensure your code passes all quality checks:

```bash
# Format code
make format

# Run all checks (lint + test)
make check

# Or run individually:
make lint
make test
```

Alternative using direct commands:
```bash
# Format code
black src/daglint tests
isort src/daglint tests

# Lint code
flake8 src/daglint

# Type checking
mypy src/daglint

# Run tests
pytest
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
1. On `develop`, run `bumpver` to bump the version (creates a commit + tag):
   ```bash
   bumpver update --minor --no-fetch   # or --patch / --major
   ```
2. Update `CHANGELOG.md` then open a PR from `develop` → `main`.
3. After the PR merges, push the tag and publish manually:
   ```bash
   git push origin --tags
   python -m build && python -m twine upload dist/*
   ```

## Pull Request Process

1. Create a branch named `issue-<number>` from `develop`
2. Make your changes with tests
3. Ensure all tests and linting pass: `make check`
4. Commit your changes with a descriptive message
5. Push and open a PR targeting `develop`
6. Resolve all review comments before merging

## Coding Standards

- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep functions focused and small
- Write tests for new functionality

## Adding New Rules

To add a new linting rule:

1. Choose the appropriate module in `src/daglint/rules/` based on your rule category:
   - `naming.py`: Naming convention rules
   - `configuration.py`: Configuration validation rules
   - `metadata/`: Metadata rules
   - `validation.py`: Structural validation rules
2. Create a new rule class that inherits from `BaseRule`
3. Implement the required methods (`rule_id`, `description`, `check`)
4. Export the rule in `src/daglint/rules/__init__.py` and add to `AVAILABLE_RULES`
5. Add default configuration in `src/daglint/config.py` and `.daglint.example.yaml`
6. Write tests in `tests/rules/test_<rule_id>.py`
7. Update documentation

## Reporting Issues

- Use GitHub Issues to report bugs or request features
- Provide clear reproduction steps for bugs
- Include Python version and relevant dependencies

## Code of Conduct

Be respectful and constructive in all interactions.
