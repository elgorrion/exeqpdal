"""exeqpdal - Python API for executing PDAL CLI commands with native syntax.

A development-stage Python package that bridges access to PDAL CLI from Python code,
especially designed for QGIS plugin development.

Usage:
    import exeqpdal as pdal

    # Create pipeline
    pipeline = pdal.Pipeline(pipeline_json)
    count = pipeline.execute()

    # Or use stage chaining
    pipeline = (
        pdal.Reader.las("input.las")
        | pdal.Filter.range(limits="Classification[2:2]")
        | pdal.Writer.las("output.las")
    )
    pipeline.execute()

    # Use applications
    info = pdal.info("input.las", stats=True)
    pdal.translate("input.las", "output.laz")
"""

from __future__ import annotations

__version__ = "0.1.0-dev"
__author__ = "ElGorrion"
__license__ = "MIT"

# Core imports
from exeqpdal.core.pipeline import Pipeline
from exeqpdal.core.config import (
    config,
    get_pdal_path,
    get_pdal_version,
    set_pdal_path,
    set_verbose,
    validate_pdal,
)

# Stage imports
from exeqpdal.stages import (
    Reader,
    Filter,
    Writer,
    Stage,
    ReaderStage,
    FilterStage,
    WriterStage,
    read_las,
    read_copc,
    read_text,
    write_las,
    write_copc,
    write_text,
)

# Application imports
from exeqpdal.apps import (
    info,
    translate,
    convert,
    merge,
    split,
    tile,
    tindex,
    pipeline as pipeline_app,
    get_bounds,
    get_count,
    get_dimensions,
    get_srs,
    get_stats,
)

# Exception imports
from exeqpdal.exceptions import (
    PDALError,
    PDALNotFoundError,
    PDALExecutionError,
    PipelineError,
    StageError,
    ValidationError,
    DimensionError,
    MetadataError,
    ConfigurationError,
)

# Type imports
from exeqpdal.types import (
    Dimension,
    DataType,
    Classification,
    DIMENSION_TYPES,
)

__all__ = [
    # Core
    "Pipeline",
    "config",
    "get_pdal_path",
    "get_pdal_version",
    "set_pdal_path",
    "set_verbose",
    "validate_pdal",
    # Stages
    "Reader",
    "Filter",
    "Writer",
    "Stage",
    "ReaderStage",
    "FilterStage",
    "WriterStage",
    "read_las",
    "read_copc",
    "read_text",
    "write_las",
    "write_copc",
    "write_text",
    # Applications
    "info",
    "translate",
    "convert",
    "merge",
    "split",
    "tile",
    "tindex",
    "pipeline_app",
    "get_bounds",
    "get_count",
    "get_dimensions",
    "get_srs",
    "get_stats",
    # Exceptions
    "PDALError",
    "PDALNotFoundError",
    "PDALExecutionError",
    "PipelineError",
    "StageError",
    "ValidationError",
    "DimensionError",
    "MetadataError",
    "ConfigurationError",
    # Types
    "Dimension",
    "DataType",
    "Classification",
    "DIMENSION_TYPES",
]
