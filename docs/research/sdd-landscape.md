# Spec-driven development: the landscape (October 2026)

Research done before designing the harness (dossier 000), to learn what is in use and what to
borrow. Sources are listed at the end; most are practitioner blogs and vendor guides, so numbers
(stars, benchmarks) are indicative only and dated.

## What SDD means

Spec-driven development puts a written, reviewable specification at the centre of AI-assisted
work: people agree on *what* to build in a spec, the agent derives a plan and tasks from it, and
the code is judged against the spec. It answers the main failure of "vibe coding": the agent's
output drifts because nothing durable says what was wanted.

## The tools in use

| Tool | What it is | Workflow | Strengths | Limits (for us) |
|---|---|---|---|---|
| **GitHub Spec Kit** | open-source toolkit, agent-agnostic (works with ~30 agents); the reference implementation of the category | constitution → specify → clarify → plan → tasks → analyze → implement; files in `.specify/` (memory/constitution.md, templates, scripts) and numbered feature folders | clear artifacts per step; a *constitution* of non-negotiable principles; broad tool support | approval steps are conventions, not enforced; no notion of governed people roles |
| **OpenSpec** | lightweight open-source SDD framework | change proposals with *delta* markers against existing specs | best fit for existing codebases (brownfield); fast | validation is structural only; specs are not updated during implementation; no multi-agent orchestration |
| **BMAD-METHOD** | heavyweight method simulating an agile team with many role agents | analyst → PM → architect → scrum master → dev → QA personas | thorough; caught issues the lighter tools missed in one comparison | slow (days vs hours in reported comparisons); a lot of ceremony |
| **Kiro** (AWS) | an IDE built around specs (GA since Nov 2025) | requirements in **EARS** notation → design → tasks | EARS makes acceptance criteria testable | tied to its own editor; gates are review-based, not enforced |

Comparisons converge on: BMAD for complex greenfield work, OpenSpec for legacy changes, Spec Kit
for teams that scale, Kiro for AWS-centric shops. None of them **enforces** human approval
gates; that is the gap our operating model depends on.

## Cross-tool conventions

- **AGENTS.md** is the de facto, tool-agnostic instruction file at the repository root, read by
  most agents (Codex, Cursor, Copilot, Gemini CLI and others); it is now an open format under
  the Linux Foundation's Agentic AI Foundation. Claude Code reads `CLAUDE.md`; support for
  `AGENTS.md` was reported in a recent release but could not be confirmed, so our `CLAUDE.md`
  simply imports it (`@AGENTS.md`).
- **Agent Skills (`SKILL.md`)** is an open standard (agentskills.io): a folder with a `SKILL.md`
  whose front matter has only `name` and `description`; agents load the description at start-up
  and the body when a task matches. Reported to be read by 30+ tools. The *format* is portable,
  the *location* is not: Codex reads `.agents/skills/`, Claude Code `.claude/skills/`, Copilot
  `.github/skills/`, `.claude/skills/` and `.agents/skills/`.
- Tool-specific files remain: `.cursor/rules/*.mdc`, `.github/copilot-instructions.md`,
  `.github/prompts/*.prompt.md`, `.claude/agents/` (subagents), `.claude/settings.json` (hooks).

## Harness engineering

Birgitta Böckeler (Thoughtworks, on martinfowler.com) frames a *harness* as everything around a
coding agent except the model: **guides** that steer it before it acts (AGENTS.md, architecture
documents, skills) and **sensors** that check what it produced (linters, type checkers, tests,
dependency rules, review agents), with fast sensors before commit and heavier ones after.
Practitioners add that the most valuable instruction lines each encode a past agent failure, and
that security needs *deterministic* enforcement, not instructions alone.

## What we borrowed, and what we added

| From | We took | Where |
|---|---|---|
| Spec Kit | a constitution; one artifact per step; templates; spec → plan → tasks | [constitution](../../harness/constitution.md), [templates](../../harness/templates/README.md) |
| Kiro | EARS acceptance criteria and behaviours | [acceptance criteria primer](../learn/primers/acceptance-criteria.md), backlog and spec templates |
| BMAD | focused role personas (lightweight: ten roles, no ceremony) | [roles](../../harness/roles/README.md) |
| OpenSpec | the idea of change deltas (for later, once the platform exists) | future enabler dossier |
| AGENTS.md, Agent Skills | canonical, tool-agnostic sources; generated adapters | [ADR-0002](../architecture/decisions/0002-agents-md-and-agent-skills-are-canonical.md) |
| Harness engineering | guides + sensors; deterministic enforcement | [how it works, §6](../../harness/how-it-works.md#6-how-each-rule-is-enforced) |
| **Added by us** | human gates **enforced** by a TTY-only approval bound to content digests; a commit guard (no code before G4); the operating model's seven phases and two planes; a mandatory teaching guide per dossier; traceability to the RT catalogue | [ADR-0001](../architecture/decisions/0001-spec-driven-development-with-our-own-harness.md), [ADR-0003](../architecture/decisions/0003-gates-approved-by-people-bound-to-digests.md) |

## Sources

- [6 Best Spec-Driven Development Tools for AI Coding in 2026 (Augment Code)](https://www.augmentcode.com/tools/best-spec-driven-development-tools)
- [BMAD vs Spec Kit vs OpenSpec: Choosing Your Spec-Driven AI Framework in 2026 (Medium)](https://medium.com/@reenbit/bmad-vs-spec-kit-vs-openspec-choosing-your-spec-driven-ai-framework-in-2026-a6996b3ebb8d)
- [spec-compare: interactive comparison of SDD tools](https://github.com/cameronsjo/spec-compare)
- [8 Best Spec-Driven Development Tools for Regulated Industries (HackerNoon)](https://hackernoon.com/8-best-spec-driven-development-tools-for-software-engineers-in-regulated-industries-2026)
- [Spec-Driven Development in 2026: Guide + Tool Comparison (CodeMySpec)](https://codemyspec.com/blog/spec-driven-development)
- [The Best Spec-Driven Development Tools in 2026 (BrainGrid)](https://www.braingrid.ai/blog/spec-driven-development-tools)
- [OpenSpec vs Spec Kit vs Superpowers (Felipe Fontoura)](https://felipefontoura.com/articles/spec-driven-development-tools-compared/)
- [OpenSpec vs Spec Kit vs BMAD (AI Coding Patterns)](https://aicodingpatterns.com/en/patterns/openspec-vs-spec-kit-vs-bmad/)
- [GitHub Spec Kit practical guide (Augment Code)](https://www.augmentcode.com/guides/github-spec-kit-practical-guide-sdd-workflow)
- [Spec Kit analysis (Bitovi)](https://wiki.at.bitovi.com/wiki/spaces/AIEnabledDevelopment/pages/1799847940/Spec+Kit+-+Analysis)
- [Harness engineering for coding agent users (Birgitta Böckeler, martinfowler.com)](https://martinfowler.com/articles/harness-engineering.html)
- [Harness engineering: making AI coding agents reliable and secure (Endor Labs)](https://www.endorlabs.com/learn/harness-engineering-how-to-make-ai-coding-agents-reliable-and-secure)
- [The emerging "harness engineering" playbook](https://www.ignorance.ai/p/the-emerging-harness-engineering)
- [AGENTS.md guide: recommended sections, AGENTS.md vs CLAUDE.md vs .cursorrules (Morph)](https://www.morphllm.com/agents-md-guide)
- [AGENTS.md best practices (BetterClaw)](https://www.betterclaw.io/blog/agents-md-best-practices)
- [AI agent configuration files: complete cross-tool guide](https://www.productbuilder.net/learn/agent-config-files)
- [Agent Skills: a cross-tool task knowledge standard (Agent Patterns)](https://www.agentpatterns.ai/standards/agent-skills-standard/)
- [SKILL.md open standard reaches 30+ AI coding tools (Noqta)](https://noqta.tn/en/news/skill-md-open-standard-30-ai-coding-tools-adoption-2026)
- [Cross-platform agent portability: one SKILL.md for every runtime](https://codex.danielvaughan.com/2026/04/08/cross-platform-agent-portability-skill-md/)
- [Material for MkDocs: documentation theme and framework (status and Zensical)](https://pydevtools.com/handbook/reference/mkdocs-material/)
