# Gates G0-G7

A gate is the checkpoint that closes a phase. Its state is computed by `sdd` from the evidence in
`dossier.yaml` and the current files ([how it works, §4](how-it-works.md#4-gates-and-their-states)).
Human gates are closed when **both of us** approved the current content (policy in
[team.yaml](team.yaml)); automated gates are closed by a machine.

| Gate | Phase | Kind | Judges | Passes when |
|---|---|---|---|---|
| **G0** Context | 0 | automated | `dossier.yaml` + every artifact | every RT cited exists; every dossier has a rationale |
| **G1** PRD validated | 1 Discover | human | `prd.md` | both of us approved the current `prd.md` |
| **G2** Backlog approved | 2 Plan | human | `backlog.md` | both of us approved the current `backlog.md` |
| **G3** Approach approved | 3 Structure | human | `ux-approach.md` | both of us approved the current `ux-approach.md` |
| **G4** Spec approved | 4 Specify | human | `spec.md`, `plan.md`, `tasks.md` | both of us approved the current three files |
| **G5** Checks passed | 5 Build | automated | every governed file | the last `sdd verify` passed every check on the current code |
| **G6** Approved for merge | 6 Validate | human | `validation.md`, `teaching-guide.md` | both of us approved the current two files (and G5 is passed, not stale) |
| **G7** Results validated | 7 Release & Learn | human | `release.md` | both of us approved the current `release.md` |

## What every human gate requires before it can be approved

`poetry run sdd approve <id> <gate> --as <you>` refuses unless:

1. **every earlier gate passed** (no skipping, no stale predecessor);
2. **the artifacts are ready:** every `##` section of the template is present and no
   `TODO(sdd)` placeholder remains;
3. **you are at an interactive terminal** and answer `y` to the summary shown (`Approve? [y/N]`;
   anything else cancels and records nothing,
   [ADR-0016](../docs/architecture/decisions/0016-approval-confirmation-is-a-yes-no-prompt.md)).

What it records: your member id, the UTC time, the digest of the artifacts, your git identity and
an optional `--note`. The second approval of the same gate turns it *passed*.

**Files appear as gates pass.** When an approval turns a gate *passed*, the harness creates the
artifacts of the next gate from their templates and tells you which ones. A file that already
exists is never overwritten. So the artifact of a phase does not exist before the gate in front of
it is closed ([ADR-0018](../docs/architecture/decisions/0018-artifacts-are-created-as-gates-pass.md)):

| When this happens | the harness creates |
|---|---|
| `sdd new` | `dossier.yaml`, `prd.md` |
| G1 passes | `backlog.md` |
| G2 passes | `ux-approach.md` |
| G3 passes | `spec.md`, `plan.md`, `tasks.md` |
| G4 passes | `validation.md`, `teaching-guide.md` (the build writes them; G5 is automatic) |
| G6 passes | `release.md` |

## What we check before approving (judgement, not machine)

| Gate | Questions we answer together |
|---|---|
| G1 | Is this the right problem? Are the goals measurable, and the metric something we can really observe? Is the scope honest about what is out? Are the RTs the right ones? |
| G2 | Does every item trace to a goal and to RTs? Are acceptance criteria testable EARS statements? Is the order risk-first? Is any item too big to review in one sitting? |
| G3 | Do we really need a prototype? Would a user of this interface succeed in the PRD's scenarios? |
| G4 | Is every behaviour testable? Does the validation plan prove each RT's "how we verify it"? Is the architecture impact drawn with logos? Are the ADRs written and are we convinced by them? Is the threat model complete? Is the plan small-stepped and reversible? |
| G6 | Did we read the diff? Does it match the spec and the plan's file list? Was the review independent? Does the teaching guide teach: could the mentee rebuild the feature from it? Is every document of the upkeep matrix updated? |
| G7 | Did the goals' metrics move? What did we learn, and does the harness need to change because of it? |

## Sending work back

A rejection is not a command: it is a conversation. Write what must change in the artifact (or
in the PR-style review notes of `validation.md`), and the agent revises it. Since the content
changes, any partial approval becomes stale automatically; nothing has to be "un-approved".

## When a gate becomes stale

| Situation | What happens | What to do |
|---|---|---|
| An approved artifact is edited | the gate turns *stale*, later gates *blocked* | review the change (`git diff`), then both re-approve |
| A task box is ticked in `tasks.md` | nothing: the digest ignores box state | — |
| A governed file changes after `sdd verify` | G5 turns *stale*, G6/G7 *blocked* | run `poetry run sdd verify <id>` again |
| A card's text is edited (dossier with `progress.yaml`) | only that card's approvals go stale; the commit guard refuses governed files on its branch | both re-approve the card (`sdd item approve`) |
| Someone leaves or joins the team | approvals by unknown members are reported by `sdd check` | update `team.yaml` (a guardrail file, people only) |

## Commands

```bash
poetry run sdd status [<id>]                      # states and next step
poetry run sdd approve <id> <G1|G2|G3|G4|G6|G7> --as <mentor|mentee> [--note "..."]
poetry run sdd verify <id>                        # closes G5
poetry run sdd item status <id> [<nn>]            # per-card state and approvals
poetry run sdd item approve <id> <nn> --as <mentor|mentee>
poetry run sdd item verify <id> <nn>              # AC tests + suite for one card
poetry run sdd item next <id>                     # open the next card's branch
poetry run sdd item merged <id> <nn>              # record a merge confirmed by git
poetry run sdd check                              # reports stale gates as warnings
```
