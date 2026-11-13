"""Command-line and adapter tests of the per-card flow (`sdd item ...`)."""

from __future__ import annotations

import pytest

from sdd.domain.errors import InvalidDossierError, ItemRefusedError
from sdd.domain.item_progress import ItemProgress, ItemState
from sdd.infrastructure.pytest_ac_reader import PytestAcStatusReader, parse_report
from sdd.infrastructure.yaml_progress_repository import YamlProgressRepository
from tests.sdd import test_cli
from tests.sdd.fakes import NOW
from tests.sdd.test_item_progress import BACKLOG, approval

repo = test_cli.repo
run = test_cli.run

REPORT = """<testsuites><testsuite>
<testcase name="a"><properties><property name="ac" value="PBI-9:AC1"/></properties></testcase>
<testcase name="b">
<properties><property name="ac" value="PBI-9:AC2"/></properties><failure/></testcase>
<testcase name="c">
<properties><property name="ac" value="PBI-9:AC3"/></properties><skipped/></testcase>
<testcase name="d"><properties><property name="ac" value="PBI-9:AC1"/></properties></testcase>
<testcase name="plain"/>
</testsuite></testsuites>"""


class TestProgressFile:
    def test_round_trip_and_missing_file(self, tmp_path):
        repository = YamlProgressRepository(tmp_path, "specs")
        (tmp_path / "specs/001-demo").mkdir(parents=True)
        assert repository.load("001") is None
        progress = ItemProgress().with_approval("01", approval("mentor", "sha256:d"), False)
        repository.save("001", progress)
        loaded = repository.load("001")
        assert loaded is not None and loaded.record("01") == progress.record("01")
        assert loaded.record("01").state is ItemState.REFINED
        assert repository.load("002") is None

    def test_saving_without_a_folder_and_a_malformed_file_are_errors(self, tmp_path):
        repository = YamlProgressRepository(tmp_path, "specs")
        with pytest.raises(InvalidDossierError):
            repository.save("001", ItemProgress())
        folder = tmp_path / "specs/001-demo"
        folder.mkdir(parents=True)
        (folder / "progress.yaml").write_text("items: [1]\n", encoding="utf-8")
        with pytest.raises(InvalidDossierError):
            repository.load("001")

    def test_merged_time_is_kept(self, tmp_path):
        (tmp_path / "specs/001-demo").mkdir(parents=True)
        repository = YamlProgressRepository(tmp_path, "specs")
        text = (
            "version: 1\nitems:\n  '01':\n    state: merged\n"
            "    merged_at: 2026-10-21T12:00:00+00:00\n"
        )
        (tmp_path / "specs/001-demo/progress.yaml").write_text(text, encoding="utf-8")
        loaded = repository.load("001")
        assert loaded is not None and loaded.record("01").merged_at == NOW


class TestAcReader:
    def test_report_is_folded_per_criterion(self, tmp_path):
        report = tmp_path / "ac.xml"
        report.write_text(REPORT, encoding="utf-8")
        assert parse_report(report) == {"PBI-9:AC1": True, "PBI-9:AC2": False, "PBI-9:AC3": False}

    def test_marked_tests_of_a_project_are_run(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[tool.pytest.ini_options]\nmarkers = ["ac(id): criterion"]\n', encoding="utf-8"
        )
        (tmp_path / "conftest.py").write_text(
            "def pytest_collection_modifyitems(items):\n"
            "    for i in items:\n"
            "        for m in i.iter_markers('ac'):\n"
            "            i.user_properties.append(('ac', m.args[0]))\n",
            encoding="utf-8",
        )
        (tmp_path / "test_x.py").write_text(
            "import pytest\n"
            "@pytest.mark.ac('PBI-9:AC1')\n"
            "def test_ok():\n    pass\n"
            "@pytest.mark.ac('PBI-9:AC2')\n"
            "def test_bad():\n    assert False\n",
            encoding="utf-8",
        )
        assert PytestAcStatusReader(tmp_path).read() == {"PBI-9:AC1": True, "PBI-9:AC2": False}

    def test_nothing_marked_gives_an_empty_verdict(self, tmp_path):
        assert PytestAcStatusReader(tmp_path).read() == {}


class TestItemCommands:
    def _dossier(self, repo):
        run("new", "X", "--slug", "x", "--rt", "RT01")
        (repo / "specs/000-x/backlog.md").write_text(BACKLOG, encoding="utf-8")

    def test_status_lists_every_card_or_one(self, repo):
        self._dossier(repo)
        shown = run("item", "status", "000")
        assert shown.exit_code == 0, shown.output
        assert "PBI-001-01 - First" in shown.output and "waiting: mentor, mentee" in shown.output
        assert run("item", "status", "000", "2").output.count("PBI") == 1

    def test_unknown_card_and_unready_specification_exit_with_2(self, repo):
        self._dossier(repo)
        assert run("item", "status", "000", "09").exit_code == 2
        assert run("item", "approve", "000", "01", "--as", "mentor").exit_code == 2
        refused = run("item", "verify", "000", "01")
        assert refused.exit_code == 2 and "after G4" in refused.output

    def test_a_refused_card_exits_with_1_and_lists_the_reasons(self, repo, monkeypatch):
        class Refusing:
            def execute(self, *args, **kwargs):
                raise ItemRefusedError(("card 01 is not approved",))

        class Stub:
            verify_item = Refusing()

        monkeypatch.setattr("sdd.interfaces.cli.app._harness", lambda: Stub())
        refused = run("item", "verify", "000", "1")
        assert refused.exit_code == 1 and "card 01 is not approved" in refused.output
