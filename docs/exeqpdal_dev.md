# exeqpdal Development Guide

**Purpose**: Complete implementation reference for developers and AI agents
**Authority**: Second only to `.specify/memory/constitution.md`
**Version**: 1.0.0
**Last Updated**: 2025-10-08

This guide provides concrete implementation patterns for all constitutional principles. When the constitution says "what" and "why", this guide shows "how".

---

## §1 - Development Environment

### 1.1 Requirements

**Python Version**:
- Python 3.12+ (required)
- Newer features preferred (match/case, improved type hints, etc.)

**PDAL CLI Installation**:
- **Windows**: Bundled with QGIS 3.40+ at `{QGIS_ROOT}/bin/pdal.exe`, or standalone from conda
- **Linux**: `sudo apt install pdal` or `sudo yum install pdal` or conda
- **macOS**: `brew install pdal` or conda

**Development Tools**:
```bash
# Install with uv (recommended)
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

Includes:
- `ruff` - Linting and formatting
- `mypy` - Static type checking
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting

### 1.2 Dependency Management

**Core Dependencies** (minimal):
- `numpy>=1.26.4` - Array operations for point cloud data

**Development Dependencies**:
- `ruff>=0.13.3` - Code quality
- `mypy>=1.18.2` - Type checking
- `pytest>=8.0.0` - Testing
- `pytest-cov>=6.0.0` - Coverage

**Philosophy**: Minimal dependencies. PDAL CLI provides all point cloud functionality.

### 1.3 Quality Commands

```bash
# Format code (auto-fix)
ruff format .

# Check code quality
ruff check .

# Auto-fix violations
ruff check --fix .

# Type check (strict mode)
mypy exeqpdal/

# Run tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=exeqpdal --cov-report=term-missing
```

**Before every commit**:
```bash
ruff format && ruff check && mypy exeqpdal && pytest tests/
```

---

## §2 - Project Structure

### 2.1 Directory Organization

```
exeqpdal/                      # Package root
├── __init__.py                # Public API exports
├── exceptions.py              # Exception hierarchy
├── py.typed                   # PEP 561 type marker
│
├── core/                      # Core execution (rarely changes)
│   ├── __init__.py
│   ├── config.py              # PDAL CLI discovery, configuration
│   ├── executor.py            # subprocess execution engine
│   └── pipeline.py            # Pipeline orchestration
│
├── stages/                    # Stage definitions (extends with PDAL)
│   ├── __init__.py
│   ├── base.py                # Stage, ReaderStage, FilterStage, WriterStage
│   ├── readers.py             # Reader factory (38 readers)
│   ├── filters.py             # Filter factory (90+ filters)
│   └── writers.py             # Writer factory (22 writers)
│
├── apps/                      # High-level applications
│   ├── __init__.py
│   ├── info.py                # File information
│   ├── translate.py           # Format conversion
│   └── pipeline_apps.py       # merge, split, tile, tindex
│
└── types/                     # PDAL type definitions
    ├── __init__.py
    └── dimensions.py          # Dimension, DataType, Classification

tests/                         # Test suite (repo root)
├── test_exeqpdal.py           # Main test file
└── XXX-feature-name/          # Feature-specific tests (spec-driven)

docs/                          # Documentation (repo root)
├── examples/                  # Gold standard patterns
│   ├── stage_creation_pattern.md
│   ├── pipeline_assembly_pattern.md
│   └── ...
├── exeqpdal_dev.md            # This file
└── claude/                    # Historical reference docs

specs/                         # Spec-driven development (repo root)
└── XXX-feature-name/          # Feature specifications
    ├── spec.md
    ├── plan.md
    ├── tasks.md
    └── verification/
```

### 2.2 Module Dependencies

**Dependency Rules** (enforced):
```
apps/     → stages/ + core/
stages/   → core/
core/     → (stdlib + numpy only)
types/    → (stdlib only)

NO circular dependencies
NO reverse dependencies (core never imports from stages/apps)
```

### 2.3 Critical Directory Rules

**Code Location** (NEVER violate):
- Implementation code ONLY in `exeqpdal/` directory
- Tests ONLY in `tests/` at repo root
- Spec artifacts ONLY in `specs/` at repo root
- Documentation ONLY in `docs/` at repo root

**Anti-patterns**:
- ❌ `exeqpdal/tests/` - tests don't live in package
- ❌ `exeqpdal/specs/` - specs don't live in package
- ❌ `tests/exeqpdal/` - avoid nesting
- ❌ Code in `docs/` or `specs/` - documentation only

### 2.4 Architecture Overview

**Design Philosophy**: exeqpdal is a thin wrapper around PDAL CLI, not a reimplementation.

**Core Principles**:
1. **CLI-First**: All operations via `subprocess.run()` to PDAL CLI
2. **Type-Safe**: Strict type hints, mypy compliance, py.typed marker
3. **Pythonic**: Pipe operator (`|`), natural chaining, clear exceptions
4. **Modular**: core/ (stable) + stages/ (extensible) + apps/ (convenient)

**Architecture Layers**:
```
User Code (import exeqpdal)
    ↓
Public API (exeqpdal/__init__.py)
    ↓
Applications (apps/) ←─ High-level convenience
    ↓
Pipeline (core/pipeline.py) ←─ JSON generation, stage collection
    ↓
Executor (core/executor.py) ←─ CLI execution, error parsing
    ↓
subprocess.run() ←─ PDAL CLI invocation
    ↓
PDAL (external) ←─ Point cloud processing
```

**Design Rationale**:
- **Why CLI Wrapper?**: PDAL CLI is authoritative, battle-tested, and comprehensive. Python reimplementation introduces bugs, version skew, and maintenance burden.
- **Why Subprocess?**: Clean process boundary, no PDAL internals coupling, platform-agnostic, works in constrained environments (QGIS).
- **Why JSON Pipelines?**: PDAL's native format, supports all operations, reproducible, human-readable, debuggable.
- **Why Type Hints?**: Catch errors at development time (mypy), enable IDE autocomplete, self-document APIs, prevent runtime surprises.

**Execution Flow**:
1. **Stage Creation**: User calls factory methods (`Reader.las()`, `Filter.range()`, `Writer.las()`)
2. **Stage Chaining**: Pipe operator (`|`) connects stages, setting `inputs` attribute on right-hand stage
3. **Pipeline Assembly**: `Pipeline` class walks backward from final stage, collecting all stages in execution order
4. **JSON Generation**: Each stage serializes to dict via `to_dict()`, assembled into `{"pipeline": [...]}`
5. **Temporary File**: Pipeline JSON written to temp file (auto-cleaned in finally block)
6. **CLI Execution**: `subprocess.run()` executes `pdal pipeline <temp_file.json>`
7. **Result Parsing**: Point count, metadata, numpy arrays extracted from PDAL output

**PDAL Binary Discovery** (priority order):
1. `PDAL_EXECUTABLE` environment variable
2. Custom path set via `set_pdal_path()`
3. System PATH search
4. QGIS installation detection (Windows: `C:\Program Files\QGIS 3.x\bin\pdal.exe`)
5. Raise `PDALNotFoundError` if not found

**Extensibility**:
- New readers/filters/writers: Add factory method to `stages/readers.py`, `stages/filters.py`, or `stages/writers.py`
- New applications: Create function in `apps/`, export via `apps/__init__.py` and main `__init__.py`
- New types: Add to `types/dimensions.py` (dimension names, data types, classification codes)
- Core execution: Stable, rarely changes (subprocess management is mature)

**See Also**:
- §4 (Architecture Patterns) for execution flow implementation details
- §5 (Stage Implementation) for adding new PDAL operations
- §9 (API Design Guidelines) for when to extend the API

---

## §3 - Code Standards

### 3.1 Style and Formatting

**Automated via ruff**:
- Line length: 100 characters
- Indentation: 4 spaces (no tabs)
- String quotes: Double quotes `"` (configured in ruff)
- Trailing commas: Required in multi-line structures

**Import organization** (ruff autofix):
```python
# Standard library
from __future__ import annotations
from pathlib import Path
from typing import Any

# Third-party
import numpy as np

# Local
from exeqpdal.core.executor import executor
from exeqpdal.exceptions import PDALError
```

**Pathlib required**:
```python
# ✓ Correct
from pathlib import Path
file_path = Path("input.las")

# ✗ Wrong
import os.path
file_path = "input.las"  # str, not Path
```

### 3.2 Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `PipelineError`, `ReaderStage` |
| Functions | snake_case | `execute_pipeline()`, `get_logger()` |
| Methods | snake_case | `to_dict()`, `validate()` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_TIMEOUT`, `MAX_RETRIES` |
| Private | Leading underscore | `_parse_stderr()`, `_temp_file` |
| Module variables | snake_case | `logger`, `executor` |

**Descriptive names required**:
```python
# ✓ Good - intention clear
def create_filter_stage(stage_type: str, **options: Any) -> FilterStage:
    ...

# ✗ Bad - unclear abbreviations
def cfs(st: str, **opts: Any) -> FS:
    ...
```

### 3.3 Type Annotations

**Mandatory on ALL public APIs**:
```python
# ✓ Complete type hints
def execute_pipeline(
    pipeline_json: str,
    stream_mode: bool | None = None,
    timeout: int = 120
) -> tuple[int, dict[str, Any]]:
    """Execute PDAL pipeline and return point count + metadata."""
    ...

# ✗ Missing type hints (mypy strict fails)
def execute_pipeline(pipeline_json, stream_mode=None, timeout=120):
    ...
```

**Mypy strict mode** (no compromises):
```python
# Use modern union syntax (Python 3.12+)
def process(file: Path | str) -> dict[str, Any] | None:
    ...

# NOT old-style: Optional[Dict[str, Any]]
```

**Type hints for dataclasses**:
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class StageConfig:
    stage_type: str
    filename: Path | str | None = None
    options: dict[str, Any] = None  # ✗ Wrong - mutable default

    def __post_init__(self) -> None:  # ✓ Type hint on __post_init__
        # Validation here
        ...
```

**Fix mutable defaults**:
```python
@dataclass(frozen=True)
class StageConfig:
    options: dict[str, Any] | None = None  # ✓ None, not {}

    def __post_init__(self) -> None:
        if self.options is None:
            object.__setattr__(self, 'options', {})
```

### 3.4 Documentation

**Docstring style** (Google format):
```python
def translate(
    input_file: str | Path,
    output_file: str | Path,
    **options: Any
) -> None:
    """Convert point cloud file to different format.

    Args:
        input_file: Path to input file
        output_file: Path to output file
        **options: Additional PDAL translate options

    Raises:
        PDALNotFoundError: PDAL CLI not found
        PDALExecutionError: Translation failed
    """
```

**Brevity**:
- Aim for 1 line when possible
- Maximum 5 lines
- Focus on purpose, not mechanics

**Single-line sufficient**:
```python
def get_point_count(file_path: Path) -> int:
    """Return number of points in file."""
```

**Comments** (minimize):
```python
# ✓ Good - explains "why"
# PDAL streaming requires explicit --stream flag for filters.range
args.append("--stream")

# ✗ Bad - explains "what" (code already shows this)
# Append stream flag to arguments
args.append("--stream")

# ✗ Terrible - commented code
# old_method()  # Don't do this
new_method()
```

### 3.5 Constants Management

**All magic values as constants**:
```python
# ✓ Good
DEFAULT_TIMEOUT_SECONDS = 120
MAX_RETRIES = 3

def execute(timeout: int = DEFAULT_TIMEOUT_SECONDS) -> None:
    ...

# ✗ Bad
def execute(timeout: int = 120) -> None:  # Magic number
    ...
```

**Constants location**:
- Module-level for module-specific constants
- Class-level for class-specific constants
- `core/config.py` for global configuration

---

## §4 - Architecture Patterns

### 4.1 Core Data Flow

```
User Code → Stage Creation → Pipeline Assembly → JSON Generation → CLI Execution → Result Parsing
```

**Example - complete flow**:
```python
# 1. User Code - Pythonic API
import exeqpdal as pdal

pipeline = (
    pdal.Reader.las("input.las")               # 2. Stage Creation
    | pdal.Filter.range(limits="Classification[2:2]")
    | pdal.Writer.las("output.las")
)                                               # 3. Pipeline Assembly

count = pipeline.execute()                      # 4-6. JSON→CLI→Parse
print(f"Processed {count} points")
```

**Internal flow** (what execute() does):
```python
# 4. JSON Generation
pipeline_json = pipeline.serialize_to_json()
# {"pipeline": [{"type": "readers.las", "filename": "input.las"}, ...]}

# 5. CLI Execution
result = executor.execute_pipeline(pipeline_json)
# subprocess.run(["pdal", "pipeline", temp_file])

# 6. Result Parsing
point_count = result['point_count']
metadata = result['metadata']
```

### 4.2 Stage Creation Pattern

**Factory methods** (static methods on Reader/Filter/Writer):
```python
from exeqpdal.stages import Reader, Filter, Writer

# Factory pattern - clean API
reader = Reader.las("input.las")
filter_stage = Filter.range(limits="Classification[2:2]")
writer = Writer.las("output.las")

# Each factory returns appropriate stage type
assert isinstance(reader, ReaderStage)
assert isinstance(filter_stage, FilterStage)
assert isinstance(writer, WriterStage)
```

**Validation at creation**:
```python
# Good - validates immediately
try:
    reader = Reader.las("nonexistent.las")
except ValueError as e:
    print(f"Invalid file: {e}")

# Validation in Stage.__init__()
class ReaderStage(Stage):
    def __init__(self, stage_type: str, filename: str | Path, **options: Any):
        if not Path(filename).exists():
            raise ValueError(f"File not found: {filename}")
        super().__init__(stage_type, filename=filename, **options)
```

### 4.3 Pipeline Assembly Pattern

**Pipe operator chaining**:
```python
# Chaining with | operator
pipeline = reader | filter1 | filter2 | writer

# Equivalent to:
filter1.inputs = [reader]
filter2.inputs = [filter1]
writer.inputs = [filter2]
pipeline = Pipeline(writer)  # Final stage passed to Pipeline
```

**Explicit Pipeline creation**:
```python
# From JSON string
json_pipeline = '{"pipeline": ["input.las", "output.las"]}'
pipeline = Pipeline(json_pipeline)

# From dict
pipeline_dict = {"pipeline": ["input.las", {"type": "writers.las", "filename": "out.las"}]}
pipeline = Pipeline(pipeline_dict)

# From Stage chain
pipeline = Pipeline(reader | filter_stage | writer)
```

### 4.4 Validation Before Execution

```python
# Pipeline validates before execution
try:
    pipeline.validate()  # Checks stage compatibility
    count = pipeline.execute()
except ValidationError as e:
    print(f"Invalid pipeline: {e}")
except PDALExecutionError as e:
    print(f"Execution failed: {e}")
```

---

## §5 - Stage Implementation

### 5.1 Adding New Reader

**When**: PDAL adds new reader type

**Pattern**:
```python
# In stages/readers.py

class Reader:
    # ... existing readers ...

    @staticmethod
    def new_format(filename: str | Path, **options: Any) -> ReaderStage:
        """Read new format files.

        Args:
            filename: Path to new format file
            **options: Additional reader options

        Returns:
            ReaderStage configured for new format
        """
        return ReaderStage("readers.newformat", filename=filename, **options)
```

### 5.2 Adding New Filter

**When**: PDAL adds new filter type

**Pattern**:
```python
# In stages/filters.py

class Filter:
    # ... existing filters ...

    @staticmethod
    def new_filter(**options: Any) -> FilterStage:
        """Apply new filter to point cloud.

        Args:
            **options: Filter-specific options (see PDAL docs)

        Returns:
            FilterStage configured for new filter
        """
        return FilterStage("filters.newfilter", **options)
```

### 5.3 Stage Serialization

**Every Stage must serialize to PDAL JSON**:
```python
class Stage:
    def to_dict(self) -> dict[str, Any]:
        """Serialize stage to PDAL JSON format."""
        result = {"type": self.stage_type}
        if self.filename:
            result["filename"] = str(self.filename)
        result.update(self.options)
        return result
```

**Example output**:
```python
stage = Reader.las("input.las", extra_dims="all")
print(stage.to_dict())
# {"type": "readers.las", "filename": "input.las", "extra_dims": "all"}
```

---

## §6 - Pipeline Patterns

### 6.1 Basic Pipeline Execution

```python
import exeqpdal as pdal

# Simple pipeline
pipeline = pdal.Reader.las("input.las") | pdal.Writer.las("output.las")
count = pipeline.execute()
print(f"Copied {count} points")

# Access metadata after execution
metadata = pipeline.metadata
bounds = metadata['metadata']['readers.las']['bounds']
print(f"Bounds: {bounds}")
```

### 6.2 Complex Pipeline

```python
# Multi-stage processing
pipeline = (
    pdal.Reader.las("input.las")
    | pdal.Filter.range(limits="Classification[2:2]")  # Ground points only
    | pdal.Filter.outlier(method="statistical", mean_k=8)
    | pdal.Filter.smrf()  # Ground classification
    | pdal.Writer.las("ground.las", compression="laszip")
)

try:
    count = pipeline.execute()
    print(f"Processed {count} ground points")
except pdal.PDALExecutionError as e:
    print(f"Pipeline failed: {e}")
    print(f"PDAL stderr: {e.stderr}")
```

### 6.3 Streaming Mode

```python
# Force streaming for large files
pipeline = pdal.Pipeline(pipeline_json, stream_mode=True)

# Check if streamable
if pipeline.is_streamable:
    count = pipeline.execute()
else:
    print("Pipeline cannot stream - loading all points")
```

---

## §7 - Error Handling

### 7.1 Exception Hierarchy

```python
PDALError                    # Base exception
├── PDALNotFoundError        # PDAL CLI not found
├── PDALExecutionError       # CLI execution failed
│   ├── returncode: int      # Process exit code
│   └── stderr: str          # CLI error output
├── PipelineError            # Pipeline configuration invalid
├── ValidationError          # Input validation failed
├── MetadataError            # Metadata parsing failed
└── ConfigurationError       # Configuration invalid
```

### 7.2 CLI Error Parsing

**Executor parses PDAL stderr**:
```python
# exeqpdal contextualizes CLI errors
try:
    pipeline.execute()
except PDALExecutionError as e:
    print(f"PDAL CLI error (code {e.returncode}):")
    print(f"  {e}")  # Contextualized message
    print(f"Original stderr: {e.stderr}")
```

**Example error transformation**:
```
PDAL stderr: "readers.las: Cannot open input.las"
                    ↓
exeqpdal raises:  PDALExecutionError(
    "PDAL execution failed: Cannot open input.las. "
    "Check that file exists and is a valid LAS file."
)
```

### 7.3 Cleanup on Error

**Always cleanup temp files**:
```python
def execute_pipeline(pipeline_json: str) -> dict[str, Any]:
    temp_file = None
    try:
        temp_file = create_temp_pipeline_file(pipeline_json)
        result = subprocess.run(["pdal", "pipeline", temp_file], ...)
        return parse_result(result)
    finally:
        if temp_file and temp_file.exists():
            temp_file.unlink()  # Cleanup even on error
```

### 7.4 Logging

**Use standard logging module**:
```python
import logging

logger = logging.getLogger(__name__)

def execute_pipeline(pipeline_json: str) -> dict[str, Any]:
    logger.info(f"Executing pipeline with {len(stages)} stages")
    try:
        result = run_cli(pipeline_json)
        logger.debug(f"Pipeline succeeded: {result['point_count']} points")
        return result
    except PDALExecutionError as e:
        logger.exception("Pipeline execution failed")
        raise
```

---

## §8 - Testing Strategy

### 8.1 Test Organization

```
tests/
├── test_exeqpdal.py           # Main test file
│   ├── TestPipeline           # Pipeline tests
│   ├── TestStages             # Stage creation tests
│   ├── TestCLIExecution       # Executor tests
│   └── TestErrorHandling      # Exception tests
│
└── XXX-feature-name/          # Feature-specific (spec-driven)
    ├── test_stage_creation.py
    ├── test_pipeline_assembly.py
    └── test_integration.py
```

### 8.2 Unit Tests (Mocked CLI)

```python
from unittest.mock import patch, MagicMock
import exeqpdal as pdal

def test_pipeline_creates_correct_json(mocker):
    """Pipeline serializes stages to correct PDAL JSON."""
    # Mock subprocess to avoid actual PDAL call
    mock_run = mocker.patch('subprocess.run')
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout='{"point_count": 1000}',
        stderr=''
    )

    pipeline = pdal.Reader.las("test.las") | pdal.Writer.las("out.las")
    pipeline.execute()

    # Verify correct JSON was generated
    call_args = mock_run.call_args
    temp_file_path = call_args[0][0][2]  # ["pdal", "pipeline", temp_file]

    with open(temp_file_path) as f:
        pipeline_json = json.load(f)

    assert pipeline_json["pipeline"][0]["type"] == "readers.las"
    assert pipeline_json["pipeline"][1]["type"] == "writers.las"
```

### 8.3 Integration Tests (Real PDAL)

```python
import pytest
from pathlib import Path

@pytest.mark.integration
def test_real_pipeline_execution(tmp_path):
    """Test with actual PDAL CLI (requires PDAL installed)."""
    # Create test LAS file (or use fixture)
    input_file = tmp_path / "test.las"
    output_file = tmp_path / "output.las"

    # This calls real PDAL
    pipeline = pdal.Reader.las(str(input_file)) | pdal.Writer.las(str(output_file))

    try:
        count = pipeline.execute()
        assert count > 0
        assert output_file.exists()
    except pdal.PDALNotFoundError:
        pytest.skip("PDAL CLI not installed")
```

### 8.4 Coverage Requirements

**Minimum: 80%**

Check coverage:
```bash
pytest --cov=exeqpdal --cov-report=term-missing
```

**Focus coverage on**:
- Public API methods
- Stage serialization (to_dict)
- Error handling paths
- CLI parsing logic

**Acceptable to skip**:
- `__repr__` methods
- Debug-only code paths
- Trivial getters

---

## §9 - API Design Guidelines

### 9.1 When to Add New Stage Factory

**Add to Reader/Filter/Writer** when:
- PDAL adds new reader/filter/writer type
- Existing PDAL stage not yet wrapped
- Factory method provides type-safe access

**Example**:
```python
# PDAL adds filters.newfilter
# → Add Filter.newfilter() static method
```

### 9.2 When to Create New App

**Add to apps/** when:
- High-level operation combines multiple stages
- Common use case deserves convenience function
- Wraps PDAL application (info, translate, merge, etc.)

**Example**:
```python
# apps/translate.py
def translate(input_file: str | Path, output_file: str | Path, **options: Any) -> None:
    """Convenience wrapper for PDAL translate."""
    # Internally uses executor.execute_application()
```

### 9.3 When to Extend types/

**Add to types/dimensions.py** when:
- PDAL adds new dimension types
- New classification codes standardized
- Data type definitions needed

**Conservative approach**: Only add when PDAL officially supports.

---

## §10 - Performance & Best Practices

### 10.1 Streaming Mode

**Large files** (>1GB point clouds):
```python
# Enable streaming
pipeline = pdal.Pipeline(pipeline_json, stream_mode=True)

# Check if pipeline supports streaming
if not pipeline.is_streamable:
    logger.warning("Pipeline cannot stream - memory usage may be high")
```

### 10.2 Subprocess Timeouts

**Prevent hangs**:
```python
# Default timeout: 120 seconds
# For large files, increase timeout
pipeline.execute(timeout=600)  # 10 minutes
```

### 10.3 Temporary File Cleanup

**Always cleanup**:
```python
# Executor handles cleanup automatically
# But for custom temp files:
temp_file = create_temp_file()
try:
    process_file(temp_file)
finally:
    temp_file.unlink(missing_ok=True)  # Safe even if already deleted
```

### 10.4 Array Access (Lazy Loading)

```python
# Arrays only loaded when accessed
pipeline.execute()

# This loads point data into memory
arrays = pipeline.arrays  # Now in memory

# For large datasets, avoid loading all points
# Instead, use PDAL filters to reduce point count first
```

### 10.5 PDAL Discovery Performance

**Cache PDAL path**:
```python
# Config caches PDAL path after first discovery
# Subsequent calls are instant
pdal_path = config.get_pdal_path()  # Fast after first call
```

---

## Quick Reference: Common Patterns

### Creating Pipeline
```python
# Method 1: Chaining
pipeline = pdal.Reader.las("in.las") | pdal.Filter.range(limits="Z[0:100]") | pdal.Writer.las("out.las")

# Method 2: JSON string
pipeline = pdal.Pipeline('{"pipeline": ["in.las", "out.las"]}')

# Method 3: Dict
pipeline = pdal.Pipeline({"pipeline": [{"type": "readers.las", "filename": "in.las"}]})
```

### Error Handling
```python
try:
    count = pipeline.execute()
except pdal.PDALNotFoundError:
    print("Install PDAL CLI first")
except pdal.PDALExecutionError as e:
    print(f"PDAL failed: {e}")
    print(f"Details: {e.stderr}")
```

### Adding New Stage
```python
# In stages/readers.py or filters.py or writers.py
@staticmethod
def new_stage(**options: Any) -> StageType:
    """Brief description."""
    return StageType("stage.type", **options)
```

### Testing with Mocks
```python
def test_feature(mocker):
    mock_run = mocker.patch('subprocess.run')
    mock_run.return_value = MagicMock(returncode=0, stdout='{}', stderr='')
    # Test code here
```

---

## See Also

- **Constitution**: `.specify/memory/constitution.md` - The "why" behind patterns
- **Gold Standards**: `docs/examples/*.md` - Reference implementations
- **Troubleshooting**: `docs/troubleshooting.md` - Installation and runtime issues
