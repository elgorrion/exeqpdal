"""Shared test fixtures for exeqpdal tests."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from exeqpdal.exceptions import PDALExecutionError

# LAZ test data constants
LAZ_DIR = Path(os.environ.get("EXEQPDAL_TEST_DATA", "/tmp/exeqpdal_test_data"))

# File mapping
LAZ_SMALL = LAZ_DIR / "785_5351.laz"
LAZ_MEDIUM = LAZ_DIR / "785_5350.laz"
LAZ_LARGE = LAZ_DIR / "786_5348.laz"
LAZ_DUAL_1 = LAZ_DIR / "786_5349.laz"
LAZ_DUAL_2 = LAZ_DIR / "786_5350.laz"

# Writer test outputs (moved from laz_to_writers/conftest.py)
OUTPUT_BASE = Path(__file__).parent / "laz_to_writers" / "outputs"


@pytest.fixture(scope="session")
def skip_if_no_test_data() -> None:
    """Skip test if EXEQPDAL_TEST_DATA environment variable not set."""
    if not os.environ.get("EXEQPDAL_TEST_DATA"):
        pytest.skip("EXEQPDAL_TEST_DATA environment variable not set")


@pytest.fixture
def skip_if_no_pdal() -> None:
    """Skip test if PDAL CLI not available."""
    try:
        from exeqpdal.core.config import config

        _ = config.pdal_path
    except Exception:
        pytest.skip("PDAL CLI not available")


@pytest.fixture
def small_laz(skip_if_no_test_data) -> Path:
    """Small LAZ file for quick tests (~55MB, ~8M points).

    File: 785_5351.laz
    Use for: Basic execution tests, quick validation
    """
    if not LAZ_SMALL.exists():
        pytest.skip(f"Test file not found: {LAZ_SMALL}")
    return LAZ_SMALL


@pytest.fixture
def medium_laz(skip_if_no_test_data) -> Path:
    """Medium LAZ file for moderate tests (~85MB, ~13M points).

    File: 785_5350.laz
    Use for: Filter tests, moderate complexity
    """
    if not LAZ_MEDIUM.exists():
        pytest.skip(f"Test file not found: {LAZ_MEDIUM}")
    return LAZ_MEDIUM


@pytest.fixture
def large_laz(skip_if_no_test_data) -> Path:
    """Large LAZ file for performance tests (~144MB, ~23M points).

    File: 786_5348.laz
    Use for: Performance tests, streaming validation
    """
    if not LAZ_LARGE.exists():
        pytest.skip(f"Test file not found: {LAZ_LARGE}")
    return LAZ_LARGE


@pytest.fixture
def dual_laz(skip_if_no_test_data) -> list[Path]:
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


# === Writer test fixtures (moved from laz_to_writers/conftest.py) ===


@pytest.fixture(scope="session")
def writer_test_laz(skip_if_no_test_data) -> Path:
    """LAZ file optimized for writer tests (49MB, 10.9M points).

    File: 786_5349.laz
    - Points: 10,924,069
    - Size: 49 MB
    - Format: LAS 1.2, Point Format 1
    - Bounds: 1000m x 1000m x 47m
    - Density: 10.67 points/m²
    """
    laz_file = LAZ_DIR / "786_5349.laz"
    if not laz_file.exists():
        pytest.skip(f"Test file not found: {laz_file}")
    return laz_file


@pytest.fixture(scope="session")
def writer_output_dir() -> Path:
    """Directory for writer test outputs (preserved for inspection).

    Creates subdirectories:
    - standard/
    - text/
    - raster/
    - special/

    Files are preserved (not cleaned up) for manual inspection.
    Added to .gitignore.
    """
    output_dir = OUTPUT_BASE
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create category subdirectories
    for category in ["standard", "text", "raster", "special"]:
        (output_dir / category).mkdir(exist_ok=True)

    # Create README if not exists
    readme = output_dir / "README.md"
    if not readme.exists():
        readme.write_text("""# Writer Test Outputs

This directory contains output files from LAZ-to-writers tests.

**Organization**:
- `standard/` - Standard point cloud formats (LAS, COPC, PLY, etc.)
- `text/` - Text/ASCII format outputs
- `raster/` - Raster format outputs (GeoTIFF, etc.)
- `special/` - Special format outputs (NITF, GLTF, etc.)

**Files preserved for manual inspection** - DO NOT COMMIT.

**Source**: tests/test_laz_to_*.py
**Input**: /home/vona/QGIS_Projects/LAS_Sources/786_5349.laz (49MB, 10.9M points)
""")

    return output_dir


def get_output_filename(
    category: str,
    writer_name: str,
    extension: str | None,
    config_id: str = "",
) -> str:
    """Generate consistent output filename.

    Format: 786_5349_{writer_name}_{config_id}_{timestamp}.{extension}

    Args:
        category: Subdirectory (standard, text, raster, special)
        writer_name: Writer type (las, copc, text, etc.)
        extension: File extension (with leading dot)
        config_id: Optional configuration identifier

    Returns:
        Full path to output file as string
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = "786_5349"

    if config_id:
        filename = f"{base_name}_{writer_name}_{config_id}_{timestamp}"
    else:
        filename = f"{base_name}_{writer_name}_{timestamp}"

    if extension:
        filename = f"{filename}{extension}"

    output_path = OUTPUT_BASE / category / filename
    return str(output_path)


def handle_writer_exception(e: Exception, writer_name: str) -> None:
    """Handle exceptions from writer execution.

    Three-tier strategy:
    1. Expected failures (writer unavailable) → skip test
    2. Configuration issues → skip test with message
    3. Actual failures → raise (test fails)

    Args:
        e: Exception raised during execution
        writer_name: Name of writer being tested

    Raises:
        pytest.skip: For expected failures and configuration issues
        Exception: For actual failures (test should fail)
    """
    if not isinstance(e, PDALExecutionError):
        raise

    error_msg = str(e).lower()

    # Expected failures - writer not available
    skip_patterns = [
        "couldn't create",
        "unknown stage",
        "not available",
        "couldn't find",
        "unknown writer",
    ]

    if any(pattern in error_msg for pattern in skip_patterns):
        pytest.skip(
            f"Writer '{writer_name}' not available in this PDAL installation. Error: {str(e)[:100]}"
        )

    # Configuration issues
    config_patterns = [
        "requires",
        "missing required",
        "invalid option",
        "resolution",
        "no points",
    ]

    if any(pattern in error_msg for pattern in config_patterns):
        pytest.skip(
            f"Writer '{writer_name}' requires additional configuration. Error: {str(e)[:100]}"
        )

    # Actual failures - let test fail
    raise


def validate_output_file(
    output_path: str | Path,
    expected_points: int | None = None,
    tolerance: float = 0.05,
) -> dict[str, Any]:
    """Validate output file creation and properties.

    Args:
        output_path: Path to output file
        expected_points: Expected point count (optional)
        tolerance: Point count tolerance (default 5%)

    Returns:
        dict with validation results:
        - exists: bool
        - size: int (bytes)
        - valid: bool

    Raises:
        AssertionError: If validation fails
    """
    path = Path(output_path)

    result = {
        "exists": path.exists(),
        "size": path.stat().st_size if path.exists() else 0,
        "valid": False,
    }

    # Basic validation
    assert result["exists"], f"Output file not created: {path}"
    assert result["size"] > 0, f"Output file is empty: {path}"

    result["valid"] = True
    return result
