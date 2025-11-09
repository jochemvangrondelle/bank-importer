# Developer Guide

This guide provides detailed information for developers working on Bank Importer Thailand.

## Development Setup

### Prerequisites

- Python 3.11, 3.12, or 3.13
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip
- Git

### Initial Setup

1. **Clone the repository**:

   ```bash
   git clone https://github.com/jochemvangrondelle/bank-importer.git
   cd bank-importer
   ```

2. **Install dependencies**:

   ```bash
   uv sync --group dev
   ```

3. **Install pre-commit hooks**:

   ```bash
   uv run poe dev-setup
   ```

   This installs pre-commit hooks that automatically check code quality before each commit. The hooks run:

   - `ruff` for linting and formatting
   - `mypy` and `pyright` for type checking
   - `pytest` for running tests
   - `commitizen` for validating commit messages

4. **Copy example configuration**:
   ```bash
   cp config-example.toml config.toml
   ```

## Task Automation with Poe the Poet

This project uses [poethepoet](https://github.com/nat-n/poethepoet) for task automation. All tasks are defined in `pyproject.toml` under `[tool.poe.tasks]`.

### Installation Tasks

```bash
# Install production dependencies
uv run poe install

# Install development dependencies
uv run poe install-dev

# Install documentation dependencies
uv run poe install-docs

# Install all dependencies (production + dev + docs)
uv run poe install-all
```

### Linting and Formatting Tasks

```bash
# Check linting and formatting (read-only)
uv run poe lint

# Fix linting and formatting issues automatically
uv run poe lint-fix

# Format code only
uv run poe format

# Check formatting only (read-only)
uv run poe format-check
```

### Type Checking Tasks

```bash
# Run both mypy and pyright
uv run poe type-check

# Run mypy only (strict mode)
uv run poe type-check-mypy

# Run pyright only
uv run poe type-check-pyright
```

### Testing Tasks

```bash
# Run all tests
uv run poe test

# Run tests in parallel (faster)
uv run poe test-fast

# Run tests with coverage report
uv run poe test-cov

# Run tests with XML coverage (for CI)
uv run poe test-cov-xml

# Run all checks: tests + linting + type checking
uv run poe test-all
```

### Pre-commit Tasks

```bash
# Install pre-commit hooks
uv run poe pre-commit-install

# Run all pre-commit hooks manually
uv run poe pre-commit-run

# Update pre-commit hooks to latest versions
uv run poe pre-commit-update
```

### Tox Tasks

```bash
# Run tox (tests across multiple Python versions)
uv run poe tox

# List available tox environments
uv run poe tox-list

# Run specific tox environment (e.g., qa)
uv run poe tox-qa
```

### Documentation Tasks

```bash
# Build documentation
uv run poe docs-build

# Serve documentation locally (with live reload)
uv run poe docs-serve

# Deploy documentation to GitHub Pages
uv run poe docs-deploy
```

### Development Setup Tasks

```bash
# Complete development setup (install deps + pre-commit hooks)
uv run poe dev-setup

# Clean build artifacts
uv run poe clean

# Clean everything including virtual environments
uv run poe clean-all
```

### Release Tasks

```bash
# Bump version and generate changelog
uv run poe release

# Publish release (bump version + create git tag + publish)
uv run poe release-publish
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

Write your code following the project's coding standards:

- Use type hints for all functions
- Follow PEP 8 style guide (enforced by ruff)
- Write docstrings for all public functions and classes
- Add tests for new functionality

### 3. Run Quality Checks

Before committing, run all checks:

```bash
uv run poe test-all
```

This will:

- Run all tests with coverage
- Check linting and formatting
- Run type checkers (mypy and pyright)

### 4. Fix Issues Automatically

If linting issues are found, fix them automatically:

```bash
uv run poe lint-fix
```

### 5. Commit Your Changes

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```bash
git commit -m "feat: add support for new bank X"
git commit -m "fix: resolve translation issue"
git commit -m "docs: update README with new features"
```

The pre-commit hooks will automatically validate your commit message format.

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Code Quality Standards

### Type Checking

- **mypy**: Configured in strict mode
- **pyright**: Also configured for additional type checking
- All functions must have type hints
- Use `typing` module for complex types

### Linting and Formatting

- **ruff**: Used for both linting and formatting
- Configured with strict rules (see `pyproject.toml`)
- Line length: 88 characters (handled by formatter)
- Run `poe lint-fix` to automatically fix issues

### Testing

- **pytest**: Test framework
- **pytest-xdist**: Parallel test execution
- **pytest-cov**: Coverage reporting
- Target: 90% code coverage
- Tests should use centralized fixtures from `conftest.py`
- Use parameterized tests where applicable

### Pre-commit Hooks

Pre-commit hooks automatically run before each commit:

- `ruff-check`: Linting
- `ruff-format`: Formatting
- `mypy`: Type checking (strict)
- `pyright`: Type checking
- `pytest`: Tests (if Python files changed)
- `commitizen`: Commit message validation

## Project Structure

```
bank-importer/
├── src/bank_importer/    # Source code
│   ├── banks/                # Bank parsers
│   ├── targets/              # Export targets
│   ├── models/               # Data models
│   ├── translation_terms/    # Translation dictionaries
│   └── cli/                  # CLI commands
├── tests/                    # Test suite
│   ├── conftest.py          # Shared fixtures
│   └── ...
├── docs/                     # Documentation
├── config-example.toml       # Example configuration
├── pyproject.toml            # Project configuration
└── README.md                 # Project README
```

## Common Development Tasks

### Adding a New Bank Parser

1. Create parser in `src/bank_importer/banks/`
2. Implement the `Parser` interface
3. Add tests in `tests/parsers/`
4. Update `config-example.toml`
5. Update documentation

### Adding a New Export Target

1. Create target in `src/bank_importer/targets/`
2. Implement the `Target` interface
3. Add tests in `tests/targets/`
4. Update documentation

### Running Specific Tests

```bash
# Run specific test file
uv run pytest tests/test_processor.py

# Run specific test
uv run pytest tests/test_processor.py::TestProcessor::test_init

# Run with verbose output
uv run pytest tests/test_processor.py -v

# Run with coverage for specific file
uv run pytest tests/test_processor.py --cov=src/bank_importer/processor
```

### Debugging

```bash
# Run with debug output
uv run pytest tests/ -v -s

# Run with pdb on failure
uv run pytest tests/ --pdb

# Run specific test with pdb
uv run pytest tests/test_processor.py::TestProcessor::test_init --pdb
```

## CI/CD Integration

All quality checks run automatically in GitHub Actions:

- Tests (Python 3.11, 3.12, 3.13)
- Linting (ruff)
- Type checking (mypy, pyright)
- Code coverage (Codecov)
- Documentation build

Ensure your changes pass all checks locally before pushing:

```bash
uv run poe test-all
```

## Getting Help

- **Documentation**: [Read the Docs](https://bank-importer.readthedocs.io/)
- **Issues**: [GitHub Issues](https://github.com/jochemvangrondelle/bank-importer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jochemvangrondelle/bank-importer/discussions)

## Additional Resources

- [Conventional Commits](https://www.conventionalcommits.org/)
- [PEP 8 Style Guide](https://pep8.org/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)
- [ruff Documentation](https://docs.astral.sh/ruff/)
- [mypy Documentation](https://mypy.readthedocs.io/)
