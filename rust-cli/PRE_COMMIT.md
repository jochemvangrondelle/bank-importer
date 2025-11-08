# Pre-commit Hooks for Rust CLI

## Overview

Pre-commit hooks for the Rust CLI are configured in the root `.pre-commit-config.yaml` file. These hooks run automatically before each commit to ensure code quality.

## Included Hooks

The following hooks are configured for Rust files in `rust-cli/`:

1. **rustfmt** - Formats Rust code
   - Matches: `cargo fmt --check` in CI
   - Auto-fixes formatting issues

2. **clippy** - Lints Rust code
   - Matches: `cargo clippy --all-features -- -D warnings` in CI
   - Catches common mistakes and style issues

3. **cargo check** - Verifies code compiles
   - Matches: Build step in CI
   - Ensures code compiles before commit

## Installation

Pre-commit hooks are installed at the repository root:

```bash
# From project root
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
```

## Usage

Hooks run automatically on `git commit`. To run manually:

```bash
# From project root
uv run pre-commit run --all-files

# Run only Rust hooks
uv run pre-commit run --all-files --hook-stage manual rust

# Run specific hook
uv run pre-commit run rustfmt --all-files
uv run pre-commit run clippy --all-files
```

## Matching CI

The pre-commit hooks match the GitHub Actions workflow (`.github/workflows/rust-cli.yml`):

| CI Check | Pre-commit Hook | Status |
|----------|----------------|--------|
| `cargo fmt --check` | `rustfmt` | ✅ Matches |
| `cargo clippy --all-features -- -D warnings` | `clippy` | ✅ Matches |
| `cargo build --release` | `cargo-check` | ✅ Matches |

## Skipping Hooks

In rare cases, you can skip hooks (not recommended):

```bash
# Skip all hooks
git commit --no-verify -m "message"

# Skip specific hook
SKIP=clippy git commit -m "message"
```

**Note**: Skipping hooks may cause CI to fail. Only skip if absolutely necessary.

## Troubleshooting

### Hook Installation

```bash
# Reinstall hooks
uv run pre-commit uninstall
uv run pre-commit install
```

### Hook Failures

If a hook fails:
1. **Auto-fixable issues**: Most hooks will auto-fix issues. Review changes and commit again.
2. **Manual fixes**: Some issues require manual fixes (e.g., clippy warnings, compilation errors).

### Performance

Rust hooks can be slow. They only run on changed files by default. To speed up:
- Use `cargo watch` for development
- Run hooks manually before committing
- Use `SKIP` for temporary work (remember to fix before pushing)

