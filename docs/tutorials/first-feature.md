# Tutorial: your first feature with SDD

A walk through one dossier from the first idea to the release, with every command and what to
look at. The example is a plausible first feature of the platform: a CRUD to register data
sources and their integration contracts. The steps are the same for any work. Read
[how the harness works](../../harness/how-it-works.md) first.

**You talk; the agent drives the commands.** In every phase you ask your agent in plain words.
It reads the requirements and the harness, writes the artifact, and runs the `sdd` commands.
You do three things yourselves: review, edit what is wrong, and approve at your terminal
(`sdd approve`, which agents are not allowed to run). The commands below show what happens
under the hood, so you can follow it or do it by hand.

## 0. One-time set-up

```bash
poetry install --with docs          # Python environment (.venv/) with the tools
poetry run pre-commit install       # the local gates run on every commit from now on
git config user.name "Your Name"    # approvals record your git identity
git config user.email "you@example.com"
```

Then put your names in [harness/team.yaml](../../harness/team.yaml) (ids stay `mentor` and
`mentee`). Agents are not allowed to edit that file: do it yourselves.

## 1. Phase 0 · Context: start the dossier (G0)

Tell the agent what you want. You don't name requirements; the agent reads all 42 and maps
the request (skill `sdd-start`):

> **We:** We want a CRUD to register our data sources and their integration contracts.
>
> **Agent:** I read the whole catalogue (`sdd rt`). Proposal:
>
> - **Title:** Source integration contracts · **slug:** `source-contracts` · **kind:** feature
> - **Serves RT02**: every source has a contract with owner, interface, fields, identifier,
>   time reference, limits, frequency and history. The CRUD is where contracts live.
> - **Serves RT01**: a contract declares a read-only interface, and saving one that grants
>   write access is refused.
> - **Must not break RT36**: the CRUD stores no credentials, only a reference to where they
>   are kept.
> - **Related, left out:** RT06 (enforcing the limits during extraction belongs to the loader,
>   later), RT38 (an audit trail of contract changes: a follow-up item).
>
> Shall I create it?
>
> **We:** Yes, but add RT38: we want the audit trail from the start.

The agent updates the mapping, then runs:

```bash
poetry run sdd new "Source integration contracts" --slug source-contracts --rt RT01 --rt RT02 --rt RT38
git switch -c spec/001-source-contracts
poetry run sdd status 001
```

**Look at:** `specs/001-source-contracts/` now has `dossier.yaml` and nine artifacts copied from
the templates. `prd.md` already contains a table of the cited RTs and how each one is verified.
In the status, **G0 is passed** and G1 is *pending*. The README status board shows the new
dossier. If you just want to read a requirement yourself, `poetry run sdd rt RT02` prints it.

### When no requirement applies

Not everything you want is in the catalogue. Say you ask for *"a CRUD where we keep bookmarks
of useful queries"*. The agent reads every RT, finds that none is served (RT31 and RT32 are
about query interfaces, not bookmarks), and tells you plainly:

> **Agent:** No RT covers this. It would be a feature *outside the catalogue*. That's
> allowed, but we need a reason. Proposed rationale: "speeds up our investigations; no
> industrial data involved". It must still respect RT35 (permissions) and RT36 (no
> credentials). Create it?

Once you agree, it runs `sdd new` with `--rationale` instead of `--rt`:

```bash
poetry run sdd new "Query bookmarks" --slug query-bookmarks --rationale "speeds up our investigations; no industrial data involved"
```

G0 passes because the rationale is there. The board shows the dossier as
`feature (outside RTs)`, and the [traceability matrix](../requirements/traceability.md) lists
it under "Work outside the catalogue". The PRD lists the RTs the agent considered, so you can
check at G1 that nothing was missed
([ADR-0014](../architecture/decisions/0014-work-outside-the-requirements-catalogue.md)).

## 2. Phase 1 · Discover (G1)

Ask your agent: *"Use the sdd-discover skill for dossier 001. The need: before loading anything,
we want each source described by a contract we can check, and every connection must be
read-only."* It fills `prd.md`.

**The agent reviews it with us, in the chat** (skill `sdd-review-gate`). It does not hand over a
stack of finished documents: it drafted only the PRD. It briefs us on what the PRD commits us
to, the decisions and what it assumed or invented, and then asks three to five questions we
cannot answer with "yes". For example:

> **Agent:** The PRD measures success by "time to locate and reconcile the data for a case".
> Is that the number you believe in, or would you rather count contracts completed?
> Which scope item would you cut first? Line 58 says "bulk import of contracts": is that
> really in scope for the first release?

We answer, or ask for changes, and the agent applies them. Nothing is written for the approval
itself. When we are satisfied, the agent proposes a one-line note summarising our answers and
stops: **it does not draft the backlog until `sdd status` shows G1 passed.** Then each of us,
at our own terminal:

```bash
poetry run sdd approve 001 G1 --as mentor --note "chose time-to-reconcile; cut bulk import"
poetry run sdd approve 001 G1 --as mentee
```

Each command shows what you approve (artifacts and digest) and asks you to type `001 G1`.

**Look at:** after the first approval G1 is *partial* (waiting for the other); after the second,
*passed*, and G2 becomes *pending*. Try this once: change a word in `prd.md` and run
`poetry run sdd status 001`. G1 is now **stale** and everything after it *blocked*: the approval
was for the old text. Undo the change (or both re-approve).

## 3. Phase 2 · Plan (G2)

Once G1 shows *passed*, ask: *"Use sdd-plan for 001."* The agent writes epics, features and work
items with EARS acceptance criteria in `backlog.md`, then reviews them with us the same way
(briefing, questions, changes). Check that every criterion is testable and that RT01's
verification (*a write attempt is denied*) appears as a criterion. Approve G2, both of us.
The same rhythm repeats for G3, G4, G6 and G7: **one artifact, one review, one approval, then
the next.**

## 4. Phase 3 · Structure (G3)

Agent: *"Use sdd-structure for 001."* For contracts, the interface is probably a YAML file per
source plus a validation command, and no prototype is needed. The file says so, with the reason.
Approve G3.

## 5. Phase 4 · Specify (G4)

Agent: *"Use sdd-specify for 001."* This is the most important review. `spec.md` must have:
numbered behaviours (`SPEC-001-B01 ...`), the architecture before/after with logos, the contract
schema, the classes and patterns, a STRIDE table, a validation plan covering every cited RT, and
ADR drafts (for example "source contracts are YAML validated by a schema"). `plan.md` and
`tasks.md` break the build into small, test-first steps.

```bash
poetry run sdd check                # logos, links, ADR index must be clean
poetry run sdd approve 001 G4 --as mentor
poetry run sdd approve 001 G4 --as mentee
```

**Look at:** before G4, try to commit a file under `src/`: the commit is refused by
`sdd guard-commit` ("G4 is pending"). After G4, the same commit is accepted.

## 6. Phase 5 · Build (G5)

Agent: *"Use sdd-build for 001."* It implements task by task and runs, after each one:

```bash
poetry run sdd verify 001
```

Watch the loop: each check prints PASS or FAIL; a failure shows the last lines of the tool's
output; the agent fixes and verifies again; after three consecutive failures on the same task it
must stop and ask you. When all checks pass, **G5 is passed**, bound to the digest of the code.
Change any governed file afterwards and G5 becomes *stale* until the next `sdd verify`.

## 7. Phase 6 · Validate (G6)

In a **new** agent session (independence): *"Use sdd-validate for 001, acting as the reviewer."*
It reviews the diff against the spec and fills `validation.md`; the teacher role completes
`teaching-guide.md`. You:

```bash
git diff --stat main...spec/001-source-contracts
git diff main...spec/001-source-contracts
```

Read the teaching guide as the mentee would: could you rebuild the feature from it? Then approve
G6 (both) and merge:

```bash
poetry run sdd approve 001 G6 --as mentor
poetry run sdd approve 001 G6 --as mentee
git switch main
git merge --no-ff spec/001-source-contracts
```

## 8. Phase 7 · Release and learn (G7)

Agent: *"Use sdd-release for 001."* It starts the services with Docker Compose, collects the
numbers the PRD's goals need, and drafts `release.md`. We judge the results against the goals,
record the learnings (a lesson about the process becomes a new enabler dossier), and approve G7.

```bash
poetry run sdd status 001           # every gate passed: "done"
```

The dossier's teaching guide joins the [learning path](../learn/README.md) as a new chapter.

## What you practised

- Asking in plain words; the agent maps the request to the requirements, and we confirm (G0).
- One gate at a time: a review conversation with the agent, then six human decisions, each about
  an exact text (digests), at a terminal.
- No code before the specification (commit guard).
- A deterministic build loop with a limit (G5).
- Documentation and teaching as part of the merge (G6).
