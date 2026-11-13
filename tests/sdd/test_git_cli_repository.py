"""Adapter tests of `GitCliRepository` against real temporary repositories (bare remote)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from sdd.domain.errors import ForbiddenGitCommandError
from sdd.infrastructure.git_cli_repository import GitCliRepository, ensure_allowed


def git(cwd: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-c", "user.name=T", "-c", "user.email=t@example.com", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout.strip()


@pytest.fixture
def clone(tmp_path):
    remote, work = tmp_path / "remote.git", tmp_path / "work"
    git(tmp_path, "init", "--bare", "-b", "main", str(remote))
    git(tmp_path, "clone", str(remote), str(work))
    git(work, "switch", "-c", "main")
    (work / "a.txt").write_text("a", encoding="utf-8")
    git(work, "add", ".")
    git(work, "commit", "-m", "first")
    git(work, "push", "-u", "origin", "main")
    return work


class TestSafety:
    @pytest.mark.ac("PBI-002-03:AC4")
    @pytest.mark.parametrize(
        "args",
        [
            ("branch", "-D", "x"),
            ("push", "--force"),
            ("push", "origin", "main"),
            ("fetch", "--force"),
            ("reset", "--hard"),
            ("clean", "-fd"),
        ],
    )
    def test_forbidden_commands_are_refused(self, args):
        with pytest.raises(ForbiddenGitCommandError):
            ensure_allowed(args)

    @pytest.mark.ac("PBI-002-03:AC4")
    def test_every_call_of_the_adapter_is_checked(self, clone):
        with pytest.raises(ForbiddenGitCommandError):
            GitCliRepository(clone)._git("branch", "-D", "main")

    @pytest.mark.ac("PBI-002-03:AC4")
    def test_the_adapter_source_never_names_a_forbidden_call(self):
        source = Path(GitCliRepository.__module__.replace(".", "/") + ".py")
        text = (Path("tools") / source).read_text(encoding="utf-8")
        calls = [line for line in text.splitlines() if "self._git(" in line]
        assert calls and not any(w in line for line in calls for w in ('"-D"', "force", '"push"'))


class TestOperations:
    def test_a_clean_clone_reports_branch_and_no_dirt(self, clone):
        repo = GitCliRepository(clone)
        assert repo.fetch() and repo.current_branch() == "main"
        assert repo.dirty_paths() == () and repo.local_branches() == ("main",)
        (clone / "b.txt").write_text("b", encoding="utf-8")
        assert repo.dirty_paths() == ("b.txt",)

    def test_branch_lifecycle_merged_and_unmerged(self, clone):
        repo = GitCliRepository(clone)
        assert repo.create_branch("feat/x", "main") and repo.current_branch() == "feat/x"
        (clone / "x.txt").write_text("x", encoding="utf-8")
        git(clone, "add", ".")
        git(clone, "commit", "-m", "x")
        assert not repo.is_merged("feat/x", "origin/main")
        commit = repo.tip("feat/x")
        assert len(commit) == 40 and not repo.contains("origin/main", commit)
        git(clone, "push", "origin", "feat/x:main")
        assert repo.fetch() and repo.contains("origin/main", commit)
        assert repo.is_merged("feat/x", "origin/main")
        assert repo.switch("main") and repo.fast_forward("main")
        assert repo.delete_merged_branch("feat/x") and repo.local_branches() == ("main",)

    def test_git_itself_refuses_to_delete_an_unmerged_branch(self, clone):
        repo = GitCliRepository(clone)
        repo.create_branch("feat/y", "main")
        (clone / "y.txt").write_text("y", encoding="utf-8")
        git(clone, "add", ".")
        git(clone, "commit", "-m", "y")
        repo.switch("main")
        assert not repo.delete_merged_branch("feat/y")

    def test_unknown_refs_and_a_missing_remote_are_reported_as_failures(self, clone):
        repo = GitCliRepository(clone)
        assert repo.tip("nope") == "" and not repo.switch("nope")
        git(clone, "remote", "set-url", "origin", str(clone / "missing.git"))
        assert not repo.fetch()
