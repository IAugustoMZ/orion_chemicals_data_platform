"""Unit tests of the documentation rules, the generators and the check/sync use cases."""

from __future__ import annotations

from sdd.application.doc_rules.adr import AdrRule
from sdd.application.doc_rules.links import LocalLinkRule
from sdd.application.doc_rules.markdown import fenced_blocks, prose_lines
from sdd.application.doc_rules.mermaid import MermaidDiagramTypeRule, MermaidLogoRule
from sdd.application.generators.adapters import AdapterGenerator
from sdd.application.generators.status import StatusGenerator
from sdd.application.generators.text_tools import replace_block, split_front_matter
from sdd.application.generators.traceability import TraceabilityGenerator
from sdd.application.ports.documents import Document
from sdd.application.use_cases.check_harness import CheckHarness
from sdd.application.use_cases.evaluate_dossier import EvaluateDossier
from sdd.application.use_cases.lint_docs import LintDocs
from sdd.application.use_cases.sync_generated import SyncGenerated
from sdd.domain.approval import Approval
from sdd.domain.findings import Severity
from sdd.domain.gates import GateId
from tests.sdd.fakes import (
    NOW,
    READY,
    FakeCatalog,
    FakeDossiers,
    FakeTeam,
    FakeWorkspace,
    MemoryStore,
    StaticLogos,
    dossier,
)

FENCE = "```"


def mermaid(body: str) -> str:
    return f"{FENCE}mermaid\n{body}\n{FENCE}\n"


class TestMarkdownHelpers:
    def test_fenced_blocks_and_prose(self):
        text = f"intro `[x](y)`\n{FENCE}python\nprint(1)\n{FENCE}\nafter\n"
        (block,) = fenced_blocks(text)
        assert (block.language, block.start_line, block.lines) == ("python", 2, ("print(1)",))
        assert [line for _, line in prose_lines(text)] == ["intro ``", "after"]


class TestMermaidRules:
    def test_unknown_diagram_type(self):
        doc = Document("a.md", mermaid("%% comment\nflowchrt LR\n  A --> B"))
        (finding,) = MermaidDiagramTypeRule().check(doc)
        assert finding.location == "a.md:1"
        assert (
            list(MermaidDiagramTypeRule().check(Document("b.md", mermaid("sequenceDiagram"))))
            == []
        )

    def test_logo_required_in_strict_paths(self):
        rule = MermaidLogoRule(StaticLogos().logos(), ("docs/architecture/",))
        body = 'flowchart LR\n  DB[("Postgres 16")] --> API["<img src=\'x\'/> Python API"]'
        (finding,) = rule.check(Document("docs/architecture/x.md", mermaid(body)))
        assert finding.severity is Severity.ERROR
        assert "PostgreSQL" in finding.message
        (warning,) = rule.check(Document("specs/001-x/teaching-guide.md", mermaid(body)))
        assert warning.severity is Severity.WARNING

    @staticmethod
    def findings(body: str):
        rule = MermaidLogoRule(StaticLogos().logos(), ("docs/",))
        return list(rule.check(Document("docs/a.md", mermaid(body))))

    def test_subgraphs_plain_labels_and_other_diagrams(self):
        assert self.findings('flowchart LR\n subgraph s["Python"]\n end') == []
        assert len(self.findings("graph TD\n  A[Python job]")) == 1
        assert self.findings("sequenceDiagram\n  A->>B: Python") == []

    def test_paths_and_file_names_are_not_tool_mentions(self):
        assert self.findings('flowchart LR\n  A["tools/python/x · python.md · .python/"]') == []
        assert len(self.findings('flowchart LR\n  A["Runs Python."]')) == 1


class TestLinkRule:
    def test_reports_broken_relative_links_only(self):
        store = MemoryStore({"docs/a.md": "", "docs/b.md": ""})
        text = (
            "[ok](b.md) [anchor](b.md#x) [ext](https://x.org) [top](#t) [bad](missing.md)\n"
            f"{FENCE}\n[ignored](nope.md)\n{FENCE}\n`[code](nope.md)`\n"
        )
        (finding,) = LocalLinkRule(store).check(Document("docs/a.md", text))
        assert finding.location == "docs/a.md:1"
        assert "missing.md" in finding.message


class TestAdrRule:
    def test_format_index_and_numbers(self):
        folder = "docs/architecture/decisions"
        store = MemoryStore(
            {
                f"{folder}/README.md": "[one](0001-one.md)",
                f"{folder}/0001-one.md": "- **Status:** Accepted\n- **Date:** 2026-10-21\n",
                f"{folder}/0001-dup.md": "- **Status:** Accepted\n",
            }
        )
        rule = AdrRule(store, folder)
        index = list(
            rule.check(Document(f"{folder}/README.md", store.files[f"{folder}/README.md"]))
        )
        assert {f.rule for f in index} == {"adr-number", "adr-index"}
        bad = list(
            rule.check(Document(f"{folder}/0001-dup.md", store.files[f"{folder}/0001-dup.md"]))
        )
        assert [f.rule for f in bad] == ["adr-format"]
        assert list(rule.check(Document("docs/other.md", ""))) == []


class TestTextTools:
    def test_front_matter_round_trip(self):
        fields, body = split_front_matter("---\nname: x\ndescription: 'Do: this'\n---\nBody\n")
        assert fields == {"name": "x", "description": "Do: this"}
        assert body == "Body\n"
        assert split_front_matter("no header") == ({}, "no header")

    def test_replace_block(self):
        text = "a\n<!-- sdd:s:start -->\nold\n<!-- sdd:s:end -->\nz"
        assert (
            replace_block(text, "s", "new")
            == "a\n<!-- sdd:s:start -->\nnew\n<!-- sdd:s:end -->\nz"
        )
        assert replace_block("no markers", "s", "x") is None


def world():
    dossiers = FakeDossiers()
    dossiers.save(dossier())
    evaluate = EvaluateDossier(dossiers, FakeCatalog(), FakeTeam(), FakeWorkspace())
    store = MemoryStore(
        {
            "README.md": "x\n<!-- sdd:status:start -->\n<!-- sdd:status:end -->\n"
            "<!-- sdd:coverage:start -->\n<!-- sdd:coverage:end -->\n",
            ".agents/skills/sdd-plan/SKILL.md": (
                "---\nname: sdd-plan\ndescription: Plan it\n---\nSteps\n"
            ),
            "harness/roles/planner.md": (
                "---\nname: planner\ndescription: Plans\ntools: Read\n---\nRole\n"
            ),
            "harness/roles/README.md": "index",
            ".claude/skills/old/SKILL.md": "orphan",
        }
    )
    generators = (
        StatusGenerator(evaluate),
        TraceabilityGenerator(evaluate, FakeCatalog()),
        AdapterGenerator(store),
    )
    return dossiers, evaluate, store, SyncGenerated(store, generators)


def sync_and_read(sync, store) -> str:
    sync.execute(write=True)
    return store.files["docs/requirements/traceability.md"]


class TestSync:
    def test_writes_generated_files_and_removes_orphans(self):
        _, _, store, sync = world()
        result = sync.execute(write=True)
        assert "README.md" in result.changed
        assert ".claude/skills/old/SKILL.md" in result.removed
        assert "[001 · Demo](specs/001-demo/prd.md)" in store.files["README.md"]
        assert "in discovery **1**" in store.files["README.md"]
        assert "GENERATED" in store.files[".claude/skills/sdd-plan/SKILL.md"]
        assert "tools: Read" in store.files[".claude/agents/planner.md"]
        assert ".claude/agents/README.md" not in store.files
        assert "Plan it" in store.files[".github/prompts/sdd-plan.prompt.md"]
        assert "RT01" in store.files["docs/requirements/traceability.md"]
        assert sync.execute(write=False).findings() == ()

    def test_work_outside_the_catalogue_is_listed_with_its_rationale(self):
        dossiers, _, store, sync = world()
        assert "_None._" in sync_and_read(sync, store)
        dossiers.save(dossier("002", requirements=()))
        matrix = sync_and_read(sync, store)
        assert "| [002 · Demo](../../specs/002-demo/prd.md) | because | Discover (G1) |" in matrix
        assert "| feature (outside RTs) |" in store.files["README.md"]

    def test_drift_and_missing_markers_are_errors(self):
        _, _, store, sync = world()
        store.files["README.md"] = "no markers here"
        findings = sync.execute(write=False).findings()
        assert {f.rule for f in findings} == {"generated-drift", "generated-block"}
        assert all(f.severity is Severity.ERROR for f in findings)


class TestCheckHarness:
    def test_reports_context_unknown_approvers_and_docs(self):
        dossiers, evaluate, store, sync = world()
        sync.execute(write=True)
        bad = dossier(requirements=("RT77",)).with_approval(
            GateId.G1, Approval("ghost", NOW, "sha256:x", "g")
        )
        dossiers.save(bad)
        store.files["docs/a.md"] = "[x](nowhere.md)"
        lint = LintDocs(store, (LocalLinkRule(store),), (".claude/",))
        findings = CheckHarness(evaluate, dossiers, FakeTeam(), lint, sync).execute()
        rules = {f.rule for f in findings}
        assert {"dossier-context", "unknown-approver", "broken-link", "generated-drift"} <= rules

    def test_artifacts_written_before_the_previous_gate_are_flagged(self):
        dossiers, evaluate, store, sync = world()
        sync.execute(write=True)
        dossiers.write("001", "backlog.md", READY)
        dossiers.write("001", "plan.md", "## Plan\nTODO(sdd): later\n")
        lint = LintDocs(store, (), ())
        findings = CheckHarness(evaluate, dossiers, FakeTeam(), lint, sync).execute()
        (ahead,) = [f for f in findings if f.rule == "written-ahead"]
        assert ahead.severity is Severity.WARNING
        assert "backlog.md written before G1 passed" in ahead.message

    def test_work_in_order_is_not_flagged(self):
        dossiers, evaluate, store, sync = world()
        sync.execute(write=True)
        dossiers.write("001", "prd.md", READY)
        lint = LintDocs(store, (), ())
        findings = CheckHarness(evaluate, dossiers, FakeTeam(), lint, sync).execute()
        assert [f for f in findings if f.rule == "written-ahead"] == []
