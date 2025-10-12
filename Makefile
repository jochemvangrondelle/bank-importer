.PHONY: help install test lint clean version docker-build docker-push release semantic-release

# Default target
help: ## Show this help message
	@echo "Bank Importer - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development
install: ## Install development dependencies
	uv sync --group dev --python 3.11

test: ## Run tests
	uv run --python 3.11 pytest tests/ -v

lint: ## Run linting
	uv run --python 3.11 ruff check src/ tests/
	uv run --python 3.11 mypy src/

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/

# Version management
version: ## Show current version
	@uv run --python 3.11 python -c "from src.bank_importer_th import __version__; print(__version__)"

# Docker
docker-build: ## Build Docker image (Python 3.13) for local platform
	./scripts/docker-build.sh --local

docker-build-multi: ## Build Docker image for multiple platforms (amd64, arm64)
	./scripts/docker-build.sh --multi-platform

docker-build-push: ## Build and push Docker image to Harbor registry
	./scripts/docker-build.sh --multi-platform --push

docker-build-arm64: ## Build Docker image for ARM64 platform
	./scripts/docker-build.sh --platform linux/arm64

docker-build-amd64: ## Build Docker image for AMD64 platform
	./scripts/docker-build.sh --platform linux/amd64

docker-push: ## Push Docker image to registry (deprecated, use docker-build-push)
	@echo "Use 'make docker-build-push' instead"

# Semantic Release
semantic-release: ## Run semantic release (version, changelog, publish)
	uv run --python 3.11 semantic-release version
	uv run --python 3.11 semantic-release changelog
	uv run --python 3.11 semantic-release publish

# Release
release: ## Create a new release using semantic-release
	@echo "Creating release using semantic-release..."
	$(MAKE) semantic-release
	@echo "Release created successfully!"

# CI/CD helpers
ci-test: ## Run tests for CI
	uv run --python 3.11 pytest tests/ --cov=src/ --cov-report=xml

ci-lint: ## Run linting for CI
	uv run --python 3.11 ruff check src/ tests/
	uv run --python 3.11 mypy src/

ci-build: ## Build for CI
	uv run --python 3.11 python -m build

# Development workflow
dev-setup: ## Setup development environment
	uv sync --group dev --python 3.11
	uv run --python 3.11 pre-commit install

dev-check: ## Run all development checks
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) version

# Commit helpers
commit: ## Interactive commit using commitizen
	uv run --python 3.11 cz commit

# Pre-commit
pre-commit: ## Run pre-commit on all files
	uv run --python 3.11 pre-commit run --all-files

# Test Gitea release configuration
test-gitea-release: ## Test Gitea release configuration
	./scripts/test-gitea-release.sh
