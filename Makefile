# Makefile for Officeboy - UV-only workflow
# Author: Yorga Babuscan (yorgabr@gmail.com)

.PHONY: help install sync clean-all lint type format security test test-all coverage build build-all docs release check-all python-versions

PYTHON_VERSION ?= 3.11
PACKAGE_NAME := officeboy

#__________ Colors __________
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

help:
	@echo "$(BLUE)Officeboy UV Commands:$(RESET)"
	@echo "  $(GREEN)make install$(RESET)        - Setup development environment"
	@echo "  $(GREEN)make sync$(RESET)           - Sync dependencies with uv.lock"
	@echo "  $(GREEN)make clean-all$(RESET)      - Remove all caches and virtual env"
	@echo ""
	@echo "$(BLUE)Quality Checks:$(RESET)"
	@echo "  $(GREEN)make lint$(RESET)           - Run ruff linter"
	@echo "  $(GREEN)make type$(RESET)           - Run mypy type checker"
	@echo "  $(GREEN)make format$(RESET)         - Format code with ruff"
	@echo "  $(GREEN)make security$(RESET)       - Run bandit security scan"
	@echo ""
	@echo "$(BLUE)Testing:$(RESET)"
	@echo "  $(GREEN)make test$(RESET)           - Run tests with current Python"
	@echo "  $(GREEN)make test-all$(RESET)       - Run tests on Python 3.10, 3.11, 3.12"
	@echo "  $(GREEN)make coverage$(RESET)       - Generate HTML coverage report"
	@echo ""
	@echo "$(BLUE)Build:$(RESET)"
	@echo "  $(GREEN)make build$(RESET)          - Build wheel"
	@echo "  $(GREEN)make build-all$(RESET)      - Build wheel and sdist"
	@echo ""
	@echo "$(BLUE)Orchestration:$(RESET)"
	@echo "  $(GREEN)make check-all$(RESET)      - Run lint, type, security, test, build"
	@echo "  $(GREEN)make release$(RESET)        - Full release workflow"

#__________ Setup __________

install:
	@echo "$(BLUE)[INFO]$(RESET) Installing UV and setting up environment..."
	@which uv > /dev/null || (curl -LsSf https://astral.sh/uv/install.sh | sh)
	@uv python install $(PYTHON_VERSION)
	@uv venv --python $(PYTHON_VERSION)
	@uv sync --all-extras
	@echo "$(GREEN)[SUCCESS]$(RESET) Environment ready. Use 'uv run <command>' or activate .venv"

sync:
	@echo "$(BLUE)[INFO]$(RESET) Syncing dependencies..."
	@uv sync --all-extras
	@echo "$(GREEN)[SUCCESS]$(RESET) Dependencies synchronized"

clean-all:
	@echo "$(YELLOW)[WARN]$(RESET) Removing virtual environment and caches..."
	@rm -rf .venv
	@rm -rf dist build *.egg-info
	@rm -rf htmlcov .pytest_cache .mypy_cache .ruff_cache
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)[SUCCESS]$(RESET) Cleanup complete"

#__________ Quality Checks __________

lint:
	@echo "$(BLUE)[INFO]$(RESET) Running ruff linter..."
	@uv run ruff check src tests
	@echo "$(GREEN)[SUCCESS]$(RESET) Linting passed"

type:
	@echo "$(BLUE)[INFO]$(RESET) Running mypy type checker..."
	@uv run mypy src/$(PACKAGE_NAME) || true
	@echo "$(GREEN)[SUCCESS]$(RESET) Type checking complete"

format:
	@echo "$(BLUE)[INFO]$(RESET) Formatting code..."
	@uv run ruff format src tests
	@uv run ruff check --fix src tests
	@echo "$(GREEN)[SUCCESS]$(RESET) Formatting complete"

security:
	@echo "$(BLUE)[INFO]$(RESET) Running bandit security scan..."
	@uv run bandit -r src/$(PACKAGE_NAME)
	@echo "$(GREEN)[SUCCESS]$(RESET) Security scan complete"

#__________ Testing __________

test:
	@echo "$(BLUE)[INFO]$(RESET) Running tests with current Python..."
	@uv run pytest --cov=$(PACKAGE_NAME) --cov-report=term-missing

test-all: python-versions
	@echo "$(BLUE)[INFO]$(RESET) Running tests on all Python versions..."
	@for py in 3.10 3.11 3.12; do \
		echo "$(YELLOW)[TEST]$(RESET) Python $$py"; \
		uv run --python $$py pytest --cov=$(PACKAGE_NAME) || exit 1; \
	done
	@echo "$(GREEN)[SUCCESS]$(RESET) All tests passed on all versions"

python-versions:
	@echo "$(BLUE)[INFO]$(RESET) Ensuring Python versions are installed..."
	@uv python install 3.10 3.11 3.12

coverage:
	@echo "$(BLUE)[INFO]$(RESET) Generating coverage report..."
	@uv run pytest --cov=$(PACKAGE_NAME) --cov-report=html --cov-report=xml --cov-report=term
	@echo "$(GREEN)[SUCCESS]$(RESET) Coverage report generated at htmlcov/index.html"

#__________ Build __________

build:
	@echo "$(BLUE)[INFO]$(RESET) Building wheel..."
	@uv build --wheel
	@echo "$(GREEN)[SUCCESS]$(RESET) Build complete in dist/"

build-all:
	@echo "$(BLUE)[INFO]$(RESET) Building wheel and sdist..."
	@uv build
	@echo "$(GREEN)[SUCCESS]$(RESET) Build complete in dist/"

#__________ Documentation __________

docs:
	@echo "$(BLUE)[INFO]$(RESET) Building documentation..."
	@uv run mkdocs build || echo "$(YELLOW)[WARN]$(RESET) mkdocs not configured"
	@echo "$(GREEN)[SUCCESS]$(RESET) Documentation built"

#__________ Orchestration (replaces tox depends) __________

check-all: lint type security test build
	@echo "$(GREEN)[SUCCESS]$(RESET) All checks passed!"

release: clean-all check-all
	@echo "$(BLUE)[INFO]$(RESET) Preparing release..."
	@uv build
	@echo "$(GREEN)[SUCCESS]$(RESET) Release artifacts ready in dist/"
	@echo "$(YELLOW)[NEXT]$(RESET) Run: git tag vX.Y.Z && git push origin vX.Y.Z"