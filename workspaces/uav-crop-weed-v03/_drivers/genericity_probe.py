"""Genericity + parity probes (2026-10-17 decontamination run).

A parity: research-config provider reproduces the r3 emitted compact string byte-for-byte.
B default: kit-default ArxivProvider emits a domain-free compact string (no
  stoplist, no stem family) and never invents weed morphology.
C gery: the patched kit files must contain no domain tokens; the research
  values must live only at the harness layer.
All read-only; no writes.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "scholar-search-kit" / "src"))
sys.path.insert(0, str(ROOT / "workspaces" / "uav-crop-weed-v03" / "_drivers"))

import uav_query_translator as uqt

DOMAIN_TOKENS = (
    "weedy",
    "weediness",
    " a weed",
    "'weed'",
    " weed ",
    "crop-weed",
    "orthomosaic",
    "aerial ",
    " uav",
    "uas",
    "drone",
    "crop)",
    "('crop'",
    "sorghum",
    "maize",
    "rice",
    "herbicide",
    "sentinel-2",
    "landsat",
)


def probe_parity():
    q = uqt.build_protocol_boolean_query(
        ROOT / "workspaces" / "uav-crop-weed-v03" / "protocol.json"
    )
    got = uqt.emitted_compact_query(uqt.make_research_arxiv_provider(), q)
    ok = got == uqt.R3_RECORDED_EMITTED_QUERY
    print(f"PROBE-A PARITY: {'PASS' if ok else 'FAIL'}")
    if not ok:
        print("expected:", uqt.R3_RECORDED_EMITTED_QUERY)
        print("got     :", got)
    return ok


def probe_default():
    from scholar_search.providers import ArxivProvider

    ax = ArxivProvider()
    assert ax.compact_stoplist == frozenset() and ax.compact_stem_families == (), (
        "kit default must be empty"
    )
    q = uqt.build_protocol_boolean_query(
        ROOT / "workspaces" / "uav-crop-weed-v03" / "protocol.json"
    )
    emitted = uqt.emitted_compact_query(ax, q)
    has_stem = ("all:weedy" in emitted) or ("all:weediness" in emitted)
    has_ortho = "all:orthomosaic" in emitted
    print(
        "PROBE-B DEFAULT: compact_stoplist=EMPTY, stem_families=EMPTY -> "
        f"stem_expansion_absent_from_default={not has_stem} "
        f"domain_head_kept_by_default={has_ortho} "
        "(domain morphology reachable only via research config)"
    )
    return (not has_stem) and has_ortho


def probe_kit_clean():
    targets = [
        "providers/arxiv.py",
        "models.py",
        "providers/pubmed.py",
        "providers/openalex.py",
        "providers/semanticscholar.py",
        "enrichment.py",
        "dedup.py",
    ]
    bad = []
    for rel in targets:
        text = (
            (ROOT / "tools" / "scholar-search-kit" / "src" / "scholar_search" / rel)
            .read_text(encoding="utf-8")
            .lower()
        )
        for tok in DOMAIN_TOKENS:
            if tok.lower() in text:
                bad.append((rel, tok))
    print(
        f"PROBE-C KIT-CLEAN: {'PASS (7 files domain-token-free)' if not bad else f'FAIL {bad}'}"
    )
    return not bad


def main():
    a = probe_parity()
    b = probe_default()
    c = probe_kit_clean()
    verdicts = {"parity": a, "default_domain_free": b, "kit_clean": c}
    print("PROBE-VERDICTS:", verdicts)
    sys.exit(0 if all(verdicts.values()) else 1)


if __name__ == "__main__":
    main()
