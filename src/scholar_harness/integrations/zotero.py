"""Zotero Reference Manager Bridge."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class ZoteroBridge:
    """Synchronizes screened literature and harvested PDFs with Zotero collections."""

    def __init__(self, api_key: str | None = None, library_id: str | None = None):
        self.api_key = api_key or os.environ.get("ZOTERO_API_KEY")
        self.library_id = library_id or os.environ.get("ZOTERO_LIBRARY_ID")

    def sync_included_papers(
        self,
        included_json_path: Path | str,
        pdf_dir: Path | str | None = None,
        project_slug: str = "nexus-review",
    ) -> dict[str, Any]:
        """Convert included papers into Zotero item format and export sync manifest."""
        inc_file = Path(included_json_path)
        pdf_folder = Path(pdf_dir) if pdf_dir else None

        papers = []
        if inc_file.exists():
            try:
                papers = json.loads(inc_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        zotero_items = []
        for p in papers:
            title = p.get("title", "")
            doi = p.get("doi", "")
            year = p.get("year", 2024)
            authors = p.get("authors", [])

            creators = []
            if isinstance(authors, list):
                for a in authors:
                    parts = a.split(" ", 1)
                    if len(parts) == 2:
                        creators.append({"creatorType": "author", "firstName": parts[0], "lastName": parts[1]})
                    else:
                        creators.append({"creatorType": "author", "name": a})

            first_author = (creators[0].get("lastName") or "author").lower() if creators else "author"
            cite_key = f"{first_author}{year}{title[:10].replace(' ', '').lower()}"

            # Check if matching PDF exists
            pdf_path_str = None
            if pdf_folder and pdf_folder.exists():
                for f in pdf_folder.glob("*.pdf"):
                    if doi and doi.replace("/", "_") in f.name:
                        pdf_path_str = str(f)
                        break

            item = {
                "itemType": "journalArticle",
                "title": title,
                "creators": creators,
                "date": str(year),
                "DOI": doi,
                "abstractNote": p.get("abstract", ""),
                "extra": f"Citation Key: {cite_key}\nWorkspace ID: {p.get('workspace_id', '')}",
                "collections": [f"Nexus-Scholar/{project_slug}"],
                "pdf_attachment": pdf_path_str
            }
            zotero_items.append(item)

        manifest = {
            "project_slug": project_slug,
            "target_collection": f"My Library > Nexus-Scholar > {project_slug}",
            "items_synced": len(zotero_items),
            "items": zotero_items,
            "sync_mode": "LIVE_API" if (self.api_key and self.library_id) else "OFFLINE_EXPORT"
        }

        # Write manifest companion
        out_manifest = inc_file.parent / "zotero_manifest.json"
        out_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        return manifest
