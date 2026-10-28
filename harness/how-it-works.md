# How the harness works

This page explains, from end to end, how work happens in this repository: who does what, how a
need becomes released software, which checkpoints (*gates*) it passes, and how each rule is
enforced. It is the page to read first, and the one to come back to when something blocks you.

> **In one minute.** Every piece of work is a *dossier*: a folder `specs/<id>-<slug>/` with one
> Markdown artifact per phase. AI agents draft the artifacts and write the code; **we** (the
> mentor and the mentee) decide. Eight gates, G0 to G7, close the phases: six are closed by our
> approvals, two by machines. Approvals are bound to the content they approved, so editing an
> approved artifact silently invalidates the approval until we look again. Code can only change
> after we approved the specification. Everything runs locally: the `sdd` command, `pre-commit`
> and the agents' hooks are the enforcement; there is no CI.

The model comes from the target operating model *"AI-native software execution: driven by
specifications, governed by people, AI executes at scale"*. In this repository every human role
of that model (stakeholder, product owner, designer, tech lead, QA engineer) is played by the two
of us.

## 1. The actors

```mermaid
flowchart TB
    subgraph people["👥 We (harness/team.yaml)"]
        direction LR
        MENTOR["Mentor"]
        MENTEE["Mentee"]
    end
    subgraph agents["🤖 Coding agents (any tool)"]
        direction LR
        CC["<img src='https://cdn.simpleicons.org/claude/D97757' width='28' height='28'/><br/>Claude Code"]
        CU["<img src='https://cdn.simpleicons.org/cursor/000000' width='28' height='28'/><br/>Cursor"]
        CX["<img src='https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/openai.svg' width='28' height='28'/><br/>Codex"]
        CP["<img src='https://cdn.simpleicons.org/githubcopilot/000000' width='28' height='28'/><br/>GitHub Copilot"]
    end
    subgraph machine["⚙️ The machine (deterministic)"]
        direction LR
        SDD["sdd command<br/>gates · approvals · checks"]
        PC["<img src='https://cdn.simpleicons.org/precommit/FAB040' width='28' height='28'/><br/>pre-commit"]
    end
    REPO[("<img src='https://cdn.simpleicons.org/git/F05032' width='28' height='28'/><br/>Repository on branch spec/NNN-slug<br/>requirements · harness · specs · code · docs")]

    people -->|"approve gates"| SDD
    agents -->|"status · check · verify"| SDD
    agents -->|"draft artifacts, write code"| REPO
    PC -->|"every commit"| SDD
    SDD -->|"evidence"| REPO
```

| Actor | What it does | What it may never do |
|---|---|---|
| **We** (mentor, mentee) | share the need, review every artifact, approve or send back each human gate, review the code, decide the merge, judge the results | approve without reading: every approval shows the digest of what is approved |
| **Coding agents** | read the requirements and the harness, draft the PRD, backlog, approach and spec, implement with tests, run the checks, write the documentation and the teaching guide, review each other | approve a gate, edit an approval, change code before G4, skip hooks, touch secrets |
| **The machine** (`sdd`, pre-commit, hooks) | computes gate states from the files, records approvals, runs the quality suite, refuses commits that break the rules, regenerates derived documents | decide anything that needs judgement |

## 2. The workflow, end to end

This is the whole lifecycle in one picture. 👥 marks our activities, 🤖 the agents', ◆ the gates
that only we can close.

```mermaid
flowchart TD
    NEED(["👥 We ask in plain words<br/>'we want a CRUD for X'"]) --> MAP["🤖 Agent maps it to the RTs<br/>(skill sdd-start), or marks it<br/>outside the catalogue with a why"]
    REQ[("docs/requirements<br/>RT01-RT42 catalogue")] -.->|"read first, always"| MAP
    MAP --> OK{"👥 We confirm<br/>the mapping"}
    OK -->|"adjust"| MAP
    OK -->|"yes"| NEW["🤖 sdd new 'Title' --slug x --rt RTnn<br/>creates specs/NNN-x/ and branch spec/NNN-x"]
    NEW --> G0{"G0 · Context<br/>RTs exist? rationale<br/>when none is cited?"}
    G0 -->|"no: fix dossier.yaml"| NEW
    G0 -->|"yes (automatic)"| P1

    subgraph P1["Phase 1 · Discover"]
        W1["👥 We share the need,<br/>the expected results"] --> A1["🤖 Agent analyses inputs,<br/>drafts prd.md (skill sdd-discover)"]
    end
    P1 --> G1{"◆ G1 · PRD validated"}
    G1 -->|"changes requested"| P1
    G1 -->|"both approve"| P2

    subgraph P2["Phase 2 · Plan"]
        A2["🤖 Agent proposes epics, features,<br/>items with EARS acceptance criteria"] --> W2["👥 We review, adjust, prioritise"]
    end
    P2 --> G2{"◆ G2 · Backlog approved"}
    G2 -->|"changes requested"| P2
    G2 -->|"both approve"| P3

    subgraph P3["Phase 3 · Structure"]
        A3["🤖 Agent decides if a prototype is needed,<br/>sketches the interface approach"] --> W3["👥 We validate the approach<br/>(usability only when needed)"]
    end
    P3 --> G3{"◆ G3 · Approach approved"}
    G3 -->|"changes requested"| P3
    G3 -->|"both approve"| P4

    subgraph P4["Phase 4 · Specify"]
        A4["🤖 Agent collects context (RTs, ADRs, code),<br/>writes spec.md, plan.md, tasks.md, draft ADRs"] --> W4["👥 We review and adjust<br/>architecture decisions"]
    end
    P4 --> G4{"◆ G4 · Spec approved for execution"}
    G4 -->|"changes requested"| P4
    G4 -->|"both approve: code may change now"| P5

    subgraph P5["Phase 5 · Build (agentic loop)"]
        A5["🤖 Agent implements one task<br/>+ tests + docs + diagrams"] --> V5["sdd verify NNN<br/>format · lint · types · layers · tests<br/>security · secrets · deps · docs"]
        V5 -->|"fail (up to 3 times)"| A5
        V5 -->|"fail 3 times in a row"| ESC["👥 Agent stops and asks us"]
        ESC --> A5
    end
    V5 -->|"all pass"| G5{"G5 · Checks passed<br/>(automatic, bound to the code)"}

    G5 --> P6
    subgraph P6["Phase 6 · Validate"]
        R6["🤖 Independent reviewer agent:<br/>code, architecture, security"] --> W6["👥 We review the branch diff,<br/>validate functionally, read the teaching guide"]
    end
    P6 --> G6{"◆ G6 · Approved for merge"}
    G6 -->|"changes requested: back to build"| P5
    G6 -->|"both approve"| MERGE["<img src='https://cdn.simpleicons.org/git/F05032' width='24' height='24'/><br/>git merge into main"]

    MERGE --> P7
    subgraph P7["Phase 7 · Release & Learn"]
        A7["<img src='https://cdn.simpleicons.org/docker/2496ED' width='24' height='24'/><br/>🤖 Agent deploys with Docker Compose,<br/>collects telemetry and usage"] --> W7["👥 We validate business results,<br/>prioritise the next items"]
    end
    P7 --> G7{"◆ G7 · Results validated"}
    G7 -->|"both approve"| DONE(["Released and learned"])
    G7 -.->|"lessons about the process"| HARNESS["Improve the harness<br/>(a new enabler dossier)"]
```

Three properties of this flow matter more than any single box:

1. **Nothing is skipped.** A gate can only pass when every earlier gate passed. If an earlier
   gate becomes stale (someone edited its artifact), every later gate shows *blocked* until we
   re-approve it.
2. **Code follows the spec, never the other way round.** Governed files (code, tests,
   containers, dependencies, the harness itself) can only be committed on the dossier's branch
   after G4. Discovering mid-build that the spec is wrong means editing the spec, which makes G4
   stale, which brings us back into the loop. That is intended.
3. **Every loop ends with people.** Rejections at a human gate send the work back to its
   phase; the build loop has a hard limit after which the agent must ask us.

## 3. The dossier

```text
specs/001-source-contracts/
├── dossier.yaml        metadata + evidence: RTs served, approvals, G5 verification
├── prd.md              phase 1 · G1
├── backlog.md          phase 2 · G2
├── ux-approach.md      phase 3 · G3
├── spec.md             phase 4 · G4  ┐
├── plan.md             phase 4 · G4  ├ approved together
├── tasks.md            phase 4 · G4  ┘
├── validation.md       phases 5-6 · G6  ┐ approved together
├── teaching-guide.md   phases 5-6 · G6  ┘
└── release.md          phase 7 · G7
```

`sdd new` creates the folder from [the templates](templates/README.md), pre-filled with what is
known: the title, the branch, and a table of the cited requirements with how each one is
verified. Two conventions turn templates into a *definition of ready*:

- every `##` heading of a template is a **required section** of the artifact;
- every `TODO(sdd)` is text the author **must replace**; `sdd approve` refuses while one remains.

`dossier.yaml` holds the evidence. The parts we edit by hand are the title, the requirements and
the rationale; `approvals` and `verification` are written only by `sdd` (agents are blocked from
editing them, see §6).

## 4. Gates and their states

A gate's state is **never stored**: it is computed every time from the evidence in
`dossier.yaml` and the *current* content of the files. That is how a stale approval becomes
visible the moment an approved artifact changes.

```mermaid
stateDiagram-v2
    direction LR
    [*] --> blocked
    blocked --> pending: every earlier gate passed
    pending --> partial: one of us approved the current content
    partial --> passed: the other one approved it too
    pending --> passed: policy "any" and one approval
    passed --> stale: an approved artifact was edited
    partial --> stale: an approved artifact was edited
    stale --> partial: one of us re-approves
    stale --> passed: both re-approve
    passed --> blocked: an earlier gate became stale
```

The two automated gates have their own rules:

- **G0 · Context** passes when every RT cited in `dossier.yaml` *or mentioned in any artifact*
  exists in the catalogue, and an enabler or a feature that cites no RT (*outside the
  catalogue*, [ADR-0014](../docs/architecture/decisions/0014-work-outside-the-requirements-catalogue.md))
  states its rationale.
  It is checked continuously; no action closes it.
- **G5 · Checks passed** passes when the last `sdd verify` ran every check of
  [checks.yaml](checks.yaml) successfully **on the current governed code**. Change one governed
  file afterwards and G5 is *stale*.

```mermaid
stateDiagram-v2
    direction LR
    [*] --> pending: no verification yet
    pending --> failed: sdd verify, a check failed
    pending --> passed: sdd verify, all checks passed
    failed --> passed: fixed, sdd verify again
    passed --> stale: a governed file changed
    stale --> passed: sdd verify again
    stale --> failed: sdd verify again, a check failed
```

The criteria of every gate, one by one, are in [gates.md](gates.md).

### Why digests

An approval stores the SHA-256 digest of the gate's artifacts at the moment we approved. Two
normalisations keep the digest about meaning, not noise: line endings are unified (Windows and
Linux agree), and Markdown task boxes are reset (ticking `- [x]` in `tasks.md` during the build
does not invalidate the approved plan, but rewording a task does).

## 5. What happens when…

### …a phase ends and a gate is next

Reading and signing is not a review, so the agent never hands us a finished stack of documents.
It works one gate at a time and reviews each one with us ([ADR-0015](../docs/architecture/decisions/0015-one-gate-at-a-time-reviewed-in-chat.md)).

```mermaid
sequenceDiagram
    autonumber
    actor W as We (mentor + mentee)
    participant A as Agent (skill sdd-review-gate)
    participant M as sdd (status, approve)
    A->>A: draft only this gate's artifact
    A->>W: brief: what we commit to, decisions and rejected alternatives,<br/>what it assumed or invented, risks
    A->>W: 3-5 specific questions (a choice, a cut, a spot check, a consequence)
    W->>A: answers, or requested changes
    A->>W: applies the changes, re-briefs only what changed
    A->>W: ready: proposed note + the two approve commands
    W->>M: each of us approves at our own terminal (type "001 G1")
    A->>M: sdd status: is the gate passed?
    M-->>A: passed
    A->>A: only now start the next phase
```

`sdd check` warns when an artifact is complete while the gate before it has not passed
(`written-ahead`), so running ahead is visible.

### …we approve a gate

```mermaid
sequenceDiagram
    autonumber
    actor P as One of us (at a terminal)
    participant CLI as sdd approve
    participant UC as ApproveGate (use case)
    participant FS as specs/NNN-x/
    P->>CLI: poetry run sdd approve 001 G4 --as mentor
    CLI->>UC: execute("001", G4, "mentor", note)
    UC->>UC: human gate? known member?
    UC->>FS: read dossier.yaml + artifacts
    UC->>UC: G0-G3 passed? spec/plan/tasks have every section, no TODO(sdd)?
    UC->>P: summary: dossier, gate, artifacts, digest, approver
    UC->>P: "Type '001 G4' to approve"
    P->>UC: 001 G4
    UC->>FS: dossier.yaml += approval {member, at (UTC), digest, git identity, note}
    UC-->>CLI: G4 is "partial" (waiting for mentee) or "passed"
    CLI->>FS: sdd sync: README status board, specs index, traceability
```

If any check fails, nothing is written and the command explains why (`Not ready for approval:`
followed by the missing sections and placeholders, or the earlier gate that is not passed).

### …an agent tries to approve

```mermaid
sequenceDiagram
    autonumber
    participant A as Coding agent
    participant H as Agent hook (where the tool supports it)
    participant CLI as sdd approve
    A->>H: run "poetry run sdd approve 001 G4 --as mentor"
    alt tool with hooks (Claude Code)
        H-->>A: blocked: approvals are made by people (exit 2)
    else tool without hooks
        H->>CLI: the command runs
        CLI-->>A: refused: no interactive terminal on stdin
    end
    Note over A: The agent reports that G4 is ready and asks us to approve.
```

The terminal check is what makes this work for **every** tool: agents execute commands with no
terminal attached, so `isatty()` is false and the approval is refused before anything is asked.
Piping the answer in (`echo "001 G4" | sdd approve ...`) fails for the same reason.

### …the agent builds

```mermaid
sequenceDiagram
    autonumber
    participant A as Build agent
    participant R as Repository (branch spec/001-x)
    participant V as sdd verify 001
    loop each task in tasks.md
        A->>R: implement the task, its tests, its docs
        A->>V: run the quality suite
        alt every check passes
            V-->>A: G5 passed, bound to the governed digest
            A->>R: tick the task, commit (pre-commit runs)
        else a check fails (attempt 1-3)
            V-->>A: failing check + last lines of its output
            A->>R: fix and try again
        else third consecutive failure
            A-->>A: stop, write the build log, ask us
        end
    end
```

### …anyone commits

```mermaid
sequenceDiagram
    autonumber
    actor D as Person or agent
    participant G as git commit
    participant PC as pre-commit
    participant S as sdd
    D->>G: git commit
    G->>PC: run the hooks on the staged files
    PC->>S: sdd guard-commit (the staged file names)
    alt governed file staged and (not on spec/NNN-x or G4 not passed)
        S-->>PC: refused (commit stops)
    else allowed
        PC->>PC: ruff format · ruff check · mypy · lint-imports · pytest · detect-secrets
        PC->>S: sdd sync (regenerate derived documents)
        PC->>S: sdd check (dossiers, docs, logos, links, ADRs, drift)
        PC-->>G: all hooks passed: the commit is recorded
    end
```

## 6. How each rule is enforced

The harness follows the *guides and sensors* idea of harness engineering: **guides** steer the
agent before it acts (feed-forward), **sensors** check what it produced (feedback), and the
decisions stay with people.

```mermaid
flowchart LR
    subgraph guides["Guides (before the agent acts)"]
        AG["AGENTS.md<br/>+ one pointer file per tool"]
        CO["constitution.md · lifecycle.md · gates.md"]
        SK["Skills .agents/skills/<br/>one per phase + cross-cutting"]
        TP["Templates harness/templates/<br/>required sections, TODO(sdd)"]
    end
    subgraph sensors["Sensors (after the agent acts)"]
        HK["<img src='https://cdn.simpleicons.org/claude/D97757' width='24' height='24'/><br/>Agent hook<br/>(Claude Code PreToolUse)"]
        PCM["<img src='https://cdn.simpleicons.org/precommit/FAB040' width='24' height='24'/><br/>pre-commit<br/>guard · lint · types · tests · check"]
        VF["sdd verify (G5)<br/>full deterministic suite"]
        CK["sdd check<br/>consistency of everything"]
    end
    subgraph decide["Decisions (people)"]
        AP["sdd approve<br/>TTY only, digest-bound"]
    end
    guides --> sensors --> decide
```

| Rule | Guide | Sensor | Works in every tool? |
|---|---|---|---|
| Read the requirements first | AGENTS.md §1, every skill | G0 fails on unknown RTs | yes |
| Only people approve | AGENTS.md §3, constitution art. II | TTY check in `sdd approve`; hook blocks `sdd approve` and edits of `approvals:` | yes (TTY); hook adds a second net in Claude Code |
| No code before G4 | constitution art. III | `sdd guard-commit` in pre-commit | yes |
| Don't bypass the gates | AGENTS.md §3 | hook blocks `--no-verify`, `pre-commit uninstall`; guardrail files protected | Claude Code only; elsewhere relies on the guide |
| Quality, security, layers | principles.md, security.md, quality.md | pre-commit subset; full suite in `sdd verify` | yes |
| Documentation with every change | documentation-standard.md, architecture-upkeep.md | `sdd check`: ADR index, links, logos, generated drift; G6 needs a complete teaching guide | yes |
| No secrets | security.md, RT36 | detect-secrets; hook blocks `.env`, keys, `deploy/secrets/` | yes (scan); hook in Claude Code |

**Limits, stated honestly.** The harness protects against *mistakes* by agents and people, not
against a person deliberately cheating: someone with a terminal can approve without reading, and
someone can uninstall pre-commit. The digest and the git identity stored with each approval make
that visible in the history, which is the right tool between two people who trust each other.

## 7. The two planes of the operating model

The operating model has two horizontal planes under the lifecycle. Here is where each of their
parts lives in this repository; details in [context-plane.md](context-plane.md) and
[ai-control-plane.md](ai-control-plane.md).

| Governed context plane (what agents know) | Here |
|---|---|
| Work items, repositories, PRs | dossiers in `specs/`, backlog as Markdown, git branches (ADR-0012) |
| Codebase | the repository itself; module maps in the architecture pages |
| Architecture: patterns, guides | `docs/architecture/`, ADRs, [principles.md](principles.md) |
| Design system: tokens, components | added by the first spec with a user interface |
| Documentation: product, technology, domain | `docs/`, the teaching guides, the requirement catalogue |
| APIs and data: schemas, contracts | contracts sections of each spec; added with the platform |
| Test infrastructure, test data | `tests/`, fixtures, `harness/checks.yaml` |
| Observability: metrics, logs | added with the platform (OpenTelemetry is a candidate) |
| Security and policies | [security.md](security.md), the agent guard, detect-secrets |

| AI control plane (how agents are governed) | Here |
|---|---|
| Model routing | which model plays which role: [ai-control-plane.md](ai-control-plane.md#model-routing) |
| Guardrails: safety, policy | the agent guard, the constitution, TTY-only approvals |
| Cost control: tokens, budget | budget per dossier, stated in `plan.md` |
| Observability: usage, quality | the build log in `validation.md`, `sdd verify` history in `dossier.yaml` |
| Audit: traceability | approvals with digest and identity; RT → dossier → ADR → code traceability matrix |
| Fallback and loop limits | 3 failed verifications then escalate; fallback to a person |

## 8. One feature, start to finish (commands)

```bash
# 0. Context: we ask the agent in plain words; it reads every RT, proposes the mapping
#    (here RT01, RT02) and, once we agree, runs:
poetry run sdd rt
poetry run sdd new "Source integration contracts" --slug source-contracts --rt RT01 --rt RT02
git switch -c spec/001-source-contracts

# 1-4. The agent drafts prd.md, backlog.md, ux-approach.md, spec.md/plan.md/tasks.md;
#      after each one we review it together, then each of us approves at the terminal:
poetry run sdd approve 001 G1 --as mentor
poetry run sdd approve 001 G1 --as mentee
#      ... the same for G2, G3, G4

# 5. The agent builds, task by task, looping on the suite:
poetry run sdd verify 001

# 6. Review, validation.md and teaching-guide.md complete; then we approve the merge:
poetry run sdd approve 001 G6 --as mentor
poetry run sdd approve 001 G6 --as mentee
git switch main && git merge --no-ff spec/001-source-contracts

# 7. Release with Docker Compose, observe, write release.md, then approve G7.
poetry run sdd status 001
```

The long version, with what to look at in each step, is the tutorial
[Your first feature with SDD](../docs/tutorials/first-feature.md).

## 9. Why it is built this way

| Choice | Decision record |
|---|---|
| Our own lightweight harness instead of adopting one framework as is | [ADR-0001](../docs/architecture/decisions/0001-spec-driven-development-with-our-own-harness.md) |
| AGENTS.md and Agent Skills as the canonical, tool-agnostic sources | [ADR-0002](../docs/architecture/decisions/0002-agents-md-and-agent-skills-are-canonical.md) |
| Gates approved by both of us, bound to digests, at a terminal | [ADR-0003](../docs/architecture/decisions/0003-gates-approved-by-people-bound-to-digests.md) |
| Local enforcement only (pre-commit, `sdd`), no CI | [ADR-0004](../docs/architecture/decisions/0004-local-enforcement-without-ci.md) |
| Every feature has a teaching guide inside its dossier | [ADR-0010](../docs/architecture/decisions/0010-every-dossier-has-a-teaching-guide.md) |

All decisions: [docs/architecture/decisions/](../docs/architecture/decisions/README.md). The
code of `sdd` itself, class by class, is explained in the
[teaching guide of dossier 000](../specs/000-sdd-harness/teaching-guide.md).
