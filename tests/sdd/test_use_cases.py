"""Unit tests of the use cases with in-memory fakes."""

from __future__ import annotations

from dataclasses import replace

import pytest

from sdd.application.scaffold_artifacts import ScaffoldArtifacts
from sdd.application.use_cases.approve_gate import ApproveGate
from sdd.application.use_cases.create_dossier import CreateDossier, NewDossier
from sdd.application.use_cases.evaluate_dossier import EvaluateDossier
from sdd.application.use_cases.guard_commit import GuardCommit
from sdd.application.use_cases.verify_quality import VerifyQuality
from sdd.domain.dossier import DossierKind
from sdd.domain.errors import (
    ApprovalDeclinedError,
    GateKindError,
    GateNotReadyError,
    GateOrderError,
    HumanConfirmationRequiredError,
    UnknownMemberError,
    UnknownRequirementError,
)
from sdd.domain.findings import Severity
from sdd.domain.gate_status import GateState
from sdd.domain.gates import GateId
from tests.sdd.fakes import (
    READY,
    DictTemplates,
    FakeCatalog,
    FakeChecks,
    FakeConfirmation,
    FakeDossiers,
    FakeRunner,
    FakeTeam,
    FakeWorkspace,
    FixedClock,
    dossier,
)


class World:
    """A wired set of fakes and use cases for one test."""

    def __init__(self, approves: bool = True, interactive: bool = True) -> None:
        self.dossiers = FakeDossiers()
        self.workspace = FakeWorkspace()
        self.confirmation = FakeConfirmation(approves, interactive)
        self.runner = FakeRunner()
        self.evaluate = EvaluateDossier(self.dossiers, FakeCatalog(), FakeTeam(), self.workspace)
        self.scaffold = ScaffoldArtifacts(DictTemplates(), FakeCatalog(), self.dossiers)
        self.create = CreateDossier(self.dossiers, self.scaffold, FakeCatalog(), FixedClock())
        self.approve = ApproveGate(
            self.dossiers,
            self.evaluate,
            FakeTeam(),
            DictTemplates(),
            self.scaffold,
            self.workspace,
            self.confirmation,
            FixedClock(),
        )
        self.verify = VerifyQuality(
            self.dossiers, self.evaluate, FakeChecks(), self.runner, self.workspace, FixedClock()
        )
        self.guard = GuardCommit(self.workspace, self.evaluate)

    def ready_dossier(self) -> None:
        self.dossiers.save(dossier())
        for name in ("prd.md", "backlog.md", "ux-approach.md", "spec.md", "plan.md", "tasks.md"):
            self.dossiers.write("001", name, READY)
        for name in ("validation.md", "teaching-guide.md", "release.md"):
            self.dossiers.write("001", name, READY)

    def start_dossier(self) -> None:
        """A dossier as `sdd new` leaves it: only the PRD exists, and it is complete."""
        self.dossiers.save(dossier())
        self.dossiers.write("001", "prd.md", READY)

    def approve_through(self, last: GateId) -> None:
        for gate in (GateId.G1, GateId.G2, GateId.G3, GateId.G4, GateId.G6, GateId.G7):
            for member in ("mentor", "mentee"):
                self.approve.execute("001", gate, member, "")
            if gate is last:
                return


class TestCreate:
    def test_assigns_ids_in_sequence_and_renders_templates(self):
        world = World()
        first = world.create.execute(NewDossier("One", "one", DossierKind.FEATURE, ("RT01",)))
        second = world.create.execute(NewDossier("Two", "two", DossierKind.FEATURE, ("RT02",)))
        assert (first.id, second.id) == ("000", "001")
        assert [k[1] for k in world.dossiers.artifacts if k[0] == "000"] == ["prd.md"]

    def test_rejects_unknown_requirement(self):
        with pytest.raises(UnknownRequirementError):
            World().create.execute(NewDossier("X", "x", DossierKind.FEATURE, ("RT77",)))

    def test_requirements_table_is_rendered(self):
        world = World()
        world.create = CreateDossier(
            world.dossiers,
            ScaffoldArtifacts(
                DictTemplates({"prd.md": "{{requirements_table}} {{branch}}"}),
                FakeCatalog(),
                world.dossiers,
            ),
            FakeCatalog(),
            FixedClock(),
        )
        world.create.execute(NewDossier("X", "x", DossierKind.ENABLER, (), "tooling"))
        prd = world.dossiers.artifacts[("000", "prd.md")]
        assert "enabler" in prd
        assert "spec/000-x" in prd

    def test_feature_without_rt_is_marked_outside_the_catalogue(self):
        world = World()
        world.create = CreateDossier(
            world.dossiers,
            ScaffoldArtifacts(
                DictTemplates({"prd.md": "{{requirements_table}} ({{requirements}})"}),
                FakeCatalog(),
                world.dossiers,
            ),
            FakeCatalog(),
            FixedClock(),
        )
        world.create.execute(NewDossier("Crud", "crud", DossierKind.FEATURE, (), "we need it"))
        prd = world.dossiers.artifacts[("000", "prd.md")]
        assert "outside the requirements catalogue" in prd
        assert "(none)" in prd


class TestContext:
    def g0(self, value) -> tuple[GateState, tuple[str, ...]]:
        world = World()
        world.dossiers.save(value)
        report = world.evaluate.one(value.id)
        return report.status(GateId.G0).state, report.evidence.context_problems

    def test_feature_citing_rts_passes(self):
        assert self.g0(dossier()) == (GateState.PASSED, ())

    def test_feature_outside_the_catalogue_passes_with_a_rationale(self):
        assert self.g0(dossier(requirements=()))[0] is GateState.PASSED

    @pytest.mark.parametrize(
        ("kind", "requirements", "expected"),
        [
            (DossierKind.FEATURE, (), "outside the catalogue"),
            (DossierKind.ENABLER, ("RT01",), "an enabler must state its rationale"),
        ],
    )
    def test_missing_rationale_fails(self, kind, requirements, expected):
        value = replace(dossier(kind=kind, requirements=requirements), rationale=" ")
        state, problems = self.g0(value)
        assert state is GateState.FAILED
        assert expected in problems[0]

    def test_unknown_rt_in_an_artifact_fails(self):
        world = World()
        world.dossiers.save(dossier())
        world.dossiers.write("001", "spec.md", "serves RT77")
        problems = world.evaluate.one("001").evidence.context_problems
        assert problems == ("unknown requirements cited: RT77",)


class TestApprove:
    def test_both_approvals_pass_the_gate(self):
        world = World()
        world.ready_dossier()
        first = world.approve.execute("001", GateId.G1, "mentor", "")
        assert first.status.state is GateState.PARTIAL
        second = world.approve.execute("001", GateId.G1, "mentee", "looks right")
        assert second.status.state is GateState.PASSED
        recorded = world.dossiers.load("001").approvals_for(GateId.G1)
        assert {a.member for a in recorded} == {"mentor", "mentee"}
        assert recorded[-1].note == "looks right"
        assert "Approver  mentee" in world.confirmation.shown[-1]

    def test_cannot_skip_a_gate(self):
        world = World()
        world.ready_dossier()
        with pytest.raises(GateOrderError):
            world.approve.execute("001", GateId.G2, "mentor", "")

    def test_incomplete_artifact_is_not_ready(self):
        world = World()
        world.ready_dossier()
        world.dossiers.write("001", "prd.md", "## Section\nTODO(sdd): later\n")
        with pytest.raises(GateNotReadyError) as error:
            world.approve.execute("001", GateId.G1, "mentor", "")
        assert "unresolved TODO(sdd)" in error.value.problems[0]

    def test_agents_without_terminal_are_refused(self):
        world = World(interactive=False)
        world.ready_dossier()
        with pytest.raises(HumanConfirmationRequiredError):
            world.approve.execute("001", GateId.G1, "mentor", "")
        assert world.dossiers.load("001").approvals_for(GateId.G1) == ()

    def test_answer_other_than_yes_saves_nothing(self):
        world = World(approves=False)
        world.ready_dossier()
        with pytest.raises(ApprovalDeclinedError):
            world.approve.execute("001", GateId.G1, "mentor", "")
        assert world.dossiers.load("001").approvals_for(GateId.G1) == ()

    def test_missing_artifacts_read_as_not_complete(self):
        world = World()
        world.start_dossier()
        report = world.evaluate.one("001")
        assert report.status(GateId.G1).state is GateState.PENDING
        assert report.status(GateId.G2).state is GateState.BLOCKED

    def test_first_approval_creates_nothing(self):
        world = World()
        world.start_dossier()
        result = world.approve.execute("001", GateId.G1, "mentor", "")
        assert result.status.state is GateState.PARTIAL
        assert result.created == ()
        assert ("001", "backlog.md") not in world.dossiers.artifacts

    def test_second_approval_creates_the_next_gates_files(self):
        world = World()
        world.start_dossier()
        world.approve.execute("001", GateId.G1, "mentor", "")
        result = world.approve.execute("001", GateId.G1, "mentee", "")
        assert result.created == ("backlog.md", "progress.yaml")
        assert "TODO(sdd)" in world.dossiers.artifacts[("001", "backlog.md")]

    def test_existing_artifacts_are_never_overwritten(self):
        world = World()
        world.start_dossier()
        world.dossiers.write("001", "backlog.md", "my own work")
        world.approve.execute("001", GateId.G1, "mentor", "")
        result = world.approve.execute("001", GateId.G1, "mentee", "")
        assert result.created == ("progress.yaml",)
        assert world.dossiers.artifacts[("001", "backlog.md")] == "my own work"

    def test_failed_scaffolding_undoes_the_approval(self):
        world = World()
        world.start_dossier()
        world.approve.execute("001", GateId.G1, "mentor", "")
        before = world.dossiers.load("001")
        world.dossiers.fail_on = "backlog.md"
        with pytest.raises(OSError, match="backlog.md"):
            world.approve.execute("001", GateId.G1, "mentee", "")
        assert world.dossiers.load("001") == before
        assert ("001", "backlog.md") not in world.dossiers.artifacts
        world.dossiers.fail_on = None
        retried = world.approve.execute("001", GateId.G1, "mentee", "")
        assert retried.status.state is GateState.PASSED
        assert retried.created == ("backlog.md", "progress.yaml")

    def test_automated_gate_and_unknown_member(self):
        world = World()
        world.ready_dossier()
        with pytest.raises(GateKindError):
            world.approve.execute("001", GateId.G5, "mentor", "")
        with pytest.raises(UnknownMemberError):
            world.approve.execute("001", GateId.G1, "intruder", "")

    def test_editing_an_approved_artifact_makes_it_stale(self):
        world = World()
        world.ready_dossier()
        world.approve_through(GateId.G1)
        world.dossiers.write("001", "prd.md", READY + "\nOne more idea.\n")
        assert world.evaluate.one("001").status(GateId.G1).state is GateState.STALE


class TestVerify:
    def test_requires_g4(self):
        world = World()
        world.ready_dossier()
        with pytest.raises(GateOrderError):
            world.verify.execute("001")

    @pytest.mark.ac("PBI-002-04:AC6")
    def test_without_recording_the_dossier_is_not_modified(self):
        world = World()
        world.ready_dossier()
        world.approve_through(GateId.G4)
        before = world.dossiers.load("001")
        result = world.verify.execute("001", record=False)
        assert result.passed and world.dossiers.load("001") == before
        assert world.evaluate.one("001").status(GateId.G5).state is GateState.PENDING

    def test_records_passing_and_failing_runs(self):
        world = World()
        world.ready_dossier()
        world.approve_through(GateId.G4)
        seen = []
        result = world.verify.execute("001", lambda check, outcome: seen.append(check.id))
        assert result.passed
        assert seen == ["lint", "lint", "tests", "tests"]
        assert world.evaluate.one("001").status(GateId.G5).state is GateState.PASSED
        world.runner.failing.add("tests")
        assert world.verify.execute("001").failed_checks == ("tests",)
        assert world.evaluate.one("001").status(GateId.G5).state is GateState.FAILED

    def test_code_change_after_verify_is_stale(self):
        world = World()
        world.ready_dossier()
        world.approve_through(GateId.G4)
        world.verify.execute("001")
        world.workspace.digest = "sha256:code-v2"
        assert world.evaluate.one("001").status(GateId.G5).state is GateState.STALE


class TestGuard:
    def test_docs_only_changes_are_always_allowed(self):
        world = World()
        world.workspace.branch = "main"
        assert world.guard.execute(["docs/a.md", "specs/001-demo/prd.md"]) == ()

    def test_governed_change_off_a_spec_branch_is_refused(self):
        world = World()
        world.workspace.branch = "main"
        (finding,) = world.guard.execute(["tools/sdd/x.py"])
        assert finding.severity is Severity.ERROR
        assert "spec/<id>-<slug>" in finding.message

    def test_unknown_dossier_and_unapproved_spec_are_refused(self):
        world = World()
        world.workspace.branch = "spec/009-ghost"
        assert "does not exist" in world.guard.execute(["tools/x.py"])[0].message
        world.workspace.branch = "spec/001-demo"
        world.ready_dossier()
        assert "G4 is" in world.guard.execute(["tools/x.py"])[0].message

    def test_approved_spec_allows_governed_changes(self):
        world = World()
        world.ready_dossier()
        world.approve_through(GateId.G4)
        assert world.guard.execute(["tools/x.py", "pyproject.toml"]) == ()
