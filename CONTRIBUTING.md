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
./dev.sh install-dev
```

## Running Tests

Run all tests:
```bash
./dev.sh test
```

Run with coverage:
```bash
./dev.sh test-cov
```

## Code Quality

Before submitting a PR, ensure your code passes all quality checks:

```bash
# Format code
./dev.sh format

# Run all checks (lint + test)
./dev.sh check

# Or run individually:
./dev.sh lint
./dev.sh test
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

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Coding Standards

- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep functions focused and small
- Write tests for new functionality

## Adding New Rules

To add a new linting rule:

1. Create a new rule class in `src/daglint/rules.py` that inherits from `BaseRule`
2. Implement the required methods (`rule_id`, `description`, `check`)
3. Add the rule to `AVAILABLE_RULES` dictionary
4. Write tests in `tests/test_rules.py`
5. Update documentation

## Reporting Issues

- Use GitHub Issues to report bugs or request features
- Provide clear reproduction steps for bugs
- Include Python version and relevant dependencies

## Code of Conduct

Be respectful and constructive in all interactions.

