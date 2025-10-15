# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

`exeqpdal 0.1.0a1` is under active development and has not yet been published to PyPI.

### Added
- Pipeline orchestration with the `Pipeline` class, including `validate`, metadata access, and point
  count parsing.
- Stage factories covering the most frequently used PDAL drivers (~40 readers, 80+ filters, 25
  writers).
- High-level wrappers for PDAL CLI applications: `info`, `translate`/`convert`, `merge`, `split`,
  `tile`, and `tindex`.
- PDAL discovery and configuration utilities (`set_pdal_path`, `get_pdal_version`, `validate_pdal`,
  `set_verbose`).
- Custom exception hierarchy (`PDALError`, `PipelineError`, `PDALExecutionError`, etc.).
- Packaging metadata with `py.typed` for downstream type checkers.

### Testing
- Pytest suite covering pipeline assembly, stage factories, and application wrappers.
- Integration tests gated by `@pytest.mark.integration` and the `EXEQPDAL_TEST_DATA` fixture
  directory.
- Strict typing enforced via `mypy --strict`.

### Known Limitations
- `Pipeline.arrays` is not yet implemented and currently returns an empty list.
- Stage factories do not yet expose every PDAL driver; unsupported stages can be invoked with custom
  JSON.
- Publishing workflow is not finalised; installation is currently from source.

---
