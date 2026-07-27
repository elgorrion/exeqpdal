"""Unit tests for pipeline application wrappers (mocked executor)."""

from __future__ import annotations

from typing import Any

import pytest

import exeqpdal as pdal
from exeqpdal.core.executor import executor


@pytest.fixture
def captured_app(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Capture executor.execute_application calls instead of running PDAL."""
    calls: dict[str, Any] = {}

    def fake(app_name: str, args: list[str], input_file: Any = None) -> tuple[str, str, int]:
        calls["app"] = app_name
        calls["args"] = args
        return ("", "", 0)

    monkeypatch.setattr(executor, "execute_application", fake)
    return calls


class TestSortApp:
    """Argument construction for the `pdal sort` wrapper."""

    def test_sort_basic(self, captured_app: dict[str, Any]) -> None:
        pdal.sort("input.las", "output.las")
        assert captured_app["app"] == "sort"
        assert captured_app["args"] == ["input.las", "output.las"]

    def test_sort_with_flags(self, captured_app: dict[str, Any]) -> None:
        pdal.sort("input.las", "output.laz", compress=True, metadata=True)
        assert captured_app["args"] == ["input.las", "output.laz", "--compress", "--metadata"]

    def test_sort_accepts_paths(self, captured_app: dict[str, Any], tmp_path: Any) -> None:
        pdal.sort(tmp_path / "in.las", tmp_path / "out.las")
        assert captured_app["args"] == [str(tmp_path / "in.las"), str(tmp_path / "out.las")]


class TestMergeApp:
    """Argument construction for the `pdal merge` wrapper."""

    def test_las_uses_automatic_offsets(self, captured_app: dict[str, Any]) -> None:
        pdal.merge(["one.las", "two.las"], "output.las")

        assert captured_app["app"] == "merge"
        assert captured_app["args"] == [
            "one.las",
            "two.las",
            "output.las",
            "--writers.las.offset_x=auto",
            "--writers.las.offset_y=auto",
            "--writers.las.offset_z=auto",
        ]

    def test_laz_detection_is_case_insensitive(self, captured_app: dict[str, Any]) -> None:
        pdal.merge(["one.las", "two.las"], "output.LAZ")

        assert captured_app["args"][-3:] == [
            "--writers.las.offset_x=auto",
            "--writers.las.offset_y=auto",
            "--writers.las.offset_z=auto",
        ]

    @pytest.mark.parametrize("output", ["output.bpf", "output.copc.laz"])
    def test_non_las_writers_get_no_las_defaults(
        self, captured_app: dict[str, Any], output: str
    ) -> None:
        pdal.merge(["one.las", "two.las"], output)

        assert captured_app["args"] == ["one.las", "two.las", output]

    def test_caller_options_override_defaults(self, captured_app: dict[str, Any]) -> None:
        pdal.merge(
            ["one.las", "two.las"],
            "output.las",
            stage_options={
                "writers.las.offset_x": 33_000_000,
                "writers.las.scale_x": 0.001,
            },
        )

        assert captured_app["args"] == [
            "one.las",
            "two.las",
            "output.las",
            "--writers.las.offset_x=33000000",
            "--writers.las.offset_y=auto",
            "--writers.las.offset_z=auto",
            "--writers.las.scale_x=0.001",
        ]

    def test_explicit_options_pass_through_for_other_writers(
        self, captured_app: dict[str, Any]
    ) -> None:
        pdal.merge(
            ["one.las", "two.las"],
            "output.bpf",
            stage_options={"writers.bpf.compression": True},
        )

        assert captured_app["args"] == [
            "one.las",
            "two.las",
            "output.bpf",
            "--writers.bpf.compression=True",
        ]
