"""Keep local fixtures and publication drafts out of built documentation."""

from pathlib import Path

import pytest


@pytest.fixture
def docs_checkout(tmp_path: Path) -> Path:
    """Copy the real configuration into an isolated checkout with readable local files."""
    config = Path(__file__).resolve().parents[2] / "mkdocs.yml"
    (tmp_path / config.name).write_bytes(config.read_bytes())
    (tmp_path / "README.md").write_text("# Published documentation\n", encoding="utf-8")
    for name in (
        "data/ts_source/truth/plant.json",
        "data/ts_source/catalog/tags.parquet",
        "data/ts_source/truth/tag_key.parquet",
        "linkedin-posts/draft.md",
    ):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("local test fixture", encoding="utf-8")
    return tmp_path


@pytest.mark.ac("PBI-004-05:AC1")
def test_docs_file_selection_excludes_local_outputs(docs_checkout: Path) -> None:
    """Apply MkDocs' configured file selection to the primary page and local output trees."""
    config_module = pytest.importorskip("mkdocs.config")
    files_module = pytest.importorskip("mkdocs.structure.files")
    config = config_module.load_config(str(docs_checkout / "mkdocs.yml"), nav=["README.md"])
    selected = {
        file.src_uri for file in files_module.get_files(config) if file.inclusion.is_included()
    }
    assert "README.md" in selected
    assert not any(name.startswith(("data/", "linkedin-posts/")) for name in selected)


@pytest.mark.ac("PBI-004-05:AC2")
def test_strict_site_build_omits_local_output_trees(docs_checkout: Path) -> None:
    """Build the normal page in strict mode without copying any local artifacts."""
    config_module = pytest.importorskip("mkdocs.config")
    build_module = pytest.importorskip("mkdocs.commands.build")
    site_dir = docs_checkout / ".cache" / "site"
    config = config_module.load_config(
        str(docs_checkout / "mkdocs.yml"), nav=["README.md"], site_dir=str(site_dir), strict=True
    )
    build_module.build(config)
    assert "Published documentation" in (site_dir / "index.html").read_text(encoding="utf-8")
    assert not (site_dir / "data").exists()
    assert not (site_dir / "linkedin-posts").exists()
