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
