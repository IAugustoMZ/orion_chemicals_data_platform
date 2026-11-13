"""Typed errors of the generator.

Every error the generator raises on purpose derives from ``TssourceError``, so the command line
can turn it into one line and exit code 1 without a stack trace.
"""

from __future__ import annotations


class TssourceError(Exception):
    """Base class of every handled error: the message says what happened and what to do."""
