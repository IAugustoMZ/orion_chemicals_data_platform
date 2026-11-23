"""Exercise the plant command and its private publication boundary."""

import json
import stat
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tssource.interfaces.cli.app import app

runner = CliRunner()


@pytest.mark.ac("PBI-004-01:AC2")
@pytest.mark.ac("PBI-004-01:AC6")
def test_cli_writes_only_the_versioned_private_model(tmp_path: Path) -> None:
    """Compare the exact files produced with the same seed in two destinations."""
    outputs = []
    for name in ("first", "second"):
        out = tmp_path / name
        result = runner.invoke(app, ["plant", "build", "--seed", "42", "--out", str(out)])
        path = out / "truth" / "plant.json"
        assert result.exit_code == 0, result.output
        assert result.stdout == f"{path}\n"
        assert not result.stderr
        assert sorted(out.rglob("*")) == [path.parent, path]
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        outputs.append(path.read_bytes())
    assert outputs[0] == outputs[1]
    document = json.loads(outputs[0].decode("utf-8"))
    assert document["schema_version"] == 1
    assert document["generator"] == "tssource"
    assert document.keys() == {
        "schema_version",
        "generator",
        "sites",
        "areas",
        "equipment",
        "instruments",
        "control_loops",
        "streams",
        "drivers",
        "inventory",
    }


def test_cli_uses_settings_with_explicit_overrides(tmp_path: Path) -> None:
    """Reuse seed and destination settings while allowing an explicit seed."""
    env = {"TSSOURCE_SEED": "101", "TSSOURCE_OUT": str(tmp_path)}
    path = tmp_path / "truth" / "plant.json"
    assert runner.invoke(app, ["plant", "build"], env=env).exit_code == 0
    first = path.read_bytes()
    assert runner.invoke(app, ["plant", "build", "--seed", "42"], env=env).exit_code == 0
    assert path.read_bytes() != first


@pytest.mark.parametrize(
    ("args", "env"),
    [(["--seed", "-1"], {}), ([], {"TSSOURCE_SEED": "-1"}), ([], {"TSSOURCE_SEED": "bad"})],
)
def test_invalid_seeds_are_usage_errors(
    args: list[str], env: dict[str, str], tmp_path: Path
) -> None:
    """Reject invalid seeds before creating files."""
    result = runner.invoke(app, ["plant", "build", "--out", str(tmp_path), *args], env=env)
    assert result.exit_code == 2
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("symlink_child", [True, False])
def test_cli_rejects_private_output_symlinks(tmp_path: Path, symlink_child: bool) -> None:
    """Keep existing data untouched even if a fixed output component is redirected."""
    target = tmp_path / "other"
    target.mkdir()
    existing = target / "plant.json"
    existing.write_text("keep", encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    truth = out / "truth"
    if symlink_child:
        truth.symlink_to(target, target_is_directory=True)
    else:
        truth.mkdir()
        (truth / "plant.json").symlink_to(existing)
    result = runner.invoke(app, ["plant", "build", "--out", str(out)])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "symlink" in result.stderr
    assert existing.read_text(encoding="utf-8") == "keep"


def test_failed_replace_preserves_existing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Clean the staged file on failure and report no success path."""
    args = ["plant", "build", "--out", str(tmp_path)]
    assert runner.invoke(app, args).exit_code == 0
    path = tmp_path / "truth" / "plant.json"
    before = path.read_bytes()

    def fail_replace(self: Path, target: Path) -> Path:
        """Simulate a failure at the final publication step."""
        raise OSError("replacement failed")

    monkeypatch.setattr(Path, "replace", fail_replace)
    result = runner.invoke(app, [*args, "--seed", "101"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "replacement failed" in result.stderr
    assert list(path.parent.iterdir()) == [path]
    assert path.read_bytes() == before
