.PHONY: help install test lint clean version docker-build docker-push release semantic-release test-tox test-tox-sequential test-tox-py311 test-tox-py312 test-tox-py313 test-tox-py314 clean-tox ci-test ci-lint ci-build dev-setup dev-check pre-commit pre-commit-all commit docs-build docs-serve docs-linkcheck docs test-github-release docker-build-multi docker-build-push docker-build-arm64 docker-build-amd64

# Default target
help: ## Show this help message
	@echo "Bank Importer - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development
install: ## Install development dependencies
	uv sync --group dev

test: ## Run all tests
	uv run pytest tests/

test-unit: ## Run unit tests only (excludes integration tests)
	uv run pytest tests/ -m 'not integration'

test-integration: ## Run integration tests only
	uv run pytest tests/integration/ -v -m integration

test-tox: ## Run tests with tox in parallel (all Python versions)
	tox --parallel auto

test-tox-sequential: ## Run tests with tox sequentially (all Python versions) - DEPRECATED
	tox

test-tox-py311: ## Run tests with tox (Python 3.11 only)
	tox -e py311

test-tox-py312: ## Run tests with tox (Python 3.12 only)
	tox -e py312

test-tox-py313: ## Run tests with tox (Python 3.13 only)
	tox -e py313

test-tox-py314: ## Run tests with tox (Python 3.14 only)
	tox -e py314

lint: ## Run linting and type checking
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/
	uv run mypy src/ --strict
	uv run pyright src/

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/

clean-tox: ## Clean tox environments
	tox --clean

# Version management
version: ## Show current version
	@uv run python -c "import importlib.metadata; print(importlib.metadata.version('bank-importer'))"

# Version bumping is handled by semantic-release based on conventional commits
# See docs/RELEASE_PROCESS.md for details

# Docker
docker-build: ## Build Docker image (Python 3.13) for local platform
	./scripts/docker-build.sh --local

docker-build-multi: ## Build Docker image for multiple platforms (amd64, arm64)
	./scripts/docker-build.sh --multi-platform

docker-build-push: ## Build and push Docker image to Docker Hub
	./scripts/docker-build.sh --multi-platform --push

docker-build-arm64: ## Build Docker image for ARM64 platform
	./scripts/docker-build.sh --platform linux/arm64

docker-build-amd64: ## Build Docker image for AMD64 platform
	./scripts/docker-build.sh --platform linux/amd64

docker-push: ## Push Docker image to registry (deprecated - use docker-build-push)
	docker push bank-importer:$(shell cat VERSION 2>/dev/null || echo "latest")
	docker push bank-importer:latest

# Release (uses semantic-release)
release: ## Create a new release using semantic-release
	@echo "Creating release using semantic-release..."
	uv run semantic-release version
	uv run semantic-release changelog
	uv run semantic-release publish
	@echo "Release created successfully!"

semantic-release: ## Run semantic release (version, changelog, publish)
	uv run semantic-release version
	uv run semantic-release changelog
	uv run semantic-release publish

# CI/CD helpers
ci-test: ## Run tests for CI
	uv run pytest tests/ --cov=src/bank_importer --cov-report=xml

ci-lint: ## Run linting for CI
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/
	uv run mypy src/ --strict
	uv run pyright src/

ci-build: ## Build for CI
	uv build

# Development workflow
dev-setup: ## Setup development environment and pre-commit hooks
	uv sync --group dev
	uv run pre-commit install
	uv run pre-commit install --hook-type commit-msg

dev-check: ## Run all development checks (matches CI)
	uv run pre-commit run --all-files

pre-commit: ## Run pre-commit hooks on staged files
	uv run pre-commit run

pre-commit-all: ## Run pre-commit hooks on all files
	uv run pre-commit run --all-files

# Commit helpers
commit: ## Interactive commit using commitizen
	uv run cz commit

# Documentation
docs-build: ## Build documentation
	uv sync --group docs
	uv run mkdocs build

docs-serve: ## Serve documentation locally
	uv sync --group docs
	uv run mkdocs serve

docs-linkcheck: ## Check documentation links
	uv sync --group docs
	uv run mkdocs build --strict
	uv run mkdocs-linkcheck

docs: docs-build ## Alias for docs-build

# Test GitHub release configuration
test-github-release: ## Test GitHub release configuration
	./scripts/test-github-release.sh
