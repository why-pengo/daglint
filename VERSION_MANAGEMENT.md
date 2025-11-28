# Version Management with Bumpver

This project uses [bumpver](https://github.com/mbarkhau/bumpver) to manage version numbers consistently across multiple files.

## Installation

Bumpver is included in the dev dependencies and can be installed with:

```bash
pip install -e ".[dev]"
```

Or install it directly:

```bash
pip install bumpver
```

## Configuration

Bumpver is configured in `pyproject.toml` under the `[tool.bumpver]` section:

```toml
[tool.bumpver]
current_version = "0.5.0"
version_pattern = "MAJOR.MINOR.PATCH"
commit_message = "bump version {old_version} -> {new_version}"
commit = true
tag = true
push = false

[tool.bumpver.file_patterns]
"pyproject.toml" = [
    'current_version = "{version}"',
    'version = "{version}"',
]
"src/daglint/__init__.py" = [
    '__version__ = "{version}"',
]
"PROJECT_SUMMARY.md" = [
    '**Version:** {version}',
]
"DEPLOYMENT.md" = [
    '**Version**: {version}',
]
```

### Configuration Options

- **current_version**: The current version of the project
- **version_pattern**: The versioning scheme (MAJOR.MINOR.PATCH)
- **commit**: Automatically create a git commit (default: true)
- **tag**: Automatically create a git tag (default: true)
- **push**: Automatically push to remote (default: false for safety)
- **file_patterns**: Files and patterns to update

## Usage

### Show Current Version

```bash
bumpver show --no-fetch
```

### Preview Changes (Dry Run)

Always preview changes before applying them:

```bash
# Patch version (0.5.0 -> 0.5.1)
bumpver update --patch --dry --no-fetch

# Minor version (0.5.0 -> 0.6.0)
bumpver update --minor --dry --no-fetch

# Major version (0.5.0 -> 1.0.0)
bumpver update --major --dry --no-fetch
```

### Update Version

#### Patch Release (Bug fixes)

Increment the patch version (0.5.0 -> 0.5.1):

```bash
bumpver update --patch --no-fetch
```

#### Minor Release (New features)

Increment the minor version (0.5.0 -> 0.6.0):

```bash
bumpver update --minor --no-fetch
```

#### Major Release (Breaking changes)

Increment the major version (0.5.0 -> 1.0.0):

```bash
bumpver update --major --no-fetch
```

#### Set Specific Version

Set version explicitly:

```bash
bumpver update --set-version "1.2.3" --no-fetch
```

### Additional Options

#### Dry Run

Use `--dry` or `-d` to preview changes without modifying files:

```bash
bumpver update --patch --dry --no-fetch
```

#### No Commit

Update files but don't commit:

```bash
bumpver update --patch --no-commit --no-fetch
```

#### No Tag

Commit changes but don't create a git tag:

```bash
bumpver update --patch --no-tag-commit --no-fetch
```

#### Push to Remote

Automatically push the commit and tag to remote:

```bash
bumpver update --patch --push
```

⚠️ **Warning**: Be careful with `--push` as it immediately pushes to the remote repository.

## Workflow Examples

### Standard Release Workflow

1. **Make your changes and commit them**
   ```bash
   git add .
   git commit -m "Add new feature"
   ```

2. **Preview the version bump**
   ```bash
   bumpver update --minor --dry --no-fetch
   ```

3. **Apply the version bump**
   ```bash
   bumpver update --minor --no-fetch
   ```
   
   This will:
   - Update version in `pyproject.toml` (2 places)
   - Update version in `src/daglint/__init__.py`
   - Update version in `PROJECT_SUMMARY.md`
   - Update version in `DEPLOYMENT.md`
   - Create a git commit with message: "bump version 0.5.0 -> 0.6.0"
   - Create a git tag: "v0.6.0"

4. **Push to remote**
   ```bash
   git push origin main --tags
   ```

### Quick Patch Release

For quick bug fixes:

```bash
# Preview
bumpver update --patch --dry --no-fetch

# Apply and push
bumpver update --patch --no-fetch
git push origin main --tags
```

### Pre-release Testing

Test version bump without committing:

```bash
bumpver update --minor --no-commit --no-fetch
# Review changes
# If satisfied: git add . && git commit -m "bump version"
# If not: git checkout -- .
```

## Semantic Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Incompatible API changes
- **MINOR** (0.X.0): New features, backward compatible
- **PATCH** (0.0.X): Bug fixes, backward compatible

### When to Bump Each Version

#### Patch (0.5.0 -> 0.5.1)
- Bug fixes
- Documentation updates
- Internal refactoring
- Performance improvements (no API changes)

#### Minor (0.5.0 -> 0.6.0)
- New features
- New rules added
- New CLI options
- Deprecations (with backward compatibility)

#### Major (0.5.0 -> 1.0.0)
- Breaking API changes
- Removing deprecated features
- Major redesign
- Incompatible changes to configuration format

## Files Updated by Bumpver

When you run bumpver, it automatically updates:

1. **`pyproject.toml`**
   - Line: `version = "X.Y.Z"` (in `[project]` section)
   - Line: `current_version = "X.Y.Z"` (in `[tool.bumpver]` section)

2. **`src/daglint/__init__.py`**
   - Line: `__version__ = "X.Y.Z"`

3. **`PROJECT_SUMMARY.md`**
   - Line: `**Version:** X.Y.Z`

4. **`DEPLOYMENT.md`**
   - Line: `**Version**: X.Y.Z`

## Troubleshooting

### Error: "Command 'git fetch' returned non-zero exit status"

Use the `--no-fetch` or `-n` flag to skip fetching from remote:

```bash
bumpver update --patch --no-fetch
```

### Working Directory Has Uncommitted Changes

If you have uncommitted changes and want to bump anyway:

```bash
bumpver update --patch --allow-dirty --no-fetch
```

⚠️ **Warning**: Only use `--allow-dirty` if you're sure about your changes.

### Verify Configuration

Check if bumpver can find and parse the configuration:

```bash
bumpver show --no-fetch -v
```

### Manual Version Update

If bumpver fails, you can manually update these files:

1. `pyproject.toml` - Update both `version` and `current_version`
2. `src/daglint/__init__.py` - Update `__version__`
3. `PROJECT_SUMMARY.md` - Update `**Version:**` line
4. `DEPLOYMENT.md` - Update `**Version**:` line

Then commit and tag:

```bash
git add pyproject.toml src/daglint/__init__.py PROJECT_SUMMARY.md DEPLOYMENT.md
git commit -m "bump version 0.5.0 -> 0.5.1"
git tag v0.5.1
```

## Integration with CI/CD

### GitHub Actions

You can automate version bumping in GitHub Actions:

```yaml
- name: Bump version
  run: |
    pip install bumpver
    bumpver update --patch --no-fetch
    
- name: Push changes
  run: |
    git push origin main --tags
```

### Pre-commit Hook

You can validate versions are synchronized:

```bash
# Ensure all version strings match
python -c "
from importlib.metadata import version
import tomli
with open('pyproject.toml', 'rb') as f:
    toml = tomli.load(f)
assert toml['project']['version'] == version('daglint')
"
```

## Best Practices

1. **Always use `--dry` first** to preview changes
2. **Use `--no-fetch`** if you're working offline or don't need to sync tags
3. **Create a release branch** for major versions
4. **Update CHANGELOG.md** before bumping version
5. **Test your changes** before bumping version
6. **Use semantic versioning** consistently
7. **Don't use `--push`** unless you're sure - prefer manual push for more control

## Additional Resources

- [Bumpver Documentation](https://github.com/mbarkhau/bumpver)
- [Semantic Versioning](https://semver.org/)
- [Python Packaging User Guide](https://packaging.python.org/)

