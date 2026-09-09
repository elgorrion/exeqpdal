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

import exeqpdal as pdal
from exeqpdal.apps import pipeline as pipeline_app
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
    """Pipeline execution and validation retain their documented error contracts."""

    def test_execute_preserves_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def raise_not_found(*args: Any, **kwargs: Any) -> None:
            raise PDALNotFoundError("PDAL executable not found")

        monkeypatch.setattr(executor, "execute_pipeline", raise_not_found)
        pipeline = Pipeline(PIPELINE_JSON)

        with pytest.raises(PDALNotFoundError, match="PDAL executable not found"):
            pipeline.execute()

    def test_validate_preserves_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def raise_not_found(*args: Any, **kwargs: Any) -> None:
            raise PDALNotFoundError("PDAL executable not found")

        monkeypatch.setattr(executor, "validate_pipeline", raise_not_found)
        pipeline = Pipeline(PIPELINE_JSON)

        with pytest.raises(PDALNotFoundError, match="PDAL executable not found"):
            pipeline.validate()

    def test_is_streamable_preserves_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def raise_not_found(*args: Any, **kwargs: Any) -> None:
            raise PDALNotFoundError("PDAL executable not found")

        monkeypatch.setattr(executor, "validate_pipeline", raise_not_found)
        pipeline = Pipeline(PIPELINE_JSON)

        with pytest.raises(PDALNotFoundError, match="PDAL executable not found"):
            _ = pipeline.is_streamable

    def test_validate_wraps_execution_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def raise_execution_error(*args: Any, **kwargs: Any) -> None:
            raise PDALExecutionError("PDAL pipeline validation failed", returncode=1)

        monkeypatch.setattr(executor, "validate_pipeline", raise_execution_error)
        pipeline = Pipeline(PIPELINE_JSON)

        with pytest.raises(ValidationError) as exc_info:
            pipeline.validate()
        assert isinstance(exc_info.value.__cause__, PDALExecutionError)

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


PUBLIC_CALLS = [
    ("merge", lambda: pdal.merge(["input.las"], "output.las")),
    ("translate", lambda: pdal.translate("input.las", "output.las")),
    ("convert", lambda: pdal.convert("input.las", "output.las")),
    ("sort", lambda: pdal.sort("input.las", "output.las")),
    ("split", lambda: pdal.split("input.las", "output_#.las")),
    ("tile", lambda: pdal.tile("input.las", "output_#.las")),
    ("tindex", lambda: pdal.tindex(["input.las"], "index.json")),
    ("pipeline", lambda: pipeline_app("pipeline.json")),
    ("info", lambda: pdal.info("input.las")),
    ("get_bounds", lambda: pdal.get_bounds("input.las")),
    ("get_count", lambda: pdal.get_count("input.las")),
    ("get_dimensions", lambda: pdal.get_dimensions("input.las")),
    ("get_srs", lambda: pdal.get_srs("input.las")),
    ("get_stats", lambda: pdal.get_stats("input.las")),
    ("Pipeline.execute", lambda: Pipeline(PIPELINE_JSON).execute()),
]


@pytest.mark.usefixtures("quiet_config")
@pytest.mark.parametrize("name, call", PUBLIC_CALLS, ids=[name for name, _ in PUBLIC_CALLS])
class TestPublicExecutionErrors:
    @pytest.mark.parametrize(
        "stderr, expected_detail",
        [
            ("earlier line\n  coordinate overflow  \n\n ", ": coordinate overflow"),
            (
                "PDAL: previous diagnostic\nPDAL: filters.range: Invalid range expression 'bad'\n"
                "\n(pdal translate Error)\n",
                ": PDAL: filters.range: Invalid range expression 'bad'",
            ),
            (
                "PDAL: filters.range: " + "x" * 250 + " END\n(pdal translate Error)\n",
                ": PDAL: filters.range: " + "x" * 179,
            ),
            ("input.laz: " + "x" * 250 + " END\n", ": input.laz: " + "x" * 189),
            ("", ""),
            (" \n\t", ""),
            (None, ""),
        ],
    )
    def test_failure_includes_bounded_tail(
        self,
        monkeypatch: pytest.MonkeyPatch,
        name: str,
        call: Any,
        stderr: str | None,
        expected_detail: str,
    ) -> None:
        def fail(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(args[0], 1, stdout="partial output", stderr=stderr)

        monkeypatch.setattr(subprocess, "run", fail)
        with pytest.raises(PipelineError) as caught:
            call()
        cause = caught.value.__cause__
        assert isinstance(cause, PDALExecutionError)
        assert cause.stderr == stderr
        assert cause.stdout == "partial output"
        assert cause.returncode == 1
        assert cause.command
        assert str(caught.value) == cause.message + expected_detail
        assert "(pdal translate Error)" not in str(caught.value)
        assert "END" not in str(caught.value)

    def test_missing_executable_stays_distinct(
        self, monkeypatch: pytest.MonkeyPatch, name: str, call: Any
    ) -> None:
        def missing(*args: Any, **kwargs: Any) -> None:
            raise FileNotFoundError("missing PDAL")

        monkeypatch.setattr(subprocess, "run", missing)
        with pytest.raises(PDALNotFoundError, match="missing PDAL"):
            call()

    def test_timeout_includes_stderr(
        self, monkeypatch: pytest.MonkeyPatch, name: str, call: Any
    ) -> None:
        def timeout(*args: Any, **kwargs: Any) -> None:
            raise subprocess.TimeoutExpired(args[0], 5, stderr=b"timeout detail")

        monkeypatch.setattr(subprocess, "run", timeout)
        with pytest.raises(PipelineError, match="timeout detail") as caught:
            call()
        assert isinstance(caught.value.__cause__, PDALExecutionError)


@pytest.mark.usefixtures("quiet_config")
def test_info_invalid_json_uses_pipeline_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(
            a[0], 0, stdout="not JSON", stderr="parser detail\n"
        ),
    )
    with pytest.raises(PipelineError, match="parser detail") as caught:
        pdal.info("input.las")
    cause = caught.value.__cause__
    assert isinstance(cause, PDALExecutionError)
    assert cause.stdout == "not JSON"
    assert isinstance(cause.__cause__, ValueError)
