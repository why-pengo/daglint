# DAGLint Deployment Guide

## Local Development Setup

### Prerequisites
- Python 3.8 or higher
- pip
- Git

### Installation Steps

1. **Clone/Navigate to the repository**

2. **Create virtual environment** (if not exists)
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install the package**
   ```bash
   pip install -e .
   ```

4. **Install development dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

5. **Verify installation**
   ```bash
   daglint --version
   daglint rules
   ```

## Testing the Installation

### Run Tests
```bash
pytest tests/ -v --cov=daglint
```

### Test CLI Commands
```bash
# List rules
daglint rules

# Check example DAGs
daglint check examples/valid_dag.py
daglint check examples/invalid_dag.py

# Generate config
daglint init --output test-config.yaml
```

### Run Code Quality Checks
```bash
# Format code
black src/daglint tests
isort src/daglint tests

# Lint
flake8 src/daglint

# Type check (optional - some warnings expected)
mypy src/daglint --ignore-missing-imports
```

## CI/CD Pipeline

### Automated Checks on Every PR
The CI pipeline will automatically:
1. Run tests on Python 3.9, 3.10, 3.11
2. Check code formatting (black, isort)
3. Run linting (flake8)
4. Type check with mypy
5. Generate coverage reports
6. Build the package

### Pull Request Requirements
For a PR to be merged, it must:
- ✅ Pass all tests
- ✅ Maintain or improve code coverage
- ✅ Pass all linting checks
- ✅ Be formatted correctly

## Using DAGLint in Your Airflow Project

### Option 1: Install from Local Source
```bash
pip install -e .
```

### Option 2: Install from PyPI

DAGLint is available on PyPI: https://pypi.org/project/daglint/

```bash
pip install daglint
```

## Integration with Airflow Projects

### 1. Add Configuration
Create `.daglint.yaml` in your Airflow project root:
```bash
cd /path/to/your/airflow-project
daglint init
```

### 2. Customize Configuration
Edit `.daglint.yaml` to match your team's standards:
- Valid owners
- Required tags
- Naming patterns
- Retry limits

### 3. Run Linter
```bash
# Check all DAGs
daglint check dags/

# Check specific file
daglint check dags/my_dag.py
```

### 4. Add to CI/CD
Add to your `.github/workflows/ci.yml`:
```yaml
- name: Lint DAG files
  run: |
    pip install daglint
    daglint check dags/
```

### 5. Add Pre-commit Hook (Optional)
Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: local
    hooks:
      - id: daglint
        name: DAGLint
        entry: daglint check
        language: system
        files: \.py$
```

## Publishing to PyPI

When ready to publish a new version:

### 1. Update Version with Bumpver

```bash
# Preview the version bump
bumpver update --patch --dry --no-fetch   # Bug fixes: 0.5.0 -> 0.5.1
bumpver update --minor --dry --no-fetch   # New features: 0.5.0 -> 0.6.0
bumpver update --major --dry --no-fetch   # Breaking changes: 0.5.0 -> 1.0.0

# Apply the version bump (updates all files, creates commit and tag)
bumpver update --minor --no-fetch
```

This automatically updates:
- `pyproject.toml` (2 locations)
- `src/daglint/__init__.py`
- `PROJECT_SUMMARY.md`
- `DEPLOYMENT.md`

### 2. Build Distribution Packages

```bash
# Clean old builds
rm -rf dist/ build/ *.egg-info

# Build source and wheel distributions
python -m build
```

This creates:
- `dist/daglint-X.Y.Z.tar.gz` (source distribution)
- `dist/daglint-X.Y.Z-py3-none-any.whl` (wheel distribution)

### 3. Check Package with Twine

```bash
# Verify the package metadata and files
python -m twine check dist/*
```

### 4. Test Upload to TestPyPI (Recommended)

```bash
# Upload to TestPyPI first
python -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --no-deps daglint
```

### 5. Upload to Production PyPI

```bash
# Upload to production PyPI
python -m twine upload dist/*
```

You'll be prompted for your PyPI credentials or API token.

### 6. Push Changes to GitHub

```bash
# Push the commit and tags
git push origin main --tags
```

### Authentication Options

**Option 1: API Token (Recommended)**

Create a PyPI API token at https://pypi.org/manage/account/token/

```bash
# Set environment variables
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmc...

# Or use .pypirc file
cat > ~/.pypirc << EOF
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...

[testpypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...
EOF
chmod 600 ~/.pypirc
```

**Option 2: Username/Password**

Enter credentials when prompted by twine.

## Monitoring and Maintenance

### Check Test Coverage
```bash
pytest --cov=daglint --cov-report=html
open htmlcov/index.html
```

### View GitHub Actions
- Go to repository → Actions tab
- View workflow runs and logs
- Check test results and coverage

### Update Dependencies
```bash
pip list --outdated
pip install --upgrade <package>
```

## Troubleshooting

### Tests Failing
```bash
# Clear cache and rerun
pytest --cache-clear tests/
```

### Import Errors
```bash
# Reinstall in editable mode
pip install -e .
```

### CI Failing
- Check GitHub Actions logs
- Run tests locally first
- Ensure all dependencies are in requirements.txt

## Support

For issues or questions:
- Check documentation in `README.md`
- Review `CONTRIBUTING.md` for development
- See `PROJECT_SUMMARY.md` for architecture
- Use `QUICKSTART.md` for quick reference

---

**Status**: ✅ Ready for production use
**Version**: 0.6.1
**Last Updated**: November 28, 2025

