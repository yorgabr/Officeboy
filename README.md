# Officeboy

![Officeboy Mascot](docs/images/the_officeboy.png)

![License](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)

Officeboy is a comprehensive command-line utility for MS Access database version control and automation. Inspired by the amazing [msaccess-vcs-addin](https://github.com/joyfullservice/msaccess-vcs-addin) project, Officeboy brings Git-friendly source control to MS Access applications with advanced testing capabilities.

## Features

**Version Control Integration**
- Export MS Access objects (forms, reports, modules, queries, macros, tables) to text-based source files
- Import source files back into Access databases
- SHA-256 hashing for efficient change detection
- Incremental exports that skip unchanged objects

**Testing Automation**
- Generate unit test add-ins for VBA code modules with 100% coverage
- Create Robot Framework functional tests for Access forms
- Automatic detection of form controls, buttons, and event handlers

**Build System**
- UV-based build pipeline (ultra-fast Python package manager)
- Automated packaging for multiple distribution formats
- Continuous integration ready with GitHub Actions

## Installation

### Using UV (Recommended)

[UV](https://github.com/astral-sh/uv) is an ultra-fast Python package manager written in Rust.

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Officeboy
uv tool install officeboy
```

### From Source (Development)

```bash
git clone https://github.com/yorgabr/officeboy.git
cd officeboy

# Setup with provided script
./scripts/uv_setup.sh

# Or manually with UV
uv python install 3.11
uv venv --python 3.11
uv sync --all-extras
```

## Quick Start

Export an Access database to source files:

```bash
officeboy disassembly MyDatabase.accdb ./src
```

Rebuild database from source:

```bash
officeboy assembly ./src MyDatabase.accdb
```

Generate unit tests:

```bash
officeboy make-unit-tests MyDatabase.accdb --output ./tests/unit
```

Generate functional tests:

```bash
officeboy make-functional-tests MyDatabase.accdb --output ./tests/robot
```

## Development Commands

```bash
# Run tests
uv run pytest

# Run linting
uv run ruff check src tests

# Run type checking
uv run mypy src/officeboy

# Build package
uv build

# Run CLI in development
uv run officeboy --help
```

## Documentation

- [Contributing Guidelines](./CONTRIBUTING.md)
- [Changelog](./CHANGELOG.md)
- [License](./LICENSE.md)

## Requirements

- Windows with MS Access 2010 or later
- Python 3.10+
- Microsoft Access Object Library
- [UV](https://github.com/astral-sh/uv)

## Repository Initialization (GitHub)

To initialize a new GitHub repository with proper structure:

```bash
./scripts/init_repo.sh --github-user yourusername --github-repo officeboy \
    --dev-name "Your Name" --dev-email "your@email.com" --pack-version 0.1.0
```

### Autocomplete Support

Enable bash autocomplete for `init_repo.sh`:

```bash
# Temporary (current session)
./scripts/init_repo.sh --generate-completion TEMP

# Permanent (user)
./scripts/init_repo.sh --generate-completion USER

# System-wide (requires sudo)
sudo ./scripts/init_repo.sh --generate-completion SYSTEM
```

## License

This project is licensed under the GNU General Public License v3.0 or later - see the [LICENSE.md](LICENSE.md) file for details.

## Acknowledgments

This project was inspired by the [msaccess-vcs-addin](https://github.com/joyfullservice/msaccess-vcs-addin) project by joyfullservice. We extend our gratitude to the contributors of that project for demonstrating effective techniques for MS Access version control.

## Author

**Yorga Babuscan** - yorgabr@gmail.com
