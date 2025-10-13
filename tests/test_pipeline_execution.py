"""Integration tests for Pipeline execution with real PDAL CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import exeqpdal as pdal
from exeqpdal import Pipeline
from exeqpdal.exceptions import PipelineError


class TestPipelineRealExecution:
    """Test Pipeline.execute() with real PDAL CLI."""

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_execute_simple(self, small_laz: Path, tmp_path: Path) -> None:
        """Test basic pipeline execution."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)))

        point_count = pipeline.execute()

        assert point_count > 0
        assert output.exists()
        assert pipeline._executed is True

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_execute_returns_count(self, small_laz: Path, tmp_path: Path) -> None:
        """Test pipeline execution returns correct point count."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)))

        point_count = pipeline.execute()

        assert isinstance(point_count, int)
        assert point_count > 0
        assert point_count == pipeline._point_count

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_execute_with_metadata(self, small_laz: Path, tmp_path: Path) -> None:
        """Test accessing metadata after execution."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)))

        pipeline.execute()

        metadata = pipeline.metadata
        assert metadata is not None
        assert isinstance(metadata, dict)
        assert "stages" in metadata or len(metadata) > 0

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_execute_multi_stage(self, small_laz: Path, tmp_path: Path) -> None:
        """Test execution of multi-stage pipeline (3+ stages)."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "filtered.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(small_laz))
            | pdal.Filter.range(limits="Classification[2:2]")
            | pdal.Filter.crop(bounds="([785000,786000],[5351000,5352000])")
            | pdal.Writer.las(str(output))
        )

        point_count = pipeline.execute()

        assert point_count > 0
        assert output.exists()

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_validate_before_execute(self, small_laz: Path, tmp_path: Path) -> None:
        """Test validating pipeline before execution."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(small_laz))
            | pdal.Filter.range(limits="Z[0:400]")
            | pdal.Writer.las(str(output))
        )

        is_valid = pipeline.validate()
        assert is_valid is True

        point_count = pipeline.execute()
        assert point_count >= 0

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_arrays_not_loaded(self, small_laz: Path, tmp_path: Path) -> None:
        """Test that arrays are not loaded by default."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)))

        pipeline.execute()

        arrays = pipeline.arrays
        assert isinstance(arrays, list)
        assert len(arrays) == 0

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_streaming_enabled(self, small_laz: Path, tmp_path: Path) -> None:
        """Test pipeline execution with streaming mode enabled."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)), stream_mode=True
        )

        point_count = pipeline.execute()

        assert point_count > 0
        assert output.exists()

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_to_json(self, small_laz: Path, tmp_path: Path) -> None:
        """Test pipeline JSON generation."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)))

        pipeline_json = pipeline.pipeline_json
        assert isinstance(pipeline_json, str)
        assert len(pipeline_json) > 0

        parsed = json.loads(pipeline_json)
        assert "pipeline" in parsed
        assert isinstance(parsed["pipeline"], list)
        assert len(parsed["pipeline"]) == 2

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_with_filter_chain(self, small_laz: Path, tmp_path: Path) -> None:
        """Test pipeline with multiple filters chained."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "filtered.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(small_laz))
            | pdal.Filter.range(limits="Classification[2:2]")
            | pdal.Filter.crop(bounds="([785000,785500],[5351000,5351500])")
            | pdal.Filter.sort(dimension="Z")
            | pdal.Writer.las(str(output))
        )

        point_count = pipeline.execute()

        assert point_count > 0
        assert output.exists()

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_execution_error(self, tmp_path: Path) -> None:
        """Test pipeline execution with invalid input file raises error."""
        pipeline = Pipeline(
            pdal.Reader.las("/nonexistent/file.laz") | pdal.Writer.las(str(tmp_path / "out.las"))
        )

        with pytest.raises(PipelineError) as exc_info:
            pipeline.execute()

        assert "Pipeline execution failed" in str(exc_info.value)

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_invalid_json_error(self) -> None:
        """Test pipeline creation with invalid JSON raises error."""
        with pytest.raises(PipelineError) as exc_info:
            Pipeline('{"invalid": json syntax')

        assert "Invalid JSON pipeline" in str(exc_info.value)

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_parse_metadata_count(self, small_laz: Path, tmp_path: Path) -> None:
        """Test _parse_metadata_count() extracts point count from metadata."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)))

        point_count = pipeline.execute()

        assert point_count > 0
        metadata = pipeline.metadata
        assert metadata is not None

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_with_multiple_outputs(self, small_laz: Path, tmp_path: Path) -> None:
        """Test pipeline with multiple writer outputs."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output1 = tmp_path / "output1.las"
        output2 = tmp_path / "output2.laz"

        reader = pdal.Reader.las(str(small_laz))
        filter_stage = pdal.Filter.range(limits="Classification[2:2]")

        pipeline_json = {
            "pipeline": [
                reader.to_dict(),
                filter_stage.to_dict(),
                pdal.Writer.las(str(output1)).to_dict(),
                pdal.Writer.las(str(output2), compression="laszip").to_dict(),
            ]
        }

        pipeline = Pipeline(pipeline_json)
        point_count = pipeline.execute()

        assert point_count > 0
        assert output1.exists()
        assert output2.exists()

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_quick_info(self, small_laz: Path) -> None:
        """Test pipeline quick info (metadata only, no output files)."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        pipeline_json = {
            "pipeline": [
                {"type": "readers.las", "filename": str(small_laz)},
                {"type": "filters.head", "count": 100},
            ]
        }

        pipeline = Pipeline(pipeline_json)
        point_count = pipeline.execute()

        assert point_count >= 0
        metadata = pipeline.metadata
        assert metadata is not None

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_execute_cleanup(self, small_laz: Path, tmp_path: Path) -> None:
        """Test that temporary files are cleaned up after execution."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)))

        initial_temp_files = list(Path("/tmp").glob("tmp*.json"))
        initial_count = len(initial_temp_files)

        pipeline.execute()

        final_temp_files = list(Path("/tmp").glob("tmp*.json"))
        final_count = len(final_temp_files)

        assert final_count <= initial_count + 1


class TestPipelineValidation:
    """Test Pipeline validation methods."""

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_validate_valid_pipeline(self, small_laz: Path, tmp_path: Path) -> None:
        """Test validation of valid pipeline returns True."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(small_laz))
            | pdal.Filter.range(limits="Z[0:400]")
            | pdal.Writer.las(str(output))
        )

        is_valid = pipeline.validate()
        assert is_valid is True
        assert pipeline._is_valid is True

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_validate_sets_streamable_flag(self, small_laz: Path, tmp_path: Path) -> None:
        """Test validation sets is_streamable flag."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(small_laz))
            | pdal.Filter.range(limits="Z[0:400]")
            | pdal.Writer.las(str(output))
        )

        pipeline.validate()

        assert pipeline._is_streamable is not None
        assert isinstance(pipeline._is_streamable, bool)

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_is_streamable_property(self, small_laz: Path, tmp_path: Path) -> None:
        """Test is_streamable property triggers validation."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(small_laz))
            | pdal.Filter.range(limits="Z[0:400]")
            | pdal.Writer.las(str(output))
        )

        is_streamable = pipeline.is_streamable
        assert isinstance(is_streamable, bool)
        assert pipeline._is_streamable is not None


class TestPipelineProperties:
    """Test Pipeline property accessors."""

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_metadata_property_before_execute_raises(self, small_laz: Path, tmp_path: Path) -> None:
        """Test accessing metadata before execution raises error."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)))

        with pytest.raises(PipelineError) as exc_info:
            _ = pipeline.metadata

        assert "must be executed" in str(exc_info.value).lower()

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_log_property_before_execute_raises(self, small_laz: Path, tmp_path: Path) -> None:
        """Test accessing log before execution raises error."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)))

        with pytest.raises(PipelineError) as exc_info:
            _ = pipeline.log

        assert "must be executed" in str(exc_info.value).lower()

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_arrays_property_before_execute_raises(self, small_laz: Path, tmp_path: Path) -> None:
        """Test accessing arrays before execution raises error."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)))

        with pytest.raises(PipelineError) as exc_info:
            _ = pipeline.arrays

        assert "must be executed" in str(exc_info.value).lower()

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_json_property_accessible(self, small_laz: Path, tmp_path: Path) -> None:
        """Test pipeline_json property accessible before execution."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)))

        pipeline_json = pipeline.pipeline_json
        assert isinstance(pipeline_json, str)
        assert len(pipeline_json) > 0

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_repr(self, small_laz: Path, tmp_path: Path) -> None:
        """Test Pipeline __repr__ method."""
        if not small_laz.exists():
            pytest.skip(f"LAZ file not found: {small_laz}")

        output = tmp_path / "output.las"

        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)))

        repr_str = repr(pipeline)
        assert "Pipeline" in repr_str
        assert "not executed" in repr_str

        pipeline.execute()

        repr_str = repr(pipeline)
        assert "executed" in repr_str
        assert "points" in repr_str
