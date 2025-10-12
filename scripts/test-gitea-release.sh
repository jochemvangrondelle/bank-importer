#!/bin/bash

# Test script for Gitea release configuration
# This script helps verify that the semantic-release configuration is correct for Gitea

set -e

echo "🧪 Testing Gitea release configuration..."

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check if semantic-release is installed
if ! uv run semantic-release --version > /dev/null 2>&1; then
    echo "❌ Error: semantic-release not installed"
    echo "Run: uv sync --group dev"
    exit 1
fi

echo "✅ Semantic-release is installed"

# Test configuration
echo "🔧 Testing semantic-release configuration..."
if uv run semantic-release print-config > /dev/null 2>&1; then
    echo "✅ Configuration is valid"
else
    echo "❌ Configuration error"
    uv run semantic-release print-config
    exit 1
fi

# Test dry-run version bump
echo "🔍 Testing version bump (dry-run)..."
if uv run semantic-release version --dry-run > /dev/null 2>&1; then
    echo "✅ Version bump test passed"
else
    echo "❌ Version bump test failed"
    uv run semantic-release version --dry-run
    exit 1
fi

# Test dry-run changelog
echo "📝 Testing changelog generation (dry-run)..."
if uv run semantic-release changelog --dry-run > /dev/null 2>&1; then
    echo "✅ Changelog generation test passed"
else
    echo "❌ Changelog generation test failed"
    uv run semantic-release changelog --dry-run
    exit 1
fi

# Test dry-run publish
echo "🚀 Testing release creation (dry-run)..."
if uv run semantic-release publish --dry-run > /dev/null 2>&1; then
    echo "✅ Release creation test passed"
else
    echo "❌ Release creation test failed"
    uv run semantic-release publish --dry-run
    exit 1
fi

echo ""
echo "🎉 All tests passed! Your Gitea release configuration is working correctly."
echo ""
echo "📋 What will happen when you make a release:"
echo "  • Version will be bumped based on commit messages"
echo "  • Changelog will be generated from conventional commits"
echo "  • Git tag will be created (e.g., v1.2.3)"
echo "  • Release will be created on Gitea release page"
echo "  • Release assets will be uploaded (wheel, source dist, etc.)"
echo ""
echo "🔧 To make a real release:"
echo "  make release"
echo ""
echo "📚 For more information, see docs/GITEA_SETUP.md"
