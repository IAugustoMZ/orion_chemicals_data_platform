# Learning path

This repository is also a course. Read it in this order; each step builds on the previous ones.
Every feature adds a chapter: its dossier's teaching guide.

## Step 1 · The big picture (30 minutes)

1. The [root README](../../README.md): what this is and where things are.
2. [How the harness works](../../harness/how-it-works.md): actors, workflow, gates, enforcement.
3. [The requirements](../requirements/README.md): the Orion Chemicals case and RT01-RT42.

## Step 2 · The ideas behind it (primers)

Short, self-contained explanations of the concepts the repository applies everywhere.

| Primer | Answers |
|---|---|
| [Spec-driven development](primers/spec-driven-development.md) | why write a spec before code when an AI writes the code? |
| [Clean architecture and SOLID](primers/clean-architecture-and-solid.md) | why layers, ports and adapters; what each SOLID letter means in practice |
| [Design patterns](primers/design-patterns.md) | repository, strategy, composition root, value object, aggregate, mapper: what, when, when not |
| [Architecture decision records](primers/architecture-decision-records.md) | how to record a decision so that someone can disagree with it later |
| [Acceptance criteria with EARS](primers/acceptance-criteria.md) | how to write requirements and criteria a test can check |

## Step 3 · Do it (tutorials)

1. [Your first feature with SDD](../tutorials/first-feature.md): a dossier from G0 to G7, step
   by step, with the commands and what to look at.
2. [Working with coding agents](../tutorials/agents.md): Claude Code, Cursor, Codex, Copilot,
   Gemini CLI on this repository.
3. [The documentation site](../tutorials/docs-site.md): run, read and extend the site.

## Step 4 · The chapters (one per dossier)

| Chapter | Dossier | What it teaches |
|---|---|---|
| 0 | [The SDD harness](../../specs/000-sdd-harness/teaching-guide.md) | how the `sdd` tool is built: clean architecture, ports and adapters, strategies, digests, a computed state machine, the composition root, testing with fakes |

New chapters are added here when a dossier's teaching guide is approved (G6).

## Always at hand

- [Glossary](glossary.md): every term of the repository, one line each.
- [Decisions](../architecture/decisions/README.md): the ADRs, the *why* of everything.
