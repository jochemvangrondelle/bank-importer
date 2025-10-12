#!/bin/bash

# Setup script for semantic release and pre-commit hooks
# This script should be run once to set up the development environment

set -e

echo "🚀 Setting up semantic release and pre-commit hooks..."

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv sync --python 3.11 --all-groups

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg

# Verify installation
echo "✅ Verifying installation..."

# Check if commitizen is working
if uv run --python 3.11 cz --version > /dev/null 2>&1; then
    echo "✅ Commitizen installed successfully"
else
    echo "❌ Commitizen installation failed"
    exit 1
fi

# Check if semantic-release is working
if uv run --python 3.11 semantic-release --version > /dev/null 2>&1; then
    echo "✅ Semantic-release installed successfully"
else
    echo "❌ Semantic-release installation failed"
    exit 1
fi

# Check pre-commit hooks
if uv run --python 3.11 pre-commit --version > /dev/null 2>&1; then
    echo "✅ Pre-commit installed successfully"
else
    echo "❌ Pre-commit installation failed"
    exit 1
fi

echo ""
echo "🎉 Setup complete! You can now:"
echo ""
echo "  • Use 'make commit' for interactive commits"
echo "  • Use 'make release' for manual releases"
echo "  • Use 'make dev-check' to run all checks"
echo "  • Use 'make version' to check current version"
echo ""
echo "📚 For more information, see docs/RELEASE_PROCESS.md"
echo "🔧 For Gitea setup, see docs/GITEA_SETUP.md"
echo ""
echo "🚀 Releases will be automatically created on your Gitea release page!"
echo ""
echo "🔧 To test the setup, try:"
echo "  make commit"
echo "  make dev-check"
