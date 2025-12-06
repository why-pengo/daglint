# DAGLint Quick Start Guide

## Installation

### From the project root, install in editable mode:
```bash
pip install -e .
```

## Basic Usage

### Check a single DAG file
```bash
daglint check path/to/your_dag.py
```

### Check all DAGs in a directory
```bash
daglint check path/to/dags/
```

### List available rules
```bash
daglint rules
```

### Generate configuration file
```bash
daglint init
```

## Running Tests

```bash
# Run all tests
./dev.sh test

# Run with coverage
./dev.sh test-cov
```

## Development Commands

```bash
# Install dev dependencies
./dev.sh install-dev

# Format code
./dev.sh format

# Run linting
./dev.sh lint

# Clean build artifacts
./dev.sh clean

# Build package
./dev.sh build

# Run all checks (lint + test)
./dev.sh check

# See all available commands
./dev.sh help
```

## Example Output

### ✅ Valid DAG
```bash
$ daglint check examples/valid_dag.py
✓ examples/valid_dag.py

--------------------------------------------------
All checks passed!
```

### ❌ Invalid DAG
```bash
$ daglint check examples/invalid_dag.py
✗ examples/invalid_dag.py
  ERROR [owner_validation] Line 8: Invalid owner 'invalid-team'
  ERROR [dag_id_convention] Line 19: DAG ID 'InvalidDAGID' does not match pattern
  ERROR [no_duplicate_task_ids] Line 35: Duplicate task_id 'InvalidTaskID'

--------------------------------------------------
Found 9 issue(s) in 1 file(s).
```

## Configuration

Create `.daglint.yaml` in your project root:

```yaml
rules:
  dag_id_convention:
    enabled: true
    pattern: "^[a-z][a-z0-9_]*$"
  
  owner_validation:
    enabled: true
    valid_owners:
      - data-team
      - analytics-team
```

## CI/CD Integration

The project includes GitHub Actions workflows that:
- Run tests on Python 3.10, 3.11, 3.12
- Check code quality (black, flake8, isort, mypy)
- Generate coverage reports
- Validate pull requests

Workflows are located in `.github/workflows/`

## Project Stats

- **39 tests** - All passing ✅
- **94% coverage** - Excellent coverage
- **9 linting rules** - Comprehensive validation
- **3 CLI commands** - Simple interface

## Next Steps

1. Try linting your own DAG files
2. Customize `.daglint.yaml` for your needs
3. Add to your CI/CD pipeline
4. Contribute new rules or improvements

## Getting Help

- Check `README.md` for full documentation
- See `PROJECT_SUMMARY.md` for architecture details
- Read `CONTRIBUTING.md` for development guidelines
- View examples in `examples/` directory

