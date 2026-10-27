"""Phase D mechanical skill rewrite (spec ``03`` §4/§10) and audit.

One deterministic pass over ``.agents/skills/*/SKILL.md``:

1. ``rewrite_text`` — the §4 rewrite rules (``uv run scholar-<x>`` →
   ``{CLI:<x>}``, ``uv run python`` → ``{PY}``, ``tools/scholar-<kit>/`` →
   ``{KIT_ROOT:<kit>}/``, repo workspace paths → ``{WORKSPACE}``).
2. Frontmatter insertion — the §3 contract, generated from the per-skill
   table below; the ``variables`` list is *unioned with the placeholders the
   rewritten body actually uses* so the declared set can never drift from
   the body.
3. Audit report — idioms the mechanical pass cannot own (prose SHAs,
   ``docs/`` pointers, remaining literal invocations). Those are surfaced as
   findings; ``--check`` exits 1 when any remain.

Content is otherwise unchanged (mechanical, not editorial). Idempotent.

Usage::

    uv run python scripts/skill_portability_transform.py            # apply + report
    uv run python scripts/skill_portability_transform.py --check    # audit only
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from scholar_harness.skills_portability import (
    audit_text,
    parse_frontmatter,
    rewrite_text,
)

SKILLS_DIR = ROOT / ".agents" / "skills"

#: Spec 03 §9 skill ↔ role mapping. ``requires`` names kit CLI helpers a
#: preflight must resolve; research-facing skills only (dev-only
#: ``pull-request-gate`` is rewritten but excluded from app packaging).
SKILL_CONTRACTS: dict[str, dict[str, Any]] = {
    "scholar-agent-kit": {
        "applies_to": ["orchestrator", "inception-agent"],
        "requires": ["scholar-agent"],
        "returns": "json",
        "layer": "domain",
        "base_variables": ["CLI", "CONFIG", "CACHE", "WORKSPACE", "SKILL_DIR"],
    },
    "scholar-search-kit": {
        "applies_to": ["screener", "inception-agent"],
        "requires": ["scholar-search"],
        "returns": "json",
        "layer": "domain",
        "base_variables": ["CLI", "CONFIG", "CACHE", "WORKSPACE", "SKILL_DIR"],
    },
    "scholar-pdf-kit": {
        "applies_to": ["extractor-a", "extractor-b"],
        "requires": ["scholar-pdf"],
        "returns": "files",
        "layer": "domain",
        "base_variables": ["CLI", "CONFIG", "WORKSPACE", "SKILL_DIR", "KIT_ROOT"],
    },
    "scholar-protocol-kit": {
        "applies_to": ["inception-agent", "screener"],
        "requires": ["scholar-protocol"],
        "returns": "json",
        "layer": "domain",
        "base_variables": ["CLI", "CONFIG", "WORKSPACE", "SKILL_DIR"],
    },
    "scholar-bib-kit": {
        "applies_to": ["inception-agent"],
        "requires": ["scholar-bib"],
        "returns": "json",
        "layer": "domain",
        "base_variables": ["CLI", "CONFIG", "WORKSPACE", "SKILL_DIR"],
    },
    "scholar-rag-kit": {
        "applies_to": ["extractor-a", "extractor-b"],
        "requires": ["scholar-rag"],
        "returns": "json",
        "layer": "domain",
        "base_variables": ["CLI", "CONFIG", "WORKSPACE", "SKILL_DIR"],
    },
    "scholar-graph-kit": {
        "applies_to": ["inception-agent"],
        "requires": ["scholar-graph"],
        "returns": "json",
        "layer": "domain",
        "base_variables": ["CLI", "CONFIG", "WORKSPACE", "SKILL_DIR"],
    },
    "scholar-verify-kit": {
        "applies_to": ["extraction-critic"],
        "requires": ["scholar-verify"],
        "returns": "json",
        "layer": "domain",
        "base_variables": ["CLI", "CONFIG", "WORKSPACE", "SKILL_DIR"],
    },
    "workspace-manager": {
        "applies_to": ["orchestrator", "inception-agent"],
        "requires": [],
        "returns": "prose",
        "layer": "procedure",
        "base_variables": ["WORKSPACE", "SKILL_DIR", "PY"],
    },
    "inception-agent": {
        "applies_to": ["inception-agent"],
        "requires": ["scholar-agent"],
        "returns": "prose",
        "layer": "procedure",
        "base_variables": ["CLI", "CONFIG", "CACHE", "WORKSPACE", "SKILL_DIR", "PY"],
    },
    "methodology-copilot": {
        "applies_to": ["inception-agent"],
        "requires": [],
        "returns": "prose",
        "layer": "procedure",
        "base_variables": ["WORKSPACE", "SKILL_DIR"],
    },
    "doer-contract": {
        "applies_to": ["screener", "extractor-a", "extractor-b", "adjudicator"],
        "requires": [],
        "returns": "prose",
        "layer": "policy",
        "base_variables": ["SKILL_DIR"],
    },
    "critic-contract": {
        "applies_to": ["screening-critic", "extraction-critic", "reviewer"],
        "requires": [],
        "returns": "prose",
        "layer": "policy",
        "base_variables": ["SKILL_DIR"],
    },
    "pull-request-gate": {
        # Dev-only: §9 — none; excluded from app packaging by Phase D.
        "applies_to": [],
        "requires": [],
        "returns": "prose",
        "layer": "policy",
        "base_variables": ["SKILL_DIR"],
    },
}

_VARIABLE_RE = __import__("re").compile(
    r"\{(CLI|KIT_ROOT|SKILL_DIR|WORKSPACE|CACHE|CONFIG|PY)"
)


def _frontmatter_block(name: str, text: str) -> str:
    """Build the §3 frontmatter; description comes from the current body."""

    body = text.lstrip("\n")
    if name in ("critic-contract", "doer-contract", "pull-request-gate"):
        # Description-first skills keep their one-sentence openers.
        first_para = re.search(r"^([^#\n][^\n]+\n)", body, re.MULTILINE)
        description = first_para.group(1).strip().rstrip(".") if first_para else name
    else:
        # Existing skills open with a role paragraph; derive a short sentence.
        description = {
            "scholar-agent-kit": "The MCP front-door to the eight kit CLIs: discovery, screening hand-off, retrieval, verification, and recon — with declared-unsupported refusals.",
            "scholar-search-kit": "Federated academic search, deduplication, verification, screening batches, and export across OpenAlex, Crossref, PubMed, arXiv, and bioRxiv.",
            "scholar-pdf-kit": "Open Access discovery, resilient download, magic-byte validation, and fulltext extraction with YAML frontmatter.",
            "scholar-protocol-kit": "Deterministic research-protocol compilation, validation, fingerprinting, and criteria rendering.",
            "scholar-bib-kit": "Bibliography parse, lint, merge, dedup, and DOI/reference resolution for BibTeX databases.",
            "scholar-rag-kit": "Structural AST chunking, methodology tagging, hybrid graph-boosted retrieval, and grounded synthesis.",
            "scholar-graph-kit": "Citation knowledge networks, normalized PageRank, and interactive HTML graphs.",
            "scholar-verify-kit": "Retraction status, open-science DAS/CAS scanning, COI audit, and QUADAS-2/PROBAST risk-of-bias scoring.",
            "workspace-manager": "Workspace routing, batch operations, audit journal logging, and catalog synchronization.",
            "inception-agent": "Grounded exploratory inception: probe the literature, distill directions, and scaffold a protocol-bound workspace.",
            "methodology-copilot": "Socratic methodology guidance from paradigm selection to rigor criteria.",
        }[name]

    spec = SKILL_CONTRACTS[name]
    used = sorted({part for part in _VARIABLE_RE.findall(rewrite_text(text))})
    variables = sorted(set(spec["base_variables"]) | set(used))
    lines = ["---", f"name: {name}"]
    lines += [f"description: {description}"]
    if spec["applies_to"]:
        lines += ["applies_to: [" + ", ".join(spec["applies_to"]) + "]"]
    if spec["requires"]:
        lines += ["requires: [" + ", ".join(spec["requires"]) + "]"]
    lines += [
        "variables: [" + ", ".join(variables) + "]",
        f"returns: {spec['returns']}",
        f"layer: {spec['layer']}",
        "---",
        "",
    ]
    return "\n".join(lines)


def _strip_existing_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 1)
        if end != -1:
            return text[end + len("\n---\n") :].lstrip("\n")
    return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="skill_portability_transform.py",
        description="Phase D mechanical skill rewrite + portability audit.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="audit only; exit 1 if any finding remains (no writes)",
    )
    args = parser.parse_args(argv)

    findings_out: list[str] = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        path = skill_dir / "SKILL.md"
        if not path.is_file():
            continue
        name = skill_dir.name
        raw = path.read_text(encoding="utf-8")
        if args.check:
            findings = audit_text(raw)
            if raw.startswith("---") and re.match(r"^---\nname:", raw):
                # Post-transform: also parse the contract frontmatter.
                parse_frontmatter(raw, path)
        else:
            rewritten = _strip_existing_frontmatter(raw)
            rewritten = rewrite_text(rewritten)
            text = _frontmatter_block(name, rewritten) + rewritten
            path.write_text(text, encoding="utf-8", newline="\n")
            findings = audit_text(text)
            if findings and not SKILL_CONTRACTS.get(name):
                findings_out.append(f"{name}: not in the contract table")
        for finding in findings:
            findings_out.append(
                f"{name}/{path.name}:{finding.line_no} [{finding.rule}] {finding.detail}"
            )
    if findings_out:
        print(f"{len(findings_out)} finding(s):")
        for line in findings_out:
            print(f"  {line}")
        return 1
    print("PORTABILITY_OK: no mechanical violations remain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
