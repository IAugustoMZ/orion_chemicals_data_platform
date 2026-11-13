"""Adapter of the `ProgressRepository` port: `specs/<id>-<slug>/progress.yaml` on disk.

Infrastructure layer. The file is written only by `sdd` (the agent guard refuses edits by agents),
so approvals in it are as trustworthy as the ones in `dossier.yaml`. The format is versioned:
``version: 1``, then ``items`` keyed by card number.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from sdd.domain.approval import Approval
from sdd.domain.errors import InvalidDossierError
from sdd.domain.item_progress import ItemProgress, ItemRecord, ItemState

PROGRESS = "progress.yaml"
_HEADER = """\
# Progress of the backlog, one entry per card (ADR-0023). Written only by `sdd`:
# never edit by hand. Approvals are bound to the digest of the card's section of backlog.md.
"""
_FOLDER = re.compile(r"^(?P<id>\d{3})-")


class YamlProgressRepository:
    """Store the progress of each dossier next to its other artifacts."""

    def __init__(self, root: Path, specs_dir: str) -> None:
        """Remember where dossiers live.

        Args:
            root: absolute path of the repository root.
            specs_dir: repository-relative folder of the dossiers ("specs").
        """
        self._base = root / specs_dir

    def load(self, dossier_id: str) -> ItemProgress | None:
        """Return the stored progress, or None when the dossier has no `progress.yaml`.

        Args:
            dossier_id: three-digit dossier id.

        Raises:
            InvalidDossierError: when the file cannot be parsed or mapped.
        """
        path = self._path(dossier_id)
        if path is None or not path.is_file():
            return None
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return _from_data(data)
        except (yaml.YAMLError, KeyError, TypeError, ValueError, AttributeError) as error:
            raise InvalidDossierError(f"{path.parent.name}/{PROGRESS}: {error}") from error

    def save(self, dossier_id: str, progress: ItemProgress) -> None:
        """Write the progress next to the dossier's other artifacts.

        Args:
            dossier_id: three-digit dossier id.
            progress: the snapshot to store.

        Raises:
            InvalidDossierError: when the dossier folder does not exist.
        """
        folder = self._folder(dossier_id)
        if folder is None:
            raise InvalidDossierError(f"no dossier folder for id {dossier_id}")
        body = yaml.safe_dump(_to_data(progress), sort_keys=False, allow_unicode=True)
        (folder / PROGRESS).write_text(_HEADER + body, encoding="utf-8", newline="\n")

    def _folder(self, dossier_id: str) -> Path | None:
        """Return the folder of a dossier, or None when it does not exist.

        Args:
            dossier_id: three-digit dossier id.
        """
        if not self._base.is_dir():
            return None
        return next(
            (
                f
                for f in sorted(self._base.iterdir())
                if f.is_dir() and (m := _FOLDER.match(f.name)) and m.group("id") == dossier_id
            ),
            None,
        )

    def _path(self, dossier_id: str) -> Path | None:
        """Return the path of the dossier's `progress.yaml`, or None without a folder.

        Args:
            dossier_id: three-digit dossier id.
        """
        folder = self._folder(dossier_id)
        return None if folder is None else folder / PROGRESS


def _to_data(progress: ItemProgress) -> dict[str, Any]:
    """Return the plain-data form of a progress snapshot.

    Args:
        progress: the snapshot.
    """
    return {
        "version": progress.version,
        "items": {
            number: {
                "state": record.state.value,
                "approvals": [_approval_data(a) for a in record.approvals],
                "branch": record.branch,
                "commit": record.commit,
                "pull_request": record.pull_request,
                "merged_at": record.merged_at.isoformat() if record.merged_at else None,
            }
            for number, record in sorted(progress.items.items())
        },
    }


def _from_data(data: Any) -> ItemProgress:
    """Build a progress snapshot from the plain data of the file.

    Args:
        data: the parsed YAML document.
    """
    if not isinstance(data, dict):
        raise TypeError("progress.yaml must be a mapping")
    items = {}
    for raw_number, entry in (data.get("items") or {}).items():
        number = str(raw_number).zfill(2)
        merged = entry.get("merged_at")
        items[number] = ItemRecord(
            number=number,
            state=ItemState(entry.get("state", ItemState.OUTLINE.value)),
            approvals=tuple(_approval(a) for a in entry.get("approvals") or ()),
            branch=str(entry.get("branch") or ""),
            commit=str(entry.get("commit") or ""),
            pull_request=str(entry.get("pull_request") or ""),
            merged_at=datetime.fromisoformat(str(merged)) if merged else None,
        )
    return ItemProgress(items=items, version=int(data.get("version", 1)))


def _approval_data(approval: Approval) -> dict[str, str]:
    """Return the plain-data form of an approval.

    Args:
        approval: the approval.
    """
    return {
        "member": approval.member,
        "at": approval.approved_at.isoformat(),
        "digest": approval.digest,
        "git_identity": approval.git_identity,
        "note": approval.note,
    }


def _approval(data: dict[str, Any]) -> Approval:
    """Build an approval from its plain data.

    Args:
        data: one entry of a card's ``approvals`` list.
    """
    return Approval(
        member=str(data["member"]),
        approved_at=datetime.fromisoformat(str(data["at"])),
        digest=str(data["digest"]),
        git_identity=str(data.get("git_identity", "")),
        note=str(data.get("note") or ""),
    )
