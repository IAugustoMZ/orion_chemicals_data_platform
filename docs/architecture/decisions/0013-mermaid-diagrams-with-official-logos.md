# ADR-0013: Diagrams are Mermaid with official logos from a registry, checked by `sdd check`

- **Status:** Accepted
- **Date:** 2026-10-21
- **Dossier:** specs/000-sdd-harness
- **Requirements:** none: documentation decision

## Context

Every change must be documented with diagrams that use the official logo of each tool. Diagrams
must be diffable in review, render on GitHub, in editors and on the documentation site, and be
written by agents as easily as by people.

## Decision

- Diagrams are **Mermaid** in Markdown. Tool nodes embed their official logo as an `<img>` in the
  label (the approach the reference platform used).
- Logos come from one registry, `docs/architecture/logos/registry.yaml` (Simple Icons CDN first,
  Devicon or a pinned Simple Icons release when a brand is missing; every URL checked to answer).
- `sdd check` (rule `mermaid-logo`) flags flowchart nodes naming a registered tool without an
  image: an error in `docs/architecture/` and the root README, a warning elsewhere. Rule
  `mermaid-type` rejects unknown diagram types.

## Alternatives considered

| Option | Why it lost |
|---|---|
| Generated SVG pictures (as the reference's high-level image) | beautiful, but not diffable and needs a generator per picture; kept as a fallback if a renderer refuses images |
| Mermaid `architecture-beta` with icon packs | icon packs must be registered by the renderer; GitHub does not register them |
| Draw.io / Excalidraw files | binary-ish, not reviewable in a diff, not writable by agents reliably |

## Consequences

- + One syntax for every kind of diagram; logos stay consistent; the check keeps them so.
- − Images come from CDNs: offline, diagrams show their text without logos.
- − Renderers must allow HTML labels; verified with Mermaid's own renderer. If a renderer strips
  them, the fallback is a generated SVG for that page.
