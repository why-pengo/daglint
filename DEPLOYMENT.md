# DAGLint Deployment Guide

For installation and development setup, see [README.md](README.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## CI/CD Pipeline

### Automated Checks on Every PR
The CI pipeline will automatically:
1. Run tests on Python 3.10, 3.11, 3.12
2. Check code formatting (black, isort)
3. Run linting (flake8)
4. Type check with mypy
5. Generate coverage reports
6. Build the package

### Pull Request Requirements
For a PR to be merged, it must:
- ✅ Pass all tests on Python 3.10, 3.11, and 3.12
- ✅ Pass linting (flake8) and type checking (mypy)
- ✅ Be formatted correctly (black, isort)

All of these are enforced by CI — any failure blocks the merge. Coverage is
reported on every run but not currently gated. Run `make check` locally to
run the identical gates before pushing.

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

Releases are published automatically by CI (`.github/workflows/release.yml`) using
[PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) — no API tokens or
stored secrets. Pushing a release tag (unprefixed, e.g. `1.1.0`) triggers the workflow,
which builds the sdist and wheel, verifies them with `twine check`, and publishes to
PyPI from the protected `pypi` environment.

The release flow is: bump the version on `develop`, open a PR to `main`, merge, push
the tag — CI does the rest.

### 1. Update Version with Bumpver

Run on the `develop` branch before opening the release PR:

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
- `DEPLOYMENT.md`

### 2. Open and Merge the Release PR

Open a PR from `develop` to `main` and merge it once CI passes.

### 3. Push the Tag

bumpver already created the tag locally (unprefixed, e.g. `1.1.0`):

```bash
git push origin --tags
```

### 4. Approve the Publish

The tag push starts the **Release** workflow. It builds the sdist and wheel, runs
`twine check`, then pauses: the publish job waits for approval on the `pypi`
environment. Approve it under Actions → the workflow run → **Review deployments**.
Once approved, CI publishes via Trusted Publishing (OIDC) — no credentials involved.

### 5. Verify

```bash
pip install --upgrade daglint
daglint --version
```

Or check https://pypi.org/project/daglint/ for the new version.

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
- Ensure all dependencies are declared in pyproject.toml

## Support

For issues or questions:
- Check [README.md](README.md) for usage and configuration
- Review [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- See [VERSION_MANAGEMENT.md](VERSION_MANAGEMENT.md) for versioning details

---

**Status**: ✅ Ready for production use
**Version**: 1.0.0
**Last Updated**: November 28, 2025

