"""Unit tests for translate application argument construction."""

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


class TestTranslateOptions:
    """PDAL stage options retain their exact canonical names."""

    def test_canonical_underscored_options(self, captured_app: dict[str, Any]) -> None:
        pdal.translate(
            "input.las",
            "output.las",
            stage_options={
                "writers.las.offset_x": "auto",
                "writers.las.scale_x": 0.001,
                "writers.las.minor_version": 4,
                "writers.las.dataformat_id": 7,
                "writers.las.a_srs": "EPSG:5650",
            },
        )

        assert captured_app["app"] == "translate"
        assert captured_app["args"] == [
            "input.las",
            "output.las",
            "--writers.las.offset_x=auto",
            "--writers.las.scale_x=0.001",
            "--writers.las.minor_version=4",
            "--writers.las.dataformat_id=7",
            "--writers.las.a_srs=EPSG:5650",
        ]

    def test_legacy_single_word_option_remains_supported(
        self, captured_app: dict[str, Any]
    ) -> None:
        pdal.translate(
            "input.las",
            "output.las",
            filters=["range"],
            filters_range_limits="Classification[2:2]",
        )

        assert captured_app["args"][-1] == "--filters.range.limits=Classification[2:2]"

    def test_dims_application_option(self, captured_app: dict[str, Any]) -> None:
        pdal.translate(
            "input.las",
            "output.las",
            dims="X,Y,Z,Classification",
        )

        assert captured_app["args"] == [
            "input.las",
            "output.las",
            "--dims=X,Y,Z,Classification",
        ]

    def test_ambiguous_legacy_option_is_rejected(self, captured_app: dict[str, Any]) -> None:
        with pytest.raises(ValueError, match="stage_options"):
            pdal.translate("input.las", "output.las", writers_las_offset_x="auto")

        assert captured_app == {}

    @pytest.mark.parametrize(
        "option_name",
        ["writers.las", "writers..offset_x", ".las.offset_x", "writers.las.offset.x"],
    )
    def test_malformed_canonical_option_is_rejected(
        self, captured_app: dict[str, Any], option_name: str
    ) -> None:
        with pytest.raises(ValueError, match=r"stage\.driver\.option"):
            pdal.translate(
                "input.las",
                "output.las",
                stage_options={option_name: "auto"},
            )

        assert captured_app == {}

    def test_duplicate_legacy_and_canonical_option_is_rejected(
        self, captured_app: dict[str, Any]
    ) -> None:
        with pytest.raises(ValueError, match="specified more than once"):
            pdal.translate(
                "input.las",
                "output.las",
                stage_options={"writers.las.forward": "all"},
                writers_las_forward="none",
            )

        assert captured_app == {}

    def test_convert_forwards_canonical_options(self, captured_app: dict[str, Any]) -> None:
        pdal.convert(
            "input.las",
            "output.las",
            stage_options={"writers.las.offset_x": "auto"},
        )

        assert captured_app["args"][-1] == "--writers.las.offset_x=auto"

    def test_convert_forwards_dims(self, captured_app: dict[str, Any]) -> None:
        pdal.convert("input.las", "output.las", dims="X,Y,Z")

        assert captured_app["args"][-1] == "--dims=X,Y,Z"
