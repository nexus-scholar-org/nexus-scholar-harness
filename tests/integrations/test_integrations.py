"""Unit tests for Academic Ecosystem Integrations in scholar-harness."""

import json
from pathlib import Path
import pytest

from scholar_harness.integrations.latex_typst import AcademicTypesettingExporter
from scholar_harness.integrations.obsidian import ObsidianVaultExporter
from scholar_harness.integrations.zotero import ZoteroBridge


@pytest.fixture
def mock_workspace(tmp_path):
    lit_dir = tmp_path / "literature"
    synth_dir = tmp_path / "synthesis"
    lit_dir.mkdir()
    synth_dir.mkdir()

    # Create included.json
    included = [
        {
            "workspace_id": "SCI-000001",
            "title": "Attention Is All You Need",
            "authors": ["Ashish Vaswani", "Noam Shazeer"],
            "year": 2017,
            "doi": "10.5555/3295222.3295349",
            "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks."
        },
        {
            "workspace_id": "SCI-000002",
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "authors": ["Jacob Devlin", "Ming-Wei Chang"],
            "year": 2018,
            "doi": "10.18653/v1/N19-1423",
            "abstract": "We introduce a new language representation model called BERT."
        }
    ]
    (lit_dir / "included.json").write_text(json.dumps(included), encoding="utf-8")

    # Create references.bib
    bib_content = (
        "@article{vaswani2017attention,\n"
        "  title={Attention is all you need},\n"
        "  author={Vaswani, Ashish},\n"
        "  year={2017}\n"
        "}\n"
    )
    (lit_dir / "references.bib").write_text(bib_content, encoding="utf-8")

    # Create synthesis markdown
    synth_md = (
        "# Literature Review on Transformers\n\n"
        "## Empirical Breakthroughs\n"
        "Transformers demonstrate state-of-the-art sequence modeling [SCI-000001].\n"
        "Furthermore, bidirectional pre-training achieved superior language understanding [SCI_000002#results#chk01].\n"
    )
    (synth_dir / "literature_review.md").write_text(synth_md, encoding="utf-8")

    return tmp_path


def test_latex_exporter(mock_workspace):
    md_file = mock_workspace / "synthesis" / "literature_review.md"
    bib_file = mock_workspace / "literature" / "references.bib"
    tex_out = mock_workspace / "synthesis" / "literature_review.tex"

    out = AcademicTypesettingExporter.export_latex(md_file, bib_file, tex_out)
    assert out.exists()

    content = out.read_text(encoding="utf-8")
    assert "\\section{Literature Review on Transformers}" in content
    assert "\\subsection{Empirical Breakthroughs}" in content
    assert "\\cite{SCI-000001}" in content
    assert "\\cite{SCI_000002}" in content
    assert "\\bibliography{references}" in content


def test_typst_exporter(mock_workspace):
    md_file = mock_workspace / "synthesis" / "literature_review.md"
    bib_file = mock_workspace / "literature" / "references.bib"
    typ_out = mock_workspace / "synthesis" / "literature_review.typ"

    out = AcademicTypesettingExporter.export_typst(md_file, bib_file, typ_out)
    assert out.exists()

    content = out.read_text(encoding="utf-8")
    assert "= Literature Review on Transformers" in content
    assert "== Empirical Breakthroughs" in content
    assert "@SCI-000001" in content
    assert "#bibliography(\"references.bib\")" in content


def test_obsidian_vault_exporter(mock_workspace):
    vault_out = mock_workspace / "obsidian_vault"
    out = ObsidianVaultExporter.export_vault(mock_workspace, vault_out)
    assert out.exists()

    # Check Map of Content
    moc_file = vault_out / "Map of Content.md"
    assert moc_file.exists()
    moc_text = moc_file.read_text(encoding="utf-8")
    assert "Attention Is All You Need" in moc_text
    assert "BERT: Pre-training of Deep Bidirectional Transformers" in moc_text

    # Check Note files
    notes_dir = vault_out / "literature_notes"
    note_files = list(notes_dir.glob("*.md"))
    assert len(note_files) == 2

    sample_note = notes_dir / "SCI-000001_2017.md"
    assert sample_note.exists()
    note_text = sample_note.read_text(encoding="utf-8")
    assert "Ashish Vaswani" in note_text
    assert "10.5555/3295222.3295349" in note_text
    assert "tags:" in note_text


def test_zotero_bridge(mock_workspace):
    bridge = ZoteroBridge()
    inc_file = mock_workspace / "literature" / "included.json"
    manifest = bridge.sync_included_papers(inc_file, project_slug="transformer-review")

    assert manifest["project_slug"] == "transformer-review"
    assert manifest["items_synced"] == 2
    assert len(manifest["items"]) == 2

    item0 = manifest["items"][0]
    assert item0["title"] == "Attention Is All You Need"
    assert item0["DOI"] == "10.5555/3295222.3295349"
    assert "Citation Key:" in item0["extra"]

    manifest_file = mock_workspace / "literature" / "zotero_manifest.json"
    assert manifest_file.exists()
