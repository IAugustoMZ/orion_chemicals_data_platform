"""Immutable settings of one run, read once.

Contract: ``Settings.from_environment`` reads ``TSSOURCE_<NAME>`` variables from the mapping it
is given (never from the process directly, so tests pass a dict), validates them and returns a
frozen object. Command-line options win over the environment; that merge happens in the
composition root. No credential is ever a setting (RT36).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from tssource.domain.errors import TssourceError

PREFIX = "TSSOURCE_"


class Mode(StrEnum):
    """How time runs: ``backfill`` as fast as possible, ``stream`` paced by the speed factor."""

    BACKFILL = "backfill"
    STREAM = "stream"


@dataclass(frozen=True)
class Settings:
    """Everything a run needs to know, fixed at start.

    Attributes:
        seed: base of the deterministic random generator.
        output_folder: where files are written.
        mode: backfill or stream.
        start: first simulated instant, or None for "the default of the run".
        end: last simulated instant, or None.
        speed_factor: simulated seconds per real second in stream mode (1.0 is real time).
    """

    seed: int = 42
    output_folder: Path = Path("data/ts_source")
    mode: Mode = Mode.BACKFILL
    start: datetime | None = None
    end: datetime | None = None
    speed_factor: float = 1.0

    @classmethod
    def from_environment(cls, environ: Mapping[str, str]) -> Settings:
        """Build the settings from ``TSSOURCE_*`` variables, using defaults for the rest.

        Args:
            environ: a mapping such as ``os.environ``.

        Returns:
            The validated, immutable settings.

        Raises:
            TssourceError: a value cannot be read, with the variable named.
        """
        defaults = cls()
        try:
            return cls(
                seed=int(environ.get(PREFIX + "SEED", defaults.seed)),
                output_folder=Path(environ.get(PREFIX + "OUT", str(defaults.output_folder))),
                mode=Mode(environ.get(PREFIX + "MODE", defaults.mode)),
                start=_instant(environ.get(PREFIX + "START")),
                end=_instant(environ.get(PREFIX + "END")),
                speed_factor=_positive(environ.get(PREFIX + "SPEED_FACTOR", "1.0")),
            )
        except ValueError as error:
            raise TssourceError(f"invalid TSSOURCE_* setting: {error}") from error


def _instant(text: str | None) -> datetime | None:
    """Parse an ISO 8601 instant, or return None when the variable is not set."""
    return None if text is None else datetime.fromisoformat(text)


def _positive(text: str) -> float:
    """Parse a strictly positive number."""
    value = float(text)
    if value <= 0:
        raise ValueError(f"speed factor must be positive, got {text}")
    return value
