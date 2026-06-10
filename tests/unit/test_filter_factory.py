"""Unit tests for Filter factory wrappers."""

from __future__ import annotations

import exeqpdal as pdal


class TestFilterFactory:
    """Smoke tests for representative filter factories."""

    def test_filter_range(self) -> None:
        filter_stage = pdal.Filter.range(limits="Classification[2:2]")
        assert filter_stage.stage_type == "filters.range"
        assert filter_stage.options["limits"] == "Classification[2:2]"

    def test_filter_outlier(self) -> None:
        filter_stage = pdal.Filter.outlier(method="statistical", mean_k=8, multiplier=2.0)
        assert filter_stage.stage_type == "filters.outlier"
        assert filter_stage.options["method"] == "statistical"

    def test_filter_smrf(self) -> None:
        filter_stage = pdal.Filter.smrf()
        assert filter_stage.stage_type == "filters.smrf"

    def test_filter_reprojection(self) -> None:
        filter_stage = pdal.Filter.reprojection(
            in_srs="EPSG:4326",
            out_srs="EPSG:3857",
        )
        assert filter_stage.stage_type == "filters.reprojection"

    def test_filter_streamcallback(self) -> None:
        filter_stage = pdal.Filter.streamcallback(where="Classification[2:2]")
        assert filter_stage.stage_type == "filters.streamcallback"
        assert filter_stage.options["where"] == "Classification[2:2]"

    def test_filter_m3c2(self) -> None:
        filter_stage = pdal.Filter.m3c2(searchradius=2.0)
        assert filter_stage.stage_type == "filters.m3c2"
        assert filter_stage.options["searchradius"] == 2.0

    def test_filter_supervoxel(self) -> None:
        filter_stage = pdal.Filter.supervoxel()
        assert filter_stage.stage_type == "filters.supervoxel"

    def test_filter_shell(self) -> None:
        filter_stage = pdal.Filter.shell(command="echo done")
        assert filter_stage.stage_type == "filters.shell"
        assert filter_stage.options["command"] == "echo done"

    def test_filter_griddecimation_camelcase_stage_type(self) -> None:
        """PDAL 2.10 only accepts the camelCase registered name."""
        filter_stage = pdal.Filter.griddecimation(resolution=1.0)
        assert filter_stage.stage_type == "filters.gridDecimation"
