"""In-memory fakes of every port, for fast unit tests of the use cases.

Each fake honours its Protocol's contract (Liskov substitution), so a use case cannot tell it
from the real adapter. They hold their state in plain attributes so tests can inspect it.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from sdd.application.ports.reference_data import Logo
from sdd.domain.approval import CheckOutcome
from sdd.domain.dossier import Dossier, DossierKind
from sdd.domain.errors import DossierNotFoundError, HumanConfirmationRequiredError
from sdd.domain.quality import QualityCheck
from sdd.domain.requirement import Requirement, RequirementPhase
from sdd.domain.team import ApprovalPolicy, Team, TeamMember

NOW = datetime(2026, 10, 21, 12, 0, tzinfo=UTC)


def requirement(rt: str, category: str = "integration") -> Requirement:
    return Requirement(rt, category, RequirementPhase.PROTOTYPE, False, f"{rt} must hold", "test")


def dossier(
    dossier_id: str = "001",
    kind: DossierKind = DossierKind.FEATURE,
    requirements: tuple[str, ...] = ("RT01",),
) -> Dossier:
    return Dossier(dossier_id, "demo", "Demo", kind, requirements, "because", date(2026, 10, 21))


TEAM = Team((TeamMember("mentor", "Ana", "mentor"), TeamMember("mentee", "Bo", "mentee")))
SOLO_TEAM = Team((TeamMember("mentor", "Ana", "mentor"),), ApprovalPolicy.ANY)


@dataclass
class FakeDossiers:
    dossiers: dict[str, Dossier] = field(default_factory=dict)
    artifacts: dict[tuple[str, str], str] = field(default_factory=dict)

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self.dossiers))

    def load(self, dossier_id: str) -> Dossier:
        if dossier_id not in self.dossiers:
            raise DossierNotFoundError(dossier_id)
        return self.dossiers[dossier_id]

    def save(self, value: Dossier) -> None:
        self.dossiers[value.id] = value

    def create(self, value: Dossier, artifacts: Mapping[str, str]) -> None:
        self.dossiers[value.id] = value
        for name, text in artifacts.items():
            self.artifacts[(value.id, name)] = text

    def read_artifact(self, value: Dossier, name: str) -> str | None:
        return self.artifacts.get((value.id, name))

    def location(self, value: Dossier) -> str:
        return f"specs/{value.folder_name}"

    def write(self, dossier_id: str, name: str, text: str) -> None:
        self.artifacts[(dossier_id, name)] = text


@dataclass
class FakeCatalog:
    requirements: dict[str, Requirement] = field(
        default_factory=lambda: {rt: requirement(rt) for rt in ("RT01", "RT02", "RT09")}
    )

    def all(self) -> Mapping[str, Requirement]:
        return self.requirements

    def categories(self) -> Mapping[str, str]:
        return {"integration": "01 / Integration"}


@dataclass
class FakeTeam:
    team: Team = TEAM

    def load(self) -> Team:
        return self.team


@dataclass
class FakeWorkspace:
    branch: str = "spec/001-demo"
    digest: str = "sha256:code-v1"
    identity: str = "Ana <ana@example.com>"

    def current_branch(self) -> str:
        return self.branch

    def git_identity(self) -> str:
        return self.identity

    def head_commit(self) -> str:
        return "abc1234"

    def governed_digest(self) -> str:
        return self.digest


@dataclass
class FakeConfirmation:
    answer: str | None = None
    interactive: bool = True
    shown: list[str] = field(default_factory=list)

    def confirm(self, summary: str, expected: str) -> bool:
        if not self.interactive:
            raise HumanConfirmationRequiredError("no terminal")
        self.shown.append(summary)
        return (self.answer if self.answer is not None else expected) == expected


class FixedClock:
    def now(self) -> datetime:
        return NOW


@dataclass
class FakeChecks:
    checks: tuple[QualityCheck, ...] = (
        QualityCheck("lint", "Lint", ("ruff", "check")),
        QualityCheck("tests", "Tests", ("pytest",)),
    )

    def all(self) -> tuple[QualityCheck, ...]:
        return self.checks


@dataclass
class FakeRunner:
    failing: set[str] = field(default_factory=set)

    def run(self, check: QualityCheck) -> CheckOutcome:
        passed = check.id not in self.failing
        return CheckOutcome(check.id, passed, "ok" if passed else "boom")


@dataclass
class MemoryStore:
    files: dict[str, str] = field(default_factory=dict)

    def paths(self, prefix: str = "", suffix: str = "") -> tuple[str, ...]:
        return tuple(sorted(p for p in self.files if p.startswith(prefix) and p.endswith(suffix)))

    def read(self, path: str) -> str | None:
        return self.files.get(path)

    def write(self, path: str, content: str) -> None:
        self.files[path] = content

    def exists(self, path: str) -> bool:
        return path in (".", "") or any(p == path or p.startswith(path + "/") for p in self.files)

    def remove(self, path: str) -> None:
        self.files.pop(path, None)


@dataclass
class DictTemplates:
    templates: dict[str, str] = field(default_factory=dict)

    def text(self, name: str) -> str:
        return self.templates.get(name, f"# {name}\n\n## Section\n\nTODO(sdd): fill\n")

    def render(self, name: str, values: Mapping[str, str]) -> str:
        return re.sub(
            r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), self.text(name)
        )


@dataclass
class StaticLogos:
    entries: tuple[Logo, ...] = (
        Logo("PostgreSQL", ("Postgres",), "https://cdn.simpleicons.org/postgresql"),
        Logo("Python", (), "https://cdn.simpleicons.org/python"),
    )

    def logos(self) -> tuple[Logo, ...]:
        return self.entries


READY = "# Artifact\n\n## Section\n\nDone and reviewed.\n"
"""An artifact that satisfies the default `DictTemplates` template."""
