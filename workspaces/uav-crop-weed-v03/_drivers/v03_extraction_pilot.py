#!/usr/bin/env python3
"""Bounded full-text pilot for the v0.3 workspace (10 included studies).

Downloads are performed separately by `scholar-pdf download` into
`pdfs/`, which is gitignored. This driver only turns those already-validated
PDF bytes into extracted Markdown and records exactly what it found.

It is deliberately non-authoritative: the kit's E2 parent-bound path needs an
accepted Contract v1 `screening_decisions` artifact, which this workspace does
not have. So this pilot uses the documented legacy `PyMuPDFEngine` convenience
contract and records that fact in the manifest. Nothing here is an acceptance
claim.

Run: uv run python workspaces/uav-crop-weed-v03/_drivers/v03_extraction_pilot.py
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

WS = Path(__file__).resolve().parents[1]
PDF_DIR = WS / "pdfs"
EXTRACTED = WS / "extracted"
SUMMARY = PDF_DIR / "download_summary.json"
OUT = EXTRACTED / "_pilot_manifest.json"

PILOT = [
    ("SCI-000006", "10.1371/journal.pone.0251008"),
    ("SCI-000291", "10.1038/s41598-025-15380-3"),
    ("SCI-000372", "10.1038/s41598-026-58738-x"),
    ("SCI-000607", "10.1038/s41598-022-23399-z"),
    ("SCI-000041", "10.48550/arxiv.2505.07444"),
    ("SCI-000044", "10.48550/arxiv.2106.10581"),
    ("SCI-000227", "10.48550/arxiv.2109.02716"),
    ("SCI-000736", "10.48550/arxiv.2608.21254"),
    ("SCI-000151", "10.3389/frsen.2022.755939"),
    ("SCI-000644", "10.3389/fpls.2021.702626"),
]

STUB_MARKER = "Extracted content from "
MIN_BODY = 200
NOTES = {
    "10.48550/arxiv.2109.02716": (
        "download failed with HTTP 404: the resolved arXiv URL is "
        "https://arxiv.org/pdf/arxiv.2109.02716 (the kit prefixes 'arxiv.' to an id "
        "that already starts with it). Not worked around silently; recorded as a "
        "kit URL-construction defect and left unresolved."
    ),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def split_frontmatter(text: str) -> tuple[dict, str] | tuple[None, str]:
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    import yaml

    try:
        meta = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError:
        return None, text
    return meta, text[end + 5 :]


def main() -> int:
    included = {}
    for rec in json.loads((WS / "literature" / "included.json").read_text()):
        if rec.get("doi"):
            included[rec["doi"].lower()] = rec

    downloaded = {}
    if SUMMARY.exists():
        for rec in json.loads(SUMMARY.read_text()):
            downloaded[rec["doi"].lower()] = rec

    from scholar_pdf.extract import PyMuPDFEngine

    EXTRACTED.mkdir(parents=True, exist_ok=True)
    records = []
    for study_id, doi in PILOT:
        rec = included.get(doi.lower())
        dl = downloaded.get(doi.lower())
        entry = {"study_id": study_id, "doi": doi}
        if rec is None:
            entry.update({"status": "FAILED", "detail": "DOI not found in included.json"})
            records.append(entry)
            continue
        entry.update({"title": rec["title"], "year": rec.get("year")})
        if dl is None:
            entry.update({
                "status": "UNRESOLVED",
                "detail": NOTES.get(
                    doi.lower(),
                    "no validated OA PDF was resolved (recorded as unresolved, not as empty success)",
                ),
            })
            records.append(entry)
            continue

        pdf = Path(dl["file_path"])
        if not pdf.exists():
            entry.update({"status": "FAILED", "detail": f"summary path missing: {pdf}"})
            records.append(entry)
            continue
        head = pdf.open("rb").read(1024)
        if b"%PDF-" not in head:
            entry.update({"status": "FAILED", "detail": "magic-byte check failed"})
            records.append(entry)
            continue

        md_path = PyMuPDFEngine.extract_markdown(
            pdf,
            EXTRACTED,
            metadata={
                "workspace_id": study_id,
                "doi": rec["doi"],
                "title": rec["title"],
                "year": rec.get("year"),
            },
        )
        text = md_path.read_text(encoding="utf-8")
        meta, body = split_frontmatter(text)
        body = body.strip()
        problems = []
        if meta is None:
            problems.append("unreadable frontmatter")
        else:
            if (meta.get("doi") or "").lower() != rec["doi"].lower():
                problems.append("frontmatter DOI does not match the included record")
            if meta.get("workspace_id") != study_id:
                problems.append("frontmatter workspace_id does not match the study")
        if STUB_MARKER in text:
            problems.append("extractor stub marker present (no real body)")
        if len(body) < MIN_BODY:
            problems.append(f"body under {MIN_BODY} characters ({len(body)})")

        entry.update({
            "status": "FAILED" if problems else "EXTRACTED_VALID",
            "pdf_sha256": sha256(pdf),
            "pdf_bytes": pdf.stat().st_size,
            "extracted_path": str(md_path.relative_to(WS)),
            "extracted_sha256": sha256(md_path),
            "body_characters": len(body),
            "has_abstract_heading": "## Abstract" in text or "# Abstract" in text,
            "frontmatter": meta,
            "problems": problems,
        })
        records.append(entry)

    valid = [r for r in records if r["status"] == "EXTRACTED_VALID"]
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "workspace": WS.name,
        "path": "legacy PyMuPDF convenience (non-authoritative)",
        "why_not_e2": (
            "The parent-bound E2 path requires an accepted Contract v1 "
            "screening_decisions artifact; this workspace records screening through "
            "decision artifacts and HumanConfirmation@1, not a Contract v1 registry. "
            "No acceptance is claimed for these files."
        ),
        "engine": "pymupdf",
        "selection": "10 included studies across journal/preprint, segmentation/classification, and transfer",
        "records": records,
        "summary": {
            "attempted": len(records),
            "extracted_valid": len(valid),
            "failed": len([r for r in records if r["status"] == "FAILED"]),
            "unresolved": len([r for r in records if r["status"] == "UNRESOLVED"]),
            "total_body_characters": sum(r.get("body_characters", 0) for r in valid),
        },
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    for r in records:
        print(f"{r['status']:16} {r['study_id']} {r['doi']} "
              f"{r.get('body_characters', '')} {r.get('problems', '')}")
    print("\n" + json.dumps(payload["summary"], indent=1))
    return 0  # the pilot records unresolved/failed items instead of failing the run


if __name__ == "__main__":
    raise SystemExit(main())
