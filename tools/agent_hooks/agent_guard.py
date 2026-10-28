"""PreToolUse guard for coding agents: block the few actions only people may take.

Wired in `.claude/settings.json` (Claude Code). The hook receives the tool call as JSON on
standard input (``{"tool_name": ..., "tool_input": {...}}``) and blocks it by exiting with
status 2 and a reason on standard error, which the agent reads (Claude Code hook contract).

What it blocks (harness/ai-control-plane.md, "Guardrails"):

1. **Approvals.** Running ``sdd approve`` and editing the ``approvals`` or ``verification``
   sections of any `dossier.yaml`. Gates are ours to close (ADR-0003).
2. **Bypassing the gates.** ``git commit --no-verify`` (skips pre-commit), ``pre-commit
   uninstall``, forced pushes, ``git reset --hard``.
3. **Changing the guardrails.** Edits to `.claude/settings.json`, `.pre-commit-config.yaml`,
   `harness/team.yaml` and this package. A person who wants an agent to change them starts the
   agent with ``SDD_ALLOW_GUARDRAIL_EDITS=1`` in its environment; the agent cannot set that for
   the hook process itself.
4. **Secrets.** Reading or writing `.env` files, `deploy/secrets/`, private keys (RT36).

It is a safety net against mistakes, not a security boundary: the deterministic gates
(pre-commit, `sdd check`, the TTY-only approval) still hold when a tool has no hooks at all.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

PROTECTED_SECTIONS = ("approvals", "verification")
GUARDRAIL_FILES = (".claude/settings.json", ".pre-commit-config.yaml", "harness/team.yaml")
GUARDRAIL_DIRS = ("tools/agent_hooks/",)
OVERRIDE_VARIABLE = "SDD_ALLOW_GUARDRAIL_EDITS"
SHELL_TOOLS = ("Bash", "PowerShell")
EDIT_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")

_FORBIDDEN_COMMANDS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bsdd\s+approve\b"), "approvals are made by people at a terminal (ADR-0003)"),
    (re.compile(r"--no-verify\b"), "skipping the pre-commit gates is not allowed"),
    (re.compile(r"\bpre-commit\s+uninstall\b"), "removing the pre-commit gates is not allowed"),
    (re.compile(r"\bgit\s+push\b.*(?:--force\b|\s-f\b)"), "forced pushes rewrite shared history"),
    (re.compile(r"\bgit\s+reset\s+--hard\b"), "hard resets destroy uncommitted work"),
)
_TOP_LEVEL_KEY = re.compile(r"^(?P<key>[A-Za-z_][\w-]*):", re.MULTILINE)
_SECRET_PATH = re.compile(
    r"(^|/)\.env(\.(?!example$)[\w.-]+)?$"  # .env, .env.local ... but not .env.example
    r"|(^|/)[^/]+\.(pem|key|p12|pfx)$"  # private keys and certificates bundles
    r"|(^|/)deploy/secrets/"  # Docker Compose secrets, never committed
)


def relative_path(file_path: str, project_dir: Path) -> str:
    """Return `file_path` relative to the project, with forward slashes.

    Args:
        file_path: absolute or relative path from the tool input.
        project_dir: the project root.
    """
    path = Path(file_path)
    with contextlib.suppress(ValueError):  # outside the project: keep the path as given
        path = path.resolve().relative_to(project_dir.resolve())
    return path.as_posix().removeprefix("./")


def protected_sections(text: str) -> dict[str, str]:
    """Return the text of each protected top-level YAML section of a dossier.

    Args:
        text: the content of a `dossier.yaml`.

    Returns:
        Section name -> its lines (the section ends at the next top-level key).
    """
    text = text.replace("\r\n", "\n")
    keys = list(_TOP_LEVEL_KEY.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(keys):
        if match.group("key") in PROTECTED_SECTIONS:
            end = keys[index + 1].start() if index + 1 < len(keys) else len(text)
            sections[match.group("key")] = text[match.start() : end].strip()
    return sections


def edited_content(tool_name: str, tool_input: dict[str, Any], current: str) -> str:
    """Return what the file would contain after the edit.

    Args:
        tool_name: Edit, MultiEdit or Write.
        tool_input: the tool's arguments.
        current: the file's current content ("" when it does not exist).
    """
    if tool_name == "Write":
        return str(tool_input.get("content", ""))
    edits = tool_input.get("edits") or [tool_input]
    content = current
    for edit in edits:
        old, new = str(edit.get("old_string", "")), str(edit.get("new_string", ""))
        content = (
            content.replace(old, new) if edit.get("replace_all") else content.replace(old, new, 1)
        )
    return content


def shell_reason(command: str) -> str | None:
    """Return why a shell command is blocked, or None when it may run.

    Args:
        command: the command line the agent wants to run.
    """
    for pattern, reason in _FORBIDDEN_COMMANDS:
        if pattern.search(command):
            return reason
    return None


def file_reason(
    tool_name: str,
    tool_input: dict[str, Any],
    relative: str,
    read_file: Callable[[str], str],
    allow_guardrails: bool,
) -> str | None:
    """Return why a file read or edit is blocked, or None when it may proceed.

    Args:
        tool_name: Read, Edit, Write, MultiEdit or NotebookEdit.
        tool_input: the tool's arguments.
        relative: the target path relative to the project.
        read_file: returns the current content of a relative path ("" when missing).
        allow_guardrails: true when a person allowed guardrail edits for this session.
    """
    if _SECRET_PATH.search(relative):
        return f"{relative} may hold credentials; agents never read or write them (RT36)"
    if tool_name not in EDIT_TOOLS:
        return None
    guarded = relative in GUARDRAIL_FILES or relative.startswith(GUARDRAIL_DIRS)
    if guarded and not allow_guardrails:
        return f"{relative} is a guardrail; ask us to change it (or set {OVERRIDE_VARIABLE}=1)"
    if relative.endswith("dossier.yaml"):
        current = read_file(relative)
        after = edited_content(tool_name, tool_input, current)
        if protected_sections(after) != protected_sections(current):
            return "approvals and verification are written only by `sdd` (ADR-0003)"
    return None


def decide(payload: dict[str, Any], project_dir: Path, environ: dict[str, str]) -> str | None:
    """Return the reason to block the tool call described by `payload`, or None to allow it.

    Args:
        payload: the hook input (tool_name, tool_input).
        project_dir: the project root.
        environ: the hook process environment.
    """
    tool_name = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input") or {}
    if tool_name in SHELL_TOOLS:
        return shell_reason(str(tool_input.get("command", "")))
    target = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not target:
        return None
    relative = relative_path(str(target), project_dir)

    def read_file(path: str) -> str:
        """Return a project file's text, or "" when it does not exist."""
        file = project_dir / path
        return file.read_text(encoding="utf-8") if file.is_file() else ""

    allow = environ.get(OVERRIDE_VARIABLE) == "1"
    return file_reason(tool_name, tool_input, relative, read_file, allow)


def main() -> int:
    """Read the hook payload from stdin and return the process exit status (0 or 2)."""
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())
    reason = decide(payload, project_dir, dict(os.environ))
    if reason is None:
        return 0
    sys.stderr.write(f"Blocked by the SDD harness guard: {reason}.\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
