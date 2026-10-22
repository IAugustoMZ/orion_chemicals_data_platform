# PRD · 000 · The SDD harness

> **Phase 1 · Discover**, closed by **G1 · PRD validated** (both of us approve).
> Dossier `specs/000-sdd-harness/` · branch `spec/000-sdd-harness` · kind **enabler** · created 2026-10-21.
> How to fill this file: [lifecycle, phase 1](../../harness/lifecycle.md#phase-1-discover).

> **Bootstrap note.** This dossier describes the harness itself, so it was necessarily written
> *before* the harness could govern it: the artifacts were drafted by the agent from our
> conversation, and the gates are approved retroactively, in order, once we have reviewed each
> artifact. From dossier 001 on, every artifact precedes its gate.

## Requirements digest

The technical requirements this work serves, read from `docs/requirements/` (gate G0 checks that
every RT cited here exists):

| RT | Phase | What must hold | How we verify it |
|---|---|---|---|
| RT36 | P | Credentials shall not appear in code or published files; their use, rotation and revocation shall have a defined procedure. | Inspect the delivery and replace a test credential without changing code. |
| RT38 | P | Changes to mappings, rules, permissions and manual reprocessing shall record actor, time, reason and before/after when applicable. | Make a change and reconstruct it from the audit log. |
| RT42 | P | Changes to integrations and rules shall pass automated validation of contracts, exceptions and regression before publication. | Introduce an incompatibility, observe a controlled failure, then fix it. |

This is an **enabler**: it delivers no platform data feature, so it delivers none of these RTs
for the platform. It applies their spirit to the way we build: no credentials in the repository
(secret scanning, the agent guard), an audit trail of every decision (approvals with actor, time,
digest and note), and automated validation before anything is merged (G5, pre-commit). Every
other RT is out of scope here and will be served by feature dossiers, starting with the
catalogue's priorities (RT01, RT09, RT12, RT20-RT25, RT28-RT29, RT34, RT39).

## Problem

We will build the Orion Chemicals data platform largely with AI coding agents, and we will use
the work to mentor. Without a harness, three things go wrong. Agents build from prompts that
drift, so what gets built is not what we agreed, and nobody can tell which agreement a piece of
code came from. Decisions are taken implicitly in chat and lost, so the mentee sees code but not
the reasoning that produced it. And quality depends on someone remembering to run checks, which
fails exactly when work moves fast.

The target operating model answers this on paper (specifications first, people govern, AI
executes, seven phases with approval gates, a governed context and an AI control plane), but it
needs to become concrete, enforced and teachable in a local repository, for any coding agent.

## Goals and success metrics

| Goal | Metric | Baseline today | Target | How we measure |
|---|---|---|---|---|
| No work without requirements | dossiers whose G0 fails at commit | no rule | 0 (commit blocked) | `sdd check` in pre-commit reports `dossier-context` errors |
| Only people close human gates | approvals recorded by an agent | no rule | 0 | `sdd approve` refuses without a TTY (test `test_agents_without_terminal_are_refused`); agent guard blocks it |
| No code before an approved spec | governed commits without G4 passed, through the normal flow | no rule | 0 | `sdd guard-commit` refuses (tests `TestGuard`). Bypassing hooks on purpose (`git commit --no-verify`) is beyond what a local harness can stop: the agent guard blocks agents, and we trust ourselves |
| Deterministic quality | checks automated in G5 | 0 | 10 checks in `harness/checks.yaml` | `sdd verify` output |
| Every change teaches | dossiers at G6 without a complete teaching guide | no rule | 0 | `sdd approve <id> G6` refuses (readiness) |
| Tool-agnostic | agents supported by canonical files | 0 | 5 (Claude Code, Cursor, Codex, Copilot, Gemini CLI) | adapter files present; `sdd sync --check` clean |
| One gate at a time (ADR-0015) | artifacts complete before the gate preceding them passed | no rule | 0 `written-ahead` warnings from dossier 001 on | `sdd check` |

## Users and scenarios

- **We, approving.** The mentor and the mentee review an artifact together and each approves it
  at a terminal; the status board in the README updates; later, an edit of the approved text is
  flagged as stale without anyone having to notice it.
- **A coding agent, working.** An agent (any tool) is asked to "specify dossier 001". It reads
  AGENTS.md, the requirements and the `sdd-specify` skill, and drafts only the spec, plan and
  tasks (the earlier gates have passed). It runs `sdd check`, briefs us in the chat and asks
  specific questions (skill `sdd-review-gate`), and stops until we approve G4 at our terminals.
  When it tries to commit code before G4, the commit is refused; when it tries to approve, the
  approval is refused.
- **The mentee, learning.** The mentee opens the documentation site, follows the learning path,
  and reads the teaching guide of each dossier to understand every decision, down to the classes.

## Scope

### In scope

- The harness documents: constitution, lifecycle, gates, how it works, principles, security,
  quality, documentation standard, upkeep matrix, context and AI control planes.
- Templates for every artifact; roles; Agent Skills; generated adapters for Claude Code, Cursor,
  Copilot; pointers for Gemini CLI and Codex.
- The `sdd` tool (Python, clean architecture) and the agent guard hook, with tests.
- Local enforcement: pre-commit configuration, the G5 suite.
- The requirement catalogue (YAML transcription of the PDF) and the traceability matrix.
- Documentation: root README, architecture pages, ADRs 0001-0015, learning path, primers,
  tutorials, the MkDocs site (local and in Docker Compose).

### Out of scope

- Any platform feature (ingestion, catalog, API): each is a future feature dossier.
- CI on a server, a hosted tracker, signed approvals (possible later enablers).
- Native hooks for agents other than Claude Code.

## Constraints and assumptions

- Local only: no CI, no hosted services (decision). Runtime is Docker Compose (decision).
- Python environments only with Poetry (decision). Everything in English (decision).
- Assumption: coding agents execute commands without an interactive terminal on standard input
  (true for the tools we use today; it is what makes TTY-only approval work).
- Assumption: Mermaid renderers we use (GitHub, MkDocs Material, editors) accept `<img>` in node
  labels; verified with Mermaid's own renderer.

## Risks and open questions

| Risk or question | Impact | Mitigation or owner |
|---|---|---|
| The harness is too heavy for small changes | we stop using it | dossiers can be small; review after dossier 001 (owner: mentor) |
| An agent tool starts attaching a TTY to commands | agents could approve | the agent guard still blocks in Claude Code; revisit ADR-0003 (owner: mentor) |
| Material for MkDocs reaches end of support | the site stops getting fixes | exit path to Zensical (ADR-0008) (owner: mentee) |
| Retroactive approval of this dossier | the process looks bypassed | stated openly in this bootstrap note; approvals still in order |
| Open question: would we notice if a tool starts giving agents a terminal? We don't know yet | in Cursor, Codex, Copilot and Gemini CLI (no agent guard) an agent could then approve | accepted for now; revisit when we change or add an agent tool, and before relying on those tools for approvals (owner: mentor) |

## Review notes (optional)

_Nothing needed to approve. The approval itself records who approved which exact text and when.
Add a line here (or use `--note` when approving) only for a decision worth remembering, such as
a risk we accept or a change we asked for._
