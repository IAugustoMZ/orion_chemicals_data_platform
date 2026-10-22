---
name: diagrams-with-logos
description: Use whenever drawing or updating a Mermaid diagram (architecture, deployment, flows, classes, data) so every tool node carries its official logo from the registry and the diagram type fits the question.
---

# Mermaid diagrams with official logos

Standard: [documentation standard, diagrams](../../../harness/documentation-standard.md#diagrams-and-official-logos).
Registry: [docs/architecture/logos/registry.yaml](../../../docs/architecture/logos/registry.yaml).

## Steps

1. Pick the type for the question: parts and connections → `flowchart`; order → `sequenceDiagram`;
   states → `stateDiagram-v2`; classes → `classDiagram`; data → `erDiagram`; user path → `journey`.
2. Quote every label, use `<br/>` for line breaks, one idea per node.
3. For every node that is a tool or technology, embed its logo from the registry:

   ```text
   API["<img src='https://cdn.simpleicons.org/fastapi/009688' width='32' height='32'/><br/>FastAPI<br/>query API"]
   ```

4. A tool missing from the registry: add it (name, aliases, URL from Simple Icons
   `https://cdn.simpleicons.org/<slug>/<hex>`, or Devicon when Simple Icons lacks it), and check
   the URL answers (`curl -sI <url>`).
5. Narrate the diagram below it: one sentence per box or arrow that is not self-evident.
6. `poetry run sdd check`: no `mermaid-type` error, no `mermaid-logo` finding.
7. Optionally preview on the site: `poetry run mkdocs serve`.

## Done when

The diagram answers one question, every tool shows its logo, and the text explains it.
