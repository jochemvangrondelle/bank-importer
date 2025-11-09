# Changelog Guide

This project uses [python-semantic-release](https://python-semantic-release.readthedocs.io/) to automatically generate beautiful, well-formatted changelogs from conventional commits.

## Changelog Format

The changelog follows the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format and is automatically generated based on your commit messages.

### Structure

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- New features

### Changed

- Changes in existing functionality

### Fixed

- Bug fixes

## [1.2.0] - 2024-01-15

### Added

- Support for new bank format
- Enhanced translation service

### Fixed

- PDF parsing issue with special characters
- Memory leak in transaction processing
```

## Automatic Generation

The changelog is automatically updated when you:

1. **Make conventional commits** - Each commit message is parsed
2. **Push to develop/main** - Semantic-release analyzes commits
3. **Release is created** - Changelog is updated with new version

### Section Mapping

Commit types are automatically mapped to changelog sections:

| Commit Type | Changelog Section | Description                      |
| ----------- | ----------------- | -------------------------------- |
| `feat`      | **Added**         | New features                     |
| `fix`       | **Fixed**         | Bug fixes                        |
| `perf`      | **Changed**       | Performance improvements         |
| `refactor`  | **Changed**       | Code refactoring                 |
| `docs`      | _Ignored_         | Documentation (not in changelog) |
| `style`     | _Ignored_         | Code style (not in changelog)    |
| `test`      | _Ignored_         | Tests (not in changelog)         |
| `build`     | _Ignored_         | Build system (not in changelog)  |
| `ci`        | _Ignored_         | CI/CD (not in changelog)         |
| `chore`     | _Ignored_         | Other changes (not in changelog) |

## Writing Good Commit Messages

To generate beautiful changelogs, write clear, descriptive commit messages:

### ✅ Good Examples

```bash
feat: add support for SCB PDF statements
feat(parser): implement AMEX CSV parser with currency conversion
fix: resolve duplicate transaction detection
fix(database): handle IntegrityError for duplicate transactions
perf: optimize PDF parsing for large files
refactor: improve translation service architecture
```

### ❌ Bad Examples

```bash
# Too vague
fix: bug fix
update: changes
wip: working on feature

# Missing type
add new parser
fix bug

# Not conventional
[FIX] Bug in parser
NEW: Added feature
```

## Changelog Features

### Automatic Features

- **Version links**: Each version links to GitHub compare view
- **Date stamps**: Release dates are automatically added
- **Grouped changes**: Changes are grouped by type
- **Scope information**: Commit scopes are included when present
- **Filtered content**: Only user-facing changes appear

### Ignored Commits

The following commits are automatically excluded from the changelog:

- Merge commits
- Commits with `[skip ci]`, `[ci skip]`, `[no ci]`
- Commits with `[skip changelog]`, `[changelog skip]`
- Documentation-only commits (`docs`)
- Style-only commits (`style`)
- Test-only commits (`test`)
- Build system commits (`build`, `ci`, `chore`)

## Manual Changelog Updates

While the changelog is automatically generated, you can manually add entries to the `[Unreleased]` section for:

- Breaking changes (documented separately)
- Migration guides
- Deprecation notices
- Important announcements

**Note**: Manual entries in `[Unreleased]` are preserved during automatic updates.

## Viewing Changelog

```bash
# View full changelog
cat CHANGELOG.md

# View only unreleased changes
grep -A 100 "## \[Unreleased\]" CHANGELOG.md

# View specific version
grep -A 50 "## \[1.2.0\]" CHANGELOG.md
```

## Changelog in Releases

When a release is created:

1. **Unreleased section** is moved to the new version
2. **Version header** is added with date and link
3. **GitHub release** includes the changelog
4. **New Unreleased section** is created for future changes

## Best Practices

1. **Write clear commit messages** - They become changelog entries
2. **Use appropriate types** - `feat` for features, `fix` for bugs
3. **Add scope when relevant** - `feat(parser): ...` is clearer than `feat: ...`
4. **Keep commits focused** - One logical change per commit
5. **Use breaking change notation** - `feat!: ...` for major version bumps

## Examples

### Feature Addition

```bash
# Commit
feat: add YAML export target for human-readable output

# Changelog Entry
### Added
- YAML export target for human-readable output
```

### Bug Fix

```bash
# Commit
fix: resolve duplicate transaction detection issue

# Changelog Entry
### Fixed
- Duplicate transaction detection issue
```

### Feature with Scope

```bash
# Commit
feat(parser): add support for AMEX Thailand CSV format

# Changelog Entry
### Added
- AMEX Thailand CSV format support (parser)
```

### Breaking Change

```bash
# Commit
feat!: change API response format

# Changelog Entry
### Added
- New API response format (BREAKING CHANGE)

# Also triggers major version bump
```

## Troubleshooting

### Changelog Not Updating

If the changelog doesn't update:

1. Check commit messages follow Conventional Commits
2. Verify semantic-release is running
3. Check GitHub Actions logs
4. Ensure commits are not ignored

### Missing Entries

If expected entries are missing:

1. Check if commit type is ignored (docs, style, test, etc.)
2. Verify commit message format
3. Check for `[skip changelog]` in commit message
4. Ensure commit is in the correct branch

### Formatting Issues

If changelog formatting looks wrong:

1. Check `pyproject.toml` changelog configuration
2. Verify semantic-release version
3. Review changelog template (if custom)
4. Check for manual formatting conflicts

## Configuration

Changelog generation is configured in `pyproject.toml`:

```toml
[tool.semantic_release]
changelog_file = "CHANGELOG.md"
changelog_scope = "src/bank_importer"
changelog_sections = ["feat", "fix", "perf", "refactor", ...]
changelog_ignore_types = ["docs", "style", "test", "build", "ci", "chore"]
```

For more details, see [Release Process Documentation](../development/release-process.md).
