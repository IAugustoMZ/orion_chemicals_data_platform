"""The `tssource` compose service follows the hardening baseline (B02, RT01, RT36)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

COMPOSE = Path(__file__).resolve().parents[2] / "compose.yaml"


def _service() -> dict[str, Any]:
    """Return the `tssource` service block of compose.yaml."""
    content = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    service: dict[str, Any] = content["services"]["tssource"]
    return service


@pytest.mark.ac("PBI-003-01:AC2")
def test_service_is_hardened() -> None:
    """Read-only root, no capability, no new privileges, non-root, no port."""
    service = _service()
    assert service["read_only"] is True
    assert service["cap_drop"] == ["ALL"]
    assert "no-new-privileges:true" in service["security_opt"]
    assert service["user"] == "10001:10001"
    assert "ports" not in service


@pytest.mark.ac("PBI-003-01:AC2")
def test_only_one_writable_bind_and_a_healthcheck() -> None:
    """Exactly one bind mount (the output folder) and a `tssource health` healthcheck."""
    service = _service()
    binds = [v for v in service["volumes"] if not str(v).endswith(":ro")]
    assert binds == ["./data/ts_source:/data/ts_source"]
    assert service["healthcheck"]["test"][-2:] == ["tssource", "health"]
