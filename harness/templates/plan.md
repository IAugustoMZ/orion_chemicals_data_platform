# Implementation plan · {{id}} · {{title}}

> Part of **Phase 4 · Specify** and approved with the spec at **G4**. The plan says *how* the
> build will proceed; the spec says *what* it must achieve.

## Approach

TODO(sdd): The strategy in one paragraph: what is built first and why (walking skeleton, riskiest
part first, test-first), and how the work stays shippable at every step.

## Steps

TODO(sdd): Numbered steps, each small enough for one build loop (implement, `sdd verify`, fix).
Each step names the SPEC behaviours it delivers and the tests that prove it.

1. TODO(sdd)

## Files to create or change

TODO(sdd): Expected files, grouped by layer (domain, application, infrastructure, interfaces,
tests, docker, docs). The reviewer compares this list with the diff at G6.

## Rollback

TODO(sdd): How to undo the change if it misbehaves after merge (revert commit, data clean-up,
feature switch). "Revert the merge commit; no data written" is a valid answer.

## Risks during the build

TODO(sdd): What could go wrong while building and the early signal of it (a failing check, a
slow test, a dependency issue), with what we do then.
