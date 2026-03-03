# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure with pyproject.toml, setup.cfg, and tox.ini
- CLI interface with Click framework supporting disassembly, assembly, make-unit-tests, and make-functional-tests commands
- MS Access automation interface using pywin32
- SHA-256 based content hashing for incremental exports
- Index management system for tracking exported objects
- Unit test generator for VBA code modules
- Functional test generator using Robot Framework and FlaUI
- Internationalization support (i18n) with gettext
- Comprehensive test suite with 100% coverage requirement
- Tox configuration with chained environments for unit testing, build, functional testing, and deployment
- Support for multiple package formats: pip, PortableApps, DEB, RPM, and MSIX
- Code quality tools: ruff, mypy, bandit, pytest
- GitHub Actions CI/CD workflow
- Complete documentation: README, CONTRIBUTING, LICENSE, and CHANGELOG

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.1.0] - 2024-XX-XX

### Added
- First stable release of Officeboy
- Core functionality for MS Access version control
- CLI with four main commands: disassembly, assembly, make-unit-tests, make-functional-tests
- Windows compatibility with MS Access integration
- GPL-3.0-or-later licensing
