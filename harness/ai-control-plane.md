# AI control plane

How coding agents are governed while they work: which model plays which role, which guardrails
hold, how cost and loops are bounded, and how their work stays auditable. The operating model
lists six capabilities; each has a concrete form here.

## Model routing

Use the strongest available model where judgement is expensive to get wrong, and a fast model
for mechanical work. The harness does not hard-code model names (they change every few months);
it fixes the *profile* per role, and each tool maps it to its current models.

| Role ([roles/](roles/README.md)) | Phase | Profile | Why |
|---|---|---|---|
| product analyst, backlog planner | 1, 2 | strong reasoning | ambiguity, trade-offs, writing for people |
| UX designer | 3 | strong reasoning | judgement about people's interaction |
| spec architect | 4 | strongest available | architecture and threat model are costly to fix later |
| implementer | 5 | strong coding | many edits, tests, tool use |
| verifier | 5 | fast | runs commands and reads output |
| reviewer | 6 | strongest available, **different session from the implementer** | independence is the point |
| QA explorer | 6 | strong coding | exploratory testing |
| teacher | 6 | strong reasoning and writing | didactic quality |
| release steward | 7 | fast | commands and summaries |

In Claude Code the subagents in `.claude/agents/` inherit the session model unless a spec says
otherwise; in other tools pick the model when starting the session.

## Guardrails

| Guardrail | Mechanism | Scope |
|---|---|---|
| Only people approve gates | `sdd approve` needs an interactive terminal (all tools); the agent guard blocks `sdd approve` (Claude Code) | all gates |
| Evidence is never forged | the agent guard blocks edits of `approvals:` / `verification:` in `dossier.yaml`; digests expose any change | all dossiers |
| No code before G4 | `sdd guard-commit` in pre-commit | governed files |
| Gates are never bypassed | the agent guard blocks `--no-verify`, `pre-commit uninstall`, forced pushes, hard resets | Claude Code |
| Guardrails are changed by people | the agent guard protects `.claude/settings.json`, `.pre-commit-config.yaml`, `harness/team.yaml`, `tools/agent_hooks/` | Claude Code |
| No secrets in context | the agent guard blocks `.env*` (except `.env.example`), keys, `deploy/secrets/`; detect-secrets | all |

The agent guard is [`tools/agent_hooks/agent_guard.py`](../tools/agent_hooks/agent_guard.py),
wired as a `PreToolUse` hook in `.claude/settings.json`. To let an agent change a guardrail
deliberately (inside an approved enabler dossier), a person starts the agent with
`SDD_ALLOW_GUARDRAIL_EDITS=1` in its environment; the agent cannot set that for the hook itself.
Other tools rely on the terminal check, pre-commit and the instructions; adding their native
hooks is a future enabler dossier.

## Cost control

- Each `plan.md` states a **budget** for the build (sessions or tokens, as the tool reports
  them) when the dossier is large; the build log in `validation.md` records what was spent.
- Prefer narrow context: point the agent at the dossier, the relevant ADRs and modules, not at
  the whole repository.
- Fast models for verification and mechanical steps (see routing).

## Observability of agent work

- **What the agent did:** the build log in `validation.md` (iterations, failures, escalations)
  and the git history of the branch.
- **How good it was:** every `sdd verify` result is stored in `dossier.yaml` (check by check,
  with the governed digest and the commit).
- **Usage:** the tool's own usage reports, summarised in the build log when a budget was set.

## Audit and traceability

- Every approval records member, UTC time, digest, git identity and note (RT38 applied to us).
- Every dossier cites its RTs; the traceability matrix
  ([docs/requirements/traceability.md](../docs/requirements/traceability.md)) links RT → dossier →
  status; ADRs link dossier → decision; the teaching guide links decision → code.

## Loop limits and escalation

- **Build loop:** after **3 consecutive failing `sdd verify` runs on the same task**, the agent
  stops, writes what it tried in the build log, and asks us. A dossier may set another limit in
  `tasks.md` with a reason.
- **Spec drift:** when the build shows that the spec is wrong, the agent stops and proposes a spec
  change; it never "fixes" the spec silently (that would make G4 stale anyway).
- **Blocked action:** when the guard blocks a call, the agent reports it and asks; it never looks
  for another way to do the same thing.
- **Fallback:** when an agent or a model is unavailable or unreliable, the work continues with a
  person; nothing in the harness depends on a specific vendor.
