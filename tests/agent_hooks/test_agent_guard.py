"""Tests of the PreToolUse guard that keeps agents away from approvals and guardrails."""

from __future__ import annotations

import io
import json

import pytest

from agent_hooks import agent_guard

DOSSIER = """\
id: '001'
title: Demo
requirements: [RT01]
approvals:
  G1:
  - member: mentor
verification: null
"""


@pytest.fixture
def project(tmp_path):
    folder = tmp_path / "specs/001-demo"
    folder.mkdir(parents=True)
    (folder / "dossier.yaml").write_text(DOSSIER, encoding="utf-8")
    return tmp_path


def decide(project, tool_name, **tool_input):
    payload = {"tool_name": tool_name, "tool_input": tool_input}
    return agent_guard.decide(payload, project, {})


@pytest.mark.parametrize(
    "command",
    [
        "poetry run sdd approve 001 G4 --as mentor",
        "git commit --no-verify -m x",
        "pre-commit uninstall",
        "git push --force origin main",
        "git reset --hard HEAD~1",
    ],
)
def test_blocks_forbidden_commands(project, command):
    assert decide(project, "Bash", command=command)


@pytest.mark.parametrize("command", ["poetry run sdd status", "git commit -m 'feat: x'", "ls"])
def test_allows_ordinary_commands(project, command):
    assert decide(project, "PowerShell", command=command) is None


def test_dossier_metadata_edits_allowed_but_not_approvals(project):
    path = str(project / "specs/001-demo/dossier.yaml")
    assert (
        decide(project, "Edit", file_path=path, old_string="title: Demo", new_string="title: X")
        is None
    )
    assert decide(
        project, "Edit", file_path=path, old_string="member: mentor", new_string="member: me"
    )
    rewritten = DOSSIER.replace("verification: null", "verification: {digest: x}")
    assert decide(project, "Write", file_path=path, content=rewritten)
    edits = [{"old_string": "RT01", "new_string": "RT02"}]
    assert decide(project, "MultiEdit", file_path=path, edits=edits) is None


def test_guardrails_need_the_override(project):
    assert decide(project, "Write", file_path=".pre-commit-config.yaml", content="")
    assert decide(project, "Edit", file_path="tools/agent_hooks/agent_guard.py")
    allowed = agent_guard.decide(
        {"tool_name": "Write", "tool_input": {"file_path": "harness/team.yaml", "content": ""}},
        project,
        {agent_guard.OVERRIDE_VARIABLE: "1"},
    )
    assert allowed is None
    assert decide(project, "Read", file_path="harness/team.yaml") is None


@pytest.mark.parametrize(
    "path", [".env", "deploy/secrets/db_password", "certs/server.key", "a/.env.local"]
)
def test_secrets_are_off_limits(project, path):
    assert decide(project, "Read", file_path=path)


def test_env_example_is_fine(project):
    assert decide(project, "Write", file_path=".env.example", content="X=") is None
    assert decide(project, "Glob") is None


def test_main_exit_codes(project, monkeypatch, capsys):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project))
    payload = {"tool_name": "Bash", "tool_input": {"command": "sdd approve 001 G1 --as mentor"}}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    assert agent_guard.main() == 2
    assert "Blocked by the SDD harness guard" in capsys.readouterr().err
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    assert agent_guard.main() == 0
    monkeypatch.setattr(
        "sys.stdin", io.StringIO(json.dumps({"tool_name": "Bash", "tool_input": {}}))
    )
    assert agent_guard.main() == 0
