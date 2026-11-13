"""Composition root: the only place that reads the environment and wires adapters.

Everything above it (the command line) receives ready-made objects; everything below it
receives ports. In card 01 there is nothing to wire but the settings; the benchmark use case
joins here in card 02.
"""

from __future__ import annotations

import os
from collections.abc import Mapping

from tssource.application.settings import Settings


def build_settings(environ: Mapping[str, str] | None = None) -> Settings:
    """Read the settings once.

    Args:
        environ: variables to read; defaults to the process environment.

    Returns:
        The immutable settings.
    """
    return Settings.from_environment(os.environ if environ is None else environ)
