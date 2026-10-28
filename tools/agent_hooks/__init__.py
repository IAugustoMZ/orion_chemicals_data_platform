"""Agent hooks: guardrails that run inside coding agents before a tool call executes.

This package is standard-library only, so an agent can run it with plain ``python`` before the
Poetry environment exists. Today it holds the Claude Code `PreToolUse` guard
(`agent_guard.py`, wired in `.claude/settings.json`). See `harness/ai-control-plane.md`.
"""
