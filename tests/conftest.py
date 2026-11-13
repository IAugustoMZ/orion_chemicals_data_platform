"""Shared pytest hooks: record the acceptance criterion each test proves (ADR-0023)."""

from __future__ import annotations

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Copy every ``ac`` marker into the test's JUnit properties.

    `sdd item verify` reads those properties to know which criteria have a passing test.

    Args:
        items: the collected tests.
    """
    for item in items:
        for marker in item.iter_markers("ac"):
            item.user_properties.append(("ac", str(marker.args[0])))
