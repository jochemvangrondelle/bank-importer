#!/bin/bash

# Release script for Bank Importer
# Usage: ./scripts/release.sh [patch|minor|major]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "pyproject.toml file not found. Are you in the project root?"
    exit 1
fi

# Get current version
CURRENT_VERSION=$(uv run --python 3.11 python -c "from src.bank_importer_th import __version__; print(__version__)")
print_status "Current version: $CURRENT_VERSION"

# Determine version bump type
BUMP_TYPE=${1:-patch}
if [[ ! "$BUMP_TYPE" =~ ^(patch|minor|major)$ ]]; then
    print_error "Invalid bump type: $BUMP_TYPE. Use patch, minor, or major."
    exit 1
fi

print_status "Bumping $BUMP_TYPE version..."

# Check if git is clean
if [ -n "$(git status --porcelain)" ]; then
    print_warning "Git working directory is not clean. Committing changes first..."
    git add .
    git commit -m "Prepare for release"
fi

# Bump version
uv run --python 3.11 bump2version --allow-dirty $BUMP_TYPE

# Get new version
NEW_VERSION=$(uv run --python 3.11 python -c "from src.bank_importer_th import __version__; print(__version__)")
print_success "Version bumped to: $NEW_VERSION"

# Run tests
print_status "Running tests..."
uv run --python 3.11 pytest tests/ -v -n auto

# Run linting
print_status "Running linting..."
uv run --python 3.11 ruff check src/ tests/
uv run --python 3.11 mypy src/

# Build package
print_status "Building package..."
uv run --python 3.11 python -m build

# Build Docker image
print_status "Building Docker image..."
docker build -t bank-importer-th:$NEW_VERSION .
docker tag bank-importer-th:$NEW_VERSION bank-importer-th:latest

print_success "Release preparation complete!"
print_status "Next steps:"
echo "  1. Review changes: git log --oneline -5"
echo "  2. Push changes: git push origin main"
echo "  3. Push tag: git push origin v$NEW_VERSION"
echo "  4. Create GitHub release for v$NEW_VERSION"
echo "  5. Push Docker image: docker push bank-importer-th:$NEW_VERSION"
