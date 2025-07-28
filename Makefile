.PHONY: help install test lint clean version bump-patch bump-minor bump-major docker-build docker-push

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

bump-patch: ## Bump patch version (0.1.0 -> 0.1.1)
	bump2version patch

bump-minor: ## Bump minor version (0.1.0 -> 0.2.0)
	bump2version minor

bump-major: ## Bump major version (0.1.0 -> 1.0.0)
	bump2version major

# Docker
docker-build: ## Build Docker image
	docker build -t bank-importer-th:$(shell cat VERSION) .
	docker tag bank-importer-th:$(shell cat VERSION) bank-importer-th:latest

docker-push: ## Push Docker image to registry
	docker push bank-importer-th:$(shell cat VERSION)
	docker push bank-importer-th:latest

# Release
release: ## Create a new release (bump patch, build, push)
	@echo "Creating release for version $(shell cat VERSION)..."
	$(MAKE) bump-patch
	$(MAKE) docker-build
	$(MAKE) docker-push
	@echo "Release $(shell cat VERSION) created successfully!"

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
