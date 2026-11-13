"""An in-memory `GitRepository` for the per-card flow tests."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FakeGit:
    """Records every mutating call in `calls`; the rest is plain data the test sets."""

    reachable: bool = True
    dirty: tuple[str, ...] = ()
    branch: str = "feat/001-01-first"
    branches: set[str] = field(default_factory=lambda: {"main", "feat/001-01-first"})
    merged: set[str] = field(default_factory=lambda: {"feat/001-01-first"})
    can_fast_forward: bool = True
    tips: dict[str, str] = field(default_factory=dict)
    in_main: set[str] = field(default_factory=set)
    calls: list[str] = field(default_factory=list)

    def fetch(self) -> bool:
        return self.reachable

    def dirty_paths(self) -> tuple[str, ...]:
        return self.dirty

    def current_branch(self) -> str:
        return self.branch

    def local_branches(self) -> tuple[str, ...]:
        return tuple(sorted(self.branches))

    def is_merged(self, branch: str, into: str) -> bool:
        return branch in self.merged

    def switch(self, branch: str) -> bool:
        self.calls.append(f"switch {branch}")
        self.branch = branch
        return branch in self.branches

    def fast_forward(self, branch: str) -> bool:
        self.calls.append(f"ff {branch}")
        return self.can_fast_forward

    def delete_merged_branch(self, branch: str) -> bool:
        self.calls.append(f"delete {branch}")
        self.branches.discard(branch)
        return True

    def create_branch(self, name: str, start: str) -> bool:
        self.calls.append(f"create {name}")
        self.branches.add(name)
        self.branch = name
        return True

    def tip(self, ref: str) -> str:
        return self.tips.get(ref, "")

    def contains(self, ref: str, commit: str) -> bool:
        return commit in self.in_main
