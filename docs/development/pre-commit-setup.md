# Pre-commit Hooks Setup

This project uses [pre-commit](https://pre-commit.com/) hooks to ensure code quality and consistency before commits. The hooks are configured to match the checks in GitHub Actions CI workflow exactly.

## Quick Start

### Install Pre-commit Hooks

```bash
# Install development dependencies and pre-commit hooks (recommended)
uv run poe dev-setup

# Or manually
uv sync --group dev
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
```

### Run Hooks Manually

```bash
# Run on all files
uv run poe pre-commit-run

# Or directly
uv run pre-commit run --all-files
```

## Configured Hooks

The pre-commit configuration (`.pre-commit-config.yaml`) includes hooks that match the CI workflow:

### 1. **General File Checks**

- Trailing whitespace removal
- End of file fixer
- YAML, JSON, TOML validation
- Merge conflict detection
- Case conflict detection
- Large file detection
- Debug statement detection
- Line ending normalization (LF)

### 2. **Ruff Linting & Formatting**

- **Linting**: Runs `ruff check` with auto-fix
- **Formatting**: Runs `ruff format` to ensure consistent code style
- Matches CI: `uv run ruff check src/` and `uv run ruff format --check src/`

### 3. **MyPy Type Checking**

- Runs type checking on `src/` directory
- Uses configuration from `pyproject.toml`
- Matches CI: `uv run mypy src/`

### 4. **Pytest Tests**

- Runs all tests before commit
- Matches CI: `uv run pytest`
- Only runs if Python files are changed

### 5. **Commitizen (Conventional Commits) - Commit Message Validation**

- **Validates commit messages** follow Conventional Commits format
- **Enforced at commit-msg stage** - prevents invalid commit messages BEFORE they are committed
- **Strict mode enabled** - ensures all commits follow the standard
- **Interactive commit helper** - use `make commit` for guided commits
- Matches CI: Uses same commit convention

**Commit Message Format:**

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Valid Types:**

- `feat`: New feature (appears in "Added" section of changelog)
- `fix`: Bug fix (appears in "Fixed" section of changelog)
- `perf`: Performance improvement (appears in "Changed" section)
- `refactor`: Code refactoring (appears in "Changed" section)
- `docs`: Documentation changes (not in changelog)
- `style`: Code style changes (not in changelog)
- `test`: Test changes (not in changelog)
- `build`: Build system changes (not in changelog)
- `ci`: CI/CD changes (not in changelog)
- `chore`: Other changes (not in changelog)

**Examples:**

```bash
feat: add support for new bank format
fix: resolve PDF parsing issue
feat(parser): add AMEX CSV parser
fix(database): handle duplicate transaction detection
perf: optimize PDF parsing for large files
refactor: improve translation service architecture

# Breaking changes (triggers major version bump)
feat!: change API response format
fix!: remove deprecated function
```

**Using Commitizen (Recommended):**

```bash
# Interactive commit helper - guides you through creating proper commit message
make commit

# Or directly
uv run cz commit
```

### 6. **Security Checks**

- **Bandit**: Security linting for Python code
- **Detect Secrets**: Scans for accidentally committed secrets

## Hook Behavior

### Automatic Execution

Hooks run automatically on:

- `git commit` - Runs on staged files AND validates commit message (commit-msg hook)
- `git commit -m "message"` - Validates commit message format before commit completes
- **Commit message validation happens at commit-msg stage** - Invalid messages will be rejected

**Example of commit message validation:**

```bash
# This will be rejected by commitizen hook
git commit -m "fix bug"

# This will pass
git commit -m "fix: resolve PDF parsing bug"

# Or use interactive helper
make commit  # Guides you through creating proper commit message
```

### Manual Execution

```bash
# Run all hooks on staged files
uv run pre-commit run

# Run specific hook
uv run pre-commit run ruff-check
uv run pre-commit run mypy
uv run pre-commit run pytest

# Run on all files (useful for CI-like checks)
uv run pre-commit run --all-files

# Validate commit message manually
uv run cz check --rev HEAD~1..HEAD
```

### Skipping Hooks

In rare cases, you can skip hooks (not recommended):

```bash
# Skip all hooks
git commit --no-verify -m "message"

# Skip specific hook
SKIP=mypy git commit -m "message"
```

**Note**: Skipping hooks may cause CI to fail. Only skip if absolutely necessary.

## Matching CI Workflow

The pre-commit hooks are configured to match `.github/workflows/ci.yml` exactly:

| CI Check                   | Pre-commit Hook                | Status     |
| -------------------------- | ------------------------------ | ---------- |
| `ruff check src/`          | `ruff-check`                   | ✅ Matches |
| `ruff format --check src/` | `ruff-format`                  | ✅ Matches |
| `mypy src/`                | `mypy`                         | ✅ Matches |
| `pytest`                   | `pytest`                       | ✅ Matches |
| Conventional Commits       | `commitizen` (commit-msg hook) | ✅ Matches |

## Configuration

### Ruff Configuration

Ruff settings are in `pyproject.toml` under `[tool.ruff]`. Pre-commit uses the same configuration.

### MyPy Configuration

MyPy settings are in `pyproject.toml` under `[tool.mypy]`. Pre-commit uses the same configuration.

### Commitizen Configuration

Commitizen settings are in `pyproject.toml` under `[tool.commitizen]`. Pre-commit uses `cz-conventional-commits` with strict mode.

## Troubleshooting

### Hook Installation Issues

```bash
# Reinstall hooks
uv run pre-commit uninstall
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
```

### Hook Failures

If a hook fails:

1. **Auto-fixable issues**: Most hooks will auto-fix issues. Review changes and commit again.
2. **Manual fixes**: Some issues require manual fixes (e.g., type errors, test failures).
3. **Check CI**: If hooks pass locally but CI fails, ensure you're using the same Python version and dependencies.

### Commit Message Validation Failures

If commit message validation fails:

```bash
# Use interactive commit helper
make commit

# Or check what's wrong
uv run cz check --rev HEAD

# Fix the commit message
git commit --amend -m "feat: proper commit message"
```

### Performance

If hooks are slow:

```bash
# Update hook versions
uv run pre-commit autoupdate

# Run only on changed files (default)
uv run pre-commit run

# Skip slow hooks during development (not recommended for commits)
SKIP=mypy,pytest git commit -m "message"
```

### Type Checking Issues

If MyPy fails:

1. Check `pyproject.toml` for MyPy configuration
2. Ensure type stubs are installed: `uv sync --group dev`
3. Review type errors and fix them
4. If needed, add type ignores with comments: `# type: ignore[error-code]`

### Test Failures

If tests fail in pre-commit:

1. Run tests manually: `uv run pytest`
2. Fix failing tests
3. Ensure all tests pass before committing

## Best Practices

1. **Always run hooks before pushing**: Use `make pre-commit-all` before pushing
2. **Fix issues immediately**: Don't skip hooks; fix the issues
3. **Keep hooks updated**: Run `uv run pre-commit autoupdate` periodically
4. **Match CI locally**: Run `make dev-check` to match CI exactly
5. **Use conventional commits**: Always use proper commit message format
6. **Use commitizen helper**: Use `make commit` for guided commit creation

## Integration with CI

The pre-commit hooks ensure that:

- Code formatting is consistent
- Type checking passes
- Tests pass
- Commit messages follow conventions
- No secrets are committed

This means if pre-commit passes locally, CI should also pass (assuming same environment).

## Updating Hooks

```bash
# Update all hooks to latest versions
uv run pre-commit autoupdate

# Update specific hook
# Edit .pre-commit-config.yaml and change the `rev` field
```

## Additional Resources

- [Pre-commit Documentation](https://pre-commit.com/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Commitizen Documentation](https://commitizen-tools.github.io/commitizen/)
- [Conventional Commits](https://www.conventionalcommits.org/)
