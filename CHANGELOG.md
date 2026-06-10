# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed
- **Breaking:** `Pipeline.arrays` and the numpy dependency. exeqpdal drives the PDAL
  CLI and never materializes point data in memory; use the official
  [PDAL Python bindings](https://github.com/PDAL/python) for numpy array access.
  The package now has no runtime dependencies.

### Changed
- Pipeline JSON is passed to `pdal pipeline --stdin` via standard input instead of a
  temporary file; all subprocess I/O is UTF-8 with replacement decoding, so non-UTF-8
  bytes in PDAL output can no longer crash a run.
- Python floor lowered from 3.12 to 3.10.
- `Pipeline.validate()` and `Pipeline.is_streamable` now report PDAL's actual verdict:
  the `--validate` JSON output is parsed instead of relying on the exit code (always 0)
  and a substring match (always true). Invalid pipelines now raise `ValidationError`
  with PDAL's error detail.
- `get_count()` reads `num_points` from `pdal info --summary` and raises
  `MetadataError` when absent (it previously always returned 0).
- `get_bounds()` reads the bounding box from `pdal info --summary` (the previous
  `--boundary` source never contained min/max keys).
- `Executor.get_driver_info()` uses `pdal --options <driver> --showjson` and returns
  a parsed `{driver, options}` structure (the previous invocation could never succeed).
- `set_verbose()` now affects already-created executors, including the module-level one.

### Added
- `set_timeout()`: configurable timeout for every PDAL subprocess call (including the
  version probe); expiry raises `PDALExecutionError` carrying any partial output.
- One-time warning when the detected PDAL version is below the supported floor (2.8).
- PDAL version string is cached; `set_pdal_path()` resets the cache.

### Fixed
- `Pipeline.execute()`/`validate()` again raise only their documented exception types
  (`PipelineError`/`ValidationError`) when PDAL is missing or broken.
- A failed PDAL launch (missing, non-executable, or wrong-architecture binary) raises
  `PDALNotFoundError` instead of a raw `OSError`.

## [0.1.0a5] - 2025-11-17

### Fixed
- Correct version references across all files (__init__.py now matches package version)

## [0.1.0a4] - 2025-11-17

### Changed
- Simplified pipeline JSON generation to omit auto-generated tags and single inputs
- Leverages PDAL's implicit sequential chaining for cleaner pipeline JSON output
- Only includes explicit inputs for multi-input stages (merge operations)

## [0.1.0a3] - 2025-10-21

### Fixed
- Hide subprocess console windows on Windows for better user experience
- Version-independent QGIS/PDAL discovery on Windows using dynamic glob patterns

## [0.1.0a2] - 2025-10-20

### Fixed
- Pipeline constructor now properly handles list of Stage objects by calling `.to_dict()` before JSON serialization
- Pipeline constructor accepts mixed lists of Stage objects and dicts

## [0.1.0a1] - 2025-10-16

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

### Tooling
- Added GitHub Actions for CI (`ci.yml`) and publishing (`publish.yml`), plus a release guide
  (`docs/publishing.md`) and supporting development dependencies.

### Known Limitations
- `Pipeline.arrays` is not yet implemented and currently returns an empty list.
- Stage factories do not yet expose every PDAL driver; unsupported stages can be invoked with custom
  JSON.
- First PyPI upload is still pending while the initial alpha stabilises.

---
