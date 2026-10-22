"""Generator of the per-tool adapters from the canonical, tool-agnostic harness sources.

Application layer. The canonical sources follow open conventions that several tools read
natively: `AGENTS.md`, and Agent Skills in `.agents/skills/<name>/SKILL.md` (read by Codex,
Copilot, Gemini CLI and others). Tools that look elsewhere get generated copies (ADR-0002):

* `.agents/skills/<n>/*` -> Claude Code skills `.claude/skills/<n>/*` (same content);
* `.agents/skills/<n>/SKILL.md` -> Cursor command `.cursor/commands/<n>.md` and Copilot prompt
  `.github/prompts/<n>.prompt.md` (short pointers to the canonical skill);
* `harness/roles/<role>.md` -> Claude Code subagent `.claude/agents/<role>.md`.
"""

from __future__ import annotations

import posixpath

from sdd.application.generators import GeneratedFile
from sdd.application.generators.text_tools import (
    generated_banner,
    render_front_matter,
    split_front_matter,
)
from sdd.application.ports.documents import DocumentStore

SKILLS_DIR = ".agents/skills/"
ROLES_DIR = "harness/roles/"
_TARGETS = (".claude/skills/", ".claude/agents/", ".cursor/commands/", ".github/prompts/")


class AdapterGenerator:
    """Generate Claude, Cursor and Copilot adapters from skills and roles."""

    def __init__(self, store: DocumentStore) -> None:
        """Receive the store the canonical sources are read from.

        Args:
            store: the repository's files.
        """
        self._store = store

    def owned_prefixes(self) -> tuple[str, ...]:
        """Return the adapter folders: every file in them is generated."""
        return _TARGETS

    def generate(self) -> tuple[GeneratedFile, ...]:
        """Return every adapter file for the current skills and roles."""
        files: list[GeneratedFile] = []
        for path in self._store.paths(prefix=SKILLS_DIR):
            files.extend(self._from_skill_file(path))
        for path in self._store.paths(prefix=ROLES_DIR, suffix=".md"):
            if posixpath.basename(path) != "README.md":
                files.append(self._subagent(path))
        return tuple(files)

    def _from_skill_file(self, path: str) -> tuple[GeneratedFile, ...]:
        """Map one file of a skill folder to its adapters.

        Args:
            path: a file under `.agents/skills/<name>/`.
        """
        text = self._store.read(path) or ""
        relative = path.removeprefix(SKILLS_DIR)
        claude_copy = f".claude/skills/{relative}"
        if posixpath.basename(path) != "SKILL.md":
            return (GeneratedFile(claude_copy, text),)
        fields, body = split_front_matter(text)
        name = fields.get("name", posixpath.basename(posixpath.dirname(path)))
        description = fields.get("description", "")
        pointer = (
            f"{generated_banner(path)}\n# {name}\n\n{description}\n\n"
            f"Read `{path}` and follow it step by step. It is the canonical skill; this file "
            "only points to it.\n"
        )
        return (
            GeneratedFile(
                claude_copy, render_front_matter(fields) + generated_banner(path) + body
            ),
            GeneratedFile(f".cursor/commands/{name}.md", pointer),
            GeneratedFile(
                f".github/prompts/{name}.prompt.md",
                render_front_matter({"description": description}) + pointer,
            ),
        )

    def _subagent(self, path: str) -> GeneratedFile:
        """Map a tool-agnostic role definition to a Claude Code subagent.

        Args:
            path: a file `harness/roles/<role>.md` with name/description/tools front matter.
        """
        fields, body = split_front_matter(self._store.read(path) or "")
        name = fields.get("name", posixpath.splitext(posixpath.basename(path))[0])
        header = {"name": name, "description": fields.get("description", "")}
        if fields.get("tools"):
            header["tools"] = fields["tools"]
        return GeneratedFile(
            f".claude/agents/{name}.md",
            render_front_matter(header) + generated_banner(path) + body,
        )
