"""`Settings` is read once from ``TSSOURCE_*`` variables and is immutable."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from tssource.application.settings import Mode, Settings
from tssource.domain.errors import TssourceError


def test_defaults_without_environment() -> None:
    """With no variable set the defaults apply."""
    settings = Settings.from_environment({})
    assert settings == Settings()
    assert settings.mode is Mode.BACKFILL


def test_environment_overrides_defaults() -> None:
    """Each variable maps to its field."""
    settings = Settings.from_environment(
        {
            "TSSOURCE_SEED": "7",
            "TSSOURCE_OUT": "x",
            "TSSOURCE_MODE": "stream",
            "TSSOURCE_START": "2026-01-01T00:00:00",
            "TSSOURCE_SPEED_FACTOR": "60",
        }
    )
    assert (settings.seed, settings.output_folder, settings.mode) == (7, Path("x"), Mode.STREAM)
    assert settings.start is not None and settings.speed_factor == 60.0


@pytest.mark.parametrize(
    "bad", [{"TSSOURCE_SEED": "abc"}, {"TSSOURCE_MODE": "x"}, {"TSSOURCE_SPEED_FACTOR": "0"}]
)
def test_invalid_value_is_a_handled_error(bad: dict[str, str]) -> None:
    """A bad value raises ``TssourceError`` naming the problem, not a raw ValueError."""
    with pytest.raises(TssourceError, match="TSSOURCE"):
        Settings.from_environment(bad)


def test_settings_are_frozen() -> None:
    """A run cannot change its settings."""
    with pytest.raises(dataclasses.FrozenInstanceError):
        Settings().seed = 1  # type: ignore[misc]
