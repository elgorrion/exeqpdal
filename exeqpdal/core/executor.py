"""PDAL CLI execution engine."""

from __future__ import annotations

import json
import logging
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Any, cast

from exeqpdal.core.config import config
from exeqpdal.exceptions import PDALExecutionError, PDALNotFoundError

logger = logging.getLogger(__name__)

_SUBPROCESS_FLAGS = (
    getattr(subprocess, "CREATE_NO_WINDOW", 0) if platform.system() == "Windows" else 0
)


def _text(value: str | bytes | None) -> str | None:
    """Decode subprocess output that may arrive as bytes (TimeoutExpired carries bytes)."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


class Executor:
    """Execute PDAL CLI commands."""

    def __init__(self, verbose: bool = False) -> None:
        """Initialize executor.

        Args:
            verbose: Enable verbose PDAL output
        """
        self._verbose = verbose

    @property
    def verbose(self) -> bool:
        """Verbose flag; follows config.set_verbose() at call time."""
        return self._verbose or config.verbose

    def _run(
        self,
        cmd: list[str],
        *,
        input_text: str | None = None,
        action: str,
        check_version: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Run a PDAL subprocess under the shared execution contract.

        Args:
            cmd: Full command line
            input_text: Optional text piped to stdin
            action: Action name used in error messages
            check_version: Run the one-time PDAL version floor check first

        Returns:
            Completed process (returncode is not checked here)

        Raises:
            PDALExecutionError: If the subprocess times out
            PDALNotFoundError: If the executable cannot be started
        """
        if check_version:
            config.check_pdal_version()

        logger.debug("Executing PDAL command: %s", " ".join(cmd))
        try:
            return subprocess.run(
                cmd,
                input=input_text,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                creationflags=_SUBPROCESS_FLAGS,
                timeout=config.timeout,
            )
        except subprocess.TimeoutExpired as e:
            raise PDALExecutionError(
                f"PDAL {action} timed out after {e.timeout} seconds",
                stdout=_text(e.output),
                stderr=_text(e.stderr),
                command=cmd,
            ) from e
        except OSError as e:
            raise PDALNotFoundError(f"Failed to run PDAL executable: {e}") from e

    def _run_pipeline(
        self,
        pipeline_json: str | dict[str, Any],
        extra_args: list[str],
        *,
        action: str,
    ) -> subprocess.CompletedProcess[str]:
        """Run `pdal pipeline --stdin` with the pipeline JSON piped to stdin."""
        if isinstance(pipeline_json, dict):
            pipeline_json = json.dumps(pipeline_json, indent=2)
        cmd = [str(config.pdal_path), "pipeline", "--stdin", *extra_args]
        logger.debug("Pipeline JSON:\n%s", pipeline_json)
        return self._run(cmd, input_text=pipeline_json, action=action)

    def execute_pipeline(
        self,
        pipeline_json: str | dict[str, Any],
        stream_mode: bool | None = None,
        metadata: bool = True,
    ) -> tuple[str, str, int, dict[str, Any] | None]:
        """Execute PDAL pipeline.

        Args:
            pipeline_json: Pipeline JSON string or dict
            stream_mode: Force stream mode (True), standard mode (False), or auto (None)
            metadata: Include metadata in output

        Returns:
            Tuple of (stdout, stderr, returncode, metadata_dict)

        Raises:
            PDALExecutionError: If pipeline execution fails or times out
            PDALNotFoundError: If the PDAL executable cannot be started
        """
        extra_args: list[str] = []

        # Add stream mode flags
        if stream_mode is True:
            extra_args.append("--stream")
        elif stream_mode is False:
            extra_args.append("--nostream")

        # Add metadata output
        metadata_file: Path | None = None
        if metadata:
            with tempfile.NamedTemporaryFile(suffix=".metadata.json", delete=False) as f:
                metadata_file = Path(f.name)
            extra_args.extend(["--metadata", str(metadata_file)])

        # Add verbose flag
        if self.verbose:
            extra_args.extend(["--verbose", "8"])

        try:
            result = self._run_pipeline(pipeline_json, extra_args, action="pipeline execution")

            # Read metadata if generated
            metadata_dict: dict[str, Any] | None = None
            if metadata_file and metadata_file.exists() and metadata_file.stat().st_size > 0:
                try:
                    with metadata_file.open(encoding="utf-8") as f:
                        metadata_dict = json.load(f)
                except (OSError, ValueError) as e:
                    logger.warning(f"Failed to read metadata: {e}")

            # Check for errors
            if result.returncode != 0:
                raise PDALExecutionError(
                    "PDAL pipeline execution failed",
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    command=cast("list[str]", result.args),
                )

            logger.info(f"Pipeline executed successfully (return code: {result.returncode})")
            return result.stdout, result.stderr, result.returncode, metadata_dict

        finally:
            # Cleanup temporary files
            try:
                if metadata_file and metadata_file.exists():
                    metadata_file.unlink()
            except OSError as e:
                logger.warning(f"Failed to cleanup temporary files: {e}")

    def execute_application(
        self,
        app_name: str,
        args: list[str],
        input_file: str | Path | None = None,
    ) -> tuple[str, str, int]:
        """Execute PDAL application.

        Args:
            app_name: Application name (e.g., 'info', 'translate')
            args: Application arguments
            input_file: Optional input file path

        Returns:
            Tuple of (stdout, stderr, returncode)

        Raises:
            PDALExecutionError: If application execution fails or times out
            PDALNotFoundError: If the PDAL executable cannot be started
        """
        # Build command
        cmd = [str(config.pdal_path), app_name]

        # Add input file if provided
        if input_file:
            cmd.append(str(input_file))

        # Add arguments
        cmd.extend(args)

        # Add verbose flag
        if self.verbose:
            cmd.extend(["--verbose", "8"])

        result = self._run(cmd, action=f"{app_name} execution")

        # Check for errors
        if result.returncode != 0:
            raise PDALExecutionError(
                f"PDAL {app_name} execution failed",
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                command=cmd,
            )

        logger.info(f"Application '{app_name}' executed successfully")
        return result.stdout, result.stderr, result.returncode

    def validate_pipeline(self, pipeline_json: str | dict[str, Any]) -> tuple[bool, bool, str]:
        """Validate pipeline without executing.

        Note: `pdal pipeline --validate` always exits 0 and reports the verdict
        in its JSON output, so the result is parsed from stdout.

        Args:
            pipeline_json: Pipeline JSON string or dict

        Returns:
            Tuple of (is_valid, is_streamable, message)

        Raises:
            PDALExecutionError: If the validation command fails or its output
                cannot be parsed
            PDALNotFoundError: If the PDAL executable cannot be started
        """
        result = self._run_pipeline(pipeline_json, ["--validate"], action="pipeline validation")
        cmd = cast("list[str]", result.args)

        if result.returncode != 0:
            raise PDALExecutionError(
                "PDAL pipeline validation failed",
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                command=cmd,
            )

        try:
            body = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise PDALExecutionError(
                f"Failed to parse validation output: {e}",
                stdout=result.stdout,
                stderr=result.stderr,
                command=cmd,
            ) from e

        if not isinstance(body, dict):
            raise PDALExecutionError(
                "Unexpected validation output (not a JSON object)",
                stdout=result.stdout,
                command=cmd,
            )

        is_valid = bool(body.get("valid", False))
        is_streamable = bool(body.get("streamable", False))
        message = str(body.get("error_detail", ""))

        logger.info(f"Pipeline validation: valid={is_valid}, streamable={is_streamable}")
        return is_valid, is_streamable, message

    def get_driver_info(self, driver_name: str) -> dict[str, Any]:
        """Get information about a PDAL driver.

        Args:
            driver_name: Driver name (e.g., 'readers.las', 'filters.range')

        Returns:
            Dictionary with 'driver' (name) and 'options' (list of option
            dicts with 'name', 'description' and optional 'default')

        Raises:
            PDALExecutionError: If command fails or output cannot be parsed
            PDALNotFoundError: If the PDAL executable cannot be started
        """
        cmd = [str(config.pdal_path), "--options", driver_name, "--showjson"]

        result = self._run(cmd, action=f"driver info for {driver_name}")

        if result.returncode != 0:
            raise PDALExecutionError(
                f"Failed to get driver info for {driver_name}",
                returncode=result.returncode,
                stderr=result.stderr,
                command=cmd,
            )

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise PDALExecutionError(
                f"Failed to parse driver info: {e}",
                stdout=result.stdout,
                command=cmd,
            ) from e

        # PDAL 2.10 emits ["<driver>", [{name, description, default?}, ...]]
        if isinstance(data, list) and len(data) == 2 and isinstance(data[1], list):
            return {"driver": data[0], "options": data[1]}
        if isinstance(data, dict):
            return cast("dict[str, Any]", data)
        raise PDALExecutionError(
            f"Unexpected driver info output for {driver_name}",
            stdout=result.stdout,
            command=cmd,
        )


# Global executor instance
executor = Executor()
