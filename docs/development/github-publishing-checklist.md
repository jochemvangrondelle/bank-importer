# GitHub Publishing Checklist

This document tracks the preparation of the project for open-source publishing on GitHub.

## ✅ Completed Tasks

### Documentation Updates

- [x] Updated README.md to replace Gitea references with GitHub

  - Updated badge URLs to GitHub Actions
  - Updated clone URLs to GitHub
  - Updated support links to GitHub Issues/PRs
  - Removed Gitea-specific documentation references

- [x] Updated CONTRIBUTING.md for GitHub

  - Updated fork/clone instructions
  - Updated help links to GitHub Issues/Discussions
  - Fixed dependency installation command (`--group dev`)

- [x] Updated SECURITY.md for GitHub
  - Added GitHub Security Advisories link
  - Updated disclosure policy for GitHub releases

### Configuration Updates

- [x] Updated pyproject.toml
  - Changed `hvcs` from "gitea" to "github"
  - Removed Gitea-specific settings
  - Updated commit author email to GitHub format

### GitHub-Specific Files Created

- [x] Created `.github/workflows/ci.yml`

  - CI workflow for testing on multiple Python versions
  - Type checking and linting
  - Package building

- [x] Created `.github/workflows/release.yml`

  - Automated release workflow using semantic-release
  - Builds and uploads release artifacts

- [x] Created `.github/workflows/dependabot.yml`

  - Auto-merge for Dependabot PRs after tests pass

- [x] Created `.github/dependabot.yml`

  - Dependency update configuration for pip and GitHub Actions

- [x] Created `.github/ISSUE_TEMPLATE/bug_report.md`

  - Bug report template

- [x] Created `.github/ISSUE_TEMPLATE/feature_request.md`

  - Feature request template

- [x] Created `.github/pull_request_template.md`
  - Pull request template

### Community Files

- [x] Created CODE_OF_CONDUCT.md
  - Contributor Covenant Code of Conduct v2.0

### Security Verification

- [x] Verified config-example.toml

  - Only contains example passwords (01011980)
  - No real API keys or sensitive data
  - Google Translate API key field is empty

- [x] Verified no hardcoded API keys in codebase
  - No real API keys found in any files

## 📋 Pre-Publishing Checklist

Before publishing to GitHub, ensure:

### Repository Setup

- [ ] Create repository on GitHub: `jochemvangrondelle/bank-importer`
- [ ] Set repository description: "A Python application that parses Thai bank export PDFs and exports transactions to CSV format suitable for import into Firefly-III"
- [ ] Add topics: `python`, `bank`, `pdf`, `parser`, `firefly-iii`, `thailand`, `financial`
- [ ] Set repository visibility: Public
- [ ] Enable Issues and Discussions
- [ ] Enable GitHub Actions
- [ ] Enable Dependabot

### GitHub Settings

- [ ] Configure branch protection rules for `main` branch
- [ ] Set up required status checks (CI workflow)
- [ ] Enable security advisories
- [ ] Configure repository secrets if needed (for releases)

### Initial Push

- [ ] Push all changes to GitHub
- [ ] Verify CI workflow runs successfully
- [ ] Create initial release (v0.1.0) if desired
- [ ] Verify badges work correctly

### Post-Publishing

- [ ] Update any external documentation that references the repository
- [ ] Announce on relevant communities (if desired)
- [ ] Monitor issues and pull requests

## 🔍 Files to Review Before Publishing

### Sensitive Data Check

- [x] `config-example.toml` - Contains only example data
- [x] `README.md` - No sensitive information
- [x] All source files - No hardcoded credentials

### Documentation Completeness

- [x] README.md - Comprehensive and up-to-date
- [x] CONTRIBUTING.md - Clear contribution guidelines
- [x] SECURITY.md - Security policy defined
- [x] LICENSE - PolyForm Noncommercial License 1.0.0 included
- [x] CODE_OF_CONDUCT.md - Community standards defined

### Configuration Files

- [x] `.gitignore` - Properly configured
- [x] `pyproject.toml` - GitHub configuration updated
- [x] GitHub workflows created

## 📝 Notes

- The project uses semantic-release for automated versioning
- GitHub Actions workflows are configured for CI/CD
- Dependabot is configured for automated dependency updates
- All Gitea-specific references have been replaced with GitHub equivalents
- Example configuration file is safe to publish (no real credentials)

## 🚀 Next Steps

1. Create the GitHub repository
2. Push all changes
3. Verify CI/CD workflows work
4. Create initial release
5. Monitor and respond to community feedback
