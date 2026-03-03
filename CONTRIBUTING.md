# Contributing to Officeboy

Thank you for your interest in contributing to Officeboy. This document provides comprehensive guidelines for understanding the framework, reporting issues, and submitting pull requests.

## Development Environment Setup

To begin contributing to Officeboy, you will need a Windows environment with MS Access installed, along with Python 3.10 or newer. We use [UV](https://github.com/astral-sh/uv), an ultra-fast Python package manager, for dependency management and build orchestration.

### Quick Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/officeboy.git
cd officeboy

# Run automated setup
./scripts/uv_setup.sh

# Or manually:
uv python install 3.11
uv venv --python 3.11
uv sync --all-extras
```

## Understanding the Architecture

Officeboy is structured as a modular CLI application designed to interface with MS Access through COM automation. The core architecture consists of several key components that work together to provide version control capabilities.

The CLI layer uses Click to define commands and handle argument parsing. The core module contains the business logic for exporting and importing Access objects, managing content hashes, and maintaining the export index. The access module provides the COM interface to MS Access through pywin32, abstracting the details of Access automation.

The generators module handles the creation of test artifacts, producing both unit test add-ins for VBA code and functional test specifications for Robot Framework. Internationalization support is implemented throughout the application using gettext, allowing for future translation of user-facing messages.

## Code Style and Quality

We maintain strict code quality standards. All Python code must follow PEP 8 conventions, which are enforced automatically by ruff. Type hints are required for all function signatures, verified by mypy in strict mode. Documentation strings should follow the Google style guide.

When writing code, prefer explicit over implicit constructs. Use pathlib for filesystem operations rather than os.path. Handle exceptions at appropriate levels and log meaningful error messages using the logging module. All user-facing strings must be wrapped with the internationalization function.

### Running Quality Checks

```bash
uv run ruff check src tests
uv run ruff format src tests
uv run mypy src/officeboy
uv run bandit -r src/officeboy
```

## Testing Requirements

Every contribution must include comprehensive tests. We require 100% code coverage for all new code. Unit tests should be placed in the tests directory and use pytest fixtures for setup and teardown. Functional tests use Robot Framework with the FlaUI library for GUI automation.

When writing tests, mock external dependencies such as the MS Access COM interface. Use pytest-mock for creating mocks and patches. Ensure tests are deterministic and do not depend on external state. Integration tests that require actual MS Access should be marked with the integration marker and skipped by default.

### Running Tests

```bash
uv run pytest --cov=officeboy --cov-report=html
```

## Submitting Changes

Before submitting a pull request, run the full quality suite locally to ensure all checks pass. This includes linting, type checking, security analysis, unit tests across Python versions, and coverage verification.

```bash
# Run all checks
uv run ruff check src tests
uv run mypy src/officeboy
uv run bandit -r src/officeboy
uv run pytest --cov=officeboy
uv build
```

Commit messages should follow conventional commit format, describing the type of change and the affected component. For example, use feat: for new features, fix: for bug fixes, docs: for documentation changes, and test: for test modifications.

When you are ready to submit, push your branch to your fork and create a pull request against the main repository. The pull request description should explain the motivation for the change, describe what was modified, and reference any related issues. Ensure the CI pipeline passes all checks before requesting review.

## Repository Initialization

When creating a new repository based on Officeboy structure, use the provided initialization script:

```bash
./scripts/init_repo.sh --git-user yourusername --repo-name yourproject \
    --dev-name "Your Name" --dev-email "your@email.com" --pack-version 0.1.0
```

This script will:
- Initialize git repository
- Create initial commit with proper structure
- Create signed version tag
- Generate release notes template

## Reporting Issues

When reporting bugs, include:
- Version of Officeboy (`officeboy --version`)
- Python version (`uv run python --version`)
- MS Access version and Windows version
- Minimal reproducible example

For feature requests, describe the use case and proposed implementation approach.

Security vulnerabilities should be reported privately to the maintainer email rather than through public issues. We are committed to addressing security concerns promptly and responsibly.

## Release Process

Releases are managed by the project maintainers. The version number follows semantic versioning principles. When a release is prepared:

1. Update CHANGELOG.md moving items from Unreleased to the new version section
2. Run `./scripts/init_repo.sh` with new `--pack-version`
3. Push tag to GitHub: `git push origin vX.Y.Z`
4. CI will automatically build and attach artifacts to release

## Community

We strive to maintain a welcoming and inclusive community. All contributors are expected to adhere to professional standards of conduct. Questions and discussions are welcome through GitHub issues and discussions.

Your contributions help make MS Access development more robust and maintainable. We appreciate your time and effort in improving Officeboy.

## Author

**Yorga Babuscan** - yorgabr@gmail.com
