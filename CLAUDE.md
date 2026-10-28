# Claude Code

@AGENTS.md

## Claude Code specifics

- **Skills** are in `.claude/skills/`, generated from the canonical `.agents/skills/` by
  `poetry run sdd sync`. Edit the canonical copy, never the generated one.
- **Subagents** are in `.claude/agents/`, generated from `harness/roles/`. Use the `reviewer`
  subagent for the independent review of phase 6, never the session that wrote the code.
- **Hooks** (`.claude/settings.json`) run `tools/agent_hooks/agent_guard.py` before every tool
  call: it blocks approvals, gate bypasses, guardrail edits and secrets. A blocked call is a
  signal to stop and ask us, not to find a workaround.
