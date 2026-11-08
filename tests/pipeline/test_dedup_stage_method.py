"""M7-method: the discovery dedup stage uses the workspace protocol's tiers.

Otherwise a corpus built by discovery would be deduplicated at the defaults
while the methods paragraph reports the protocol's values.
"""

from __future__ import annotations

import json

from scholar_harness.pipeline.deduplication import run_deduplication
from scholar_search.models import Author, Document

TITLE = "Weed mapping in maize with unmanned aerial vehicles and deep learning"


def _docs():
    return [
        Document(title=TITLE, year=2020, provider="openalex", provider_id="a", authors=[Author(family_name="Huang")]),
        Document(title=TITLE, year=2021, provider="crossref", provider_id="b", authors=[Author(family_name="Huang")]),
    ]


def test_without_a_block_the_stage_keeps_the_default_tiers(tmp_path):
    (tmp_path / "protocol.json").write_text(json.dumps({"protocol_id": "p"}), encoding="utf-8")
    assert run_deduplication(discovered_documents=_docs(), literature_dir=tmp_path / "literature").duplicates_removed == 1


def test_the_protocols_year_tolerance_applies_to_discovery(tmp_path):
    method = {
        "dedup": {"doi": True, "title_similarity": 0.97, "first_author": True, "year_tolerance": 0},
        "rules_version": "screening-rules-v1",
        "not_reported": "unclear",
        "blinding": "reveal_after_decision",
    }
    (tmp_path / "protocol.json").write_text(json.dumps({"protocol_id": "p", "method": method}), encoding="utf-8")
    assert run_deduplication(discovered_documents=_docs(), literature_dir=tmp_path / "literature").duplicates_removed == 0
