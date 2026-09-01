"""Obsidian PKM Relational Vault Exporter."""

from __future__ import annotations

import json
from pathlib import Path


class ObsidianVaultExporter:
    """Exports structured workspace literature into an Obsidian PKM Vault with wikilinks."""

    @classmethod
    def export_vault(cls, workspace_dir: Path | str, output_vault_dir: Path | str) -> Path:
        """Construct an Obsidian relational vault with frontmatter, tags, and wikilinks."""
        w_dir = Path(workspace_dir).resolve()
        vault_dir = Path(output_vault_dir).resolve()
        vault_dir.mkdir(parents=True, exist_ok=True)

        notes_dir = vault_dir / "literature_notes"
        notes_dir.mkdir(parents=True, exist_ok=True)

        inc_file = w_dir / "literature" / "included.json"
        papers = []
        if inc_file.exists():
            try:
                papers = json.loads(inc_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        note_links = []
        for p in papers:
            doc_id = p.get("workspace_id") or p.get("doi", "unknown").replace("/", "_")
            title = p.get("title", "Untitled Document")
            authors = p.get("authors", [])
            year = p.get("year", 2024)
            doi = p.get("doi", "")
            abstract = p.get("abstract", "No abstract available.")

            authors_str = ", ".join(authors) if isinstance(authors, list) else str(authors)

            note_content = (
                f"---\n"
                f"id: \"{doc_id}\"\n"
                f"title: \"{title}\"\n"
                f"authors: \"{authors_str}\"\n"
                f"year: {year}\n"
                f"doi: \"{doi}\"\n"
                f"tags:\n"
                f"  - literature\n"
                f"  - nexus-scholar\n"
                f"---\n\n"
                f"# {title}\n\n"
                f"**Authors**: {authors_str}  \n"
                f"**Year**: {year}  \n"
                f"**DOI**: [{doi}](https://doi.org/{doi})  \n"
                f"**Workspace Reference**: [[{w_dir.name}]]\n\n"
                f"## Abstract\n{abstract}\n\n"
                f"## Key Methodological Notes\n- Extracted via [[Nexus-Scholar Harness]]\n- See extraction matrix in [[Synthesis Matrix]]\n\n"
                f"## Related Studies & Citations\n- [[Map of Content]]\n"
            )

            filename = f"{doc_id}_{year}.md".replace(":", "_").replace("/", "_")
            note_path = notes_dir / filename
            note_path.write_text(note_content, encoding="utf-8")
            note_links.append((doc_id, title, year, filename))

        # Generate Map of Content (MOC.md)
        moc_rows = []
        for doc_id, title, year, filename in note_links:
            moc_rows.append(f"| [[{filename[:-3]}]] | {title} | {year} |")

        moc_content = (
            f"# Map of Content: {w_dir.name}\n\n"
            f"> Generated automatically by Nexus Scholar Harness.\n\n"
            f"| Document Reference | Title | Year |\n"
            f"| :--- | :--- | :---: |\n"
            + "\n".join(moc_rows)
            + "\n\n## Project Workspace Links\n"
            f"- [[literature_review]]\n"
            f"- [[synthesis_matrix]]\n"
        )

        (vault_dir / "Map of Content.md").write_text(moc_content, encoding="utf-8")

        # Copy synthesis review if exists
        synth_file = w_dir / "synthesis" / "literature_review.md"
        if synth_file.exists():
            (vault_dir / "literature_review.md").write_text(synth_file.read_text(encoding="utf-8"), encoding="utf-8")

        return vault_dir
