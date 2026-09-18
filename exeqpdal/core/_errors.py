"""Translate execution failures at public entry points."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from exeqpdal.exceptions import PDALExecutionError, PipelineError

if TYPE_CHECKING:
    from collections.abc import Iterator


@contextmanager
def pipeline_errors(pipeline_json: str | None = None) -> Iterator[None]:
    """Raise PipelineError carrying the execution failure's full diagnostics.

    The message ends with the last PDAL diagnostic or non-empty stderr line;
    return code, output, command line, and ``pipeline_json`` ride along.
    """
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
        raise PipelineError(
            message,
            returncode=error.returncode,
            stdout=error.stdout,
            stderr=error.stderr,
            command=error.command,
            pipeline_json=pipeline_json,
        ) from error
