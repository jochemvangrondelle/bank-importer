.PHONY: help install test lint clean version docker-build docker-push release semantic-release

# Default target
help: ## Show this help message
	@echo "Bank Importer - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development
install: ## Install development dependencies
	uv sync --group dev

test: ## Run tests
	uv run pytest tests/ -v

lint: ## Run linting
	uv run ruff check src/ tests/
	uv run mypy src/

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/

# Version management
version: ## Show current version
	@uv run python -c "from src.bank_importer_th import __version__; print(__version__)"

# Docker
docker-build: ## Build Docker image
	docker build --target production -t bank-importer-th:$(shell uv run python -c "from src.bank_importer_th import __version__; print(__version__)") .
	docker tag bank-importer-th:$(shell uv run python -c "from src.bank_importer_th import __version__; print(__version__)") bank-importer-th:latest

docker-push: ## Push Docker image to registry
	docker push bank-importer-th:$(shell uv run python -c "from src.bank_importer_th import __version__; print(__version__)")
	docker push bank-importer-th:latest

# Semantic Release
semantic-release: ## Run semantic release (version, changelog, publish)
	uv run semantic-release version
	uv run semantic-release changelog
	uv run semantic-release publish

# Release
release: ## Create a new release using semantic-release
	@echo "Creating release using semantic-release..."
	$(MAKE) semantic-release
	@echo "Release created successfully!"

# CI/CD helpers
ci-test: ## Run tests for CI
	uv run pytest tests/ --cov=src/ --cov-report=xml

ci-lint: ## Run linting for CI
	uv run ruff check src/ tests/
	uv run mypy src/

ci-build: ## Build for CI
	uv run python -m build

# Development workflow
dev-setup: ## Setup development environment
	uv sync --group dev
	uv run pre-commit install

dev-check: ## Run all development checks
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) version

# Commit helpers
commit: ## Interactive commit using commitizen
	uv run cz commit

# Pre-commit
pre-commit: ## Run pre-commit on all files
	uv run pre-commit run --all-files

# Test Gitea release configuration
test-gitea-release: ## Test Gitea release configuration
	./scripts/test-gitea-release.sh
