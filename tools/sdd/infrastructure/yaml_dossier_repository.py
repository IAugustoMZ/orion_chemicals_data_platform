"""Adapter of the `DossierRepository` port: `specs/<id>-<slug>/` folders on disk.

Infrastructure layer. `dossier.yaml` is written with a fixed header comment that tells people and
agents which parts are theirs to edit and which are written only by `sdd` (approvals and
verification, protected by the agent guard and bound to digests).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path

import yaml

from sdd.domain.dossier import Dossier
from sdd.domain.errors import DossierNotFoundError, InvalidDossierError
from sdd.infrastructure.dossier_mapper import from_data, to_data

METADATA = "dossier.yaml"
_FOLDER = re.compile(r"^(?P<id>\d{3})-[a-z0-9-]+$")
_HEADER = """\
# Dossier metadata (harness/how-it-works.md, "The dossier").
# Edit freely: title, requirements (RT ids from docs/requirements/rt-catalog.yaml), rationale.
# Never edit by hand: `approvals` (written by `sdd approve`, humans only) and `verification`
# (written by `sdd verify`). Both are bound to content digests; a hand edit is detected.
"""


class YamlDossierRepository:
    """Store dossiers as folders under `specs_dir`."""

    def __init__(self, root: Path, specs_dir: str) -> None:
        """Remember where dossiers live.

        Args:
            root: absolute path of the repository root.
            specs_dir: repository-relative folder of the dossiers ("specs").
        """
        self._root = root
        self._specs_dir = specs_dir

    def ids(self) -> tuple[str, ...]:
        """Return the ids of the folders that hold a `dossier.yaml`, sorted."""
        base = self._root / self._specs_dir
        if not base.is_dir():
            return ()
        found = (
            match.group("id")
            for folder in base.iterdir()
            if (match := _FOLDER.match(folder.name)) and (folder / METADATA).is_file()
        )
        return tuple(sorted(found))

    def load(self, dossier_id: str) -> Dossier:
        """Load a dossier by id.

        Args:
            dossier_id: three digits.

        Raises:
            DossierNotFoundError: when no folder has that id.
            InvalidDossierError: when the YAML cannot be parsed or mapped.
        """
        folder = self._folder_of(dossier_id)
        try:
            data = yaml.safe_load((folder / METADATA).read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            raise InvalidDossierError(f"{folder.name}/{METADATA}: {error}") from error
        dossier = from_data(data)
        if dossier.folder_name != folder.name:
            raise InvalidDossierError(f"{folder.name}: id/slug in {METADATA} do not match")
        return dossier

    def save(self, dossier: Dossier) -> None:
        """Rewrite `dossier.yaml` of an existing dossier.

        Args:
            dossier: the dossier to persist.
        """
        self._write_metadata(self._root / self._specs_dir / dossier.folder_name, dossier)

    def create(self, dossier: Dossier, artifacts: Mapping[str, str]) -> None:
        """Create the folder, `dossier.yaml` and the initial artifacts.

        Args:
            dossier: the new dossier.
            artifacts: file name -> initial content.

        Raises:
            InvalidDossierError: when the folder already exists.
        """
        folder = self._root / self._specs_dir / dossier.folder_name
        if folder.exists():
            raise InvalidDossierError(f"{folder} already exists")
        folder.mkdir(parents=True)
        self._write_metadata(folder, dossier)
        for name, content in artifacts.items():
            (folder / name).write_text(content, encoding="utf-8", newline="\n")

    def read_artifact(self, dossier: Dossier, name: str) -> str | None:
        """Return an artifact's text, or None when the file does not exist.

        Args:
            dossier: the dossier.
            name: the artifact file name, e.g. "spec.md".
        """
        file = self._root / self._specs_dir / dossier.folder_name / name
        return file.read_text(encoding="utf-8") if file.is_file() else None

    def location(self, dossier: Dossier) -> str:
        """Return ``specs/<id>-<slug>``.

        Args:
            dossier: the dossier.
        """
        return f"{self._specs_dir}/{dossier.folder_name}"

    def _folder_of(self, dossier_id: str) -> Path:
        """Return the folder whose name starts with the id.

        Args:
            dossier_id: three digits.
        """
        base = self._root / self._specs_dir
        matches = sorted(base.glob(f"{dossier_id}-*")) if base.is_dir() else []
        if not matches:
            raise DossierNotFoundError(f"no dossier {dossier_id!r} under {self._specs_dir}/")
        return matches[0]

    @staticmethod
    def _write_metadata(folder: Path, dossier: Dossier) -> None:
        """Write the header comment and the YAML document.

        Args:
            folder: the dossier folder.
            dossier: the dossier.
        """
        body = yaml.safe_dump(to_data(dossier), sort_keys=False, allow_unicode=True, width=99)
        (folder / METADATA).write_text(_HEADER + body, encoding="utf-8", newline="\n")
