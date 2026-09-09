"""PDAL applications - merge, sort, split, tile, tindex."""

from __future__ import annotations

import logging
import math
import struct
from pathlib import Path
from typing import TYPE_CHECKING

from exeqpdal.apps._options import stage_option_args
from exeqpdal.core._errors import pipeline_errors
from exeqpdal.core.executor import executor
from exeqpdal.exceptions import MetadataError

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)


def _las_header_options(filename: str | Path) -> dict[str, float]:
    """Read scales and offsets from the uncompressed LAS/LAZ header."""
    # LAS 1.4 R15, section 2.4 (Public Header Block), also shared by LAS 1.0-1.3.
    with Path(filename).open("rb") as source:
        header = source.read(227)
    if len(header) < 227:
        raise MetadataError(f"Truncated LAS header in {filename}: expected at least 227 bytes")
    if header[:4] != b"LASF":
        raise MetadataError(f"Invalid LAS signature in {filename}: expected LASF")
    values = struct.unpack_from("<6d", header, 131)
    names = ("scale_x", "scale_y", "scale_z", "offset_x", "offset_y", "offset_z")
    options: dict[str, float] = {}
    for name, value in zip(names, values, strict=True):
        if not math.isfinite(value) or (name.startswith("scale_") and value <= 0):
            raise MetadataError(f"Invalid LAS {name} in {filename}: {value}")
        options[f"writers.las.{name}"] = value
    return options


def merge(
    input_files: list[str | Path],
    output_file: str | Path,
    *,
    stage_options: Mapping[str, object] | None = None,
    header_from: str | Path | None = None,
) -> None:
    """Merge multiple point cloud files into one.

    Args:
        input_files: List of input file paths
        output_file: Output file path
        stage_options: Exact dotted PDAL stage options. Ordinary LAS/LAZ
            outputs default to automatic X/Y/Z offsets. Caller values override
            those defaults and header_from values.
        header_from: LAS/LAZ file whose scales and offsets apply to ordinary
            LAS/LAZ outputs. Other output formats ignore this parameter.

    Raises:
        PDALNotFoundError: If the PDAL executable cannot start
        PipelineError: If merge fails
        MetadataError: If header_from has an invalid signature, header length,
            scale, or offset
        OSError: If header_from cannot be read
    """
    args = [str(f) for f in input_files] + [str(output_file)]
    output_name = str(output_file).lower()
    is_las = output_name.endswith((".las", ".laz")) and not output_name.endswith(".copc.laz")

    effective_options: dict[str, object] = {}
    if is_las:
        effective_options = {
            "writers.las.offset_x": "auto",
            "writers.las.offset_y": "auto",
            "writers.las.offset_z": "auto",
        }
        if header_from is not None:
            effective_options.update(_las_header_options(header_from))
    if stage_options:
        effective_options.update(stage_options)
    args.extend(stage_option_args(effective_options))

    logger.info(f"Merging {len(input_files)} files to {output_file}")
    with pipeline_errors():
        executor.execute_application("merge", args)
    logger.info("Merge completed")


def sort(
    input_file: str | Path,
    output_file: str | Path,
    *,
    compress: bool = False,
    metadata: bool = False,
) -> None:
    """Sort a point cloud file into Morton (spatial) order.

    Args:
        input_file: Input file path
        output_file: Output file path
        compress: Compress output data (if supported by output format)
        metadata: Forward metadata (VLRs, header entries) from previous stages

    Raises:
        PDALNotFoundError: If the PDAL executable cannot start
        PipelineError: If sort fails
    """
    args = [str(input_file), str(output_file)]

    if compress:
        args.append("--compress")

    if metadata:
        args.append("--metadata")

    logger.info(f"Sorting {input_file} to {output_file}")
    with pipeline_errors():
        executor.execute_application("sort", args)
    logger.info("Sort completed")


def split(
    input_file: str | Path,
    output_pattern: str | Path,
    *,
    length: int | None = None,
    capacity: int | None = None,
) -> None:
    """Split a point cloud file into multiple files.

    Args:
        input_file: Input file path
        output_pattern: Output filename pattern (use # for numbers)
        length: Split by distance (meters)
        capacity: Split by point count

    Raises:
        PDALNotFoundError: If the PDAL executable cannot start
        PipelineError: If split fails

    Examples:
        >>> split("input.las", "output_#.las", capacity=100000)
    """
    args = [str(input_file), str(output_pattern)]

    if length is not None:
        args.extend(["--length", str(length)])

    if capacity is not None:
        args.extend(["--capacity", str(capacity)])

    logger.info(f"Splitting {input_file} to {output_pattern}")
    with pipeline_errors():
        executor.execute_application("split", args)
    logger.info("Split completed")


def tile(
    input_file: str | Path,
    output_pattern: str | Path,
    *,
    length: float | None = None,
    origin_x: float | None = None,
    origin_y: float | None = None,
    buffer: float | None = None,
) -> None:
    """Create tiles from a point cloud file.

    Args:
        input_file: Input file path
        output_pattern: Output filename pattern (use # for tile numbers, e.g. "tile_#.las")
        length: Tile edge length (meters)
        origin_x: X origin for tiling
        origin_y: Y origin for tiling
        buffer: Buffer around tiles (meters)

    Raises:
        PDALNotFoundError: If the PDAL executable cannot start
        PipelineError: If tiling fails

    Examples:
        >>> tile("input.las", "tiles/tile_#.las", length=100.0)
    """
    args = [str(input_file), str(output_pattern)]

    if length is not None:
        args.extend(["--length", str(length)])

    if origin_x is not None:
        args.extend(["--origin_x", str(origin_x)])

    if origin_y is not None:
        args.extend(["--origin_y", str(origin_y)])

    if buffer is not None:
        args.extend(["--buffer", str(buffer)])

    logger.info(f"Tiling {input_file} to {output_pattern}")
    with pipeline_errors():
        executor.execute_application("tile", args)
    logger.info("Tiling completed")


def tindex(
    input_files: list[str | Path],
    output_file: str | Path,
    *,
    filespec: str | None = None,
    tindex_name: str | None = None,
    fast_boundary: bool = False,
) -> None:
    """Create a tile index from multiple files.

    Args:
        input_files: List of input file paths
        output_file: Output index file path
        filespec: File specification pattern
        tindex_name: Tile index column name
        fast_boundary: Use fast boundary computation

    Raises:
        PDALNotFoundError: If the PDAL executable cannot start
        PipelineError: If tindex creation fails
    """
    args = ["create", "--tindex", str(output_file), "-f", "GeoJSON"] + [str(f) for f in input_files]

    if filespec is not None:
        args.extend(["--filespec", filespec])

    if tindex_name is not None:
        args.extend(["--tindex_name", tindex_name])

    if fast_boundary:
        args.append("--fast_boundary")

    logger.info(f"Creating tile index from {len(input_files)} files")
    with pipeline_errors():
        executor.execute_application("tindex", args)
    logger.info("Tile index created")


def pipeline(
    pipeline_file: str | Path,
    *,
    validate: bool = False,
    stream: bool | None = None,
) -> None:
    """Execute a PDAL pipeline from JSON file.

    Args:
        pipeline_file: Path to pipeline JSON file
        validate: Validate without executing
        stream: Force stream mode (True) or standard mode (False)

    Raises:
        PDALNotFoundError: If the PDAL executable cannot start
        PipelineError: If pipeline execution fails
    """
    args = [str(pipeline_file)]

    if validate:
        args.append("--validate")

    if stream is True:
        args.append("--stream")
    elif stream is False:
        args.append("--nostream")

    logger.info(f"Executing pipeline from {pipeline_file}")
    with pipeline_errors():
        executor.execute_application("pipeline", args)
    logger.info("Pipeline executed")
