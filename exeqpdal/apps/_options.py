"""Shared PDAL application option formatting."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


def stage_option_args(
    stage_options: Mapping[str, object] | None = None,
    legacy_options: Mapping[str, object] | None = None,
) -> list[str]:
    """Build exact ``--stage.driver.option=value`` arguments.

    Legacy keyword options remain supported when all three components are
    single words, for example ``filters_range_limits``. Names containing
    additional underscores are ambiguous and must use ``stage_options``.
    """
    options: dict[str, object] = {}

    if legacy_options:
        for key, value in legacy_options.items():
            if key.count("_") != 2:
                raise ValueError(
                    f"Ambiguous PDAL option {key!r}; pass its exact dotted name in stage_options"
                )
            option_name = key.replace("_", ".")
            options[option_name] = value

    if stage_options:
        for option_name, value in stage_options.items():
            parts = option_name.split(".")
            if len(parts) != 3 or any(not part for part in parts):
                raise ValueError(
                    f"PDAL option {option_name!r} must use exact 'stage.driver.option' notation"
                )
            if option_name in options:
                raise ValueError(f"PDAL option {option_name!r} was specified more than once")
            options[option_name] = value

    return [f"--{name}={value}" for name, value in options.items()]
