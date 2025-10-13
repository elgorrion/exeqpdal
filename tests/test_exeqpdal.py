"""Tests for exeqpdal package."""

from __future__ import annotations

from pathlib import Path

import pytest

import exeqpdal as pdal
from exeqpdal.core.config import Config
from exeqpdal.exceptions import (
    ConfigurationError,
    PipelineError,
    StageError,
)
from exeqpdal.stages.base import FilterStage, ReaderStage, WriterStage


class TestConfig:
    """Tests for configuration management."""

    def test_config_singleton(self) -> None:
        """Test that config is a singleton."""
        assert pdal.config is pdal.config

    def test_set_pdal_path_valid(self, tmp_path: Path) -> None:
        """Test setting valid PDAL path."""
        # Create dummy executable
        pdal_exe = tmp_path / "pdal"
        pdal_exe.touch()
        pdal_exe.chmod(0o755)

        config = Config()
        config.set_pdal_path(pdal_exe)
        assert config._pdal_path == pdal_exe

    def test_set_pdal_path_nonexistent(self) -> None:
        """Test setting nonexistent PDAL path."""
        config = Config()
        with pytest.raises(ConfigurationError, match="not found"):
            config.set_pdal_path("/nonexistent/path/to/pdal")

    def test_verbose_setting(self) -> None:
        """Test verbose mode setting."""
        config = Config()
        assert not config.verbose

        config.set_verbose(True)
        assert config.verbose

        config.set_verbose(False)
        assert not config.verbose


class TestStages:
    """Tests for stage classes."""

    def test_reader_stage_creation(self) -> None:
        """Test creating reader stage."""
        reader = ReaderStage("readers.las", filename="input.las")
        assert reader.stage_type == "readers.las"
        assert reader.filename == "input.las"

    def test_filter_stage_creation(self) -> None:
        """Test creating filter stage."""
        filter_stage = FilterStage("filters.range", limits="Classification[2:2]")
        assert filter_stage.stage_type == "filters.range"
        assert filter_stage.options["limits"] == "Classification[2:2]"

    def test_writer_stage_creation(self) -> None:
        """Test creating writer stage."""
        writer = WriterStage("writers.las", filename="output.las", compression="laszip")
        assert writer.stage_type == "writers.las"
        assert writer.filename == "output.las"
        assert writer.options["compression"] == "laszip"

    def test_stage_to_dict(self) -> None:
        """Test converting stage to dictionary."""
        reader = ReaderStage("readers.las", filename="input.las", tag="reader")
        stage_dict = reader.to_dict()

        assert stage_dict["type"] == "readers.las"
        assert stage_dict["filename"] == "input.las"
        assert stage_dict["tag"] == "reader"

    def test_stage_pipe_operator(self) -> None:
        """Test piping stages together."""
        reader = pdal.Reader.las("input.las")
        filter_stage = pdal.Filter.range(limits="Classification[2:2]")
        writer = pdal.Writer.las("output.las")

        pipeline = reader | filter_stage | writer

        # Final stage should be writer
        assert pipeline.stage_type == "writers.las"
        # Writer should have filter as input
        assert len(pipeline.inputs) > 0

    def test_stage_pipe_invalid_type(self) -> None:
        """Test piping with invalid type."""
        reader = pdal.Reader.las("input.las")

        with pytest.raises(StageError, match="Cannot pipe"):
            _ = reader | "invalid"  # type: ignore


class TestReaders:
    """Tests for reader factory."""

    def test_reader_las(self) -> None:
        """Test LAS reader creation."""
        reader = pdal.Reader.las("input.las")
        assert reader.stage_type == "readers.las"
        assert reader.filename == "input.las"

    def test_reader_copc(self) -> None:
        """Test COPC reader creation."""
        reader = pdal.Reader.copc("input.copc.laz")
        assert reader.stage_type == "readers.copc"

    def test_reader_text(self) -> None:
        """Test text reader creation."""
        reader = pdal.Reader.text("input.txt")
        assert reader.stage_type == "readers.text"

    def test_reader_with_options(self) -> None:
        """Test reader with options."""
        reader = pdal.Reader.las("input.las", spatialreference="EPSG:4326")
        assert reader.options["spatialreference"] == "EPSG:4326"


class TestFilters:
    """Tests for filter factory."""

    def test_filter_range(self) -> None:
        """Test range filter creation."""
        filter_stage = pdal.Filter.range(limits="Classification[2:2]")
        assert filter_stage.stage_type == "filters.range"
        assert filter_stage.options["limits"] == "Classification[2:2]"

    def test_filter_outlier(self) -> None:
        """Test outlier filter creation."""
        filter_stage = pdal.Filter.outlier(method="statistical", mean_k=8, multiplier=2.0)
        assert filter_stage.stage_type == "filters.outlier"
        assert filter_stage.options["method"] == "statistical"

    def test_filter_smrf(self) -> None:
        """Test SMRF ground filter creation."""
        filter_stage = pdal.Filter.smrf()
        assert filter_stage.stage_type == "filters.smrf"

    def test_filter_reprojection(self) -> None:
        """Test reprojection filter creation."""
        filter_stage = pdal.Filter.reprojection(
            in_srs="EPSG:4326",
            out_srs="EPSG:3857",
        )
        assert filter_stage.stage_type == "filters.reprojection"


class TestWriters:
    """Tests for writer factory."""

    def test_writer_las(self) -> None:
        """Test LAS writer creation."""
        writer = pdal.Writer.las("output.las")
        assert writer.stage_type == "writers.las"
        assert writer.filename == "output.las"

    def test_writer_copc(self) -> None:
        """Test COPC writer creation."""
        writer = pdal.Writer.copc("output.copc.laz")
        assert writer.stage_type == "writers.copc"

    def test_writer_with_compression(self) -> None:
        """Test writer with compression."""
        writer = pdal.Writer.las("output.laz", compression="laszip")
        assert writer.options["compression"] == "laszip"


class TestPipeline:
    """Tests for Pipeline class."""

    def test_pipeline_from_json_string(self) -> None:
        """Test creating pipeline from JSON string."""
        json_str = """
        {
            "pipeline": [
                "input.las",
                {
                    "type": "filters.range",
                    "limits": "Classification[2:2]"
                },
                "output.las"
            ]
        }
        """
        pipeline = pdal.Pipeline(json_str)
        assert pipeline._pipeline_dict["pipeline"] is not None

    def test_pipeline_from_dict(self) -> None:
        """Test creating pipeline from dictionary."""
        pipeline_dict = {
            "pipeline": [
                {"type": "readers.las", "filename": "input.las"},
                {"type": "filters.range", "limits": "Classification[2:2]"},
                {"type": "writers.las", "filename": "output.las"},
            ]
        }
        pipeline = pdal.Pipeline(pipeline_dict)
        assert "pipeline" in pipeline._pipeline_dict

    def test_pipeline_from_stages(self) -> None:
        """Test creating pipeline from stage objects."""
        final_stage = (
            pdal.Reader.las("input.las")
            | pdal.Filter.range(limits="Classification[2:2]")
            | pdal.Writer.las("output.las")
        )
        pipeline = pdal.Pipeline(final_stage)
        assert pipeline._pipeline_dict["pipeline"] is not None

    def test_pipeline_invalid_type(self) -> None:
        """Test creating pipeline with invalid type."""
        with pytest.raises(PipelineError, match="Invalid pipeline type"):
            pdal.Pipeline(123)  # type: ignore

    def test_pipeline_json_property(self) -> None:
        """Test pipeline JSON property."""
        pipeline_dict = {
            "pipeline": [
                {"type": "readers.las", "filename": "input.las"},
            ]
        }
        pipeline = pdal.Pipeline(pipeline_dict)
        json_str = pipeline.pipeline_json
        assert "readers.las" in json_str


class TestDimensions:
    """Tests for dimension definitions."""

    def test_dimension_constants(self) -> None:
        """Test dimension constants."""
        assert pdal.Dimension.X == "X"
        assert pdal.Dimension.Y == "Y"
        assert pdal.Dimension.Z == "Z"
        assert pdal.Dimension.CLASSIFICATION == "Classification"

    def test_dimension_types(self) -> None:
        """Test dimension type mappings."""
        assert pdal.DIMENSION_TYPES[pdal.Dimension.X] == pdal.DataType.DOUBLE
        assert pdal.DIMENSION_TYPES[pdal.Dimension.INTENSITY] == pdal.DataType.UINT16
        assert pdal.DIMENSION_TYPES[pdal.Dimension.CLASSIFICATION] == pdal.DataType.UINT8

    def test_classification_codes(self) -> None:
        """Test classification codes."""
        assert pdal.Classification.GROUND == 2
        assert pdal.Classification.LOW_VEGETATION == 3
        assert pdal.Classification.BUILDING == 6


class TestExceptions:
    """Tests for custom exceptions."""

    def test_pdal_error(self) -> None:
        """Test base PDAL error."""
        with pytest.raises(pdal.PDALError):
            raise pdal.PDALError("Test error")

    def test_pdal_not_found_error(self) -> None:
        """Test PDAL not found error."""
        with pytest.raises(pdal.PDALNotFoundError):
            raise pdal.PDALNotFoundError()

    def test_pdal_execution_error(self) -> None:
        """Test PDAL execution error."""
        error = pdal.PDALExecutionError(
            "Execution failed",
            returncode=1,
            stderr="Error output",
        )
        assert error.returncode == 1
        assert "Error output" in str(error)

    def test_pipeline_error(self) -> None:
        """Test pipeline error."""
        with pytest.raises(pdal.PipelineError):
            raise pdal.PipelineError("Pipeline failed")


class TestIntegration:
    """Integration tests (require PDAL installed)."""

    def test_stage_chaining(self) -> None:
        """Test complete stage chaining."""
        pipeline = (
            pdal.Reader.las("input.las")
            | pdal.Filter.range(limits="Classification[2:2]")
            | pdal.Filter.outlier(method="statistical", mean_k=8)
            | pdal.Writer.las("output.las", compression="laszip")
        )

        # Check pipeline structure
        assert pipeline.stage_type == "writers.las"
        assert pipeline.filename == "output.las"

    def test_complex_pipeline(self) -> None:
        """Test complex pipeline with multiple filters."""
        pipeline = (
            pdal.Reader.las("input.las")
            | pdal.Filter.range(limits="Classification[2:2]")
            | pdal.Filter.hag_nn()
            | pdal.Filter.ferry(dimensions="HeightAboveGround=HAG")
            | pdal.Filter.range(limits="HAG[0:50]")
            | pdal.Writer.las("output.las")
        )

        # Verify pipeline can be serialized
        json_str = pdal.Pipeline(pipeline).pipeline_json
        assert "filters.range" in json_str
        assert "filters.hag_nn" in json_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
