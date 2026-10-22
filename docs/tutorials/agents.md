# Tutorial: working with coding agents

The harness is tool-agnostic (ADR-0002): the same rules, skills and gates apply whichever agent
you use. This page shows what each tool reads and how to drive a phase with it.

## What each tool reads

| Tool | Instructions | Skills / commands | Subagents | Hooks (agent guard) |
|---|---|---|---|---|
| <img src="https://cdn.simpleicons.org/claude/D97757" height="16" alt=""> **Claude Code** | `CLAUDE.md` (imports `AGENTS.md`) | `.claude/skills/` (generated) | `.claude/agents/` (generated from `harness/roles/`) | yes, `.claude/settings.json` |
| <img src="https://cdn.simpleicons.org/cursor/000000" height="16" alt=""> **Cursor** | `AGENTS.md`, `.cursor/rules/sdd-harness.mdc` | `.cursor/commands/` (generated pointers) | — | not yet |
| <img src="https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/openai.svg" height="16" alt=""> **Codex** | `AGENTS.md` | `.agents/skills/` (canonical, native) | — | not yet |
| <img src="https://cdn.simpleicons.org/githubcopilot/000000" height="16" alt=""> **GitHub Copilot** | `AGENTS.md`, `.github/copilot-instructions.md` | `.agents/skills/`, `.github/prompts/` (generated) | — | not yet |
| <img src="https://cdn.simpleicons.org/googlegemini/8E75B2" height="16" alt=""> **Gemini CLI** | `GEMINI.md` (imports `AGENTS.md`) | `.agents/skills/` | — | not yet |

Whatever the tool, three protections always hold: **approvals need a person at a terminal**,
**pre-commit runs the gates on every commit**, and **`sdd check` reports any inconsistency**.
The agent guard (Claude Code) adds a second net: it blocks `sdd approve`, edits of approvals,
`--no-verify`, guardrail files and secrets before the command even runs.

## Driving a phase

Name the dossier and the skill; the skill tells the agent what to read, what to produce and when
to stop:

| You want | Say |
|---|---|
| Start a piece of work | "Use the sdd-start skill: we want X." |
| Draft the PRD | "Use sdd-discover for dossier 001." |
| Break into a backlog | "Use sdd-plan for 001." |
| Interface approach | "Use sdd-structure for 001." |
| Execution spec | "Use sdd-specify for 001." |
| Build | "Use sdd-build for 001." |
| Independent review (new session!) | "Act as the reviewer role and use sdd-validate for 001." |
| Teaching guide | "Use write-teaching-guide for 001." |
| Release | "Use sdd-release for 001." |

In Claude Code you can also call skills directly (`/sdd-specify`) and delegate to subagents ("ask
the reviewer subagent to review branch spec/001-source-contracts"). In Cursor, the same skills
appear as commands from `.cursor/commands/`. In Copilot, as prompt files.

## When the agent says a gate is ready

It must stop and ask; it cannot approve (and is blocked if it tries). You review the artifact and
approve at your terminal:

```bash
poetry run sdd status 001
poetry run sdd approve 001 G4 --as mentor
```

If an agent ever reports a gate as passed, check `sdd status`: it is the only source of truth.

## Changing skills and roles

Edit the canonical files only: `.agents/skills/<name>/SKILL.md` and `harness/roles/<role>.md`.
Then regenerate the adapters:

```bash
poetry run sdd sync
```

These are governed files: the change belongs to an enabler dossier with an approved spec.

## Letting an agent change a guardrail (rare)

Guardrail files (`.claude/settings.json`, `.pre-commit-config.yaml`, `harness/team.yaml`,
`tools/agent_hooks/`) are protected from agents. When an approved enabler dossier needs an agent
to change one, start the agent with the override in its environment, for that session only:

```bash
SDD_ALLOW_GUARDRAIL_EDITS=1 claude          # bash / zsh
$env:SDD_ALLOW_GUARDRAIL_EDITS = "1"; claude  # PowerShell (then close the terminal)
```
