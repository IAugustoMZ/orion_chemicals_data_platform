# ADR-0012: The backlog lives in the repository as Markdown, inside the dossiers

- **Status:** Accepted
- **Date:** 2026-10-21
- **Dossier:** specs/000-sdd-harness
- **Requirements:** none: process decision

## Context

The operating model places work items in a tracker (Azure DevOps in the original picture). This
repository runs locally, without CI or a hosted tracker, and agents must read and write the
backlog as easily as code.

## Decision

The backlog is Markdown in the repository: each dossier's `backlog.md` holds its epics, features
and work items; `specs/README.md` (generated) and `sdd status` are the board; git branches
`spec/<id>-<slug>` and their diffs play the role of pull requests.

## Alternatives considered

| Option | Why it lost |
|---|---|
| Azure DevOps or GitHub Issues | a hosted service and credentials for a local repository; agents would need an MCP server or API access |
| A single `BACKLOG.md` | not tied to dossiers or gates; grows without structure |

## Consequences

- + Versioned with the code, reviewable, approvable at G2, readable by any agent.
- − No tracker features (assignment, dashboards). A sync to a tracker through MCP can be added
  later as an enabler dossier, keeping the Markdown as the source of truth.
