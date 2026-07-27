"""PDAL translate application."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from exeqpdal.apps._options import stage_option_args
from exeqpdal.core.executor import executor

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

logger = logging.getLogger(__name__)


def translate(
    input_file: str | Path,
    output_file: str | Path,
    *,
    filters: list[str] | None = None,
    reader: str | None = None,
    writer: str | None = None,
    dims: str | None = None,
    stage_options: Mapping[str, object] | None = None,
    **options: Any,
) -> None:
    """Translate between point cloud formats.

    Args:
        input_file: Input file path
        output_file: Output file path
        filters: List of filter names to apply
        reader: Explicit reader type (e.g., 'readers.las')
        writer: Explicit writer type (e.g., 'writers.las')
        dims: Dimensions to retain in the output
        stage_options: Exact dotted PDAL stage options, such as
            ``{"writers.las.offset_x": "auto"}``
        **options: Backward-compatible single-word stage options, such as
            ``filters_range_limits``. Use ``stage_options`` when any component
            contains an underscore.

    Raises:
        PDALExecutionError: If translation fails

    Examples:
        >>> translate("input.las", "output.laz")
        >>> translate("input.las", "output.las", filters=["range", "outlier"])
        >>> translate(
        ...     "input.las",
        ...     "output.las",
        ...     filters=["range"],
        ...     filters_range_limits="Classification[2:2]",
        ...     stage_options={"writers.las.offset_x": "auto"},
        ... )
    """
    args = [str(input_file), str(output_file)]

    # Add reader
    if reader:
        args.extend(["--reader", reader])

    # Add writer
    if writer:
        args.extend(["--writer", writer])

    # Add filters
    if filters:
        for filter_name in filters:
            args.extend(["--filter", filter_name])

    if dims is not None:
        args.append(f"--dims={dims}")

    args.extend(stage_option_args(stage_options, options))

    logger.info(f"Translating {input_file} to {output_file}")
    executor.execute_application("translate", args)
    logger.info("Translation completed")


def convert(
    input_file: str | Path,
    output_file: str | Path,
    *,
    dims: str | None = None,
    stage_options: Mapping[str, object] | None = None,
    **options: Any,
) -> None:
    """Convert between point cloud formats (alias for translate).

    Args:
        input_file: Input file path
        output_file: Output file path
        dims: Dimensions to retain in the output
        stage_options: Exact dotted PDAL stage options
        **options: Translation options

    Raises:
        PDALExecutionError: If conversion fails
    """
    translate(
        input_file,
        output_file,
        dims=dims,
        stage_options=stage_options,
        **options,
    )
