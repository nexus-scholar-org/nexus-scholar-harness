"""FastMCP Server for the Nexus Scholar Suite.

Since M0.5 (specs/exploratory-grounding-agent/09_mcp_integration.md) the
suite also exposes three ``recon_*`` tools -- ``recon_probe`` /
``recon_distill`` / ``recon_delta`` -- that drive the harness exploratory-recon
layers (``scholar_harness.recon``) with FAIR session memory.  See the "Import
strategy (Option B)" note next to ``_harness_src`` for how this kit resolves
the harness package at runtime without vendoring any recon code.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

# Phase 0 Imports
from scholar_protocol.compiler import compile_protocol
from scholar_protocol.intent import IntentPacket
from scholar_protocol.models import ResearchProtocol
from scholar_protocol.render import render_screening_criteria
from scholar_protocol.validate import validate_protocol
from scholar_protocol.canonical import canonical_json, canonical_fingerprint

# Phase 1 Imports
from scholar_search.cli import search as search_discover
from scholar_search.dedup import Deduplicator
from scholar_search.engine import SearchEngine
from scholar_search.export import Exporter
from scholar_search.importers import JSONImporter
from scholar_search.models import Document, Query
from scholar_search.providers import (
    ArxivProvider,
    CrossrefProvider,
    OpenAlexProvider,
    SemanticScholarProvider,
)
from scholar_search.screening import evaluate_heuristic_screening, partition_screening_results, reconcile_multi_screener_decisions
from scholar_pdf.extract import PyMuPDFEngine
from scholar_verify.verbatim import VerbatimClaimVerifier

# Phase 2 Imports
from scholar_rag.indexer import ScholarIndexer
from scholar_rag.retriever import ScholarRetriever
from scholar_rag.synthesis import GroundedSynthesisEngine
from scholar_rag.matrix import MatrixExtractor
from scholar_graph.builder import CitationGraphBuilder
from scholar_graph.visualizer import GraphVisualizer

# Bib Imports
from scholar_bib.cli import lint as bib_clean

# Recon (M0.5) imports -- adapter seam -- do not move above the seam.
# ---------------------------------------------------------------------------- #
# Import strategy (Option B, chosen after verifying mcp_config.json): the
# server is launched as ``uv run --directory tools/scholar-agent-kit
# scholar-agent``; that runs the kit-LOCAL venv (tools/scholar-agent-kit/.venv)
# with CWD tools/scholar-agent-kit, and ``scholar_harness`` is NOT installed
# there (empirically verified: ModuleNotFoundError under that venv).  Rather
# than changing the launch config or copying the recon package into this kit,
# we resolve the harness ``src/`` directory from this file's location and
# inject it onto ``sys.path`` as a thin, documented adapter seam.  An
# optional ``NEXUS_HARNESS_SRC`` env var overrides discovery for odd layouts.
def _harness_src() -> str:
    env_override = os.environ.get("NEXUS_HARNESS_SRC")
    if env_override:
        return env_override
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "src" / "scholar_harness" / "recon" / "__init__.py"
        if candidate.is_file():
            return str(parent / "src")
    raise ImportError(
        "scholar_harness.recon not found under any ancestor of "
        + str(here)
        + "; set NEXUS_HARNESS_SRC to the harness src/ directory"
    )


_HARNESS_SRC = _harness_src()
if _HARNESS_SRC not in sys.path:
    sys.path.insert(0, _HARNESS_SRC)

# Recon cache root: CWD-relative, same sandbox convention as nexus_discover's
# ``.cache/mcp``; ``.cache/`` is gitignored in every checkout, so no repo
# pollution regardless of which venv/CWD the server runs from.
RECON_CACHE_ROOT = Path(".cache/inception_recon")
# Test/injection seam: when set, recon tools probe through this callable
# instead of the kit SearchEngine (mirrors ReconEngine(search_fn=...)).
RECON_SEARCH_FN = None

from scholar_harness.recon import (
    DEFAULT_LEXICON,
    DomainLexicon,
    ReconEngine,
    distill_pool,
    execute_followups,
)

mcp = MCPServer("ScholarAgentKit")


# ==============================================================================
# Phase 0: Socratic Protocol & Compiler Tools
# ==============================================================================

@mcp.tool()
def nexus_protocol_compile(intent_json: str) -> str:
    """
    Compile a JSON string or path representing an IntentPacket into a canonical ResearchProtocol.
    Returns the canonical protocol JSON string.
    """
    try:
        if Path(intent_json).exists() and Path(intent_json).is_file():
            intent_data = json.loads(Path(intent_json).read_text(encoding="utf-8"))
        else:
            intent_data = json.loads(intent_json)
        
        intent = IntentPacket.model_validate(intent_data)
        protocol = compile_protocol(intent)
        canon_bytes = canonical_json(protocol)
        fingerprint = canonical_fingerprint(protocol)
        return json.dumps({
            "status": "SUCCESS",
            "protocol_id": protocol.protocol_id,
            "fingerprint": fingerprint,
            "protocol": json.loads(canon_bytes.decode("utf-8"))
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


@mcp.tool()
def nexus_protocol_validate(protocol_json: str) -> str:
    """
    Validate a protocol JSON string or path against the ResearchProtocol specification.
    """
    try:
        p = Path(protocol_json)
        if p.exists() and p.is_file():
            report = validate_protocol(p)
            if report.is_valid:
                proto = ResearchProtocol.model_validate(json.loads(p.read_text(encoding="utf-8")))
                title = proto.metadata.get("title", "") if isinstance(proto.metadata, dict) else getattr(proto.metadata, "title", "")
                return json.dumps({
                    "status": "VALID",
                    "protocol_id": proto.protocol_id,
                    "title": title,
                    "fingerprint": canonical_fingerprint(proto)
                }, indent=2)
            else:
                return json.dumps({
                    "status": "INVALID",
                    "errors": [f.message for f in report.errors],
                    "warnings": [f.message for f in report.warnings]
                }, indent=2)
        else:
            raw_data = json.loads(protocol_json)
            proto = ResearchProtocol.model_validate(raw_data)
            title = proto.metadata.get("title", "") if isinstance(proto.metadata, dict) else getattr(proto.metadata, "title", "")
            return json.dumps({
                "status": "VALID",
                "protocol_id": proto.protocol_id,
                "title": title,
                "fingerprint": canonical_fingerprint(proto)
            }, indent=2)
    except Exception as e:
        return json.dumps({"status": "INVALID", "error": str(e)})


@mcp.tool()
def nexus_protocol_render_criteria(protocol_path: str) -> str:
    """
    Render human-readable SCREENING_CRITERIA.md from a protocol.json file.
    """
    p = Path(protocol_path)
    if not p.exists():
        return f"Error: Protocol file not found at {protocol_path}"
    try:
        protocol = ResearchProtocol.model_validate(json.loads(p.read_text(encoding="utf-8")))
        return render_screening_criteria(protocol)
    except Exception as e:
        return f"Error rendering criteria: {e}"


# ==============================================================================
# Phase 1: Federated Discovery, Deduplication & Screening Tools
# ==============================================================================

@mcp.tool()
async def nexus_discover(query: str, limit: int = 10, start_year: int = 2020) -> str:
    """
    Query academic literature repositories (OpenAlex, Semantic Scholar, Crossref, arXiv).
    Returns the path to the resulting JSON file with real deduplicated results.
    """
    providers = [
        OpenAlexProvider(),
        SemanticScholarProvider(),
        CrossrefProvider(),
        ArxivProvider(),
    ]
    engine = SearchEngine(providers=providers)
    q = Query(text=query, max_results=limit, year_min=start_year)
    try:
        docs = await engine.search_all(q, dedup=True)
    finally:
        await engine.close()

    cache_dir = Path(".cache/mcp")
    cache_dir.mkdir(parents=True, exist_ok=True)
    safe_slug = "".join(c for c in query if c.isalnum() or c in (" ", "_", "-"))[:20].replace(" ", "_")
    output_path = cache_dir / f"discover_{safe_slug or 'query'}_{int(time.time())}.json"
    Exporter().json(docs, output_path)
    preview = "\n".join(
        f"  - ({d.year or 'N/A'}) {d.title[:90]} | {d.provider} | {d.external_ids.doi or d.provider_id}"
        for d in docs[:limit]
    )
    return f"Search completed: {len(docs)} unique papers (deduped). Saved to {output_path}.\n{preview}"


@mcp.tool()
def nexus_dedup(input_path: str, output_path: str = "./deduped.json") -> str:
    """
    Deduplicate a collection of raw search papers by PID clustering and title similarity.
    """
    inp = Path(input_path)
    if not inp.exists():
        return f"Error: Input file {input_path} not found."
    try:
        importer = JSONImporter()
        raw_docs = list(importer.parse(inp))
        deduplicator = Deduplicator()
        clusters = deduplicator.deduplicate(raw_docs)
        unique_docs = [c.representative for c in clusters]
        
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        Exporter().json(unique_docs, out)
        return f"Successfully deduplicated {len(raw_docs)} papers into {len(unique_docs)} unique records saved to {output_path}."
    except Exception as e:
        return f"Error during deduplication: {e}"


@mcp.tool()
def nexus_screen(input_path: str, protocol_path: str, output_dir: str = "./literature") -> str:
    """
    Screen candidate literature against protocol inclusion/exclusion criteria.
    Outputs included.json, excluded.json, and prisma_screening_report.md.
    """
    inp = Path(input_path)
    proto = Path(protocol_path)
    if not inp.exists() or not proto.exists():
        return f"Error: Input or protocol file not found."
    try:
        importer = JSONImporter()
        raw_docs = list(importer.parse(inp))
        protocol_data = json.loads(proto.read_text(encoding="utf-8"))
        
        decisions = [evaluate_heuristic_screening(d, protocol_data) for d in raw_docs]
        included, excluded, conflicts, report = partition_screening_results(raw_docs, decisions)
        
        out_d = Path(output_dir)
        out_d.mkdir(parents=True, exist_ok=True)
        (out_d / "included.json").write_text(json.dumps(included, indent=2, default=str), encoding="utf-8")
        (out_d / "excluded.json").write_text(json.dumps(excluded, indent=2, default=str), encoding="utf-8")
        (out_d / "prisma_screening_report.md").write_text(report.to_markdown() if hasattr(report, "to_markdown") else str(report), encoding="utf-8")
        
        return f"Screening complete: {len(included)} included, {len(excluded)} excluded. Report saved to {out_d / 'prisma_screening_report.md'}."
    except Exception as e:
        return f"Error during screening: {e}"


@mcp.tool()
def nexus_extract_pdf(pdf_path: str, output_dir: str = "./extracted", engine: str = "pymupdf") -> str:
    """
    Extract a PDF into Markdown with YAML frontmatter using PyMuPDF.
    """
    pdf = Path(pdf_path)
    out_dir = Path(output_dir)
    if not pdf.exists():
        return f"Error: PDF {pdf_path} not found."
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        res_file = PyMuPDFEngine.extract_markdown(pdf, out_dir)
        return f"Extracted {pdf.name} to {res_file}"
    except Exception as e:
        return f"Error during PDF extraction: {e}"


# ==============================================================================
# Phase 2: RAG, Matrix Extraction & Knowledge Graph Tools
# ==============================================================================

@mcp.tool()
def nexus_rag_index(docs_dir: str, db_path: str = "./chroma_db", bib_file: str = None, workspace_id: str = None) -> str:
    """
    Index a directory of Markdown files into the Chroma Vector DB using Structural AST Chunking,
    enriching with companion BibTeX metadata if available.
    """
    d_dir = Path(docs_dir)
    if not d_dir.exists():
        return f"Error: Directory {docs_dir} not found."
    try:
        indexer = ScholarIndexer(db_path=db_path)
        b_file = Path(bib_file) if bib_file else None
        result = indexer.index_directory(docs_dir=d_dir, bib_file=b_file, workspace_id=workspace_id)
        return f"Successfully indexed {result['indexed_files']} files ({result['total_chunks']} structural chunks) into {db_path}."
    except Exception as e:
        return f"Error during indexing: {e}"


@mcp.tool()
def nexus_rag_query(
    query: str,
    db_path: str = "./chroma_db",
    section: str = None,
    section_category: str = None,
    paradigm: str = None,
    boost_doi: str = None,
    n_results: int = 5
) -> str:
    """
    Search indexed academic literature with sectional slicing and graph PageRank boosting.
    Categories: 'abstract_intro', 'methodology', 'results_empirical', 'discussion_limitations'.
    """
    try:
        retriever = ScholarRetriever(db_path=db_path)
        boost_list = [boost_doi] if boost_doi else None
        results = retriever.query(
            query_text=query,
            n_results=n_results,
            section=section,
            section_category=section_category,
            paradigm=paradigm,
            boost_dois=boost_list
        )
        
        if not results:
            return "No results found."
        
        output = []
        for i, res in enumerate(results, 1):
            meta = res.metadata
            section_name = meta.get('section', 'Unknown')
            sec_cat = meta.get('section_category', 'general')
            token = res.citation_token
            snippet = res.text[:300].replace('\n', ' ') + "..."
            output.append(
                f"Result {i} (Hybrid Score: {res.hybrid_score:.4f}, CosSim: {res.cosine_sim:.4f})\n"
                f"Token: {token} | Section: {section_name} [{sec_cat}]\n"
                f"{snippet}\n"
            )
        return "\n".join(output)
    except Exception as e:
        return f"Error during RAG query: {e}"


@mcp.tool()
def nexus_rag_synthesize(
    query: str,
    rq_id: str = "RQ1",
    db_path: str = "./chroma_db",
    section_category: str = None,
    paradigm: str = None,
    n_chunks: int = 5
) -> str:
    """
    Generate grounded synthesis with atomic citation tokens and automated claim entailment verification.
    """
    try:
        retriever = ScholarRetriever(db_path=db_path)
        engine = GroundedSynthesisEngine(retriever=retriever)
        result = engine.synthesize(
            query=query,
            rq_id=rq_id,
            n_chunks=n_chunks,
            section_category=section_category,
            paradigm=paradigm
        )
        return (
            f"Grounded Synthesis for '{query}' ({result.verified_claims_count}/{len(result.claims)} verified claims, {result.entailment_rate * 100:.1f}% entailment):\n\n"
            f"{result.synthesis_markdown}"
        )
    except Exception as e:
        return f"Error during synthesis: {e}"


@mcp.tool()
def nexus_matrix_extract(workspace_dir: str = ".", protocol_path: str = None, output_dir: str = "./literature") -> str:
    """
    Extract dynamic Protocol Matrix Dimensions across all indexed studies in the workspace.
    """
    w_dir = Path(workspace_dir).resolve()
    p_path = Path(protocol_path or (w_dir / "protocol.json"))
    out_dir = Path(output_dir)
    if not p_path.exists():
        return f"Error: Protocol not found at {p_path}"
    try:
        protocol = ResearchProtocol.model_validate(json.loads(p_path.read_text(encoding="utf-8")))
        retriever = ScholarRetriever(db_path=str(w_dir / "chroma_db"))
        extractor = MatrixExtractor(protocol=protocol, retriever=retriever)
        rows, csv_path, json_path = extractor.extract_all(output_dir=out_dir)
        return f"Successfully extracted dynamic matrix ({len(rows)} studies) to {csv_path} and {json_path}."
    except Exception as e:
        return f"Error extracting matrix: {e}"


@mcp.tool()
def nexus_graph_build(input_path: str, output_html: str = "./graph.html", json_output: str = "./graph.json") -> str:
    """
    Build a citation graph network from screening included.json and compute PageRank centrality.
    """
    inp = Path(input_path)
    if not inp.exists():
        return f"Error: File {input_path} not found."
    try:
        import asyncio
        builder = CitationGraphBuilder(http_client=None)
        
        dois = []
        if inp.suffix == ".json":
            data = json.loads(inp.read_text(encoding="utf-8"))
            if isinstance(data, list):
                dois = []
                for d in data:
                    doi = d.get("doi") or (d.get("external_ids") or {}).get("doi")
                    if doi:
                        dois.append(doi)
        
        G = asyncio.run(builder.build_graph(dois))
        CitationGraphBuilder.compute_pagerank(G)
        builder.export_json(G, Path(json_output))
        
        vis = GraphVisualizer(Path(output_html))
        vis.generate_html(G)
        return f"Citation graph built ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges). Exported to {output_html} and {json_output}."
    except Exception as e:
        return f"Error building graph: {e}"


@mcp.tool()
def nexus_bib_clean(input_bib_path: str, output_bib_path: str = None) -> str:
    """
    Clean, standardize keys, and deduplicate a BibTeX file.
    """
    input_path = Path(input_bib_path)
    if not input_path.exists():
        return f"Error: {input_bib_path} not found."
    try:
        output_path = Path(output_bib_path or input_bib_path)
        bib_clean(input_path, output_path, generate_keys=False)
        return f"Cleaned BibTeX saved to {output_path}"
    except Exception as e:
        return f"Error cleaning BibTeX: {e}"


# ==============================================================================
# Phase 4 / Rigor Enhancement: Multi-Screener Reconciliation & Verbatim Attributions
# ==============================================================================

@mcp.tool()
def nexus_screen_reconcile(screeners_json: str, adjudication_json: str = None) -> str:
    """
    Reconcile multi-screener screening decisions using strict majority voting and compute Fleiss' Kappa.
    
    Args:
        screeners_json: Path to JSON mapping screener_id -> {workspace_id: 'INCLUDE'|'EXCLUDE'} or path to a directory containing batch_*_decisions*.json.
        adjudication_json: Optional path to JSON file with adjudicated tie-breaking decisions.
    """
    try:
        p = Path(screeners_json)
        screeners_map: dict[str, dict[str, str]] = {}
        if p.is_dir():
            for f in p.glob("batch_*_decisions*.json"):
                # derive screener key
                parts = f.stem.split("_decisions")
                screener_key = parts[1].strip("_") if len(parts) > 1 and parts[1] else "screener1"
                if screener_key not in screeners_map:
                    screeners_map[screener_key] = {}
                data = json.loads(f.read_text(encoding="utf-8"))
                records = data if isinstance(data, list) else data.get("decisions", [])
                for r in records:
                    wid = r.get("workspace_id") or r.get("study_id")
                    dec = r.get("decision")
                    if wid and dec:
                        screeners_map[screener_key][wid] = dec.upper()
        elif p.is_file():
            screeners_map = json.loads(p.read_text(encoding="utf-8"))
        else:
            screeners_map = json.loads(screeners_json)

        adj_map = {}
        if adjudication_json:
            ap = Path(adjudication_json)
            if ap.is_file():
                raw_adj = json.loads(ap.read_text(encoding="utf-8"))
                if isinstance(raw_adj, list):
                    for item in raw_adj:
                        if item.get("workspace_id") and item.get("decision"):
                            adj_map[item["workspace_id"]] = item["decision"]
                elif isinstance(raw_adj, dict):
                    adj_map = raw_adj

        res = reconcile_multi_screener_decisions(screeners_map, adj_map)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


@mcp.tool()
def nexus_verify_claims(claims_json_path: str, extracted_dir_path: str, threshold: float = 0.90) -> str:
    """
    Verify claim quotes against extracted Markdown files using token n-gram and char-window matching.
    
    Args:
        claims_json_path: Path to synthesis claims JSON (e.g. synthesis/claims.json).
        extracted_dir_path: Directory containing extracted source markdown documents.
        threshold: Coverage threshold (default 0.90).
    """
    try:
        cp = Path(claims_json_path)
        ed = Path(extracted_dir_path)
        if not cp.is_file():
            return json.dumps({"status": "ERROR", "error": f"Claims file not found: {claims_json_path}"})
        if not ed.is_dir():
            return json.dumps({"status": "ERROR", "error": f"Extracted directory not found: {extracted_dir_path}"})

        claims = json.loads(cp.read_text(encoding="utf-8"))
        source_texts = {}
        for f in ed.glob("*.md"):
            content = f.read_text(encoding="utf-8", errors="replace")
            source_texts[f.stem] = content
            # Try to index by SCI-xxxx if found
            import re
            m = re.search(r"workspace_id:\s*['\"]?(SCI-\d+)['\"]?", content)
            if m:
                source_texts[m.group(1)] = content
            m2 = re.search(r"(SCI-\d+)", f.name)
            if m2:
                source_texts[m2.group(1)] = content

        verifier = VerbatimClaimVerifier(threshold=threshold)
        results, metrics = verifier.verify_claims_ledger(claims, source_texts)
        return json.dumps({"status": "SUCCESS", "metrics": metrics}, indent=2)
    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})



# ==============================================================================
# Phase 0.5: Recon MCP surface -- FAIR Memory + Agent Interop (M0.5)
#
# T5.1-T5.3 expose recon_probe / recon_distill / recon_delta.  Session state
# persists across copilot turns under
# ``.cache/inception_recon/sessions/<session_id>/session.json`` (T5.4), with
# content-addressed ``pool_<sha>.json`` / ``distilled_<sha>.json`` artifacts
# beside it.  Every result carries its lineage cache_key (T5.5).  All outputs
# are machine-readable JSON (paths/keys, never prose).
# ==============================================================================

LEXICON_FIELDS: dict[str, DomainLexicon] = {
    "default": DEFAULT_LEXICON,
}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _new_session_id() -> str:
    return "rec_" + uuid.uuid4().hex


_SESSION_ID_RE = re.compile(r"^rec_[0-9a-f]{6,64}$")


def _validate_session_id(session_id: str) -> None:
    if not isinstance(session_id, str) or _SESSION_ID_RE.fullmatch(session_id) is None:
        raise ValueError(
            "malformed session_id (expected 'rec_' followed by hex digits)"
        )


def _assert_safe_session_root(root: Path) -> None:
    """Refuse session roots under any path segment named ``workspaces``.

    Same guard semantics as ``ReconEngine._assert_safe_output`` (case-
    insensitive part match, which on Windows also covers ``Workspaces``).
    """
    resolved = Path(root).resolve()
    if any(part.lower() == "workspaces" for part in resolved.parts):
        raise RuntimeError(f"refusing to write under workspaces/: {resolved}")


def _session_root(session_id: str) -> Path:
    _validate_session_id(session_id)
    root = RECON_CACHE_ROOT / "sessions" / session_id
    _assert_safe_session_root(root)
    return root


def _blank_session(session_id: str, topic: str) -> dict:
    stamp = _now_iso()
    return {
        "session_id": session_id,
        "topic": topic,
        "cache_keys": [],
        "pools": [],
        "created_at": stamp,
        "updated_at": stamp,
    }


def load_session(session_id: str) -> dict:
    """Read a session's on-disk state (T5.4: survives across copilot turns)."""
    path = _session_root(session_id) / "session.json"
    if not path.is_file():
        raise RuntimeError(f"session not found: {session_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def save_session(session: dict) -> Path:
    session["updated_at"] = _now_iso()
    root = _session_root(str(session["session_id"]))
    root.mkdir(parents=True, exist_ok=True)
    path = root / "session.json"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(session, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    os.replace(tmp, path)
    return path


def _append_unique(entries: list, value: Any) -> None:
    if value and value not in entries:
        entries.append(value)


def _content_sha(payload: dict) -> str:
    return hashlib.sha1(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _atomic_write_json(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    os.replace(tmp, path)


def _persist_artifact(root: Path, prefix: str, payload: dict) -> Path:
    """Content-addressed artifact write: same payload -> same file, no rewrite."""
    _assert_safe_session_root(root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{prefix}_{_content_sha(payload)}.json"
    if not path.is_file():
        _atomic_write_json(path, payload)
    return path


@mcp.tool()
def recon_probe(
    topic: str,
    session_id: str | None = None,
    start_year: int = 2020,
    limit: int = 10,
) -> str:
    """Probe the literature surface for a topic and record a FAIR recon session.

    Runs the harness ``ReconEngine.probe`` (multi-provider dedup, pool capped
    at 25) and persists the pool content-addressed under
    ``.cache/inception_recon/sessions/<session_id>/pool_<sha>.json``.  The
    session is upserted: an existing ``session_id`` (``rec_<hex>``) is loaded
    from disk and extended, otherwise a new one is created.  Returns
    machine-readable JSON only -- ``cache_key`` (T5.5 lineage), ``pool_path``,
    ``n_docs`` -- never prose.
    """
    try:
        sid = session_id if session_id is not None else _new_session_id()
        root = _session_root(sid)
        engine = ReconEngine(cache_root=RECON_CACHE_ROOT, search_fn=RECON_SEARCH_FN)
        pool_file, n_docs = asyncio.run(
            engine.probe(
                query=topic,
                year_min=start_year,
                year_max=None,
                max_results=limit,
            )
        )
        pool = json.loads(pool_file.read_text(encoding="utf-8"))
        cache_key = str(pool.get("cache_key") or "")
        artifact = _persist_artifact(root, "pool", pool).resolve()
        session = (
            load_session(sid)
            if (root / "session.json").is_file()
            else _blank_session(sid, topic)
        )
        session["topic"] = topic
        _append_unique(session["cache_keys"], cache_key)
        _append_unique(session["pools"], str(artifact))
        save_session(session)
        return json.dumps(
            {
                "session_id": sid,
                "cache_key": cache_key,
                "status": "probe_ok",
                "n_docs": n_docs,
                "pool_path": str(artifact),
            },
            indent=2,
        )
    except (RuntimeError, ValueError, OSError) as exc:
        return json.dumps(
            {"status": "error", "message": str(exc), "cache_key": None}
        )


@mcp.tool()
def recon_distill(session_id: str, lexicon_field: str | None = "default") -> str:
    """Distill the latest session pool into an anchored micro-taxonomy.

    Loads the session's most recent pool from the persisted ``session.json``
    and runs the harness ``distill_pool`` with the selected ``lexicon_field``.
    Only ``"default"`` is shipped (no named-field registry is bundled); the
    pool's upstream ``cache_key`` is returned for lineage (T5.5).  Terms are
    persisted content-addressed at ``distilled_<sha>.json`` under the session
    dir and returned as ``terms_path`` plus structured summaries.
    """
    try:
        field = lexicon_field or "default"
        if field not in LEXICON_FIELDS:
            raise ValueError(
                "unknown lexicon_field "
                + repr(field)
                + "; supported: "
                + ", ".join(sorted(LEXICON_FIELDS))
            )
        session = load_session(str(session_id))
        if not session["pools"]:
            raise RuntimeError(
                f"session {session_id} has no pool; run recon_probe first"
            )
        pool = json.loads(Path(session["pools"][-1]).read_text(encoding="utf-8"))
        distilled = distill_pool(pool, lexicon=LEXICON_FIELDS[field])
        root = _session_root(str(session_id))
        terms_file = _persist_artifact(root, "distilled", distilled).resolve()
        save_session(session)
        return json.dumps(
            {
                "session_id": str(session_id),
                "cache_key": str(pool.get("cache_key") or ""),
                "terms_path": str(terms_file),
                "metrics": [
                    {"label": label, "count": count}
                    for label, count in sorted((distilled.get("metrics") or {}).items())
                ],
                "datasets": [
                    {"label": label, "count": count}
                    for label, count in sorted((distilled.get("datasets") or {}).items())
                ],
                "schools": distilled.get("schools") or [],
                "micro_taxonomy_top": (distilled.get("micro_taxonomy") or [])[:5],
            },
            indent=2,
        )
    except (RuntimeError, ValueError, OSError) as exc:
        return json.dumps(
            {"status": "error", "message": str(exc), "cache_key": None}
        )


@mcp.tool()
def recon_delta(session_id: str, followups: int = 3) -> str:
    """Run the bounded adaptive probe horizon for a session (gap follow-ups).

    Loads the latest pool from ``session.json``, re-distills it
    (deterministic), plans follow-up probes for thin sub-schools (``n <= 2``),
    and executes at most ``followups`` cache-reusing probes (hard cap 3,
    per M0.4).  The merged pool and re-distilled terms persist content-
    addressed under the session dir; ``dropped_n`` counts new docs discarded
    by the 25-doc cap.

    Confidence mapping (documented contract): each item in ``followups``
    carries the M0.4 gap-confidence reason VERBATIM under ``reason`` (e.g.
    ``"2 direct hits, 1 adjacent"``) and the SAME text under
    ``confidence.detail`` with ``confidence.label`` = ``"gap"``, so consumers
    may use either convention.
    """
    try:
        session = load_session(str(session_id))
        if not session["pools"]:
            raise RuntimeError(
                f"session {session_id} has no pool; run recon_probe first"
            )
        pool = json.loads(Path(session["pools"][-1]).read_text(encoding="utf-8"))
        distilled = distill_pool(pool)
        budget = max(0, min(int(followups), 3))
        engine = ReconEngine(cache_root=RECON_CACHE_ROOT, search_fn=RECON_SEARCH_FN)
        result = asyncio.run(
            execute_followups(pool, distilled, engine, max_followups=budget)
        )
        root = _session_root(str(session_id))
        merged_pool = result["pool"]
        merged_terms = result["distilled"]
        pool_file = _persist_artifact(root, "pool", merged_pool).resolve()
        terms_file = _persist_artifact(root, "distilled", merged_terms).resolve()
        merged_keys: list[str] = []
        _append_unique(merged_keys, str(pool.get("cache_key") or ""))
        for key in result.get("cache_keys_merged") or []:
            _append_unique(merged_keys, str(key))
        for key in merged_keys:
            _append_unique(session["cache_keys"], key)
        _append_unique(session["pools"], str(pool_file))
        save_session(session)
        return json.dumps(
            {
                "session_id": str(session_id),
                "merged_cache_keys": merged_keys,
                "followups": [
                    {
                        "term": str(item.get("term") or ""),
                        "reason": str(item.get("reason") or ""),
                        "confidence": {
                            "label": "gap",
                            "detail": str(item.get("reason") or ""),
                        },
                        "school_n": int(item.get("school_n") or 0),
                    }
                    for item in result.get("followups") or []
                ],
                "pool_path": str(pool_file),
                "terms_path": str(terms_file),
                "dropped_n": int(result.get("dropped_n") or 0),
                "pool_size_before": len(pool.get("docs") or []),
                "pool_size_after": len(merged_pool.get("docs") or []),
            },
            indent=2,
        )
    except (RuntimeError, ValueError, OSError) as exc:
        return json.dumps(
            {"status": "error", "message": str(exc), "cache_key": None}
        )


# ==============================================================================
# CLI Entrypoint
# ==============================================================================

def main():
    """Start the FastMCP server or display help."""
    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h"):
        print("Usage: scholar-agent [OPTIONS]")
        print("\nScholar Agent Kit: FastMCP Server exposing Nexus Scholar tools to AI Agents.")
        print("\nExposed MCP Tools:")
        print("  - nexus_protocol_compile: Compile intent.json into canonical protocol.json")
        print("  - nexus_protocol_validate: Validate protocol schema and checksum")
        print("  - nexus_protocol_render_criteria: Render human-readable screening criteria markdown")
        print("  - nexus_discover: Search OpenAlex for scholarly papers")
        print("  - nexus_dedup: Deduplicate candidate documents by PID clustering")
        print("  - nexus_screen: Systematic PRISMA screening against protocol criteria")
        print("  - nexus_extract_pdf: Extract structured Markdown from PDFs")
        print("  - nexus_rag_index: Index Markdown into ChromaDB with structural AST chunking")
        print("  - nexus_rag_query: Hybrid search with sectional slicing and graph PageRank boosting")
        print("  - nexus_rag_synthesize: Grounded synthesis with claim entailment verification")
        print("  - nexus_matrix_extract: Extract dynamic protocol matrix dimensions across studies")
        print("  - nexus_graph_build: Build citation graph from included studies or DOIs")
        print("  - nexus_bib_clean: Clean and deduplicate BibTeX databases")
        print("  - recon_probe: Probe a topic into a FAIR recon session (cross-turn state)")
        print("  - recon_distill: Distill the latest session pool into anchored terms")
        print("  - recon_delta: Bounded adaptive gap follow-up probes with cache reuse")
        return
    mcp.run()


if __name__ == "__main__":
    main()
