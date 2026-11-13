"""The CI workflow is a contract: it runs every check of `harness/checks.yaml` and is hardened."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
SHA = re.compile(r"^[^@\s]+@[0-9a-f]{40}$")


def _load(path: Path) -> dict[Any, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


@pytest.fixture(scope="module")
def workflow() -> dict[Any, Any]:
    return _load(WORKFLOW)


@pytest.fixture(scope="module")
def steps(workflow) -> list[dict[str, Any]]:
    return list(workflow["jobs"]["quality"]["steps"])


def _commands() -> list[str]:
    checks = _load(ROOT / "harness" / "checks.yaml")["checks"]
    return [" ".join(str(part) for part in check["command"]) for check in checks]


class TestTriggers:
    @pytest.mark.ac("PBI-002-04:AC1")
    def test_the_job_quality_runs_on_pull_requests_into_main(self, workflow):
        triggers = workflow.get("on", workflow.get(True))
        assert triggers["pull_request"]["branches"] == ["main"]
        assert triggers["push"]["branches"] == ["main"]
        assert "quality" in workflow["jobs"]


class TestEveryCheckRuns:
    @pytest.mark.ac("PBI-002-04:AC3")
    def test_a_step_runs_each_command_of_checks_yaml(self, steps):
        runs = [str(step.get("run", "")) for step in steps]
        missing = [c for c in _commands() if not any(f"poetry run {c}" in run for run in runs)]
        assert missing == []

    @pytest.mark.ac("PBI-002-04:AC3")
    def test_the_test_would_notice_a_missing_command(self, steps):
        runs = [str(step.get("run", "")) for step in steps]
        assert not any("poetry run no-such-check" in run for run in runs)

    @pytest.mark.ac("PBI-002-04:AC2")
    def test_no_step_can_hide_a_failure(self, steps, workflow):
        for step in steps:
            assert step.get("continue-on-error") is not True
            assert "|| true" not in str(step.get("run", ""))
        assert workflow["jobs"]["quality"].get("continue-on-error") is not True

    @pytest.mark.ac("PBI-002-04:AC7")
    def test_the_card_proof_is_skipped_when_the_branch_is_not_a_card(self, steps):
        (card,) = [s for s in steps if "item verify" in str(s.get("run", ""))]
        text = str(card["run"])
        assert "item current" in text and "else" in text and "exit 1" not in text


class TestHardening:
    @pytest.mark.ac("PBI-002-04:AC4")
    def test_read_only_token_a_timeout_and_cancelling_concurrency(self, workflow):
        assert workflow["permissions"] == {"contents": "read"}
        assert workflow["jobs"]["quality"]["timeout-minutes"] <= 60
        assert workflow["concurrency"]["cancel-in-progress"] is True

    @pytest.mark.ac("PBI-002-04:AC4")
    def test_no_secret_is_used(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        assert not re.search(r"\$\{\{[^}]*secrets", text)
        assert "pull_request_target" not in text

    @pytest.mark.ac("PBI-002-04:AC4")
    def test_every_action_is_pinned_to_a_full_commit_sha(self, steps):
        uses = [step["uses"] for step in steps if "uses" in step]
        assert uses and all(SHA.match(u) for u in uses), uses


class TestMergeBlocking:
    @pytest.mark.ac("PBI-002-04:AC5")
    def test_the_protection_checklist_names_the_job_and_the_manual_proof(self, workflow):
        """Only what a repository can hold is automated; red then green is proved by hand."""
        text = (ROOT / "harness" / "ci-protection.md").read_text(encoding="utf-8")
        job = next(iter(workflow["jobs"]))
        for required in (f"**`{job}`**", "Do not allow force pushes", "Include administrators"):
            assert required in text
        assert "Manual proof" in text and "validation.md" in text
