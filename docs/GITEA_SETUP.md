# Gitea Actions Setup

This project is configured to use Gitea Actions for CI/CD instead of GitHub Actions.

## Prerequisites

1. **Gitea Instance**: You need a Gitea instance with Actions enabled
2. **Repository**: Create a repository on your Gitea instance
3. **Secrets**: Configure the required secrets in your Gitea repository

## Required Secrets

Configure these secrets in your Gitea repository settings:

### RELEASE_TOKEN

- **Description**: Personal access token for Gitea API access
- **Required permissions**:
  - `repo` (Full repository access)
  - `write:packages` (Write packages)
- **How to create**:
  1. Go to your Gitea profile → Settings → Applications
  2. Generate New Token
  3. Select the required scopes
  4. Copy the token and add it to repository secrets as `RELEASE_TOKEN`

### GITEA_API_URL (Optional)

- **Description**: Custom Gitea API URL (if different from default)
- **Default**: `https://git.jochempiya.org/api/v1`
- **When to set**: If your Gitea instance uses a custom API path

## Workflow Files

The project includes two main workflow files in `.gitea/workflows/`:

### 1. Release Workflow (`release.yml`)

- **Triggers**: Push to `develop`, `beta`, `stable` branches
- **Manual trigger**: Available via Gitea Actions UI
- **Actions**:
  - Runs semantic-release
  - Updates version and changelog
  - Creates Gitea releases
  - Handles branch merging

### 2. Branch Strategy Workflow (`branch-strategy.yml`)

- **Triggers**: Push to `develop`, `beta`, `stable` branches
- **Actions**:
  - Merges `develop` → `beta` automatically
  - Merges `beta` → `stable` when release is detected

## Release Creation

When a release is triggered, the following will be automatically created on your Gitea release page:

### Release Information

- **Tag**: `v{version}` (e.g., `v1.2.3`)
- **Title**: `Release {version}`
- **Description**: Auto-generated changelog from conventional commits
- **Pre-release**: `true` for beta versions, `false` for stable versions

### Release Assets

- **Source code**: Complete source code as ZIP and TAR.GZ
- **Wheel package**: Python wheel distribution (`bank_importer_th-{version}-py3-none-any.whl`)
- **Source distribution**: Source tarball (`bank_importer_th-{version}.tar.gz`)

### Example Release

```
Release v1.2.3
Tag: v1.2.3
Pre-release: No

## What's Changed
* feat: add support for new bank format by @username in #123
* fix: resolve PDF parsing issue by @username in #124
* docs: update installation instructions by @username in #125

**Full Changelog**: https://gitea.example.com/username/bank-importer-th/compare/v1.2.2...v1.2.3

Assets:
- Source code (zip)
- Source code (tar.gz)
- bank_importer_th-1.2.3-py3-none-any.whl
- bank_importer_th-1.2.3.tar.gz
```

## Configuration

### Semantic Release

The semantic-release configuration is set for Gitea:

```toml
[tool.semantic_release]
hvcs = "gitea"
upload_to_vcs_release = true
upload_to_release = true
```

### Repository URLs

Update the repository URLs in `pyproject.toml`:

```toml
[project.urls]
Homepage      = "https://your-gitea-instance.com/username/bank-importer-th/"
Repository    = "https://your-gitea-instance.com/username/bank-importer-th"
Documentation = "https://your-gitea-instance.com/username/bank-importer-th/"
```

## Setup Steps

1. **Clone the repository**:

   ```bash
   git clone https://your-gitea-instance.com/username/bank-importer-th.git
   cd bank-importer-th
   ```

2. **Update repository URLs**:

   - Edit `pyproject.toml` and replace `gitea.example.com` with your actual Gitea instance URL
   - Update README.md badges with your Gitea instance URL

3. **Configure secrets**:

   - Add `GITEA_TOKEN` secret in repository settings

4. **Test the setup**:

   ```bash
   # Run the setup script
   ./scripts/setup-semantic-release.sh

   # Test a commit
   make commit

   # Test release (if on appropriate branch)
   make release
   ```

## Branch Protection

Configure branch protection rules in Gitea:

### Develop Branch

- Require pull request reviews
- Require status checks to pass
- Require up-to-date branches

### Beta Branch

- Require pull request reviews
- Require status checks to pass
- Allow force pushes (for automatic merging)

### Stable Branch

- Require pull request reviews
- Require status checks to pass
- Require admin review for merges

## Troubleshooting

### Common Issues

1. **Token Permissions**:

   - Ensure `GITEA_TOKEN` has sufficient permissions
   - Check token hasn't expired

2. **Workflow Not Triggering**:

   - Verify Actions are enabled on your Gitea instance
   - Check branch names match exactly (`develop`, `beta`, `stable`)

3. **Release Creation Fails**:

   - Verify semantic-release can access Gitea API
   - Check repository permissions

4. **Branch Merging Fails**:
   - Ensure the bot user has write access
   - Check for merge conflicts

### Debugging

1. **Check Action Logs**:

   - Go to Actions tab in your Gitea repository
   - Click on failed workflow runs
   - Review step logs for errors

2. **Test Locally**:

   ```bash
   # Test semantic-release locally
   uv run semantic-release version --dry-run
   uv run semantic-release changelog --dry-run
   ```

3. **Verify Configuration**:
   ```bash
   # Check current configuration
   uv run semantic-release print-config
   ```

## Migration from GitHub Actions

If migrating from GitHub Actions:

1. **Remove GitHub workflows**:

   ```bash
   rm -rf .github/workflows
   ```

2. **Update all references**:

   - Replace `github.com` with your Gitea instance URL
   - Update badge URLs
   - Update repository URLs in documentation

3. **Reconfigure secrets**:

   - Create new Gitea token
   - Add `GITEA_TOKEN` secret
   - Remove old `GITHUB_TOKEN` secret

4. **Test thoroughly**:
   - Run all workflows manually
   - Verify releases are created correctly
   - Check branch merging works as expected
