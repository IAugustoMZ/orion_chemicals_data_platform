# Tasks · 004 · Plant and tag catalogue

> Approved with the execution specification at G4. Tick each box after its tests pass.

## Tasks

- [x] T01 · Add inventory, identity and reference integrity tests, then implement the pure model and default profiles. *(B01–B03, step 1, PBI-004-01)*
- [x] T02 · Add CLI and JSON tests, then wire plant build and document its output. *(B02, B04, step 1, PBI-004-01)*
- [ ] T03 · Add grammar, variant, coverage and repeatability tests, then implement the catalogue builder and naming convention. *(B05–B07, step 2, PBI-004-02)*
- [ ] T04 · Add schema, join and scan-policy tests, then wire the Parquet writers and catalog build. *(B08–B09, step 3, PBI-004-03)*
- [ ] T05 · Add failure, retry and path-boundary tests, then verify safe staging, replacement and CLI diagnostics. *(B10, step 3, PBI-004-03)*
- [ ] T06 · Verify the completed dossier, reconcile documentation and record RT evidence for independent review. *(B01–B10, step 4)*

## Loop limits

Run the targeted tests after each task and `poetry run sdd item verify 004 NN` after each
card. Once the cards are merged, run `poetry run sdd verify 004`. Stop after three consecutive
verification failures on the same task and consult the mentor and mentee.
