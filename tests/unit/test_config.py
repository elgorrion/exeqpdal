"""Unit tests for exeqpdal configuration helpers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest

import exeqpdal as pdal
from exeqpdal.core.config import Config
from exeqpdal.exceptions import ConfigurationError, PDALNotFoundError

if TYPE_CHECKING:
    from pathlib import Path


class TestConfig:
    """Validate configuration plumbing without invoking PDAL."""

    def test_config_singleton(self) -> None:
        """The public config object should behave as a singleton alias."""
        assert pdal.config is pdal.config

    def test_set_pdal_path_valid(self, tmp_path: Path) -> None:
        """Setting pdal executable path accepts existing executables."""
        pdal_exe = tmp_path / "pdal"
        pdal_exe.touch()
        pdal_exe.chmod(0o755)

        config = Config()
        config.set_pdal_path(pdal_exe)
        assert config._pdal_path == pdal_exe

    def test_set_pdal_path_nonexistent(self) -> None:
        """Non-existent PDAL path raises ConfigurationError."""
        config = Config()
        with pytest.raises(ConfigurationError, match="not found"):
            config.set_pdal_path("/nonexistent/path/to/pdal")

    def test_verbose_setting(self) -> None:
        """Config toggles verbose flag."""
        config = Config()

        config.set_verbose(True)
        assert config.verbose

        config.set_verbose(False)
        assert not config.verbose

    def test_set_pdal_path_resets_version_cache(self, tmp_path: Path) -> None:
        """Switching binaries discards the cached version and re-arms the floor check."""
        pdal_exe = tmp_path / "pdal"
        pdal_exe.touch()
        pdal_exe.chmod(0o755)

        config = Config()
        config._pdal_version = "pdal 2.10.1"
        config._version_checked = True

        config.set_pdal_path(pdal_exe)

        assert config._pdal_version is None
        assert config._version_checked is False


class TestTimeout:
    """set_timeout validation."""

    def test_valid_values(self) -> None:
        config = Config()
        config.set_timeout(30)
        assert config.timeout == 30
        config.set_timeout(0.5)
        assert config.timeout == 0.5
        config.set_timeout(None)
        assert config.timeout is None

    @pytest.mark.parametrize("bad", [0, -5, float("inf"), float("nan")])
    def test_rejects_non_positive_and_non_finite(self, bad: float) -> None:
        config = Config()
        with pytest.raises(ConfigurationError, match="positive and finite"):
            config.set_timeout(bad)


class TestVersionFloorCheck:
    """check_pdal_version warns once, never raises, retries after failure."""

    BANNER_OLD = "pdal 2.5.0 (git-version: abc123)"
    BANNER_CURRENT = (
        "--------------------------------------------------------------------------------\n"
        "pdal 2.10.1 (git-version: 3ef768)\n"
        "--------------------------------------------------------------------------------"
    )

    def test_warns_once_below_floor(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        config = Config()
        monkeypatch.setattr(config, "get_pdal_version", lambda: self.BANNER_OLD)

        with caplog.at_level(logging.WARNING):
            config.check_pdal_version()
            config.check_pdal_version()

        warnings = [r for r in caplog.records if "below the supported floor" in r.message]
        assert len(warnings) == 1

    def test_no_warning_at_or_above_floor(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        config = Config()
        monkeypatch.setattr(config, "get_pdal_version", lambda: self.BANNER_CURRENT)

        with caplog.at_level(logging.WARNING):
            config.check_pdal_version()

        assert not [r for r in caplog.records if "below the supported floor" in r.message]
        assert config._version_checked is True

    def test_never_raises_and_retries_after_failure(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        config = Config()

        def fail() -> str:
            raise PDALNotFoundError("no pdal")

        monkeypatch.setattr(config, "get_pdal_version", fail)
        config.check_pdal_version()
        assert config._version_checked is False

        monkeypatch.setattr(config, "get_pdal_version", lambda: self.BANNER_OLD)
        with caplog.at_level(logging.WARNING):
            config.check_pdal_version()

        assert config._version_checked is True
        assert [r for r in caplog.records if "below the supported floor" in r.message]

    def test_anchored_parse_ignores_path_like_numbers(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        banner = "loaded /opt/pdal/2.6/plugins\npdal 2.10.1 (git-version: 3ef768)"
        config = Config()
        monkeypatch.setattr(config, "get_pdal_version", lambda: banner)

        with caplog.at_level(logging.WARNING):
            config.check_pdal_version()

        assert not [r for r in caplog.records if "below the supported floor" in r.message]

    def test_unparseable_banner_is_silent(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        config = Config()
        monkeypatch.setattr(config, "get_pdal_version", lambda: "no version here")

        with caplog.at_level(logging.WARNING):
            config.check_pdal_version()

        assert not [r for r in caplog.records if "below the supported floor" in r.message]
        assert config._version_checked is True
