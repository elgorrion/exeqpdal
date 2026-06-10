"""Unit tests for the subprocess execution contract and output parsers.

Fixture JSON strings are captured from a real PDAL 2.10.1 run
(see specs/0.1.0b1-plan/code-review-PR1-findings.md).
"""

from __future__ import annotations

import importlib
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from exeqpdal.core.config import config
from exeqpdal.core.executor import Executor, executor
from exeqpdal.core.pipeline import Pipeline
from exeqpdal.exceptions import (
    MetadataError,
    PDALExecutionError,
    PDALNotFoundError,
    PipelineError,
    ValidationError,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

# the `info` submodule is shadowed by the function of the same name in exeqpdal.apps
info_module = importlib.import_module("exeqpdal.apps.info")

VALIDATE_INVALID = (
    '{"error_detail": "Pipeline does not start with a reader.",'
    ' "streamable": false, "valid": false}'
)
VALIDATE_GARBAGE_INPUT = (
    '{"error_detail": "STDIN: Pipeline: parse error at line 1, column 2",'
    ' "streamable": false, "valid": false}'
)
VALIDATE_VALID_NONSTREAM = '{"error_detail": "", "streamable": false, "valid": true}'
VALIDATE_VALID_STREAM = '{"error_detail": "", "streamable": true, "valid": true}'
DRIVER_OPTIONS = (
    '["readers.las",[{"description":"Name of file to read","name":"filename"},'
    '{"default":"18446744073709551615","description":"Maximum number of points read",'
    '"name":"count"}]]'
)
PIPELINE_JSON = '{"pipeline": [{"type": "readers.las", "filename": "in.las"}]}'


@pytest.fixture
def quiet_config(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Point config at a fake PDAL and disarm the version floor check."""
    monkeypatch.setattr(config, "_pdal_path", Path("/fake/pdal"))
    monkeypatch.setattr(config, "_version_checked", True)
    monkeypatch.setattr(config, "_pdal_version", "pdal 2.10.1 (git-version: 3ef768)")
    monkeypatch.setattr(config, "_timeout", None)
    yield


def completed(stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["/fake/pdal"], returncode=returncode, stdout=stdout, stderr=""
    )


@pytest.mark.usefixtures("quiet_config")
class TestRunContract:
    """Executor._run owns timeout, encoding, and launch-failure conversion."""

    def test_timeout_maps_to_execution_error_with_partial_output(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def raise_timeout(*args: Any, **kwargs: Any) -> None:
            raise subprocess.TimeoutExpired(
                cmd=["/fake/pdal"], timeout=5, output=b"partial out", stderr=b"partial err"
            )

        monkeypatch.setattr(subprocess, "run", raise_timeout)

        with pytest.raises(PDALExecutionError, match="timed out after 5") as exc_info:
            Executor()._run(["/fake/pdal", "pipeline"], action="pipeline execution")

        assert exc_info.value.stdout == "partial out"
        assert exc_info.value.stderr == "partial err"

    def test_permission_error_maps_to_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def raise_permission(*args: Any, **kwargs: Any) -> None:
            raise PermissionError("denied")

        monkeypatch.setattr(subprocess, "run", raise_permission)

        with pytest.raises(PDALNotFoundError, match="denied"):
            Executor()._run(["/fake/pdal"], action="test")

    def test_file_not_found_maps_to_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def raise_missing(*args: Any, **kwargs: Any) -> None:
            raise FileNotFoundError("/fake/pdal")

        monkeypatch.setattr(subprocess, "run", raise_missing)

        with pytest.raises(PDALNotFoundError):
            Executor()._run(["/fake/pdal"], action="test")

    def test_run_passes_timeout_and_utf8(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: dict[str, Any] = {}

        def record(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
            captured.update(kwargs)
            return completed()

        monkeypatch.setattr(subprocess, "run", record)
        monkeypatch.setattr(config, "_timeout", 42.0)

        Executor()._run(["/fake/pdal"], action="test")

        assert captured["timeout"] == 42.0
        assert captured["encoding"] == "utf-8"
        assert captured["errors"] == "replace"

    def test_version_check_fires_through_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[bool] = []
        monkeypatch.setattr(config, "check_pdal_version", lambda: calls.append(True))
        monkeypatch.setattr(subprocess, "run", lambda *a, **k: completed())

        Executor()._run(["/fake/pdal"], action="test")
        assert calls == [True]

        Executor()._run(["/fake/pdal"], action="test", check_version=False)
        assert calls == [True]

    def test_verbose_follows_config_live(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(config, "_verbose", False)
        assert executor.verbose is False
        monkeypatch.setattr(config, "_verbose", True)
        assert executor.verbose is True


@pytest.mark.usefixtures("quiet_config")
class TestValidateParsing:
    """validate_pipeline parses the --validate JSON body, not exit codes."""

    def patch_run(self, monkeypatch: pytest.MonkeyPatch, stdout: str, returncode: int = 0) -> None:
        monkeypatch.setattr(
            Executor,
            "_run",
            lambda self, cmd, **kwargs: completed(stdout=stdout, returncode=returncode),
        )

    def test_invalid_pipeline_reported(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.patch_run(monkeypatch, VALIDATE_INVALID)
        is_valid, is_streamable, message = executor.validate_pipeline(PIPELINE_JSON)
        assert is_valid is False
        assert is_streamable is False
        assert "does not start with a reader" in message

    def test_garbage_input_reported_invalid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.patch_run(monkeypatch, VALIDATE_GARBAGE_INPUT)
        is_valid, _, message = executor.validate_pipeline("not json")
        assert is_valid is False
        assert "parse error" in message

    def test_valid_non_streamable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.patch_run(monkeypatch, VALIDATE_VALID_NONSTREAM)
        is_valid, is_streamable, message = executor.validate_pipeline(PIPELINE_JSON)
        assert is_valid is True
        assert is_streamable is False
        assert message == ""

    def test_valid_streamable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.patch_run(monkeypatch, VALIDATE_VALID_STREAM)
        assert executor.validate_pipeline(PIPELINE_JSON) == (True, True, "")

    def test_unparseable_output_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.patch_run(monkeypatch, "PDAL crashed before JSON")
        with pytest.raises(PDALExecutionError, match="parse"):
            executor.validate_pipeline(PIPELINE_JSON)

    def test_nonzero_returncode_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.patch_run(monkeypatch, "", returncode=1)
        with pytest.raises(PDALExecutionError, match="validation failed"):
            executor.validate_pipeline(PIPELINE_JSON)


@pytest.mark.usefixtures("quiet_config")
class TestDriverInfoParsing:
    """get_driver_info parses `pdal --options <driver> --showjson` output."""

    def test_options_array_parsed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            Executor, "_run", lambda self, cmd, **kwargs: completed(stdout=DRIVER_OPTIONS)
        )
        result = executor.get_driver_info("readers.las")
        assert result["driver"] == "readers.las"
        names = {opt["name"] for opt in result["options"]}
        assert names == {"filename", "count"}

    def test_unparseable_output_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            Executor, "_run", lambda self, cmd, **kwargs: completed(stdout="not json")
        )
        with pytest.raises(PDALExecutionError, match="parse"):
            executor.get_driver_info("readers.las")

    def test_nonzero_returncode_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(Executor, "_run", lambda self, cmd, **kwargs: completed(returncode=1))
        with pytest.raises(PDALExecutionError, match=r"readers\.las"):
            executor.get_driver_info("readers.las")


class TestInfoParsers:
    """get_count and get_bounds read pdal info --summary output."""

    def patch_info(self, monkeypatch: pytest.MonkeyPatch, payload: dict[str, Any]) -> None:
        monkeypatch.setattr(info_module, "info", lambda *args, **kwargs: payload)

    def test_get_count(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.patch_info(monkeypatch, {"summary": {"num_points": 1000}})
        assert info_module.get_count("file.las") == 1000

    def test_get_count_missing_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.patch_info(monkeypatch, {"summary": {}})
        with pytest.raises(MetadataError, match="point count"):
            info_module.get_count("file.las")

    def test_get_bounds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        bounds = {"minx": 0.0, "miny": 1.0, "minz": 2.0, "maxx": 3.0, "maxy": 4.0, "maxz": 5.0}
        self.patch_info(monkeypatch, {"summary": {"bounds": bounds}})
        assert info_module.get_bounds("file.las") == bounds

    def test_get_bounds_missing_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.patch_info(monkeypatch, {"summary": {}})
        with pytest.raises(MetadataError, match="bounds"):
            info_module.get_bounds("file.las")


@pytest.mark.usefixtures("quiet_config")
class TestPipelineExceptionWrapping:
    """Pipeline.execute()/validate() wrap any PDALError per their docstrings."""

    def test_execute_wraps_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def raise_not_found(*args: Any, **kwargs: Any) -> None:
            raise PDALNotFoundError("PDAL executable not found")

        monkeypatch.setattr(executor, "execute_pipeline", raise_not_found)
        pipeline = Pipeline(PIPELINE_JSON)

        with pytest.raises(PipelineError) as exc_info:
            pipeline.execute()
        assert isinstance(exc_info.value.__cause__, PDALNotFoundError)

    def test_validate_wraps_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def raise_not_found(*args: Any, **kwargs: Any) -> None:
            raise PDALNotFoundError("PDAL executable not found")

        monkeypatch.setattr(executor, "validate_pipeline", raise_not_found)
        pipeline = Pipeline(PIPELINE_JSON)

        with pytest.raises(ValidationError) as exc_info:
            pipeline.validate()
        assert isinstance(exc_info.value.__cause__, PDALNotFoundError)

    def test_validate_raises_on_invalid_verdict(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            executor,
            "validate_pipeline",
            lambda *a, **k: (False, False, "Pipeline does not start with a reader."),
        )
        pipeline = Pipeline(PIPELINE_JSON)

        with pytest.raises(ValidationError, match="does not start with a reader"):
            pipeline.validate()

    def test_is_streamable_reflects_verdict(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(executor, "validate_pipeline", lambda *a, **k: (True, False, ""))
        pipeline = Pipeline(PIPELINE_JSON)

        assert pipeline.validate() is True
        assert pipeline.is_streamable is False
