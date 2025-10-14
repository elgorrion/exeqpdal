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
# Application imports
from exeqpdal.apps import (
    convert,
    get_bounds,
    get_count,
    get_dimensions,
    get_srs,
    get_stats,
    info,
    merge,
    split,
    tile,
    tindex,
    translate,
)
from exeqpdal.apps import (
    pipeline as pipeline_app,
)
from exeqpdal.core.config import (
    config,
    get_pdal_path,
    get_pdal_version,
    set_pdal_path,
    set_verbose,
    validate_pdal,
)
from exeqpdal.core.pipeline import Pipeline

# Exception imports
from exeqpdal.exceptions import (
    ConfigurationError,
    DimensionError,
    MetadataError,
    PDALError,
    PDALExecutionError,
    PDALNotFoundError,
    PipelineError,
    StageError,
    ValidationError,
)

# Stage imports
from exeqpdal.stages import (
    Filter,
    FilterStage,
    Reader,
    ReaderStage,
    Stage,
    Writer,
    WriterStage,
    read_copc,
    read_las,
    read_text,
    write_copc,
    write_las,
    write_text,
)

# Type imports
from exeqpdal.types import (
    DIMENSION_TYPES,
    Classification,
    DataType,
    Dimension,
)

__all__ = [
    "DIMENSION_TYPES",
    "Classification",
    "ConfigurationError",
    "DataType",
    "Dimension",
    "DimensionError",
    "Filter",
    "FilterStage",
    "MetadataError",
    "PDALError",
    "PDALExecutionError",
    "PDALNotFoundError",
    "Pipeline",
    "PipelineError",
    "Reader",
    "ReaderStage",
    "Stage",
    "StageError",
    "ValidationError",
    "Writer",
    "WriterStage",
    "config",
    "convert",
    "get_bounds",
    "get_count",
    "get_dimensions",
    "get_pdal_path",
    "get_pdal_version",
    "get_srs",
    "get_stats",
    "info",
    "merge",
    "pipeline_app",
    "read_copc",
    "read_las",
    "read_text",
    "set_pdal_path",
    "set_verbose",
    "split",
    "tile",
    "tindex",
    "translate",
    "validate_pdal",
    "write_copc",
    "write_las",
    "write_text",
]
