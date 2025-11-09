# Version Management

This document describes how version management works in Bank Importer Thailand.

## Overview

The project uses [python-semantic-release](https://python-semantic-release.readthedocs.io/) for automated version management based on [Conventional Commits](https://www.conventionalcommits.org/).

## Branch Strategy

### `develop` Branch

- **Purpose**: Development and pre-release versions
- **Release Type**: Pre-release
- **Docker Tag**: `latest`
- **Git Tag**: `v{version}-prerelease.{number}`
- **Example**: `v0.2.0-prerelease.1`, `v0.2.0-prerelease.2`

### `main` Branch

- **Purpose**: Production-ready stable releases
- **Release Type**: Stable release
- **Docker Tag**: `stable`
- **Git Tag**: `v{version}`
- **Example**: `v0.2.0`, `v1.0.0`

## Version Format

Versions follow [Semantic Versioning](https://semver.org/):

- **Major**: Breaking changes (e.g., `1.0.0` → `2.0.0`)
- **Minor**: New features, backward compatible (e.g., `1.0.0` → `1.1.0`)
- **Patch**: Bug fixes, backward compatible (e.g., `1.0.0` → `1.0.1`)

## Commit Convention

All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```bash
# Examples
feat: add support for new bank format        # Minor version bump
fix: resolve PDF parsing issue              # Patch version bump
feat!: breaking change in API                # Major version bump
docs: update installation instructions       # No version bump
chore: update dependencies                  # No version bump
```

### Commit Types

- `feat`: New feature (minor version bump)
- `fix`: Bug fix (patch version bump)
- `perf`: Performance improvement (patch version bump)
- `refactor`: Code refactoring (no version bump)
- `docs`: Documentation changes (no version bump)
- `style`: Code style changes (no version bump)
- `test`: Test changes (no version bump)
- `build`: Build system changes (no version bump)
- `ci`: CI/CD changes (no version bump)
- `chore`: Other changes (no version bump)

### Breaking Changes

To trigger a major version bump, include `!` after the type:

```bash
feat!: remove deprecated API endpoint
fix!: change default behavior
```

## Version Integration

### Package Version

The version is stored in `pyproject.toml`:

```toml
[project]
version = "0.1.0"  # Managed by semantic-release
```

### CLI Version Command

```bash
bank-importer --version
# or
bank-importer version
```

Output includes:

- Package version
- Version components (major, minor, patch)
- Release status
- Git commit (if available)
- Build date (if available)

### Docker Images

Docker images are tagged with:

- **Version tag**: `ghcr.io/jochemvangrondelle/bank-importer:{version}`
- **Branch tag**:
  - `latest` for `develop` branch
  - `stable` for `main` branch

Example:

```bash
# Latest development version
docker pull ghcr.io/jochemvangrondelle/bank-importer:latest

# Specific stable version
docker pull ghcr.io/jochemvangrondelle/bank-importer:0.2.0

# Latest stable version
docker pull ghcr.io/jochemvangrondelle/bank-importer:stable
```

### Docker Labels

All Docker images include OCI labels:

- `org.opencontainers.image.version`: Package version
- `org.opencontainers.image.title`: "Bank Importer Thailand"
- `org.opencontainers.image.description`: Project description
- `org.opencontainers.image.licenses`: "PolyForm-Noncommercial-1.0.0"
- `org.opencontainers.image.revision`: Git commit SHA
- `org.opencontainers.image.source`: Repository URL
- `org.opencontainers.image.created`: Build timestamp

### Git Tags

Git tags are automatically created by semantic-release:

- Format: `v{version}` for stable releases
- Format: `v{version}-{prerelease_token}.{number}` for pre-releases
- Example: `v0.2.0`, `v0.2.0-prerelease.1`, `v0.2.0-prerelease.2`

## Release Process

### Automatic Releases

Releases are automatically triggered when:

1. Commits are pushed to `develop` or `main` branches
2. Commits follow the Conventional Commits specification
3. Semantic-release determines a version bump is needed

### Manual Release

If needed, you can trigger a release manually:

```bash
# Make a commit with conventional format
git commit -m "feat: add new feature"

# Push to trigger release
git push origin develop  # or main
```

### Release Workflow

1. **Commit**: Developer makes a commit following Conventional Commits
2. **Push**: Commit is pushed to `develop` or `main` branch
3. **CI/CD**: GitHub Actions workflow runs
4. **Semantic Release**: Analyzes commits and determines version bump
5. **Version Update**: Updates `pyproject.toml` with new version
6. **Git Tag**: Creates git tag with version
7. **GitHub Release**: Creates GitHub release with changelog
8. **Docker Build**: Builds and pushes Docker image with version tags
9. **Package Build**: Builds Python package artifacts

## Version Access

### In Python Code

```python
from bank_importer import __version__
print(__version__)  # e.g., "0.2.0"
```

### In Docker Container

```bash
# Environment variable
echo $APP_VERSION

# Version file
cat /app/.version

# CLI command
bank-importer --version
```

### In GitHub Actions

```yaml
- name: Get version
  run: |
    uv sync
    VERSION=$(python -c "import importlib.metadata; print(importlib.metadata.version('bank-importer'))")
    echo "version=$VERSION" >> $GITHUB_OUTPUT
```

## Troubleshooting

### Version Not Updating

If the version doesn't update after a commit:

1. Check commit message follows Conventional Commits format
2. Verify semantic-release is configured correctly
3. Check GitHub Actions logs for errors
4. Ensure branch is `develop` or `main`

### Docker Image Version Mismatch

If Docker image version doesn't match package version:

1. Check build logs for version extraction
2. Verify `VERSION` build arg is passed correctly
3. Check Dockerfile version extraction logic

### CLI Version Shows "0.0.0"

If CLI shows fallback version:

1. Ensure package is installed: `uv sync`
2. Check `pyproject.toml` has correct version
3. Verify package metadata is correct

## Best Practices

1. **Always use Conventional Commits**: Ensures proper version bumping
2. **Test in develop first**: Use `develop` branch for testing before merging to `main`
3. **Use breaking change notation**: Include `!` for major version bumps
4. **Check version before release**: Verify version is correct before pushing
5. **Monitor release workflow**: Check GitHub Actions for successful releases
