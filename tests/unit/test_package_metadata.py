"""Unit tests for the package version contract."""

from __future__ import annotations

import importlib
import importlib.metadata

import pytest

import exeqpdal

SOURCE_TREE_SENTINEL = "0.0.0.dev0"


class TestVersion:
    """`__version__` mirrors the installed distribution metadata."""

    def test_version_matches_installed_metadata(self) -> None:
        try:
            expected = importlib.metadata.version("exeqpdal")
        except importlib.metadata.PackageNotFoundError:
            pytest.skip("exeqpdal is not installed; __version__ uses the source-tree sentinel")

        assert exeqpdal.__version__ == expected

    def test_missing_metadata_falls_back_to_sentinel(self, monkeypatch: pytest.MonkeyPatch) -> None:
        original = exeqpdal.__version__

        def raise_not_found(distribution_name: str) -> str:
            raise importlib.metadata.PackageNotFoundError(distribution_name)

        monkeypatch.setattr(importlib.metadata, "version", raise_not_found)
        try:
            assert importlib.reload(exeqpdal).__version__ == SOURCE_TREE_SENTINEL
        finally:
            monkeypatch.undo()
            importlib.reload(exeqpdal)

        assert exeqpdal.__version__ == original
