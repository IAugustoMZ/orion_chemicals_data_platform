# ADR-0002: AGENTS.md and Agent Skills are the canonical sources; tool files are generated pointers

- **Status:** Accepted
- **Date:** 2026-10-21
- **Dossier:** specs/000-sdd-harness
- **Requirements:** none: process decision

## Context

We want the harness to work with any coding agent: Claude Code, Cursor, Codex, GitHub Copilot,
Gemini CLI. Each tool reads instructions from its own place (`CLAUDE.md`, `.cursor/rules/`,
`.github/copilot-instructions.md`, `GEMINI.md`) and looks for skills in its own folder
(`.claude/skills/`, `.agents/skills/`, `.github/skills/`). Writing the same instructions in five
places guarantees that they drift.

## Decision

- **`AGENTS.md`** at the root is the single, canonical instruction file. Tool files are short
  pointers: `CLAUDE.md` imports it (`@AGENTS.md`), `GEMINI.md` imports it, the Copilot and Cursor
  files point to it.
- **Agent Skills** in `.agents/skills/<name>/SKILL.md` (open standard: `name` + `description`
  front matter) are the canonical skills, read natively by Codex and Copilot.
- **Roles** in `harness/roles/*.md` are the canonical agent personas.
- `poetry run sdd sync` **generates** the adapters: `.claude/skills/` (copies), `.claude/agents/`
  (subagents from roles), `.cursor/commands/` and `.github/prompts/` (pointers). `sdd check`
  fails when a generated file drifts from its source, and orphans are removed.

## Alternatives considered

| Option | Why it lost |
|---|---|
| One file per tool, written by hand | five copies drift; no single place to change a rule |
| Symbolic links from tool folders to the canonical files | unreliable on Windows (needs developer mode or admin), and some tools ignore links |
| Only `CLAUDE.md` (one tool) | contradicts the goal of being tool-agnostic |
| A third-party sync tool | another dependency for about 100 lines of generator code we can test |

## Consequences

- + Changing a rule or a skill is one edit plus `sdd sync`.
- + Supporting a new tool is a new generator, not a new copy of the harness.
- − Generated files must never be edited by hand (they carry a banner saying so).
- − Native hooks exist only for Claude Code for now; other tools rely on the terminal check of
  approvals and on pre-commit (see ADR-0003, ADR-0004).
