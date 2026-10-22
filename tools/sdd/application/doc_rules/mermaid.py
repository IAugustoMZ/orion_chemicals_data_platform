"""Rules for Mermaid diagrams: a known diagram type, and official logos for every tool.

Application layer. `harness/documentation-standard.md` asks that every architecture diagram
shows each technology with its official logo, embedded in the node label as
``<img src='https://cdn.simpleicons.org/...'>``. `MermaidLogoRule` finds node labels that name a
registered tool without an image. It is an *error* in the documents listed as strict (the
architecture pages and the root README) and a *warning* elsewhere, so a teaching guide can still
use a plain sketch while we discuss it.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from sdd.application.doc_rules.markdown import FencedBlock, fenced_blocks
from sdd.application.ports.documents import Document
from sdd.application.ports.reference_data import Logo
from sdd.domain.findings import Finding, Severity

DIAGRAM_TYPES: frozenset[str] = frozenset(
    {
        "flowchart", "graph", "sequencediagram", "classdiagram", "statediagram",
        "statediagram-v2", "erdiagram", "journey", "gantt", "pie", "mindmap", "timeline",
        "gitgraph", "quadrantchart", "requirementdiagram", "c4context", "c4container",
        "c4component", "c4dynamic", "c4deployment", "architecture-beta", "block-beta",
        "sankey-beta", "xychart-beta", "kanban", "packet-beta",
    }
)  # fmt: skip
"""First keyword of every Mermaid diagram type we accept (lower-cased)."""

_LABEL = re.compile(r"[\w-]+\s*(?:\[\[|\[\(|\(\(|\[/|\[\\|\[|\(|\{\{|\{|>)\s*\"(?P<q>[^\"]*)\"")
_PLAIN_LABEL = re.compile(r"[\w-]+\s*\[(?P<p>[^\]\"(\[/\\][^\]\"]*)\]")
_IMG = re.compile(r"<img\b", re.IGNORECASE)
_TAG = re.compile(r"<[^>]+>")


def _diagram_type(block: FencedBlock) -> str:
    """Return the diagram's first keyword, skipping blank lines, comments and front matter.

    Args:
        block: a ``mermaid`` fenced block.
    """
    in_front_matter = False
    for line in block.lines:
        stripped = line.strip()
        if stripped == "---":
            in_front_matter = not in_front_matter
            continue
        if in_front_matter or not stripped or stripped.startswith("%%"):
            continue
        return stripped.split()[0].lower()
    return ""


class MermaidDiagramTypeRule:
    """Every ``mermaid`` block must start with a known diagram type."""

    def check(self, document: Document) -> Iterable[Finding]:
        """Report blocks whose first keyword is not a Mermaid diagram type.

        Args:
            document: the Markdown document.
        """
        for block in fenced_blocks(document.text):
            if block.language != "mermaid":
                continue
            kind = _diagram_type(block)
            if kind not in DIAGRAM_TYPES:
                yield Finding(
                    "mermaid-type",
                    Severity.ERROR,
                    f"unknown Mermaid diagram type {kind!r}",
                    f"{document.path}:{block.start_line}",
                )


class MermaidLogoRule:
    """Flowchart nodes that name a registered tool must embed its official logo."""

    def __init__(self, logos: tuple[Logo, ...], strict_paths: tuple[str, ...]) -> None:
        """Prepare one word-boundary pattern per tool name and alias.

        Args:
            logos: the logo registry.
            strict_paths: path prefixes (or exact paths) where a missing logo is an error.
        """
        # A tool name counts as a word, not as part of a path or file name: "Docker Compose"
        # matches, "docker/docs.Dockerfile", ".claude/" and "mkdocs.yml" do not.
        self._patterns = tuple(
            (logo, re.compile(rf"(?<![\w./-]){re.escape(n)}(?![\w/-]|\.\w)", re.IGNORECASE))
            for logo in logos
            for n in (logo.name, *logo.aliases)
        )
        self._strict = strict_paths

    def check(self, document: Document) -> Iterable[Finding]:
        """Report node labels in flowcharts that mention a tool without an ``<img>``.

        Args:
            document: the Markdown document.
        """
        severity = Severity.ERROR if document.path.startswith(self._strict) else Severity.WARNING
        for block in fenced_blocks(document.text):
            if block.language != "mermaid" or _diagram_type(block) not in {"flowchart", "graph"}:
                continue
            for offset, line in enumerate(block.lines, start=1):
                for tool in self._tools_without_logo(line):
                    yield Finding(
                        "mermaid-logo",
                        severity,
                        f"node mentions {tool} without its logo (see logos/registry.yaml)",
                        f"{document.path}:{block.start_line + offset}",
                    )

    def _tools_without_logo(self, line: str) -> tuple[str, ...]:
        """Return the tools named in node labels of `line` whose label has no image.

        Args:
            line: one line of a flowchart (subgraph titles are not node labels).
        """
        if line.strip().lower().startswith("subgraph"):
            return ()
        labels = [m.group("q") for m in _LABEL.finditer(line)]
        labels += [m.group("p") for m in _PLAIN_LABEL.finditer(line)]
        found: list[str] = []
        for label in labels:
            if _IMG.search(label):
                continue
            words = _TAG.sub(" ", label)
            found += [logo.name for logo, p in self._patterns if p.search(words)]
        return tuple(dict.fromkeys(found))
