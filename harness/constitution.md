# Constitution

The articles below are never negotiable: not for a deadline, not for a small change, not by an
agent and not by us without a new ADR that amends this file through its own dossier. Every other
document of the harness elaborates one of these articles.

## Article I · Requirements first

Every piece of work is checked against the technical requirements in `docs/requirements/`
(RT01-RT42) before anything is proposed, and cites the ones it serves. We ask in plain words;
the agent maps the request to the RTs. Work that serves no requirement is allowed, but says so:
an *enabler* (tooling) or a feature *outside the catalogue* states why it is worth doing, and
its PRD lists the RTs that were considered. *(Gate G0, ADR-0014.)*

## Article II · People decide

The mentor and the mentee decide; AI agents propose and execute. Every human gate (G1, G2, G3,
G4, G6, G7) is closed only by our approvals, given at a terminal, after reading what is
approved. No agent approves, edits an approval, or presents an unapproved gate as approved. Work goes **one gate at a time**: the
agent drafts the next phase only after the previous gate passed, and each review is a
conversation with us, not a document to sign. *(ADR-0003, ADR-0015.)*

## Article III · The specification precedes the code

Governed files (code, tests, containers, dependencies, the harness, agent configuration) change
only on the dossier's branch, after its specification was approved (G4). When the specification
turns out to be wrong, it is changed first and approved again. *(Commit guard.)*

## Article IV · Approvals bind to content

An approval is valid only for the exact content approved. Editing an approved artifact
invalidates the approval until we look again. *(Digests.)*

## Article V · Machines verify what machines can

Everything that can be checked deterministically is checked by a machine before people spend
attention on it: formatting, lint, types, architecture contracts, tests, security scans,
documentation consistency. *(Gate G5, pre-commit.)*

## Article VI · Documentation is part of the change

A change is not done until its decisions are recorded (ADRs), its architecture is drawn (Mermaid,
with the official logo of every tool), the root README tells the truth, and its teaching guide
explains every decision in detail, from the architecture down to classes and abstractions.
*(Gate G6.)*

## Article VII · Quality and security by design

Code follows clean architecture and SOLID, is fully documented and typed, and is tested together
with its implementation. Credentials never appear in the repository; every identity gets only the
permissions its function needs; every input from outside is validated. *(principles.md,
security.md.)*

## Article VIII · One toolchain, one language, one runtime

Python environments are managed only by Poetry. Everything is written in English. The platform
runs locally with Docker Compose. *(ADR-0005, ADR-0009, ADR-0006.)*

## Article IX · Tool-agnostic

The harness works the same with any coding agent. Its canonical sources follow open conventions
(`AGENTS.md`, Agent Skills); tool-specific files are generated or are short pointers.
*(ADR-0002.)*

## Article X · Bounded autonomy

Agents work within explicit limits: the phase of the current dossier, its approved scope, a loop
limit in the build, and a budget. At a limit, the agent stops and asks us; it never works around
a guardrail. *(ai-control-plane.md.)*
