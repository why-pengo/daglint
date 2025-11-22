# DAGLint

A linting tool for Apache Airflow DAG files using Python's AST (Abstract Syntax Tree) to enforce standardization and best practices.

## Features

- **DAG ID Convention**: Ensures DAG IDs follow naming conventions
- **Owner Validation**: Checks that DAG owners are specified and valid
- **Task ID Convention**: Validates task IDs follow naming patterns
- **Retry Configuration**: Ensures retry settings are properly configured
- **Tag Requirements**: Validates required tags are present
- **Import Validation**: Checks for prohibited or required imports
- **Schedule Validation**: Ensures schedule_interval is properly set
- **Documentation Checks**: Validates DAG and task documentation

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Lint a single DAG file
daglint check path/to/dag.py

# Lint all DAGs in a directory
daglint check path/to/dags/

# Lint with specific rules
daglint check path/to/dag.py --rules dag_id_convention,owner_validation

# List all available rules
daglint rules

# Generate a configuration file
daglint init
```

## Configuration

Create a `.daglint.yaml` file in your project root:

```yaml
rules:
  dag_id_convention:
    enabled: true
    pattern: "^[a-z][a-z0-9_]*$"
  
  owner_validation:
    enabled: true
    valid_owners:
      - "data-team"
      - "analytics-team"
  
  task_id_convention:
    enabled: true
    pattern: "^[a-z][a-z0-9_]*$"
  
  retry_configuration:
    enabled: true
    min_retries: 1
    max_retries: 5
  
  tag_requirements:
    enabled: true
    required_tags:
      - "environment"
      - "team"
  
  schedule_validation:
    enabled: true
    allow_none: false
```

## Development

```bash
# Install development dependencies
./dev.sh install-dev

# Run tests
./dev.sh test

# Run tests with coverage
./dev.sh test-cov

# Format code
./dev.sh format

# Run linting checks
./dev.sh lint

# Run all quality checks
./dev.sh check

# See all available commands
./dev.sh help
```

## License

MIT

