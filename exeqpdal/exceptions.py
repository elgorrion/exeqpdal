"""Custom exceptions for exeqpdal package."""

from __future__ import annotations


class PDALError(Exception):
    """Base exception for all PDAL-related errors."""

    pass


class PDALNotFoundError(PDALError):
    """Raised when PDAL binary cannot be found in system."""

    def __init__(
        self, message: str = "PDAL executable not found in PATH or QGIS installation"
    ) -> None:
        super().__init__(message)
        self.message = message


class PDALExecutionError(PDALError):
    """Raised when PDAL command execution fails."""

    def __init__(
        self,
        message: str,
        returncode: int | None = None,
        stdout: str | None = None,
        stderr: str | None = None,
        command: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.command = command

    def __str__(self) -> str:
        parts = [self.message]
        if self.returncode is not None:
            parts.append(f"Return code: {self.returncode}")
        if self.stderr:
            parts.append(f"STDERR: {self.stderr}")
        return "\n".join(parts)


# Windows reports a crashed pdal.exe as an NTSTATUS code, which subprocess
# hands over as a large unsigned or a negative return code.
_NTSTATUS_NAMES = {
    0xC0000005: "access violation",
    0xC00000FD: "stack overflow",
    0xC0000135: "DLL not found",
    0xC0000409: "fast-fail / stack buffer overrun",
}


def describe_returncode(returncode: int) -> str:
    """Return code line; a Windows NTSTATUS code names the crash."""
    if returncode < 0 or returncode > 0x7FFFFFFF:
        status = returncode & 0xFFFFFFFF
        name = _NTSTATUS_NAMES.get(status, "NTSTATUS")
        return f"Return code: {returncode} (pdal.exe crashed: {name} (0x{status:08X}))"
    return f"Return code: {returncode}"


class PipelineError(PDALError):
    """Raised when pipeline configuration, validation, or execution fails.

    An execution failure carries the return code, output, command line, and
    pipeline JSON of the PDAL run; ``str()`` prints them after the message.
    """

    def __init__(
        self,
        message: str,
        *,
        returncode: int | None = None,
        stdout: str | None = None,
        stderr: str | None = None,
        command: list[str] | None = None,
        pipeline_json: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.command = command
        self.pipeline_json = pipeline_json

    def __str__(self) -> str:
        parts = [self.message]
        if self.returncode is not None:
            parts.append(describe_returncode(self.returncode))
        if self.stdout:
            parts.append(f"STDOUT: {self.stdout}")
        if self.stderr:
            parts.append(f"STDERR: {self.stderr}")
        if self.command:
            parts.append(f"Command: {' '.join(self.command)}")
        if self.pipeline_json:
            parts.append(f"Pipeline: {self.pipeline_json}")
        return "\n".join(parts)


class StageError(PDALError):
    """Raised when stage configuration is invalid."""

    pass


class ValidationError(PDALError):
    """Raised when pipeline validation fails."""

    pass


class DimensionError(PDALError):
    """Raised when dimension access or configuration fails."""

    pass


class MetadataError(PDALError):
    """Raised when metadata parsing or access fails."""

    pass


class ConfigurationError(PDALError):
    """Raised when configuration is invalid."""

    pass
