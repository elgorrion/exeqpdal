# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- `PipelineError` raised for an execution failure carries `returncode`,
  `stdout`, `stderr`, `command`, and, for `Pipeline.execute()`, the
  `pipeline_json` that PDAL ran; `str()` prints them after the message in
  that order. Since 0.1.0a7 the message alone reached the caller, so a field
  crash reported nothing beyond one stderr line. A Windows NTSTATUS return
  code (negative or above `0x7FFFFFFF`) is named in the return code line, for
  example `pdal.exe crashed: fast-fail / stack buffer overrun (0xC0000409)`;
  access violation, stack overflow, and DLL not found are named as well.
  Nothing is truncated; the consumer's log holds the report.

## [0.1.0a8] - 2026-09-09

### Fixed
- `exeqpdal.__version__` reads the installed distribution metadata instead of a
  second, hand-maintained copy of the version. `pyproject.toml` is now the only
  place the version is written, so a released wheel can no longer report the
  previous release at runtime. A source tree with no installed distribution
  reports `0.0.0.dev0`.

## [0.1.0a7] - 2026-09-09

### Added
- `merge(header_from=...)` copies LAS/LAZ scales and offsets without runtime
  dependencies. Explicit stage options override these values. Other output formats
  ignore `header_from`. An invalid LAS signature and invalid header lengths, scales,
  and offsets raise `MetadataError`.

### Changed
- Public applications and `Pipeline.execute()` raise `PipelineError` for PDAL
  execution failures. Messages prefer the last PDAL diagnostic and preserve its first
  200 characters. Messages use the last non-empty line when no PDAL diagnostic exists.
  The original `PDALExecutionError` remains available through `__cause__`.
- `info()` surfaces unparseable PDAL output as `PipelineError` instead of
  `PDALExecutionError`, like every other application helper.
- `Pipeline.execute()`, `Pipeline.validate()`, and `Pipeline.is_streamable` let
  `PDALNotFoundError` propagate unchanged, as applications do. `validate()` still
  reports execution and parse failures as `ValidationError`.

## [0.1.0a6] - 2026-07-27

### Removed
- **Breaking:** `Pipeline.arrays` and the numpy dependency. exeqpdal drives the PDAL
  CLI and never materializes point data in memory; use the official
  [PDAL Python bindings](https://github.com/PDAL/python) for numpy array access.
  The package now has no runtime dependencies.

### Changed
- Static type checking and CI now use Astral `ty`.
- Application stage options can use exact dotted PDAL names through the shared
  `stage_options` mapping. Existing single-word underscore keywords remain supported;
  ambiguous names now fail clearly.
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
- `Pipeline.execute()` documents its return value as the number of points read:
  PDAL's pipeline metadata reports counts only for reader stages, so downstream
  filters and writers do not change it. Use `get_count()` on the output file for
  the written count.

### Added
- `set_timeout()`: configurable timeout for every PDAL subprocess call (including the
  version probe); expiry raises `PDALExecutionError` carrying any partial output.
- One-time warning when the detected PDAL version is below the supported floor (2.8).
- PDAL version string is cached; `set_pdal_path()` resets the cache.
- Stage factories for the remaining PDAL 2.10 stages: `Reader.spz`, `Writer.spz`,
  `Filter.m3c2`, `Filter.supervoxel`, `Filter.shell` — every stage documented for
  PDAL 2.10.1 now has a factory.
- `sort()`: wrapper for the `pdal sort` application (Morton-order spatial sort).
- `scripts/check_stage_drift.py` plus a pinned stage list: verifies factory coverage
  against a real `pdal --drivers` and the documented PDAL 2.10.1 stage set.

### Fixed
- `merge()` now applies automatic X/Y/Z offsets to ordinary LAS/LAZ outputs, preventing
  `int32` overflow for large projected coordinates while allowing explicit overrides.
- `translate()` no longer replaces underscores inside PDAL option names such as
  `offset_x`, `minor_version`, `dataformat_id`, and `a_srs`.
- `Pipeline.execute()`/`validate()` again raise only their documented exception types
  (`PipelineError`/`ValidationError`) when PDAL is missing or broken.
- A failed PDAL launch (missing, non-executable, or wrong-architecture binary) raises
  `PDALNotFoundError` instead of a raw `OSError`.
- `Filter.griddecimation` emits the stage name PDAL actually registers
  (`filters.gridDecimation`); the previous all-lowercase name was rejected by the
  binary.

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
- Strict static typing enforced in CI.

### Tooling
- Added GitHub Actions for CI (`ci.yml`) and publishing (`publish.yml`), plus a release guide
  (`docs/publishing.md`) and supporting development dependencies.

### Known Limitations
- `Pipeline.arrays` is not yet implemented and currently returns an empty list.
- Stage factories do not yet expose every PDAL driver; unsupported stages can be invoked with custom
  JSON.
- First PyPI upload is still pending while the initial alpha stabilises.

---
