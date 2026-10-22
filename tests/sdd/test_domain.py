"""Unit tests of the pure domain: gates, digests, team, governance, readiness, dossier."""

from __future__ import annotations

import pytest

from sdd.domain.approval import Approval, CheckOutcome, Verification
from sdd.domain.digest import digest_files, digest_texts, normalise_text, short
from sdd.domain.dossier import Dossier, DossierKind
from sdd.domain.errors import (
    InvalidDossierError,
    InvalidGateError,
    InvalidTeamError,
    UnknownMemberError,
)
from sdd.domain.gates import GATES, GateId, GateKind, all_artifacts, gates_before, parse_gate_id
from sdd.domain.governance import is_governed, spec_id_from_branch
from sdd.domain.readiness import readiness_problems, required_headings
from sdd.domain.team import ApprovalPolicy, Team, TeamMember
from tests.sdd.fakes import NOW, TEAM, dossier


class TestGates:
    def test_catalogue_is_ordered_and_complete(self):
        assert [g.id for g in GATES] == list(GateId)
        assert [g.phase for g in GATES] == list(range(8))

    def test_only_g0_and_g5_are_automated(self):
        automated = {g.id for g in GATES if g.kind is GateKind.AUTOMATED}
        assert automated == {GateId.G0, GateId.G5}

    @pytest.mark.parametrize("text", ["g4", " G4 ", "G4"])
    def test_parse_accepts_case_and_spaces(self, text):
        assert parse_gate_id(text) is GateId.G4

    def test_parse_rejects_unknown(self):
        with pytest.raises(InvalidGateError):
            parse_gate_id("G9")

    def test_gates_before(self):
        assert [g.id for g in gates_before(GateId.G2)] == [GateId.G0, GateId.G1]
        assert gates_before(GateId.G0) == ()

    def test_all_artifacts_in_phase_order(self):
        assert all_artifacts()[:2] == ("prd.md", "backlog.md")
        assert all_artifacts()[-1] == "release.md"
        assert len(all_artifacts()) == len(set(all_artifacts()))


class TestDigest:
    def test_line_endings_do_not_matter(self):
        assert digest_texts([("a.md", "x\r\ny\r\n")]) == digest_texts([("a.md", "x\ny")])

    def test_ticking_a_task_does_not_matter(self):
        before = digest_texts([("tasks.md", "- [ ] T01 build it")])
        assert digest_texts([("tasks.md", "- [x] T01 build it")]) == before

    def test_rewording_a_task_matters(self):
        before = digest_texts([("tasks.md", "- [ ] T01 build it")])
        assert digest_texts([("tasks.md", "- [ ] T01 build it twice")]) != before

    def test_order_independent_but_names_matter(self):
        pair = [("a.md", "1"), ("b.md", "2")]
        assert digest_texts(pair) == digest_texts(reversed(pair))
        assert digest_texts([("a.md", "1")]) != digest_texts([("b.md", "1")])

    def test_files_normalise_crlf(self):
        assert digest_files([("x.py", b"a\r\nb")]) == digest_files([("x.py", b"a\nb")])

    def test_short_and_normalise(self):
        assert len(short(digest_texts([]))) == 12
        assert normalise_text("\n\n text \n\n") == "text\n"


class TestTeam:
    def test_all_policy_needs_everyone(self):
        assert TEAM.missing_approvers(["mentor"]) == ("mentee",)
        assert TEAM.missing_approvers(["mentor", "mentee"]) == ()

    def test_any_policy_needs_one(self):
        team = Team(TEAM.members, ApprovalPolicy.ANY)
        assert team.missing_approvers(["mentee"]) == ()
        assert team.missing_approvers([]) == ("mentor", "mentee")

    def test_member_lookup(self):
        assert TEAM.member("mentee").name == "Bo"
        with pytest.raises(UnknownMemberError):
            TEAM.member("someone")

    def test_invariants(self):
        with pytest.raises(InvalidTeamError):
            Team(())
        with pytest.raises(InvalidTeamError):
            Team((TeamMember("a", "A", "x"), TeamMember("a", "B", "y")))


class TestGovernance:
    @pytest.mark.parametrize(
        "path",
        ["tools/sdd/x.py", "tests\\a.py", "pyproject.toml", "harness/gates.md", ".claude/x"],
    )
    def test_governed(self, path):
        assert is_governed(path)

    @pytest.mark.parametrize("path", ["docs/a.md", "specs/001-x/spec.md", "README.md"])
    def test_not_governed(self, path):
        assert not is_governed(path)

    def test_spec_branch(self):
        assert spec_id_from_branch("spec/012-source-contracts") == "012"
        assert spec_id_from_branch("main") is None
        assert spec_id_from_branch("spec/12-x") is None


class TestReadiness:
    TEMPLATE = "# T\n\n## Problem\n\n## Notes (optional)\n\n## Goals\n"

    def test_required_headings_skip_optional(self):
        assert required_headings(self.TEMPLATE) == ("Problem", "Goals")

    def test_problems(self):
        text = "## Problem\nTODO(sdd): write it\n"
        problems = readiness_problems("prd.md", text, ("Problem", "Goals"))
        assert "prd.md: missing section '## Goals'" in problems
        assert "prd.md:2: unresolved TODO(sdd)" in problems

    def test_a_marker_quoted_in_inline_code_is_not_a_placeholder(self):
        quoted = "## Problem\nSdd refuses while a `TODO(sdd)` remains.\n"
        assert readiness_problems("prd.md", quoted, ("Problem",)) == ()
        mixed = "## Problem\nSee `TODO(sdd)`, then TODO(sdd): fix\n"
        assert readiness_problems("prd.md", mixed, ("Problem",)) == (
            "prd.md:2: unresolved TODO(sdd)",
        )

    def test_missing_file_and_ready(self):
        assert readiness_problems("prd.md", None, ()) == ("prd.md: file is missing",)
        assert readiness_problems("prd.md", "## Problem\nok\n", ("Problem",)) == ()


class TestDossier:
    def test_derived_names(self):
        assert dossier().folder_name == "001-demo"
        assert dossier().branch_name == "spec/001-demo"

    @pytest.mark.parametrize(
        ("dossier_id", "slug", "title"),
        [("1", "x", "T"), ("001", "Bad Slug", "T"), ("001", "x", " ")],
    )
    def test_invariants(self, dossier_id, slug, title):
        base = dossier()
        with pytest.raises(InvalidDossierError):
            Dossier(dossier_id, slug, title, DossierKind.FEATURE, (), "", base.created)

    def test_outside_catalogue_and_rationale_rules(self):
        assert not dossier().outside_catalogue
        assert not dossier().needs_rationale
        assert dossier(requirements=()).outside_catalogue
        assert dossier(requirements=()).needs_rationale
        enabler = dossier(kind=DossierKind.ENABLER)
        assert not enabler.outside_catalogue
        assert enabler.needs_rationale

    def test_with_approval_replaces_same_member(self):
        first = Approval("mentor", NOW, "sha256:a", "Ana")
        second = Approval("mentor", NOW, "sha256:b", "Ana")
        updated = dossier().with_approval(GateId.G1, first).with_approval(GateId.G1, second)
        assert updated.approvals_for(GateId.G1) == (second,)

    def test_verification_verdict(self):
        ok = CheckOutcome("lint", True, "")
        bad = CheckOutcome("tests", False, "")
        assert Verification(NOW, "d", "c", (ok,)).passed
        assert Verification(NOW, "d", "c", (ok, bad)).failed_checks == ("tests",)
        assert not Verification(NOW, "d", "c", ()).passed
