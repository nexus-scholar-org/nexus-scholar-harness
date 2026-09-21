from __future__ import annotations

import json
import logging
import shutil
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from scholar_harness.contracts.acceptance import AcceptanceContext, accept_artifact
from scholar_harness.contracts.canonical import deterministic_id
from scholar_harness.contracts.identifiers import IdentifierKind
from scholar_harness.contracts.models import (
    ScreeningDecisionsData,
    ScreeningDecision as ContractDecision,
    MethodProvenance,
    ScreeningDecisionValue,
)

from scholar_search.models import Document
from scholar_search.screening import (
    ScreeningDecision,
    evaluate_heuristic_screening,
    partition_screening_results,
)

from .batcher import (
    _harness_commit,
    _load_decision_payload,
    _load_decisions,
    _rebuild_doc,
    _screening_dir,
)

try:
    from scholar_agent.calibration import build_checklist_schema, checklist_to_decision

    _HAS_CALIBRATION = True
except ImportError:
    _HAS_CALIBRATION = False

logger = logging.getLogger("agent_screen")

def cmd_status(workspace_dir: Path) -> None:
    """Show which batches are pending and which have decisions."""
    screening_dir = _screening_dir(workspace_dir)
    manifest_path = screening_dir / "MANIFEST.json"
    if not manifest_path.exists():
        logger.error("No manifest found. Run 'prepare' first.")
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    total = manifest["total_batches"]
    done = 0
    pending = []

    print(f"\nScreening status for: {workspace_dir.name}")
    print(f"{'Batch':<8} {'Papers':<8} {'Status':<12} {'Decision file'}")
    print("-" * 55)
    for b in manifest["batches"]:
        idx = b["batch_index"]
        decisions_file = screening_dir / f"batch_{idx:03d}_decisions.json"
        if decisions_file.exists():
            try:
                decisions = json.loads(decisions_file.read_text(encoding="utf-8"))
                inc = sum(1 for d in decisions if d.get("decision") == "INCLUDE")
                exc = sum(1 for d in decisions if d.get("decision") == "EXCLUDE")
                status = f"DONE ({inc}I/{exc}E)"
                done += 1
            except Exception:
                status = "DONE (parse error)"
                done += 1
        else:
            status = "PENDING"
            pending.append(idx)
        print(f"  {idx:<6} {b['paper_count']:<8} {status:<12} {decisions_file.name}")

    print()
    print(f"Progress: {done}/{total} batches complete.")
    if pending:
        print(f"Pending batches: {pending}")
        print(f"\nAsk the agent to screen: literature/screening/batch_{pending[0]:03d}.json")
    else:
        print("All batches done! Run: python agent_screen.py collect <workspace>")


# ---------------------------------------------------------------------------
# COLLECT
# ---------------------------------------------------------------------------

def cmd_collect(workspace_dir: Path) -> None:
    """Assemble all decision files into the final screening outputs."""
    screening_dir = _screening_dir(workspace_dir)
    lit_dir = workspace_dir / "literature"
    manifest_path = screening_dir / "MANIFEST.json"
    verified_path = lit_dir / "verified.json"

    if not manifest_path.exists():
        logger.error("No manifest found. Run 'prepare' first.")
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw_verified: list[dict] = json.loads(verified_path.read_text(encoding="utf-8"))

    registry_path = workspace_dir / "audit" / "artifact_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8")) if registry_path.exists() else {"artifacts": {}}

    # Rebuild Document objects
    docs: list[Document] = []
    for i, raw in enumerate(raw_verified):
        docs.append(_rebuild_doc(raw, fallback_id=raw.get("workspace_id") or f"SCI-{i+1:06d}"))

    # Collect all decisions
    all_decisions: list[ScreeningDecision] = []
    missing_batches: list[int] = []
    fallback_count = 0

    protocol_path = workspace_dir / "protocol.json"
    protocol_data = json.loads(protocol_path.read_text(encoding="utf-8"))

    # Build doc lookup by workspace_id
    doc_by_wsid: dict[str, Document] = {d.workspace_id: d for d in docs if d.workspace_id}

    # Check if dual-screening and adjudication files are present
    screener2_files = sorted(screening_dir.glob("batch_*_decisions_screener2.json"))
    adj_files = sorted(screening_dir.glob("_adjudication_resolved_group_*.json"))

    if screener2_files and adj_files:
        logger.info(
            "Detected dual-screening mode: %d screener2 batch files and %d adjudication group files found.",
            len(screener2_files), len(adj_files)
        )
        # Load Screener 1 decisions
        s1_map: dict[str, dict] = {}
        for b in manifest["batches"]:
            idx = b["batch_index"]
            decisions_file = screening_dir / f"batch_{idx:03d}_decisions.json"
            if decisions_file.exists():
                try:
                    for r in _load_decisions(decisions_file):
                        s1_map[r.get("workspace_id") or r.get("study_id", "")] = r
                except Exception:
                    pass

        # Load Screener 2 decisions
        s2_map: dict[str, dict] = {}
        for sf in screener2_files:
            try:
                for r in json.loads(sf.read_text(encoding="utf-8")):
                    s2_map[r["workspace_id"]] = r
            except Exception:
                pass

        # Load Adjudication decisions
        adj_map: dict[str, dict] = {}
        for af in adj_files:
            try:
                for r in json.loads(af.read_text(encoding="utf-8")):
                    adj_map[r["workspace_id"]] = r
            except Exception:
                pass

        # Load confirmed include IDs if available
        reconciled_include_file = screening_dir / "_final_reconciled_include.txt"
        confirmed_inc_ids: set[str] = set()
        if reconciled_include_file.exists():
            try:
                confirmed_inc_ids = set(json.loads(reconciled_include_file.read_text(encoding="utf-8")))
            except Exception:
                pass

        # Load provisional caveat IDs if available (Option B)
        caveats_file = screening_dir / "adjudicated_caveats.json"
        caveat_ids: set[str] = set()
        if caveats_file.exists():
            try:
                cav_list = json.loads(caveats_file.read_text(encoding="utf-8"))
                caveat_ids = {c["workspace_id"] for c in cav_list}
            except Exception:
                pass

        # Build reconciled decisions across all verified documents
        for doc in docs:
            wid = doc.workspace_id
            s1_entry = s1_map.get(wid, {})
            s2_entry = s2_map.get(wid, {})
            a_entry = adj_map.get(wid, {})

            is_disputed = (s1_entry.get("decision") != s2_entry.get("decision"))

            if wid in confirmed_inc_ids or (not confirmed_inc_ids and not is_disputed and s1_entry.get("decision") == "INCLUDE") or (not confirmed_inc_ids and is_disputed and a_entry.get("decision") == "INCLUDE"):
                decision = "INCLUDE"
                conf = float(a_entry.get("confidence", 0.90)) if is_disputed else max(float(s1_entry.get("confidence", 0.8)), float(s2_entry.get("confidence", 0.8)))
                matched = a_entry.get("final_codes", ["INC-01", "INC-02"]) if is_disputed else list(set(s1_entry.get("matched_inclusion_criteria", []) + s2_entry.get("matched_inclusion_criteria", [])))
                violated = []
                rqs = list(set(s2_entry.get("relevant_rqs", []) + s1_entry.get("relevant_rqs", []))) or ["RQ1"]
                reason = a_entry.get("adjudication_reasoning") if is_disputed else (s2_entry.get("screening_reasoning") or s1_entry.get("screening_reasoning"))
            elif wid in caveat_ids:
                decision = "INCLUDE"
                conf = float(a_entry.get("confidence", 0.60))
                matched = ["INC-01", "INC-02"]
                violated = a_entry.get("final_codes", ["EXC-06"])
                rqs = ["RQ1"]
                reason = f"PROVISIONAL INCLUSION (Stage 3 Full-Text Verification Required): {a_entry.get('adjudication_reasoning', '')}"
            else:
                decision = "EXCLUDE"
                conf = float(a_entry.get("confidence", 0.80)) if is_disputed else float(s2_entry.get("confidence", 0.8))
                matched = []
                violated = a_entry.get("final_codes", ["EXC-03"]) if is_disputed else (s2_entry.get("violated_exclusion_criteria") or s1_entry.get("violated_exclusion_criteria") or ["EXC-03"])
                rqs = []
                reason = a_entry.get("adjudication_reasoning") if is_disputed else (s2_entry.get("screening_reasoning") or s1_entry.get("screening_reasoning"))

            all_decisions.append(
                ScreeningDecision(
                    workspace_id=wid,
                    decision=decision,
                    confidence=conf,
                    matched_inclusion_criteria=matched,
                    violated_exclusion_criteria=violated,
                    relevant_rqs=rqs,
                    screening_reasoning=str(reason or "Screened in dual consensus."),
                    document_title=doc.title,
                    doi=doc.external_ids.doi if doc.external_ids else None,
                )
            )

        logger.info(
            "Dual-screening reconciliation generated %d decisions (%d INCLUDE, %d EXCLUDE).",
            len(all_decisions),
            sum(1 for d in all_decisions if d.decision == "INCLUDE"),
            sum(1 for d in all_decisions if d.decision == "EXCLUDE"),
        )

        # F-001: Publish and accept a Contract screening_decisions artifact for dual-screening flow
        # Build a lookup for all reconciled decisions
        recon_map = {d.workspace_id: d for d in all_decisions}

        for b in manifest["batches"]:
            idx = b["batch_index"]
            batch_file = screening_dir / f"batch_{idx:03d}.json"
            if not batch_file.exists():
                continue

            batch_data = json.loads(batch_file.read_text(encoding="utf-8"))
            batch_artifact_id = batch_data.get("artifact_id")
            batch_entry = registry.get("artifacts", {}).get(batch_artifact_id)
            if not batch_entry:
                continue

            batch_env = json.loads((workspace_dir / batch_entry["path"]).read_text(encoding="utf-8"))
            contract_decisions = []
            
            # Find all papers in this batch
            for paper in batch_data.get("papers", []):
                wsid = str(paper.get("workspace_id") or paper.get("study_id") or "")
                if wsid in recon_map:
                    sd = recon_map[wsid]
                    # We preserve provenance here using a stable fallback
                    decided_at = "1970-01-01T00:00:00+00:00"
                    screener_id = "agent-adjudicator"
                    method = MethodProvenance.LLM
                    dec_val = ScreeningDecisionValue(str(sd.decision).upper())
                    reason = str(sd.screening_reasoning or "Screened in dual consensus.")

                    decision_id = deterministic_id(
                        IdentifierKind.SCREENING_DECISION,
                        batch_env["workspace_id"],
                        {
                            "batch_id": batch_env["data"]["batch_id"],
                            "study_id": wsid,
                            "screener_id": screener_id,
                            "method": method.value,
                            "decision": dec_val.value,
                            "reason": reason,
                            "decided_at": decided_at,
                            "parent_decision_ids": [],
                        },
                    )
                    contract_decisions.append(
                        ContractDecision(
                            decision_id=decision_id,
                            study_id=wsid,
                            screener_id=screener_id,
                            method=method,
                            decision=dec_val,
                            confidence=sd.confidence,
                            matched_inclusion_criteria=sd.matched_inclusion_criteria,
                            violated_exclusion_criteria=sd.violated_exclusion_criteria,
                            relevant_rqs=sd.relevant_rqs,
                            reason=reason,
                            decided_at=decided_at,
                            parent_decision_ids=[]
                        )
                    )

            if contract_decisions:
                # Mint artifact
                run_id = deterministic_id(
                    IdentifierKind.RUN,
                    batch_env["workspace_id"],
                    {"adjudication_run_for": batch_env["data"]["batch_id"]}
                )
                
                dec_data = ScreeningDecisionsData(
                    binding=batch_env["data"]["binding"],
                    batch_id=batch_env["data"]["batch_id"],
                    decisions=contract_decisions
                )
                
                art_id = deterministic_id(
                    IdentifierKind.ARTIFACT,
                    batch_env["workspace_id"],
                    {"kind": "screening-decisions-artifact", "batch_id": batch_env["data"]["batch_id"]}
                )
                
                dec_env = {
                    "schema_version": "1.0.0",
                    "artifact_type": "screening_decisions",
                    "artifact_id": art_id,
                    "created_at": datetime.now(UTC).isoformat(),
                    "producer": {
                        "package": "nexus-scholar-harness",
                        "version": "1.0.0",
                        "commit": _harness_commit()
                    },
                    "workspace_id": batch_env["workspace_id"],
                    "run_id": run_id,
                    "protocol_fingerprint": batch_env["protocol_fingerprint"],
                    "corpus_fingerprint": batch_env["corpus_fingerprint"],
                    "inputs": [
                        {
                            "artifact_id": batch_env["artifact_id"],
                            "sha256": batch_entry["sha256"]
                        }
                    ],
                    "data": dec_data.model_dump(mode="json")
                }
                
                ctx = AcceptanceContext(
                    workspace_id=batch_env["workspace_id"],
                    protocol_fingerprint=batch_env["protocol_fingerprint"],
                    corpus_fingerprint=batch_env["corpus_fingerprint"],
                )
                
                res = accept_artifact(workspace_dir, dec_env, expected=ctx, actor="agent_screen.collect_dual")
                if not res.accepted:
                    logger.error("Failed to accept dual-screening decisions for batch %d: %s", idx, res.issues)

    else:
        for b in manifest["batches"]:
            idx = b["batch_index"]
            decisions_file = screening_dir / f"batch_{idx:03d}_decisions.json"
            batch_file = screening_dir / f"batch_{idx:03d}.json"

            if not decisions_file.exists():
                missing_batches.append(idx)
                logger.warning("Batch %d: decision file missing — using heuristic fallback.", idx)
                if batch_file.exists():
                    batch_data = json.loads(batch_file.read_text(encoding="utf-8"))
                    for p in batch_data.get("papers", []):
                        wsid = p.get("workspace_id", "")
                        doc = doc_by_wsid.get(wsid)
                        if doc:
                            all_decisions.append(evaluate_heuristic_screening(doc, protocol_data))
                            fallback_count += 1
                continue

            try:
                raw_decisions, decision_metadata = _load_decision_payload(decisions_file)
            except Exception as exc:
                logger.error("Batch %d: failed to parse decisions file (%s).", idx, exc)
                missing_batches.append(idx)
                continue

            # Load the parent batch artifact to mint the screening decisions
            batch_data = json.loads(batch_file.read_text(encoding="utf-8"))
            batch_artifact_id = batch_data.get("artifact_id")
            batch_entry = registry.get("artifacts", {}).get(batch_artifact_id)
            if not batch_entry:
                logger.error("Batch %d: parent artifact %s not in registry.", idx, batch_artifact_id)
                missing_batches.append(idx)
                continue

            batch_env = json.loads((workspace_dir / batch_entry["path"]).read_text(encoding="utf-8"))
            contract_decisions = []
            legacy_appends = []

            for entry in raw_decisions:
                wsid = str(entry.get("workspace_id") or entry.get("study_id") or "")
                doc = doc_by_wsid.get(wsid)

                # Support new checklist format (inc_XX/exc_XX booleans)
                # and legacy format (decision + confidence + criteria lists)
                has_checklist = any(k.startswith(("inc_", "exc_")) for k in entry)
                if has_checklist and _HAS_CALIBRATION:
                    # Deterministic derivation from boolean checklist
                    schema = build_checklist_schema(protocol_data)
                    sd = checklist_to_decision(
                        workspace_id=wsid,
                        checklist=entry,
                        schema=schema,
                        document_title=doc.title if doc else entry.get("title", ""),
                        doi=(doc.external_ids.doi if doc else None) or entry.get("doi"),
                    )
                else:
                    raw_dec = str(entry.get("decision", "INCLUDE")).upper()
                    if raw_dec not in {item.value for item in ScreeningDecisionValue}:
                        raise ValueError(
                            f"{decisions_file.name}: invalid decision {raw_dec!r}"
                        )
                    decision = "INCLUDE" if raw_dec == "INCLUDE" else "EXCLUDE"
                    try:
                        confidence = float(entry.get("confidence", 0.80))
                    except (TypeError, ValueError):
                        confidence = 0.80
                        
                    sd = ScreeningDecision(
                            workspace_id=wsid,
                            decision=decision,
                            confidence=confidence,
                            matched_inclusion_criteria=list(entry.get("matched_inclusion_criteria") or []),
                            violated_exclusion_criteria=list(entry.get("violated_exclusion_criteria") or []),
                            relevant_rqs=list(entry.get("relevant_rqs") or []),
                            screening_reasoning=str(entry.get("screening_reasoning", "Agent screened.")),
                            document_title=doc.title if doc else entry.get("title", ""),
                            doi=doc.external_ids.doi if doc else None,
                        )

                decided_at = str(
                    entry.get("decided_at")
                    or entry.get("timestamp")
                    or decision_metadata["timestamp"]
                )
                if not decided_at:
                    # F-002: Stable fallback for legacy payloads missing timestamps
                    decided_at = "1970-01-01T00:00:00+00:00" 
                screener_id = str(
                    entry.get("screener_id") or decision_metadata["reviewed_by"]
                )
                method = MethodProvenance(str(entry.get("method") or "LLM").upper())
                dec_val = ScreeningDecisionValue(str(sd.decision).upper())
                parent_ids = list(entry.get("parent_decision_ids") or [])
                reason = str(sd.screening_reasoning or "Agent screened.")
                decision_id = deterministic_id(
                    IdentifierKind.SCREENING_DECISION,
                    batch_env["workspace_id"],
                    {
                        "batch_id": batch_env["data"]["batch_id"],
                        "study_id": wsid,
                        "screener_id": screener_id,
                        "method": method.value,
                        "decision": dec_val.value,
                        "reason": reason,
                        "decided_at": decided_at,
                        "parent_decision_ids": parent_ids,
                    },
                )
                contract_decisions.append(
                    ContractDecision(
                        decision_id=decision_id,
                        study_id=wsid,
                        screener_id=screener_id,
                        method=method,
                        decision=dec_val,
                        reason=reason,
                        decided_at=decided_at,
                        model_id=entry.get("model_id"),
                        prompt_version=entry.get("prompt_version"),
                        parent_decision_ids=parent_ids,
                    )
                )
                legacy_appends.append(sd)

            if contract_decisions:
                run_id = manifest.get("screening_run_id") or batch_env["run_id"]
                dec_data = ScreeningDecisionsData(
                    binding=batch_env["data"]["binding"],
                    batch_id=batch_env["data"]["batch_id"],
                    decisions=contract_decisions
                )
                
                artifact_id = deterministic_id(
                    IdentifierKind.ARTIFACT,
                    batch_env["workspace_id"],
                    {
                        "kind": "screening-decisions",
                        "batch_id": batch_env["data"]["batch_id"],
                        "decision_ids": [item.decision_id for item in contract_decisions],
                    },
                )
                dec_env = {
                    "schema_version": "1.0.0",
                    "artifact_type": "screening_decisions",
                    "artifact_id": artifact_id,
                    "created_at": max(item.decided_at for item in contract_decisions).isoformat(),
                    "producer": {
                        "package": "scholar-harness",
                        "version": "1.0.0",
                        "commit": _harness_commit()
                    },
                    "workspace_id": batch_env["workspace_id"],
                    "run_id": run_id,
                    "protocol_fingerprint": batch_env["protocol_fingerprint"],
                    "corpus_fingerprint": batch_env["corpus_fingerprint"],
                    "inputs": [
                        {
                            "artifact_id": batch_env["artifact_id"],
                            "sha256": batch_entry["sha256"]
                        }
                    ],
                    "data": dec_data.model_dump(mode="json")
                }
                
                ctx = AcceptanceContext(
                    workspace_id=batch_env["workspace_id"],
                    protocol_fingerprint=batch_env["protocol_fingerprint"],
                    corpus_fingerprint=batch_env["corpus_fingerprint"],
                )
                
                res = accept_artifact(workspace_dir, dec_env, expected=ctx, actor="agent_screen.collect")
                if not res.accepted:
                    logger.error("Failed to accept decisions for batch %d: %s", idx, res.issues)
                    # Archive legacy mismatching decisions
                    decisions_file.rename(decisions_file.with_name(f"{decisions_file.name}.rejected"))
                    missing_batches.append(idx)
                    continue
                else:
                    all_decisions.extend(legacy_appends)
                    archive_dir = screening_dir / "legacy"
                    archive_dir.mkdir(exist_ok=True)
                    shutil.copy2(decisions_file, archive_dir / decisions_file.name)

        if missing_batches:
            logger.warning("%d batch(es) had missing/broken decision files: %s", len(missing_batches), missing_batches)
        if fallback_count:
            logger.warning("%d papers fell back to heuristic screening.", fallback_count)

    # Look for raw provenance manifest to get exact total_identified and duplicates_removed
    manifest_raw = lit_dir / "raw" / "provenance_manifest.json"
    total_identified = len(docs)
    duplicates_removed = 0
    if manifest_raw.exists():
        try:
            m = json.loads(manifest_raw.read_text(encoding="utf-8"))
            total_identified = m.get("total_raw_harvested", len(docs))
            duplicates_removed = max(0, total_identified - len(docs))
        except Exception:
            pass

    # Partition
    inc_docs, exc_docs, conflicts, report = partition_screening_results(
        docs, all_decisions,
        total_identified=total_identified,
        duplicates_removed=duplicates_removed,
    )

    # Write outputs
    (lit_dir / "included.json").write_text(
        json.dumps(inc_docs, indent=2, default=str, ensure_ascii=False), encoding="utf-8"
    )
    (lit_dir / "excluded.json").write_text(
        json.dumps(exc_docs, indent=2, default=str, ensure_ascii=False), encoding="utf-8"
    )
    (lit_dir / "conflicts.json").write_text(
        json.dumps(conflicts, indent=2, default=str, ensure_ascii=False), encoding="utf-8"
    )
    (lit_dir / "prisma_screening_report.md").write_text(
        report.to_markdown(), encoding="utf-8"
    )
    (lit_dir / "prisma_report.json").write_text(
        json.dumps(asdict(report), indent=2), encoding="utf-8"
    )

    # Update manifest statuses
    for b in manifest["batches"]:
        idx = b["batch_index"]
        decisions_file = screening_dir / f"batch_{idx:03d}_decisions.json"
        b["status"] = "DONE" if decisions_file.exists() else "MISSING"
    (screening_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    inc_with_abs = sum(1 for d in inc_docs if d.get("abstract") and len(d.get("abstract", "")) > 30)
    logger.info("=" * 60)
    logger.info("COLLECTION COMPLETE")
    logger.info("  Included:               %d", len(inc_docs))
    logger.info("  Excluded:               %d", len(exc_docs))
    logger.info("  Conflicts (audit):      %d", len(conflicts))
    logger.info("  Included with abstract: %d/%d", inc_with_abs, len(inc_docs))
    logger.info("  Missing decision files: %d", len(missing_batches))
    logger.info("=" * 60)
    print()
    print(report.to_markdown())


# ---------------------------------------------------------------------------
# CALIBRATION
# ---------------------------------------------------------------------------

