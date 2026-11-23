"""Write private plant truth as ordered JSON with atomic replacement."""

import json
import os
from dataclasses import asdict
from pathlib import Path
from tempfile import NamedTemporaryFile

from tssource.domain.errors import TssourceError
from tssource.domain.plant.model import Plant


class PlantJsonWriter:
    """Publish a single owner-only file under the trusted output directory."""

    def write(self, plant: Plant, output_folder: Path) -> Path:
        """Stage every byte beside the target before replacing the previous file."""
        target = output_folder / "truth" / "plant.json"
        try:
            if target.parent.is_symlink() or target.is_symlink():
                raise TssourceError("plant output refuses a symlink at truth or truth/plant.json")
            target.parent.mkdir(parents=True, exist_ok=True)
            document = asdict(plant)
            for row, point in zip(document["instruments"], plant.instruments, strict=True):
                row["expected_interval_seconds"] = point.expected_interval_seconds
            _publish({"schema_version": 1, "generator": "tssource", **document}, target)
        except OSError as error:
            raise TssourceError(
                f"could not write truth/plant.json ({error.strerror or error})"
            ) from error
        return target


def _publish(document: dict[str, object], target: Path) -> None:
    """Keep the staging file private and remove it if publication fails."""
    staged: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=target.parent,
            prefix=".plant-",
            suffix=".tmp",
            delete=False,
        ) as file:
            staged = Path(file.name)
            os.fchmod(file.fileno(), 0o600)
            json.dump(document, file, indent=2)
            file.write("\n")
        staged.replace(target)
        staged = None
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)
