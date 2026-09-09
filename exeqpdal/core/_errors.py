"""Translate execution failures at public entry points."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from exeqpdal.exceptions import PDALExecutionError, PipelineError

if TYPE_CHECKING:
    from collections.abc import Iterator


@contextmanager
def pipeline_errors() -> Iterator[None]:
    """Raise PipelineError with the last PDAL diagnostic or non-empty stderr line."""
    try:
        yield
    except PDALExecutionError as error:
        message = error.message
        lines = [line.strip() for line in (error.stderr or "").splitlines() if line.strip()]
        if lines:
            diagnostic = next(
                (line for line in reversed(lines) if line.startswith("PDAL")), lines[-1]
            )
            message += f": {diagnostic[:200]}"
        raise PipelineError(message) from error
