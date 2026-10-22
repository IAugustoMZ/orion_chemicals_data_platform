"""Integration tests of the adapters against real files, git and subprocesses (tmp_path)."""

from __future__ import annotations

import io
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from sdd.domain.approval import Approval, CheckOutcome, Verification
from sdd.domain.errors import (
    DossierNotFoundError,
    HumanConfirmationRequiredError,
    InvalidDossierError,
    InvalidTeamError,
)
from sdd.domain.gates import GateId
from sdd.domain.quality import QualityCheck
from sdd.infrastructure.file_document_store import FileDocumentStore
from sdd.infrastructure.file_template_library import FileTemplateLibrary
from sdd.infrastructure.git import listed_files
from sdd.infrastructure.git_workspace import GitWorkspace
from sdd.infrastructure.subprocess_check_runner import SubprocessCheckRunner, _batches
from sdd.infrastructure.system_clock import SystemClock
from sdd.infrastructure.terminal_confirmation import TerminalConfirmation
from sdd.infrastructure.yaml_dossier_repository import YamlDossierRepository
from sdd.infrastructure.yaml_reference_data import (
    YamlLogoRegistry,
    YamlQualityCheckCatalog,
    YamlRequirementCatalog,
    YamlTeamDirectory,
)
from tests.sdd.fakes import NOW, dossier

REPO = Path(__file__).resolve().parents[2]


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


class TestDossierRepository:
    def test_round_trip_with_approvals_and_verification(self, tmp_path):
        repo = YamlDossierRepository(tmp_path, "specs")
        value = dossier().with_approval(
            GateId.G1, Approval("mentor", NOW, "sha256:a", "Ana", "ok")
        )
        value = value.with_verification(
            Verification(NOW, "sha256:c", "abc", (CheckOutcome("lint", True, "fine"),))
        )
        repo.create(value, {"prd.md": "# PRD\n"})
        assert repo.ids() == ("001",)
        assert repo.load("001") == value
        assert repo.read_artifact(value, "prd.md") == "# PRD\n"
        assert repo.read_artifact(value, "spec.md") is None
        assert repo.location(value) == "specs/001-demo"
        text = (tmp_path / "specs/001-demo/dossier.yaml").read_text(encoding="utf-8")
        assert text.startswith("# Dossier metadata")
        assert "id: '001'" in text

    def test_errors(self, tmp_path):
        repo = YamlDossierRepository(tmp_path, "specs")
        with pytest.raises(DossierNotFoundError):
            repo.load("001")
        repo.create(dossier(), {})
        with pytest.raises(InvalidDossierError):
            repo.create(dossier(), {})
        (tmp_path / "specs/001-demo/dossier.yaml").write_text("id: [", encoding="utf-8")
        with pytest.raises(InvalidDossierError):
            repo.load("001")
        (tmp_path / "specs/001-demo/dossier.yaml").write_text(
            "id: 1\nslug: other\n", encoding="utf-8"
        )
        with pytest.raises(InvalidDossierError):
            repo.load("001")


class TestReferenceData:
    def test_real_catalogue_has_42_requirements(self):
        catalog = YamlRequirementCatalog(REPO / "docs/requirements/rt-catalog.yaml")
        requirements = catalog.all()
        assert len(requirements) == 42
        assert requirements["RT09"].priority
        assert len(catalog.categories()) == 5

    def test_real_team_checks_and_logos(self):
        assert len(YamlTeamDirectory(REPO / "harness/team.yaml").load().members) == 2
        ids = [c.id for c in YamlQualityCheckCatalog(REPO / "harness/checks.yaml").all()]
        assert ids[0] == "format" and "harness" in ids
        names = [
            logo.name
            for logo in YamlLogoRegistry(REPO / "docs/architecture/logos/registry.yaml").logos()
        ]
        assert "Mermaid" in names

    def test_malformed_team(self, tmp_path):
        (tmp_path / "team.yaml").write_text("members: []\n", encoding="utf-8")
        with pytest.raises(InvalidTeamError):
            YamlTeamDirectory(tmp_path / "team.yaml").load()


class TestTemplatesAndStore:
    def test_templates_render_known_keys_only(self, tmp_path):
        (tmp_path / "t.md").write_text("{{title}} {{ unknown }}", encoding="utf-8")
        library = FileTemplateLibrary(tmp_path)
        assert library.render("t.md", {"title": "X"}) == "X {{ unknown }}"

    def test_document_store(self, tmp_path):
        store = FileDocumentStore(tmp_path, lambda root: ("a.md", "docs/b.md"))
        store.write("docs/b.md", "line\n")
        assert store.paths(prefix="docs/") == ("docs/b.md",)
        assert store.read("docs/b.md") == "line\n"
        assert store.read("none.md") is None
        assert store.exists("docs")
        store.remove("docs/b.md")
        assert not store.exists("docs/b.md")


class TestGitWorkspace:
    @pytest.fixture
    def repo(self, tmp_path):
        git(tmp_path, "init", "-q", "-b", "spec/001-demo")
        git(tmp_path, "config", "user.name", "Ana")
        git(tmp_path, "config", "user.email", "ana@example.com")
        (tmp_path / ".gitignore").write_text(".venv/\n", encoding="utf-8")
        (tmp_path / "tools").mkdir()
        (tmp_path / "tools/a.py").write_text("x = 1\n", encoding="utf-8")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs/a.md").write_text("doc\n", encoding="utf-8")
        return tmp_path

    def test_facts_and_governed_digest(self, repo):
        workspace = GitWorkspace(repo)
        assert workspace.current_branch() == "spec/001-demo"
        assert workspace.git_identity() == "Ana <ana@example.com>"
        assert workspace.head_commit() == "(no commit)"
        assert "tools/a.py" in listed_files(repo)
        before = workspace.governed_digest()
        (repo / "docs/a.md").write_text("changed doc\n", encoding="utf-8")
        (repo / ".venv").mkdir()
        (repo / ".venv/ignored.py").write_text("ignored\n", encoding="utf-8")
        assert workspace.governed_digest() == before
        (repo / "tools/a.py").write_text("x = 2\n", encoding="utf-8")
        assert workspace.governed_digest() != before


class TestTerminalAndRunner:
    def test_terminal_requires_a_tty(self):
        with pytest.raises(HumanConfirmationRequiredError):
            TerminalConfirmation(stdin=io.StringIO("001 G1\n")).confirm("summary", "001 G1")

    def test_terminal_compares_the_answer(self):
        class Tty(io.StringIO):
            def isatty(self) -> bool:
                return True

        shown: list[str] = []
        yes = TerminalConfirmation(Tty(), prompt=lambda _: "001 G1", echo=shown.append)
        assert yes.confirm("summary", "001 G1")
        assert shown[0] == "summary"
        no = TerminalConfirmation(Tty(), prompt=lambda _: "y", echo=shown.append)
        assert not no.confirm("summary", "001 G1")

    def test_runner(self, tmp_path):
        runner = SubprocessCheckRunner(tmp_path, lambda root: ("f.txt",))
        python = Path(sys.executable).name
        ok = runner.run(QualityCheck("ok", "ok", (python, "-c", "print('hi')")))
        assert ok.passed and ok.summary == "hi"
        failed = runner.run(
            QualityCheck("files", "f", (python, "-c", "import sys; sys.exit(len(sys.argv))"), True)
        )
        assert not failed.passed
        missing = runner.run(QualityCheck("x", "x", ("definitely-not-a-command",)))
        assert "command not found" in missing.summary

    def test_long_file_lists_are_batched(self, tmp_path):
        files = tuple(f"docs/file-{n:05d}.md" for n in range(3000)) + ("bad",)
        assert len(batches := _batches(files)) > 1
        assert [f for batch in batches for f in batch] == list(files)
        python = Path(sys.executable).name
        script = "import sys; sys.exit('bad' in sys.argv)"
        runner = SubprocessCheckRunner(tmp_path, lambda root: files)
        assert not runner.run(QualityCheck("b", "b", (python, "-c", script), True)).passed
        clean = SubprocessCheckRunner(tmp_path, lambda root: files[:-1])
        assert clean.run(QualityCheck("b", "b", (python, "-c", script), True)).passed

    def test_clock_is_utc(self):
        assert SystemClock().now().utcoffset().total_seconds() == 0


@pytest.mark.skipif(shutil.which("git") is None, reason="git is required")
def test_listed_files_outside_a_repository(tmp_path):
    assert listed_files(tmp_path) == ()
