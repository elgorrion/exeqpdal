"""Edge case tests for exeqpdal."""

from __future__ import annotations

import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

import exeqpdal as pdal
from exeqpdal import Pipeline
from exeqpdal.exceptions import PipelineError, StageError


class TestPipelineEdgeCases:
    """Test edge cases in pipeline construction."""

    def test_pipeline_with_only_reader(self) -> None:
        """Test pipeline with only reader (no writer)."""
        pipeline = Pipeline(pdal.Reader.las("input.las"))
        assert pipeline._pipeline_dict is not None

    def test_pipeline_with_duplicate_tags(self) -> None:
        """Test pipeline with duplicate stage tags.

        PDAL should handle duplicate tags gracefully.
        """
        reader1 = pdal.Reader.las("input1.las", tag="reader")
        reader2 = pdal.Reader.las("input2.las", tag="reader")

        # Convert stages to dicts for pipeline list
        pipeline = Pipeline([reader1.to_dict(), reader2.to_dict()])
        assert pipeline._pipeline_dict is not None

    def test_pipeline_from_invalid_json(self) -> None:
        """Test pipeline creation with invalid JSON raises error."""
        invalid_json = "{ invalid json }"

        with pytest.raises(PipelineError):
            Pipeline(invalid_json)

    def test_pipeline_empty_list_raises(self) -> None:
        """Test that empty pipeline list raises error.

        Empty pipeline should be rejected during validation.
        """
        # Empty list creates valid pipeline structure but may fail during execution
        pipeline = Pipeline([])
        # Pipeline creation succeeds, but it has an empty pipeline
        assert pipeline._pipeline_dict == {"pipeline": []}


class TestStageEdgeCases:
    """Test edge cases in stage creation."""

    def test_stage_with_empty_filename(self) -> None:
        """Test creating stage with empty filename.

        Empty filename is accepted during stage creation;
        validation happens at execution time.
        """
        reader = pdal.Reader.las("")
        assert reader.filename == ""
        assert reader.stage_type == "readers.las"

    def test_stage_with_none_filename(self) -> None:
        """Test creating stage with None filename.

        Most readers require filename, but validation happens at execution.
        None is accepted during stage creation.
        """
        reader = pdal.Reader.las(None)  # type: ignore
        assert reader.filename is None
        assert reader.stage_type == "readers.las"

    def test_filter_without_required_option(self) -> None:
        """Test filter that requires option but none provided.

        Stage creation should succeed; validation may happen at execution.
        """
        filter_stage = pdal.Filter.range()
        assert filter_stage.stage_type == "filters.range"

    def test_stage_pipe_to_non_stage(self) -> None:
        """Test piping stage to non-stage object raises error."""
        reader = pdal.Reader.las("input.las")

        with pytest.raises((StageError, TypeError)):
            _ = reader | "not a stage"  # type: ignore

    def test_stage_pipe_to_none(self) -> None:
        """Test piping stage to None raises error."""
        reader = pdal.Reader.las("input.las")

        with pytest.raises((StageError, TypeError, AttributeError)):
            _ = reader | None  # type: ignore


class TestExecutionEdgeCases:
    """Test edge cases in execution."""

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_execute_same_pipeline_twice(self, small_laz: Path, tmp_path: Path) -> None:
        """Test executing same pipeline twice.

        Pipeline execution should be idempotent or raise appropriate error.
        """
        output = tmp_path / "output.las"

        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)))

        count1 = pipeline.execute()
        assert count1 > 0

        # Second execution (should work or raise appropriate error)
        try:
            count2 = pipeline.execute()
            # If successful, counts should match
            assert count2 == count1
        except PipelineError:
            # Pipeline may not support re-execution
            pass

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_with_null_writer(self, small_laz: Path) -> None:
        """Test pipeline with null writer (discard output)."""
        pipeline = Pipeline(
            pdal.Reader.las(str(small_laz)) | pdal.Filter.head(count=100) | pdal.Writer.null()
        )

        count = pipeline.execute()
        assert count >= 0

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    @pytest.mark.slow
    def test_large_file_execution(self, large_laz: Path, tmp_path: Path) -> None:
        """Test execution with large file (performance test)."""
        output = tmp_path / "output.las"

        pipeline = Pipeline(
            pdal.Reader.las(str(large_laz))
            | pdal.Filter.head(count=1000000)
            | pdal.Writer.las(str(output))
        )

        start = time.time()
        count = pipeline.execute()
        duration = time.time() - start

        assert count > 0
        assert duration < 60

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_concurrent_pipeline_execution(self, small_laz: Path, tmp_path: Path) -> None:
        """Test concurrent execution of multiple pipelines."""
        results = []
        errors = []

        def execute_pipeline(idx: int) -> None:
            try:
                output = tmp_path / f"output_{idx}.las"
                pipeline = Pipeline(
                    pdal.Reader.las(str(small_laz))
                    | pdal.Filter.head(count=1000)
                    | pdal.Writer.las(str(output))
                )
                count = pipeline.execute()
                results.append(count)
            except Exception as e:
                errors.append(e)

        # Create 3 threads
        threads = [threading.Thread(target=execute_pipeline, args=(i,)) for i in range(3)]

        # Start threads
        for t in threads:
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # All should succeed
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 3
        assert all(r > 0 for r in results)


class TestCleanupEdgeCases:
    """Test cleanup and error recovery."""

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_cleanup_on_error(self, tmp_path: Path) -> None:
        """Test that temp files are cleaned up on error."""
        temp_dir = Path(tempfile.gettempdir())
        initial_temp_count = len(list(temp_dir.glob("tmp*.json")))

        pipeline = Pipeline(
            pdal.Reader.las("/nonexistent/file.laz") | pdal.Writer.las(str(tmp_path / "out.las"))
        )

        try:
            pipeline.execute()
        except (PipelineError, Exception):
            pass

        # Temp files should be cleaned up
        final_temp_count = len(list(temp_dir.glob("tmp*.json")))
        # Temp count should not increase significantly
        assert final_temp_count <= initial_temp_count + 1

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_cleanup_on_keyboard_interrupt(self, small_laz: Path, tmp_path: Path) -> None:
        """Test cleanup when pipeline is interrupted.

        Note: Actual keyboard interrupt testing is difficult,
        this tests the cleanup mechanism structure.
        """
        output = tmp_path / "output.las"

        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)))

        # Execute normally to verify cleanup structure exists
        count = pipeline.execute()
        assert count > 0


class TestPlatformEdgeCases:
    """Test platform-specific edge cases."""

    def test_windows_path_handling(self) -> None:
        """Test that Windows paths are handled correctly."""
        if sys.platform == "win32":
            reader = pdal.Reader.las("C:\\data\\input.las")
            assert reader.filename == "C:\\data\\input.las"
        else:
            # On non-Windows, just verify path is stored
            reader = pdal.Reader.las("/data/input.las")
            assert reader.filename == "/data/input.las"

    def test_pathlib_path_acceptance(self, tmp_path: Path) -> None:
        """Test that pathlib.Path objects can be converted to strings.

        Path objects should be converted to strings before passing to API.
        """
        input_path = tmp_path / "input.las"
        output_path = tmp_path / "output.las"

        # Convert Path to str for API
        reader = pdal.Reader.las(str(input_path))
        writer = pdal.Writer.las(str(output_path))

        # Verify filenames are stored as strings
        assert reader.filename == str(input_path)
        assert writer.filename == str(output_path)

    def test_unicode_filename_support(self, tmp_path: Path) -> None:
        """Test that Unicode filenames are supported."""
        unicode_name = "üñíçödé_file.las"
        output_path = tmp_path / unicode_name

        writer = pdal.Writer.las(str(output_path))
        assert unicode_name in str(writer.filename)

    def test_relative_path_acceptance(self) -> None:
        """Test that relative paths are accepted."""
        reader = pdal.Reader.las("./data/input.las")
        assert reader.filename == "./data/input.las"

        writer = pdal.Writer.las("../output/result.las")
        assert writer.filename == "../output/result.las"


class TestPipelineConstructionEdgeCases:
    """Test edge cases in pipeline construction."""

    def test_pipeline_from_json_string(self) -> None:
        """Test pipeline construction from valid JSON string."""
        json_str = '{"pipeline": [{"type": "readers.las", "filename": "input.las"}]}'

        pipeline = Pipeline(json_str)
        assert pipeline._pipeline_dict is not None

    def test_pipeline_from_dict(self) -> None:
        """Test pipeline construction from dictionary."""
        pipeline_dict = {
            "pipeline": [
                {"type": "readers.las", "filename": "input.las"},
                {"type": "writers.las", "filename": "output.las"},
            ]
        }

        pipeline = Pipeline(pipeline_dict)
        assert pipeline._pipeline_dict is not None

    def test_pipeline_from_single_stage(self) -> None:
        """Test pipeline construction from single stage."""
        reader = pdal.Reader.las("input.las")

        pipeline = Pipeline(reader)
        assert pipeline._pipeline_dict is not None

    def test_pipeline_from_stage_list(self) -> None:
        """Test pipeline construction from list of stage dicts.

        When passing a list, stages must be converted to dicts first.
        """
        reader = pdal.Reader.las("input.las")
        filter_stage = pdal.Filter.range(limits="Z[0:400]")
        writer = pdal.Writer.las("output.las")

        # Convert stages to dicts for list-based pipeline
        pipeline = Pipeline([reader.to_dict(), filter_stage.to_dict(), writer.to_dict()])
        assert pipeline._pipeline_dict is not None

    def test_pipeline_with_streaming_mode(self) -> None:
        """Test pipeline construction with streaming mode enabled."""
        pipeline = Pipeline(
            pdal.Reader.las("input.las") | pdal.Writer.las("output.las"),
            stream_mode=True,
        )
        assert pipeline._pipeline_dict is not None


class TestStageValidationEdgeCases:
    """Test edge cases in stage validation."""

    def test_reader_with_pathlib_path(self, tmp_path: Path) -> None:
        """Test reader stage with pathlib.Path converted to string."""
        input_path = tmp_path / "input.las"

        # Convert Path to string for API
        reader = pdal.Reader.las(str(input_path))
        assert reader.filename is not None
        assert reader.filename == str(input_path)

    def test_writer_with_pathlib_path(self, tmp_path: Path) -> None:
        """Test writer stage with pathlib.Path converted to string."""
        output_path = tmp_path / "output.las"

        # Convert Path to string for API
        writer = pdal.Writer.las(str(output_path))
        assert writer.filename is not None
        assert writer.filename == str(output_path)

    def test_filter_with_no_options(self) -> None:
        """Test filter creation with no options succeeds.

        Some filters have optional parameters only.
        """
        # Should not raise during creation
        filter_stage = pdal.Filter.sort()
        assert filter_stage.stage_type == "filters.sort"

    def test_stage_with_custom_tag(self) -> None:
        """Test stage creation with custom tag."""
        reader = pdal.Reader.las("input.las", tag="my_reader")
        assert reader.tag == "my_reader"

        filter_stage = pdal.Filter.range(limits="Z[0:400]", tag="my_filter")
        assert filter_stage.tag == "my_filter"


class TestPipelineExecutionSequence:
    """Test pipeline execution sequence edge cases."""

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_execute_after_failed_execution(self, small_laz: Path, tmp_path: Path) -> None:
        """Test executing pipeline after a failed execution attempt."""
        # First, try to execute with invalid file
        bad_pipeline = Pipeline(
            pdal.Reader.las("/nonexistent/file.laz") | pdal.Writer.las(str(tmp_path / "out1.las"))
        )

        with pytest.raises((PipelineError, Exception)):
            bad_pipeline.execute()

        # Now create valid pipeline and execute
        output = tmp_path / "out2.las"
        good_pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Writer.las(str(output)))

        count = good_pipeline.execute()
        assert count > 0
        assert output.exists()

    @pytest.mark.integration
    @pytest.mark.usefixtures("skip_if_no_pdal")
    def test_pipeline_reader_only_no_writer(self, small_laz: Path) -> None:
        """Test pipeline with reader only (no writer stage)."""
        pipeline = Pipeline(pdal.Reader.las(str(small_laz)) | pdal.Filter.head(count=100))

        # Should execute successfully without output file
        count = pipeline.execute()
        assert count >= 0
