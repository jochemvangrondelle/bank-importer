# Linting Guide

This document describes the linting setup for the Rust CLI.

## Linters

The project uses two main linters:

1. **rustfmt** - Code formatter
2. **clippy** - Linter with many helpful checks

## Configuration

### rustfmt

Configuration is in `rustfmt.toml`:

- Max line width: 100 characters
- Tab spaces: 4
- Unix line endings
- Various formatting preferences

### clippy

Configuration is in `Cargo.toml` under `[lints.clippy]`:

- Most rules set to "warn" (not errors)
- Pedantic and nursery lints enabled
- Focus on correctness, performance, and style

## Running Linters

### Format Code

```bash
cargo fmt
```

### Check Formatting

```bash
cargo fmt --check
```

### Run Clippy

```bash
cargo clippy --all-features
```

### Run Clippy with Warnings as Errors

```bash
cargo clippy --all-features -- -D warnings
```

### Fix Clippy Issues Automatically

```bash
cargo clippy --all-features --fix --allow-dirty --allow-staged
```

### Using Makefile

```bash
make fmt        # Format code
make fmt-check  # Check formatting
make lint       # Run clippy
make lint-fix   # Fix clippy issues
```

## Pre-commit Hooks

To run linters before committing, you can set up pre-commit hooks:

```bash
# Install pre-commit (if not already installed)
pip install pre-commit

# Create .pre-commit-config.yaml in project root
# Then:
pre-commit install
```

Example `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/doublify/pre-commit-rust
    rev: v1.0
    hooks:
      - id: fmt
      - id: clippy
```

## CI/CD

Linters run automatically in CI/CD:

- Formatting is checked
- Clippy runs with `-D warnings` (warnings as errors)
- Both must pass for CI to succeed

See `.github/workflows/ci.yml` for details.

## Common Issues

### Line Too Long

If rustfmt complains about line length:

- Break the line manually
- Or adjust `max_width` in `rustfmt.toml`

### Clippy Warnings

Most clippy warnings can be:

- Fixed automatically with `--fix`
- Suppressed with `#[allow(clippy::lint_name)]` if needed
- Adjusted in `Cargo.toml` if too strict

### Import Ordering

rustfmt automatically orders imports. If you need different ordering:

- Adjust `imports_granularity` in `rustfmt.toml`
- Or use `#[rustfmt::skip]` for specific imports

## Best Practices

1. **Always format before committing**: `cargo fmt`
2. **Fix clippy warnings**: They're usually helpful
3. **Don't suppress warnings without reason**: Understand why the warning exists
4. **Keep configuration consistent**: Don't override linter settings unnecessarily
