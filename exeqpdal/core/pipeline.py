"""PDAL Pipeline implementation."""

from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

from exeqpdal.core.executor import executor
from exeqpdal.exceptions import MetadataError, PipelineError, ValidationError
from exeqpdal.stages.base import Stage

logger = logging.getLogger(__name__)


class Pipeline:
    """PDAL Pipeline for executing point cloud processing workflows."""

    def __init__(
        self,
        pipeline: str | dict[str, Any] | list[Any] | Stage,
        stream_mode: bool | None = None,
    ) -> None:
        """Initialize pipeline.

        Args:
            pipeline: Pipeline definition (JSON string, dict, list, or Stage)
            stream_mode: Force stream mode (True), standard mode (False), or auto (None)

        Raises:
            PipelineError: If pipeline definition is invalid
        """
        self.stream_mode = stream_mode
        self._pipeline_json: str = ""
        self._pipeline_dict: dict[str, Any] | list[Any] = {}
        self._executed: bool = False
        self._point_count: int = 0
        self._metadata: dict[str, Any] = {}
        self._arrays: list[np.ndarray] = []
        self._log: str = ""
        self._is_valid: bool | None = None
        self._is_streamable: bool | None = None

        # Parse pipeline input
        self._parse_pipeline(pipeline)

    def _parse_pipeline(self, pipeline: str | dict[str, Any] | list[Any] | Stage) -> None:
        """Parse and validate pipeline definition.

        Args:
            pipeline: Pipeline definition

        Raises:
            PipelineError: If pipeline definition is invalid
        """
        if isinstance(pipeline, str):
            # JSON string
            try:
                self._pipeline_dict = json.loads(pipeline)
                self._pipeline_json = pipeline
            except json.JSONDecodeError as e:
                raise PipelineError(f"Invalid JSON pipeline: {e}") from e

        elif isinstance(pipeline, dict):
            # Dictionary
            self._pipeline_dict = pipeline
            self._pipeline_json = json.dumps(pipeline, indent=2)

        elif isinstance(pipeline, list):
            # List of stages
            self._pipeline_dict = {"pipeline": pipeline}
            self._pipeline_json = json.dumps(self._pipeline_dict, indent=2)

        elif isinstance(pipeline, Stage):
            # Single stage - build full pipeline
            stages = self._collect_stages(pipeline)
            stage_dicts = [s.to_dict() for s in stages]
            self._pipeline_dict = {"pipeline": stage_dicts}
            self._pipeline_json = json.dumps(self._pipeline_dict, indent=2)

        else:
            raise PipelineError(
                f"Invalid pipeline type: {type(pipeline)}. "
                "Expected str, dict, list, or Stage"
            )

        # Ensure pipeline is in correct format
        if isinstance(self._pipeline_dict, dict):
            if "pipeline" not in self._pipeline_dict:
                raise PipelineError("Pipeline dict must have 'pipeline' key")
        elif not isinstance(self._pipeline_dict, list):
            raise PipelineError("Pipeline must be dict with 'pipeline' key or list of stages")

        logger.debug(f"Pipeline parsed: {len(self._pipeline_json)} bytes")

    def _collect_stages(self, final_stage: Stage) -> list[Stage]:
        """Collect all stages in pipeline by walking backwards from final stage.

        Args:
            final_stage: Final stage in pipeline

        Returns:
            List of stages in execution order
        """
        visited: set[int] = set()
        stages: list[Stage] = []

        def walk(stage: Stage) -> None:
            stage_id = id(stage)
            if stage_id in visited:
                return
            visited.add(stage_id)

            # Process inputs first
            if stage.inputs:
                for inp in stage.inputs:
                    if isinstance(inp, Stage):
                        walk(inp)

            stages.append(stage)

        walk(final_stage)
        return stages

    def execute(self) -> int:
        """Execute the pipeline.

        Returns:
            Number of points processed

        Raises:
            PipelineError: If pipeline execution fails
        """
        try:
            logger.info("Executing pipeline...")
            stdout, stderr, returncode = executor.execute_pipeline(
                self._pipeline_json,
                stream_mode=self.stream_mode,
                metadata=True,
            )

            self._executed = True
            self._log = stdout + stderr

            # Parse output for point count
            self._parse_execution_output(stdout)

            # Try to load arrays if any output was generated
            self._load_arrays()

            logger.info(f"Pipeline executed successfully: {self._point_count} points")
            return self._point_count

        except Exception as e:
            raise PipelineError(f"Pipeline execution failed: {e}") from e

    def _parse_execution_output(self, output: str) -> None:
        """Parse PDAL execution output for point count and metadata.

        Args:
            output: PDAL stdout output
        """
        # PDAL doesn't always output point count to stdout
        # We'll extract it from metadata when available
        for line in output.split("\n"):
            if "point" in line.lower() and any(c.isdigit() for c in line):
                try:
                    # Try to extract number
                    numbers = "".join(c if c.isdigit() else " " for c in line).split()
                    if numbers:
                        self._point_count = int(numbers[0])
                        break
                except (ValueError, IndexError):
                    pass

    def _load_arrays(self) -> None:
        """Load point data arrays from output files.

        This is a placeholder - actual implementation would need to:
        1. Identify output files from pipeline
        2. Read point data using appropriate reader
        3. Convert to numpy structured arrays
        """
        # TODO: Implement array loading
        # For now, arrays remain empty
        # In a full implementation, this would parse output files
        pass

    def validate(self) -> bool:
        """Validate pipeline without executing.

        Returns:
            True if pipeline is valid

        Raises:
            ValidationError: If validation fails
        """
        try:
            is_valid, is_streamable, message = executor.validate_pipeline(self._pipeline_json)

            self._is_valid = is_valid
            self._is_streamable = is_streamable

            if not is_valid:
                raise ValidationError(f"Pipeline validation failed: {message}")

            logger.info(f"Pipeline valid (streamable: {is_streamable})")
            return True

        except Exception as e:
            raise ValidationError(f"Pipeline validation failed: {e}") from e

    @property
    def arrays(self) -> list[np.ndarray]:
        """Get point data arrays.

        Returns:
            List of numpy structured arrays with point data

        Raises:
            PipelineError: If pipeline hasn't been executed
        """
        if not self._executed:
            raise PipelineError("Pipeline must be executed before accessing arrays")
        return self._arrays

    @property
    def metadata(self) -> dict[str, Any]:
        """Get pipeline metadata.

        Returns:
            Metadata dictionary

        Raises:
            PipelineError: If pipeline hasn't been executed
        """
        if not self._executed:
            raise PipelineError("Pipeline must be executed before accessing metadata")
        return self._metadata

    @property
    def log(self) -> str:
        """Get execution log.

        Returns:
            Execution log string

        Raises:
            PipelineError: If pipeline hasn't been executed
        """
        if not self._executed:
            raise PipelineError("Pipeline must be executed before accessing log")
        return self._log

    @property
    def is_streamable(self) -> bool:
        """Check if pipeline can run in stream mode.

        Returns:
            True if pipeline is streamable

        Raises:
            PipelineError: If pipeline hasn't been validated
        """
        if self._is_streamable is None:
            self.validate()
        return self._is_streamable or False

    @property
    def pipeline_json(self) -> str:
        """Get pipeline JSON string.

        Returns:
            Pipeline JSON string
        """
        return self._pipeline_json

    def __repr__(self) -> str:
        """String representation of pipeline."""
        status = "executed" if self._executed else "not executed"
        return f"Pipeline({status}, {self._point_count} points)"
