"""Shared test fixtures for exeqpdal tests."""

from __future__ import annotations

from pathlib import Path

import pytest

# LAZ test data constants
LAZ_DIR = Path("/home/vona/QGIS_Projects/LAS_Sources")

# File mapping
LAZ_SMALL = LAZ_DIR / "785_5351.laz"
LAZ_MEDIUM = LAZ_DIR / "785_5350.laz"
LAZ_LARGE = LAZ_DIR / "786_5348.laz"
LAZ_DUAL_1 = LAZ_DIR / "786_5349.laz"
LAZ_DUAL_2 = LAZ_DIR / "786_5350.laz"


@pytest.fixture
def skip_if_no_pdal() -> None:
    """Skip test if PDAL CLI not available."""
    try:
        from exeqpdal.core.config import config

        _ = config.pdal_path
    except Exception:
        pytest.skip("PDAL CLI not available")


@pytest.fixture
def small_laz() -> Path:
    """Small LAZ file for quick tests (~55MB, ~8M points).

    File: 785_5351.laz
    Use for: Basic execution tests, quick validation
    """
    if not LAZ_SMALL.exists():
        pytest.skip(f"Test file not found: {LAZ_SMALL}")
    return LAZ_SMALL


@pytest.fixture
def medium_laz() -> Path:
    """Medium LAZ file for moderate tests (~85MB, ~13M points).

    File: 785_5350.laz
    Use for: Filter tests, moderate complexity
    """
    if not LAZ_MEDIUM.exists():
        pytest.skip(f"Test file not found: {LAZ_MEDIUM}")
    return LAZ_MEDIUM


@pytest.fixture
def large_laz() -> Path:
    """Large LAZ file for performance tests (~144MB, ~23M points).

    File: 786_5348.laz
    Use for: Performance tests, streaming validation
    """
    if not LAZ_LARGE.exists():
        pytest.skip(f"Test file not found: {LAZ_LARGE}")
    return LAZ_LARGE


@pytest.fixture
def dual_laz() -> list[Path]:
    """Two LAZ files for merge/batch tests.

    Files: 786_5349.laz (~49MB), 786_5350.laz (~50MB)
    Use for: Merge tests, batch operations
    """
    files = [LAZ_DUAL_1, LAZ_DUAL_2]
    missing = [f for f in files if not f.exists()]
    if missing:
        pytest.skip(f"Test files not found: {', '.join(str(f) for f in missing)}")
    return files


@pytest.fixture
def pdal_version() -> str:
    """Get PDAL version string.

    Raises:
        pytest.skip: If PDAL not available
    """
    try:
        from exeqpdal.core.config import config

        return config.get_pdal_version()
    except Exception:
        pytest.skip("PDAL CLI not available")
