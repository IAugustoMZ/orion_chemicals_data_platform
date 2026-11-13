# Branch protection for `main` (a person applies it)

> **Not applied here (decided 2026-11-13).** This repository is private on a free GitHub plan,
> which does not offer branch protection. Until that changes (a paid plan or a public
> repository) CI only *reports*: a red `quality` does not disable *Merge*. The control is
> our own discipline: we merge a pull request only when `quality` is green, and the agent
> never merges. The checklist below stays for the day protection becomes available.

The workflow only reports. It blocks a merge when GitHub is told to require it
([ADR-0024](../docs/architecture/decisions/0024-ci-with-github-actions-blocks-merge.md)).
An agent never edits these settings; we do, at *Settings → Branches → Add rule* for `main`.

## Checklist

- [ ] Require a pull request before merging (no direct pushes to `main`).
- [ ] Require status checks to pass: select **`quality`** (it appears after the first run).
- [ ] Require branches to be up to date before merging.
- [ ] Do not allow force pushes; do not allow deletion.
- [ ] Include administrators.
- [ ] Optional: require one approving review.
- [ ] Actions → General: workflow permissions set to *Read repository contents*.

## Manual proof (acceptance criterion 5 of card 04)

Without protection, step 1 shows a red `quality` but *Merge* stays enabled; the green/red
signal is what is proved. Pull request #7 gave a real red run (the help test failed on ANSI
codes) and the green run after the fix.

1. Push a change that breaks a rule (for instance an unformatted file). `quality` turns red and
   *Merge* is disabled.
2. Push the fix. `quality` turns green and *Merge* is enabled.
3. Record both runs (links and dates) in `validation.md` of dossier 002.

## Pinned actions

The SHAs in `ci.yml` were written without access to the releases page. Before relying on them,
check each one against its tag (`actions/checkout` v4.2.2, `actions/setup-python` v5.3.0) and
fix the comment or the SHA.
