# Agent roles

Each role is a focused persona for one kind of work in the lifecycle. The files are
tool-agnostic Markdown with a small front matter (`name`, `description`, optional `tools`).
`poetry run sdd sync` turns each one into a Claude Code subagent (`.claude/agents/<name>.md`); in
other tools, start a session and paste or reference the role file ("act as
`harness/roles/reviewer.md`").

| Role | Phase | Skill it usually runs | Key constraint |
|---|---|---|---|
| [product-analyst](product-analyst.md) | 1 Discover | `sdd-discover` | proposes, never decides scope |
| [backlog-planner](backlog-planner.md) | 2 Plan | `sdd-plan` | every item traceable, testable criteria |
| [ux-designer](ux-designer.md) | 3 Structure | `sdd-structure` | prototype only when it reduces real uncertainty |
| [spec-architect](spec-architect.md) | 4 Specify | `sdd-specify`, `write-adr`, `threat-model` | no code; decisions as ADRs |
| [implementer](implementer.md) | 5 Build | `sdd-build` | only after G4; tests with the code; loop limit |
| [verifier](verifier.md) | 5 Build | `sdd-build` (verify step) | reports, never edits code |
| [reviewer](reviewer.md) | 6 Validate | `sdd-validate`, `commit-review` | independent: never the implementer's session |
| [qa-explorer](qa-explorer.md) | 6 Validate | `sdd-validate` | validates against the spec and the RTs' verification |
| [teacher](teacher.md) | 5-6 | `write-teaching-guide`, `diagrams-with-logos` | explains every decision for the mentee |
| [release-steward](release-steward.md) | 7 Release & Learn | `sdd-release` | facts and numbers, not success stories |

All roles obey [AGENTS.md](../../AGENTS.md) and the [constitution](../constitution.md): none of them
approves a gate.
