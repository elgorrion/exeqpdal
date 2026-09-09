"""Unit tests for pipeline application wrappers (mocked executor)."""

from __future__ import annotations

import struct
from typing import TYPE_CHECKING, Any

import pytest

import exeqpdal as pdal
from exeqpdal.apps.pipeline_apps import _las_header_options
from exeqpdal.core.executor import executor
from exeqpdal.exceptions import MetadataError

if TYPE_CHECKING:
    from pathlib import Path


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


@pytest.fixture
def header_source(tmp_path: Path) -> Path:
    """Write a LAS 1.2 file with one point and distinct scales and offsets."""
    header = bytearray(227)
    header[:4] = b"LASF"
    header[24:26] = bytes((1, 2))
    struct.pack_into("<HII", header, 94, 227, 227, 0)
    struct.pack_into("<BHI", header, 104, 0, 20, 1)
    struct.pack_into("<5I", header, 111, 1, 0, 0, 0, 0)
    struct.pack_into("<3d", header, 131, 0.001, 0.012345678901234567, 0.1)
    struct.pack_into("<3d", header, 155, 33000000.125, -5350000.25, 400.5)
    struct.pack_into(
        "<6d", header, 179, 33000000.125, 33000000.125, -5350000.25, -5350000.25, 400.5, 400.5
    )
    point = struct.pack("<iiiHBBbBH", 0, 0, 0, 0, 9, 0, 0, 0, 0)
    source = tmp_path / "source.las"
    source.write_bytes(header + point)
    return source


class TestMergeHeader:
    @pytest.mark.parametrize("extension", [".las", ".laz"])
    def test_parser_reads_header_fields(self, header_source: Path, extension: str) -> None:
        source = header_source.with_suffix(extension)
        source.write_bytes(header_source.read_bytes())
        assert _las_header_options(str(source)) == {
            "writers.las.scale_x": 0.001,
            "writers.las.scale_y": 0.012345678901234567,
            "writers.las.scale_z": 0.1,
            "writers.las.offset_x": 33000000.125,
            "writers.las.offset_y": -5350000.25,
            "writers.las.offset_z": 400.5,
        }

    def test_merge_preserves_all_six_doubles(
        self, captured_app: dict[str, Any], header_source: Path
    ) -> None:
        pdal.merge(["input.las"], "output.laz", header_from=header_source)
        options = dict(arg[2:].split("=", 1) for arg in captured_app["args"][2:])
        values = [
            float(options[f"writers.las.{kind}_{axis}"])
            for kind in ("scale", "offset")
            for axis in "xyz"
        ]
        assert struct.pack("<6d", *values) == header_source.read_bytes()[131:179]

    def test_caller_overrides_header(
        self, captured_app: dict[str, Any], header_source: Path
    ) -> None:
        pdal.merge(
            ["input.las"],
            "output.las",
            header_from=header_source,
            stage_options={"writers.las.scale_x": 0.5, "writers.las.offset_z": "auto"},
        )
        args = captured_app["args"]
        assert "--writers.las.scale_x=0.5" in args
        assert "--writers.las.offset_z=auto" in args
        assert "--writers.las.offset_x=33000000.125" in args
        assert len(args) == 8

    @pytest.mark.parametrize("output", ["output.copc.laz", "output.COPC.LAZ", "output.bpf"])
    def test_other_outputs_ignore_header(self, captured_app: dict[str, Any], output: str) -> None:
        pdal.merge(["input.las"], output, header_from="missing.las")
        assert captured_app["args"] == ["input.las", output]

    @pytest.mark.parametrize(
        "content, message",
        [
            (b"NOPE" + bytes(223), "Invalid LAS signature"),
            (b"", "Truncated LAS header"),
            (b"LASF" + bytes(174), "Truncated LAS header"),
            (b"LASF" + bytes(175), "Truncated LAS header"),
            (b"LASF" + bytes(222), "Truncated LAS header"),
        ],
    )
    def test_invalid_header_prevents_execution(
        self, captured_app: dict[str, Any], tmp_path: Path, content: bytes, message: str
    ) -> None:
        source = tmp_path / "bad.las"
        source.write_bytes(content)
        with pytest.raises(MetadataError, match=message):
            _las_header_options(source)
        with pytest.raises(MetadataError, match=message):
            pdal.merge(["input.las"], "output.las", header_from=source)
        assert captured_app == {}

    def test_minimum_header_length(self, header_source: Path) -> None:
        header_source.write_bytes(header_source.read_bytes()[:227])
        assert _las_header_options(header_source)["writers.las.scale_x"] == 0.001

    @pytest.mark.parametrize("axis, position", [("x", 131), ("y", 139), ("z", 147)])
    @pytest.mark.parametrize("value", [0.0, -0.01, float("nan"), float("inf"), float("-inf")])
    def test_invalid_scale_prevents_execution(
        self,
        captured_app: dict[str, Any],
        header_source: Path,
        axis: str,
        position: int,
        value: float,
    ) -> None:
        content = bytearray(header_source.read_bytes())
        struct.pack_into("<d", content, position, value)
        header_source.write_bytes(content)
        with pytest.raises(MetadataError) as caught:
            pdal.merge(["input.las"], "output.las", header_from=header_source)
        assert f"Invalid LAS scale_{axis}" in str(caught.value)
        assert f": {value}" in str(caught.value)
        assert captured_app == {}

    @pytest.mark.parametrize("axis, position", [("x", 155), ("y", 163), ("z", 171)])
    @pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
    def test_nonfinite_offset_prevents_execution(
        self,
        captured_app: dict[str, Any],
        header_source: Path,
        axis: str,
        position: int,
        value: float,
    ) -> None:
        content = bytearray(header_source.read_bytes())
        struct.pack_into("<d", content, position, value)
        header_source.write_bytes(content)
        with pytest.raises(MetadataError) as caught:
            pdal.merge(["input.las"], "output.las", header_from=header_source)
        assert f"Invalid LAS offset_{axis}" in str(caught.value)
        assert f": {value}" in str(caught.value)
        assert captured_app == {}
