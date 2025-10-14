# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Stream mode validation improvements
- Enhanced metadata parsing
- Performance optimizations
- Additional PDAL filter/writer support

---

## [0.1.0a1] - 2025-10-14

**First alpha release** - Type-safe Python API for PDAL CLI

### Added

**Core Functionality**:
- Complete Python API for PDAL CLI execution via subprocess
- Type-safe stage creation (38 readers, 90+ filters, 22 writers)
- Pythonic pipeline assembly with pipe operator (`|`)
- High-level applications: info, translate, merge, split, tile, tindex
- Comprehensive exception hierarchy (9 exception types)
- PDAL CLI auto-discovery (PATH, QGIS bundle, conda, custom paths)

**Type Safety**:
- Full type hints on all public APIs
- mypy strict mode compliance
- py.typed marker for type checker support

**Testing**:
- Comprehensive pytest test suite
- 80%+ test coverage
- Integration tests with real PDAL CLI
- Unit tests with mocked subprocess

**Documentation**:
- Complete README with quick start and examples
- Detailed developer guide (docs/exeqpdal_dev.md)
- Gold standard implementation patterns (docs/examples/)
- Contributing guide with workflow and standards
- Troubleshooting guide for installation and runtime issues

**Quality Assurance**:
- ruff linting and formatting
- mypy strict type checking
- pytest with coverage reporting
- Constitution-driven development

### Security
- subprocess execution with shell=False
- Temporary file cleanup on errors (finally blocks)
- PDAL CLI version validation

---

[Unreleased]: https://github.com/elgorrion/exeqpdal/compare/v0.1.0a1...HEAD
[0.1.0a1]: https://github.com/elgorrion/exeqpdal/releases/tag/v0.1.0a1
