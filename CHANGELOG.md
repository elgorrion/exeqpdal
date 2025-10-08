# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

**Status**: Development (v0.1.0-dev) - Not yet released

### Implemented
- Core Pipeline class with JSON pipeline support
- Stage chaining with pipe operator (Reader | Filter | Writer)
- 38 reader stages (las, copc, e57, ept, text, etc.)
- 90+ filter stages (smrf, pmf, outlier, range, etc.)
- 22 writer stages (las, copc, gdal, ply, text, etc.)
- High-level applications (info, translate, merge, split, tile)
- PDAL binary discovery (PATH, QGIS, custom paths)
- Complete type hints (mypy strict mode)
- Exception hierarchy (PDALError subtypes)

### In Progress
- Test suite completion
- Documentation improvements
- CI/CD setup
- PyPI release preparation

### Planned
- Stream mode validation
- Enhanced metadata parsing
- QGIS plugin integration examples
- Performance optimizations

## Release History

No releases yet. Project is in active development.

---

[Unreleased]: https://github.com/elgorrion/exeqpdal/compare/HEAD
