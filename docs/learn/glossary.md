# Glossary

Every term used in the repository, one line each. Add new terms in the same change that
introduces them.

| Term | Meaning |
|---|---|
| **Acceptance criterion** | a testable condition a work item must meet to be done; written in EARS here |
| **ADR** | Architecture Decision Record: one file recording a decision, its context, alternatives and consequences |
| **Adapter** | an infrastructure class that implements a port with a real technology (YAML files, git, a database) |
| **Agent guard** | the PreToolUse hook (`tools/agent_hooks/agent_guard.py`) that blocks approvals, gate bypasses, guardrail edits and secrets in Claude Code |
| **Agent Skills** | an open standard for packaged instructions: a folder with a `SKILL.md` (name, description, body) |
| **AGENTS.md** | the open, tool-agnostic instruction file for coding agents at the repository root |
| **Aggregate** | a cluster of domain objects changed only through its root (here: the `Dossier`) |
| **Approval** | one team member's "yes" to a human gate, bound to the digest of its artifacts |
| **Artifact** | a Markdown file of a dossier produced in a phase (`prd.md`, `spec.md`, ...) |
| **Blocked** | gate state: an earlier gate has not passed, so this one cannot be judged yet |
| **Checkpoint** (data) | the resume point of an incremental load; must advance only after the data is preserved (RT04) |
| **Composition root** | the one place where adapters are created and wired into use cases (`bootstrap.py`) |
| **Constitution** | the non-negotiable articles of the harness (`harness/constitution.md`) |
| **Context plane** | the governed knowledge agents read: requirements, code, architecture, docs, contracts |
| **Control plane (AI)** | how agents are governed: model routing, guardrails, cost, audit, loop limits |
| **Digest** | a SHA-256 fingerprint of content; an approval stores the digest of what was approved |
| **Dossier** | the folder `specs/<id>-<slug>/` holding everything about one piece of work |
| **EARS** | Easy Approach to Requirements Syntax: sentence patterns like "When X, the system shall Y" |
| **Enabler** | a dossier that builds tooling or foundations; supports RTs without delivering them |
| **Feature** | a dossier that delivers platform behaviour; cites the RTs it serves, or is *outside the catalogue* |
| **Outside the catalogue** | a feature that serves no RT; allowed with a rationale and the list of RTs considered (ADR-0014) |
| **Gate** | the checkpoint closing a phase (G0-G7); human gates are approved by us, automated ones by machines |
| **Governed file** | a file whose change alters behaviour or rules (code, tests, containers, dependencies, harness, agent config); changes only after G4 |
| **Grain** | what one row of a dataset represents (one reading, one order, one order activity) (RT11) |
| **Guides and sensors** | harness engineering terms: instructions that steer an agent before it acts, and checks after |
| **Harness** | everything around an AI agent except the model: guides, sensors, gates |
| **Historian** | an industrial database that stores time series from sensors (tags) |
| **import-linter** | the tool that checks the clean-architecture import contracts (`lint-imports`) |
| **Loop limit** | 3 consecutive failing verifications on one task, after which the agent must ask us |
| **Mermaid** | a text syntax for diagrams rendered in Markdown |
| **Partial** | gate state: one of us approved the current content, the other has not yet |
| **Phase** | a stretch of the lifecycle (Discover, Plan, Structure, Specify, Build, Validate, Release & Learn) |
| **Port** | an application-layer `typing.Protocol` describing what a use case needs from the outside |
| **PRD** | Product Requirements Document: the validated product intent of phase 1 |
| **Readiness** | an artifact is ready when it keeps every template section and has no `TODO(sdd)` |
| **RQ** | a business requirement of the Business Case Canvas (RQ01-RQ25), the source of the RTs |
| **RT** | a technical requirement of the Orion Chemicals catalogue (RT01-RT42) |
| **Stale** | gate state: approvals or a verification exist but the content changed since |
| **Strategy** | a pattern: interchangeable classes behind one interface (doc rules, generators) |
| **STRIDE** | threat categories: spoofing, tampering, repudiation, information disclosure, denial of service, elevation of privilege |
| **Tag** | an industrial measurement point (a sensor's time series), identified by a code in its source |
| **Teaching guide** | the didactic record of a dossier, explaining every decision for the mentee |
| **TODO(sdd)** | the placeholder marking text an author must replace before approval |
| **Traceability matrix** | the generated table RT → dossiers → status (`docs/requirements/traceability.md`) |
| **TTY** | an interactive terminal; `sdd approve` requires one, which agents do not have |
| **Use case** | an application-layer class that performs one thing a user asks for |
| **Value object** | an immutable domain value validated at construction, compared by value |
| **"We"** | the mentor and the mentee: the only approvers of human gates |
