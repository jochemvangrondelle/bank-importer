# Release Process

This project uses [python-semantic-release](https://python-semantic-release.readthedocs.io/) for automated versioning and releases based on conventional commits.

## Branch Strategy

The project follows a two-branch strategy:

- **`develop`**: Latest merged changes, continuous integration, publishes pre-release versions tagged as "latest"
- **`main`**: Production releases, publishes stable versions tagged as "stable"

## Commit Convention

All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Supported Types

- `feat`: A new feature
- `fix`: A bug fix
- `perf`: A performance improvement
- `refactor`: Code refactoring
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `test`: Adding or updating tests
- `build`: Build system changes
- `ci`: CI/CD changes
- `chore`: Other changes that don't modify source code

### Examples

```bash
feat: add support for new bank format
fix: resolve PDF parsing issue with special characters
docs: update installation instructions
chore: update dependencies
```

## Pre-commit Hooks

Pre-commit hooks are configured to enforce:

- Conventional commit message format
- Code formatting (ruff)
- Linting (ruff, mypy)
- File validation (YAML, JSON, TOML)

Install pre-commit hooks:

```bash
make dev-setup
```

## Release Workflow

### Automatic Releases

Releases are automatically triggered when:

1. Commits are pushed to `develop` or `main` branches
2. GitHub Actions workflow runs semantic-release
3. Version is bumped based on commit messages
4. Changelog is updated
5. GitHub release is created
6. Docker images are built and pushed with version tags

### Manual Release

To manually trigger a release:

```bash
# Using Makefile
make release

# Or using semantic-release directly
uv run semantic-release version
uv run semantic-release changelog
uv run semantic-release publish
```

### Version Bumping Rules

- **Patch** (0.1.0 → 0.1.1): `fix`, `perf`, `refactor`
- **Minor** (0.1.0 → 0.2.0): `feat`
- **Major** (0.1.0 → 1.0.0): Breaking changes (indicated by `!` in commit message)

### Pre-release Versions

- Pre-release versions are created on the `develop` branch
- Stable versions are created on the `main` branch
- Pre-release versions use the `prerelease` tag
- Docker images are tagged with `latest` for develop branch and `stable` for main branch

## Docker Integration

The Dockerfile is optimized for:

- Multi-stage builds for smaller image size
- Version information embedded in the image
- Health checks
- Non-root user execution

Build with version:

```bash
make docker-build
```

## Development Workflow

1. Create feature branch from `develop`
2. Make changes with conventional commits
3. Run pre-commit hooks: `make pre-commit`
4. Run tests: `make test`
5. Create pull request to `develop` or `main`
6. After merge, automatic release process begins:
   - `develop` → creates pre-release with `latest` Docker tag
   - `main` → creates stable release with `stable` Docker tag

## Configuration

Semantic release configuration is in `pyproject.toml`:

```toml
[tool.semantic_release]
version_toml = ["pyproject.toml:project.version"]
build_command = "uv build"
dist_path = "dist"
upload_to_vcs_release = true
upload_to_pypi = false
upload_to_release = true
hvcs = "github"
remote = { name = "origin" }
major_on_zero = false
prerelease_tag = "prerelease"
prerelease = true
prerelease_token = "prerelease"
changelog_file = "CHANGELOG.md"

[tool.semantic_release.branches]
develop = { name = "develop", prerelease = true, prerelease_token = "prerelease", tags = ["latest"] }
main = { name = "main", prerelease = false, tags = ["stable"] }
```

## Troubleshooting

### Commit Message Validation

If pre-commit fails on commit message:

```bash
# Use commitizen for interactive commit
make commit

# Or manually fix the commit message
git commit --amend -m "feat: your message here"
```

### Release Issues

Check GitHub Actions logs for detailed error information. Common issues:

- Missing conventional commit format
- Insufficient permissions (GITHUB_TOKEN)
- Version conflicts
- Docker build failures

### Version Information

Check current version:

```bash
make version
```

## Best Practices

1. **Always use conventional commits** - This ensures proper version bumping
2. **Keep commits atomic** - One logical change per commit
3. **Write clear commit messages** - Describe what and why, not how
4. **Test before committing** - Run `make dev-check` before pushing
5. **Use meaningful branch names** - `feature/add-new-parser`, `fix/pdf-issue`
6. **Keep PRs focused** - One feature or fix per pull request
