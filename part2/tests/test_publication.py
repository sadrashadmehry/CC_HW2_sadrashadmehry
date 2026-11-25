"""Publication changes a copy, preserving source content and the Git placeholder."""
import importlib.util
from pathlib import Path

import pytest

TOOL = Path(__file__).resolve().parents[1] / "tools" / "render_site.py"
spec = importlib.util.spec_from_file_location("render_site", TOOL)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_publication_preserves_source_and_sentence(tmp_path):
    source = TOOL.parents[1] / "site" / "index.html"
    before = source.read_bytes()
    version = "v2026-11-25-" + "a" * 40
    module.render(version, tmp_path)
    assert (tmp_path / "index.html").read_text(encoding="utf-8") == source.read_text(encoding="utf-8-sig").replace("__VERSION__", version)
    assert source.read_bytes() == before
    module.render(version, tmp_path)
    assert source.read_bytes() == before


@pytest.mark.parametrize("version", ["", "../main", "<script>", "main\n", "x" * 129])
def test_invalid_version_does_not_create_output(tmp_path, version):
    output = tmp_path / "publication"
    with pytest.raises(ValueError):
        module.render(version, output)
    assert not output.exists()



def test_rollback_uses_the_selected_sources_sentence(tmp_path, monkeypatch):
    """A previous checkout must restore its sentence, not only its version label."""
    selected = tmp_path / "selected-tag"
    (selected / "site").mkdir(parents=True)
    source = selected / "site" / "index.html"
    source.write_text('<p id="version">__VERSION__</p><p id="sentence">old sentence</p>', encoding="utf-8")
    monkeypatch.setattr(module, "__file__", str(selected / "tools" / "render_site.py"))
    output = tmp_path / "published"
    (tmp_path / "published").mkdir()
    (output / "index.html").write_text('new sentence', encoding="utf-8")
    module.render("v-old", output)
    published = (output / "index.html").read_text(encoding="utf-8")
    assert '<p id="version">v-old</p>' in published
    assert '<p id="sentence">old sentence</p>' in published
    assert 'new sentence' not in published
    assert '__VERSION__' in source.read_text(encoding="utf-8")
