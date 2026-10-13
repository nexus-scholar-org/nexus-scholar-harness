from __future__ import annotations

import json
import logging
import shutil
import sys
from dataclasses import asdict
from pathlib import Path

from scholar_harness.contracts.acceptance import AcceptanceContext, accept_artifact
from scholar_harness.contracts.canonical import deterministic_id
from scholar_harness.contracts.identifiers import IdentifierKind
from scholar_harness.contracts.models import (
    MethodProvenance,
    ScreeningDecisionsData,
    ScreeningDecisionValue,
)
from scholar_harness.contracts.models import ScreeningDecision as ContractDecision
from scholar_harness.verification_identity import (
    VERIFICATION_IDENTITY_BRIDGE_MISS,
    VERIFICATION_IDENTITY_MISSING_DOI,
    VerificationIdentityRefused,
)
from scholar_harness.workspace.audit import log_event

from scholar_search.models import Document
from scholar_search.screening import (
    ScreeningDecision,
    partition_screening_results,
)

from .batcher import (
    _harness_commit,
    _load_decision_payload,
    _load_decisions,
    _rebuild_doc,
    _screening_dir,
)
from .integrity import (
    CONTENT_CHANGED,
    STALE_BINDING,
    ScreeningIntegrityRefused,
    bind_batch,
    check_exact_coverage,
    check_no_unresolved_for_finalize,
    decision_file_sha256,
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
        print(
            f"\nAsk the agent to screen: literature/screening/batch_{pending[0]:03d}.json"
        )
    else:
        print("All batches done! Run: python agent_screen.py collect <workspace>")


# ---------------------------------------------------------------------------
# COLLECT
# ---------------------------------------------------------------------------


def _head_batch_artifact(
    workspace_dir: Path, registry: dict, batch_index: int
) -> tuple[str, str] | None:
    """Registry head batch artifact ``(artifact_id, sha256)`` for an index.

    The newest accepted ``screening_batch`` envelope whose data carries this
    ``batch_index`` (newest by registry ``accepted_at``). Unreadable payloads
    are skipped. ``None`` when no head can be resolved.
    """
    head: tuple[str, str] | None = None
    head_ts = ""
    for artifact_id, entry in registry.get("artifacts", {}).items():
        if entry.get("artifact_type") != "screening_batch":
            continue
        try:
            batch_env = json.loads(
                (workspace_dir / entry["path"]).read_text(encoding="utf-8")
            )
        except (OSError, ValueError, KeyError):
            continue
        if batch_env.get("data", {}).get("batch_index") != batch_index:
            continue
        accepted_at = str(entry.get("accepted_at", ""))
        if head is None or accepted_at >= head_ts:
            head = (str(artifact_id), str(entry.get("sha256", "")))
            head_ts = accepted_at
    return head


def _prior_decision_acceptance(
    workspace_dir: Path, registry: dict, batch_index: int
) -> tuple[str, str, str | None, str] | None:
    """Newest accepted ``screening_decisions`` bound to a batch index.

    Returns ``(parent_batch_artifact_id, parent_sha256,
    recorded_decision_file_sha256_or_None, decisions_artifact_id)`` or
    ``None`` when no prior acceptance exists. The index is read from the
    accepted parent batch envelope (not the mutable handoff file), so the
    lookup survives a re-prepare that rewrote the handoff files. Entries
    whose payloads are unreadable are skipped.
    """
    best: tuple[str, str, str | None, str] | None = None
    best_ts = ""
    for artifact_id, entry in registry.get("artifacts", {}).items():
        if entry.get("artifact_type") != "screening_decisions":
            continue
        try:
            env = json.loads(
                (workspace_dir / entry["path"]).read_text(encoding="utf-8")
            )
        except (OSError, ValueError, KeyError):
            continue
        inputs = env.get("inputs") or []
        if not inputs:
            continue
        parent_ref = inputs[0]
        parent_entry = registry.get("artifacts", {}).get(parent_ref.get("artifact_id"))
        if (
            parent_entry is None
            or parent_entry.get("artifact_type") != "screening_batch"
        ):
            continue
        try:
            batch_env = json.loads(
                (workspace_dir / parent_entry["path"]).read_text(encoding="utf-8")
            )
        except (OSError, ValueError, KeyError):
            continue
        if batch_env.get("data", {}).get("batch_index") != batch_index:
            continue
        accepted_at = str(entry.get("accepted_at", ""))
        if best is None or accepted_at >= best_ts:
            best = (
                str(parent_ref.get("artifact_id")),
                str(parent_ref.get("sha256")),
                env.get("decision_file_sha256"),
                str(artifact_id),
            )
            best_ts = accepted_at
    return best


def _refuse_single_batch(
    workspace_dir: Path,
    screening_dir: Path,
    batch_index: int,
    decisions_file: Path,
    refusal: ScreeningIntegrityRefused,
    missing_batches: list[int],
) -> None:
    """Fail-closed refusal: journal row, ``.rejected`` rename, MISSING mark.

    Mirrors the existing membership-gate handling (rename + missing list +
    the shared fail-closed tail raises): no partition output is written and
    no ``screening_decisions`` artifact is minted. A journal failure never
    masks the refusal itself.
    """
    try:
        log_event(
            workspace_dir,
            "SCREENING_COLLECT_REFUSED",
            f"Refused screening batch {batch_index} decision file "
            f"{decisions_file.name}: {refusal.code}",
            agent="agent_screen.collect",
            inputs=[decisions_file.name],
            outputs=[f"{decisions_file.name}.rejected"],
            parameters={
                "batch_index": batch_index,
                "code": refusal.code,
                "detail": refusal.message,
                **refusal.details,
            },
            metrics={"batch_index": batch_index},
            status="FAILED",
        )
    except OSError:
        pass
    if decisions_file.exists():
        decisions_file.rename(
            decisions_file.with_name(f"{decisions_file.name}.rejected")
        )
    if batch_index not in missing_batches:
        missing_batches.append(batch_index)


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
    registry = (
        json.loads(registry_path.read_text(encoding="utf-8"))
        if registry_path.exists()
        else {"artifacts": {}}
    )

    alias_to_stu = {}
    corpus_env: dict | None = None
    corpus_items = [
        (aid, entry)
        for aid, entry in registry.get("artifacts", {}).items()
        if entry.get("artifact_type") == "corpus_snapshot"
    ]
    if corpus_items:
        _, corpus_entry = max(
            corpus_items, key=lambda item: item[1].get("accepted_at", "")
        )
        corpus_env = json.loads(
            (workspace_dir / corpus_entry["path"]).read_text(encoding="utf-8")
        )
        for study in corpus_env.get("data", {}).get("studies", []):
            stu_id = study["study_id"]
            alias_to_stu[stu_id] = stu_id
            for alias in study.get("alias_ids", []):
                alias_to_stu[alias] = stu_id

    # Rebuild Document objects (HCM-04e-1 bridge-or-refuse parity: no
    # independent mint). A verified row without a workspace_id is an
    # unresolved identity that Stage 3 must have quarantined, never published.
    # Minting a positional SCI- here would re-fabricate what Stage 3 refused
    # in a second, independent position space sharing only the SCI- shape, so
    # the row is refused fail-closed with a typed reason before any
    # publication. This mirrors the existing missing-batch and dual-screening
    # refusals (RuntimeError, no outputs written): a typed exception fits the
    # CLI-driven shape better than sys.exit(1), which is reserved for usage
    # errors such as a missing manifest, because the refusal must be
    # branchable in tests and must never be confused with a CLI usage mistake.
    docs: list[Document] = []
    for i, raw in enumerate(raw_verified):
        wid = raw.get("workspace_id")
        if not wid:
            _eids = raw.get("external_ids") or {}
            _doi = _eids.get("doi") or raw.get("doi")
            if not _doi:
                _code = VERIFICATION_IDENTITY_MISSING_DOI
                _detail_reason = (
                    "no workspace_id and no DOI to bridge to a recorded dedup parent"
                )
            else:
                _code = VERIFICATION_IDENTITY_BRIDGE_MISS
                _detail_reason = (
                    f"no workspace_id; DOI {_doi!r} has no recorded "
                    "identity in verified.json"
                )
            raise VerificationIdentityRefused(
                _code,
                "screening collection blocked: verified record at position "
                f"{i} has no workspace_id ({_detail_reason}); "
                "refusing positional mint",
                position=i,
                title=raw.get("title"),
                doi=_doi,
                reason=_detail_reason,
            )
        if wid in alias_to_stu:
            wid = alias_to_stu[wid]
            raw["workspace_id"] = wid
        docs.append(_rebuild_doc(raw, fallback_id=wid))

    # Collect all decisions
    all_decisions: list[ScreeningDecision] = []
    missing_batches: list[int] = []
    # AG-02 lineage recorded per batch index on acceptance: decision-file
    # hash plus the parent binding it was collected against. Merged into
    # MANIFEST.json rows after the loop (dual path leaves this empty).
    accepted_lineage: dict[int, dict[str, str]] = {}

    protocol_path = workspace_dir / "protocol.json"
    protocol_data = json.loads(protocol_path.read_text(encoding="utf-8"))

    # Build doc lookup by workspace_id
    doc_by_wsid: dict[str, Document] = {
        d.workspace_id: d for d in docs if d.workspace_id
    }

    # Check if dual-screening and adjudication files are present
    screener2_files = sorted(screening_dir.glob("batch_*_decisions_screener2.json"))
    adj_files = sorted(screening_dir.glob("_adjudication_resolved_group_*.json"))

    if screener2_files and adj_files:
        if corpus_env is None:
            raise RuntimeError(
                "dual screening blocked: no accepted corpus snapshot is available"
            )
        batch_workspace_id = str(corpus_env["workspace_id"])
        logger.info(
            "Detected dual-screening mode: %d screener2 batch files and %d adjudication group files found.",
            len(screener2_files),
            len(adj_files),
        )

        def _canonical_wid(entry: dict) -> str:
            raw = str(entry.get("workspace_id") or entry.get("study_id") or "")
            return alias_to_stu.get(raw, raw)

        def _batch_candidate_ids(batch_idx: int) -> set[str]:
            """Authoritative per-batch membership set.

            Sourced from the *accepted* parent batch artifact registered under
            batch_data["artifact_id"]. The batch handoff file is mutable and
            unaudited, so it is never used as a membership source here.
            """
            batch_file = screening_dir / f"batch_{batch_idx:03d}.json"
            batch_artifact_id = None
            if batch_file.exists():
                try:
                    batch_artifact_id = json.loads(
                        batch_file.read_text(encoding="utf-8")
                    ).get("artifact_id")
                except Exception:
                    batch_artifact_id = None
            batch_entry = (
                registry.get("artifacts", {}).get(batch_artifact_id)
                if batch_artifact_id
                else None
            )
            if batch_entry is None:
                return set()
            batch_env = json.loads(
                (workspace_dir / batch_entry["path"]).read_text(encoding="utf-8")
            )
            return {
                str(candidate.get("study_id"))
                for candidate in batch_env.get("data", {}).get("candidates", [])
            }

        def _check_batch_membership(
            batch_idx: int, entries: list[dict], *, label: str
        ) -> None:
            """Fail closed when a decision references a study that was not a
            candidate in the accepted parent batch artifact (no silent drop)."""
            candidate_ids = _batch_candidate_ids(batch_idx)
            offenders = sorted(
                {_canonical_wid(entry) for entry in entries} - candidate_ids
            )
            if not offenders and candidate_ids:
                return
            snippet = (
                ", ".join(offenders)
                if offenders
                else "batch has no accepted parent batch artifact to validate against"
            )
            logger.error(
                "Dual screening blocked: batch %d %s decisions failed parent-batch "
                "membership validation (%s).",
                batch_idx,
                label,
                snippet,
            )
            for name in (
                f"batch_{batch_idx:03d}_decisions.json",
                f"batch_{batch_idx:03d}_decisions_screener2.json",
            ):
                path = screening_dir / name
                if path.exists():
                    path.rename(path.with_name(f"{path.name}.rejected"))
            missing_batches.append(batch_idx)
            raise RuntimeError(
                f"dual screening blocked: batch {batch_idx} {label} decisions are "
                "not verifiable against the accepted parent batch candidate set; "
                "refusing collection"
            )

        # Load Screener 1 decisions
        s1_map: dict[str, dict] = {}
        for b in manifest["batches"]:
            idx = b["batch_index"]
            decisions_file = screening_dir / f"batch_{idx:03d}_decisions.json"
            if decisions_file.exists():
                try:
                    s1_entries = _load_decisions(decisions_file)
                except Exception:
                    continue
                _check_batch_membership(idx, s1_entries, label="screener 1")
                for r in s1_entries:
                    s1_map[_canonical_wid(r)] = r

        # Load Screener 2 decisions
        s2_map: dict[str, dict] = {}
        for b in manifest["batches"]:
            idx = b["batch_index"]
            sf = screening_dir / f"batch_{idx:03d}_decisions_screener2.json"
            if not sf.exists():
                continue
            try:
                s2_entries = _load_decisions(sf)
            except Exception:
                continue
            _check_batch_membership(idx, s2_entries, label="screener 2")
            for r in s2_entries:
                s2_map[_canonical_wid(r)] = r

        # Load Adjudication decisions
        adj_map: dict[str, dict] = {}
        for af in adj_files:
            try:
                for r in json.loads(af.read_text(encoding="utf-8")):
                    wid = r.get("workspace_id") or r.get("study_id", "")
                    adj_map[alias_to_stu.get(wid, wid)] = r
            except Exception:
                pass

        def _source_decision(
            entry: dict, *, label: str, study_id: str
        ) -> ContractDecision:
            required = {
                "decision_id": entry.get("decision_id"),
                "screener_id": entry.get("screener_id"),
                "method": entry.get("method"),
                "decided_at": entry.get("decided_at") or entry.get("timestamp"),
            }
            missing = sorted(key for key, value in required.items() if not value)
            if missing:
                raise RuntimeError(
                    f"dual screening blocked for {study_id}: {label} decision "
                    f"is missing contract provenance fields {missing}"
                )
            reason = str(
                entry.get("reason")
                or entry.get("screening_reasoning")
                or entry.get("adjudication_reasoning")
                or ""
            ).strip()
            if not reason:
                raise RuntimeError(
                    f"dual screening blocked for {study_id}: {label} decision has no reason"
                )
            return ContractDecision(
                decision_id=str(required["decision_id"]),
                study_id=study_id,
                screener_id=str(required["screener_id"]),
                method=MethodProvenance(str(required["method"]).upper()),
                decision=ScreeningDecisionValue(str(entry.get("decision", "")).upper()),
                reason=reason,
                decided_at=str(required["decided_at"]),
                model_id=entry.get("model_id"),
                prompt_version=entry.get("prompt_version"),
                parent_decision_ids=list(entry.get("parent_decision_ids") or []),
            )

        # Build reconciled decisions across all verified documents.  Dual mode
        # is fail-closed: every paper needs two provenance-complete source
        # decisions, and every disagreement needs a lineage-bound adjudication.
        dual_contract_by_study: dict[str, list[ContractDecision]] = {}
        for doc in docs:
            wid = doc.workspace_id
            s1_entry = s1_map.get(wid, {})
            s2_entry = s2_map.get(wid, {})
            a_entry = adj_map.get(wid, {})

            if not s1_entry or not s2_entry:
                raise RuntimeError(
                    f"dual screening blocked for {wid}: both screener decisions are required"
                )

            s1_contract = _source_decision(s1_entry, label="screener 1", study_id=wid)
            s2_contract = _source_decision(s2_entry, label="screener 2", study_id=wid)

            is_disputed = s1_contract.decision != s2_contract.decision

            if is_disputed:
                if not a_entry:
                    raise RuntimeError(
                        f"dual screening blocked for {wid}: disagreement requires adjudication"
                    )
                final_contract = _source_decision(
                    a_entry, label="adjudication", study_id=wid
                )
                expected_parents = {
                    s1_contract.decision_id,
                    s2_contract.decision_id,
                }
                if set(final_contract.parent_decision_ids) != expected_parents:
                    raise RuntimeError(
                        f"dual screening blocked for {wid}: adjudication parent_decision_ids "
                        "must reference both screener decisions"
                    )
            else:
                parent_ids = sorted([s1_contract.decision_id, s2_contract.decision_id])
                decided_at = max(s1_contract.decided_at, s2_contract.decided_at)
                reason = "Consensus of two independently provenance-bound decisions."
                final_id = deterministic_id(
                    IdentifierKind.SCREENING_DECISION,
                    batch_workspace_id,
                    {
                        "study_id": wid,
                        "decision": s1_contract.decision.value,
                        "method": MethodProvenance.COMPOSED.value,
                        "parent_decision_ids": parent_ids,
                    },
                )
                final_contract = ContractDecision(
                    decision_id=final_id,
                    study_id=wid,
                    screener_id="dual-consensus",
                    method=MethodProvenance.COMPOSED,
                    decision=s1_contract.decision,
                    reason=reason,
                    decided_at=decided_at,
                    parent_decision_ids=parent_ids,
                )

            dual_contract_by_study[wid] = [
                s1_contract,
                s2_contract,
                final_contract,
            ]
            decision = final_contract.decision.value
            final_source = a_entry if is_disputed else s2_entry
            conf = float(final_source.get("confidence", 0.8))
            matched = list(final_source.get("matched_inclusion_criteria") or [])
            violated = list(final_source.get("violated_exclusion_criteria") or [])
            rqs = list(final_source.get("relevant_rqs") or [])

            all_decisions.append(
                ScreeningDecision(
                    workspace_id=wid,
                    decision=decision,
                    confidence=conf,
                    matched_inclusion_criteria=matched,
                    violated_exclusion_criteria=violated,
                    relevant_rqs=rqs,
                    screening_reasoning=final_contract.reason,
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

        # Publish and accept a Contract screening_decisions artifact for dual screening.
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

            batch_env = json.loads(
                (workspace_dir / batch_entry["path"]).read_text(encoding="utf-8")
            )
            contract_decisions: list[ContractDecision] = []

            # Find all papers in this batch
            for paper in batch_data.get("papers", []):
                wsid = str(paper.get("workspace_id") or paper.get("study_id") or "")
                contract_decisions.extend(dual_contract_by_study.get(wsid, []))

            if contract_decisions:
                # Decision artifacts remain bound to the screening run carried
                # by their parent batch.
                run_id = batch_env["run_id"]

                dec_data = ScreeningDecisionsData(
                    binding=batch_env["data"]["binding"],
                    batch_id=batch_env["data"]["batch_id"],
                    decisions=contract_decisions,
                )

                art_id = deterministic_id(
                    IdentifierKind.ARTIFACT,
                    batch_env["workspace_id"],
                    {
                        "kind": "screening-decisions-artifact",
                        "batch_id": batch_env["data"]["batch_id"],
                    },
                )

                dec_env = {
                    "schema_version": "1.0.0",
                    "artifact_type": "screening_decisions",
                    "artifact_id": art_id,
                    "created_at": max(
                        item.decided_at for item in contract_decisions
                    ).isoformat(),
                    "producer": {
                        "package": "nexus-scholar-harness",
                        "version": "1.0.0",
                        "commit": _harness_commit(),
                    },
                    "workspace_id": batch_env["workspace_id"],
                    "run_id": run_id,
                    "protocol_fingerprint": batch_env["protocol_fingerprint"],
                    "corpus_fingerprint": batch_env["corpus_fingerprint"],
                    "inputs": [
                        {
                            "artifact_id": batch_env["artifact_id"],
                            "sha256": batch_entry["sha256"],
                        }
                    ],
                    "data": dec_data.model_dump(mode="json"),
                }

                ctx = AcceptanceContext(
                    workspace_id=batch_env["workspace_id"],
                    protocol_fingerprint=batch_env["protocol_fingerprint"],
                    corpus_fingerprint=batch_env["corpus_fingerprint"],
                )

                res = accept_artifact(
                    workspace_dir,
                    dec_env,
                    expected=ctx,
                    actor="agent_screen.collect_dual",
                )
                if not res.accepted:
                    raise RuntimeError(
                        f"dual screening collection blocked for batch {idx}: {res.issues}"
                    )

    else:
        for b in manifest["batches"]:
            idx = b["batch_index"]
            decisions_file = screening_dir / f"batch_{idx:03d}_decisions.json"
            batch_file = screening_dir / f"batch_{idx:03d}.json"

            if not decisions_file.exists():
                missing_batches.append(idx)
                logger.error(
                    "Batch %d: decision file missing; refusing unbound heuristic fallback.",
                    idx,
                )
                continue

            try:
                raw_decisions, decision_metadata = _load_decision_payload(
                    decisions_file
                )
            except Exception as exc:
                logger.error("Batch %d: failed to parse decisions file (%s).", idx, exc)
                missing_batches.append(idx)
                continue

            # Load the parent batch artifact to mint the screening decisions
            batch_data = json.loads(batch_file.read_text(encoding="utf-8"))
            batch_artifact_id = batch_data.get("artifact_id")
            batch_entry = registry.get("artifacts", {}).get(batch_artifact_id)
            if not batch_entry:
                logger.error(
                    "Batch %d: parent artifact %s not in registry.",
                    idx,
                    batch_artifact_id,
                )
                missing_batches.append(idx)
                continue

            batch_env = json.loads(
                (workspace_dir / batch_entry["path"]).read_text(encoding="utf-8")
            )

            # AG-02 integrity gates (workflow-integrity only): replay/stale
            # binding, exact coverage, duplicate rejection, unresolved
            # refusal. Every gate runs before any ContractDecision is minted
            # or any state is touched. A refusal renames the file to
            # .rejected, marks the batch MISSING, and leaves the existing
            # fail-closed tail to raise: no new publication path.
            # The gates intentionally ignore method labels, reviewer-name
            # strings, and confidence scores: identical bytes collect (or
            # refuse) identically whatever those fields claim.
            try:
                file_hash = decision_file_sha256(decisions_file.read_bytes())
                current_binding = bind_batch(
                    idx,
                    {
                        "artifact_id": batch_artifact_id,
                        "sha256": batch_entry["sha256"],
                    },
                )
                head = _head_batch_artifact(workspace_dir, registry, idx)
                if head is not None and tuple(head) != current_binding:
                    raise ScreeningIntegrityRefused(
                        STALE_BINDING,
                        f"batch {idx} decision file is bound to superseded "
                        f"parent {current_binding[0]}; registry head is "
                        f"{head[0]}",
                        batch_index=idx,
                        bound_parent_artifact_id=current_binding[0],
                        head_parent_artifact_id=head[0],
                        decision_file_sha256=file_hash,
                    )
                prior = _prior_decision_acceptance(workspace_dir, registry, idx)
                if prior is not None:
                    prior_artifact_id, prior_sha, recorded_hash, _ = prior
                    if (
                        (prior_artifact_id, prior_sha) != current_binding
                        and recorded_hash is not None
                        and recorded_hash == file_hash
                    ):
                        raise ScreeningIntegrityRefused(
                            STALE_BINDING,
                            f"batch {idx} decision file replays bytes accepted "
                            f"under superseded parent {prior_artifact_id}; "
                            f"current parent is {current_binding[0]}",
                            batch_index=idx,
                            recorded_parent_artifact_id=prior_artifact_id,
                            current_parent_artifact_id=current_binding[0],
                            decision_file_sha256=file_hash,
                        )
                    if (
                        (prior_artifact_id, prior_sha) == current_binding
                        and recorded_hash is not None
                        and recorded_hash != file_hash
                    ):
                        raise ScreeningIntegrityRefused(
                            CONTENT_CHANGED,
                            f"batch {idx} decision file changed since "
                            f"acceptance (was {recorded_hash}, now "
                            f"{file_hash})",
                            batch_index=idx,
                            previous_decision_file_sha256=recorded_hash,
                            current_decision_file_sha256=file_hash,
                        )
                batch_candidate_ids = {
                    str(candidate.get("study_id"))
                    for candidate in batch_env.get("data", {}).get("candidates", [])
                }
                check_exact_coverage(batch_candidate_ids, raw_decisions)
                check_no_unresolved_for_finalize(raw_decisions)
            except ScreeningIntegrityRefused as refusal:
                _refuse_single_batch(
                    workspace_dir,
                    screening_dir,
                    idx,
                    decisions_file,
                    refusal,
                    missing_batches,
                )
                continue

            # Packet D deliverable: reject decisions outside the parent batch.
            # Membership is validated against the *accepted* batch artifact's
            # candidate set (the immutable truth); the batch handoff file is
            # mutable and unaudited and therefore never a membership source.
            # This runs before any ContractDecision is minted or any state is
            # touched, so a spoofed decision never reaches the published
            # ScreeningDecisionsArtifact and never contributes to the legacy
            # partition outputs.
            out_of_batch = sorted(
                {
                    str(entry.get("workspace_id") or entry.get("study_id") or "")
                    for entry in raw_decisions
                }
                - batch_candidate_ids
            )
            if out_of_batch:
                logger.error(
                    "Batch %d: decisions reference study id(s) outside the parent "
                    "batch candidate set: %s; rejecting decisions file %s.",
                    idx,
                    ", ".join(out_of_batch),
                    decisions_file.name,
                )
                decisions_file.rename(
                    decisions_file.with_name(f"{decisions_file.name}.rejected")
                )
                missing_batches.append(idx)
                continue

            # Derive legacy screening outcomes first so checklist-derived rows
            # pass through the same unresolved gate as legacy decision
            # strings. No ContractDecision is minted in this phase.
            derived: list[tuple[dict, str, ScreeningDecision]] = []
            try:
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
                            doi=(doc.external_ids.doi if doc else None)
                            or entry.get("doi"),
                        )
                    else:
                        raw_dec = str(entry.get("decision", "INCLUDE")).upper()
                        valid = {item.value for item in ScreeningDecisionValue}
                        if raw_dec not in valid:
                            raise ValueError(
                                f"{decisions_file.name}: invalid decision {raw_dec!r}"
                            )
                        # AG-02: explicit terminal values only. MAYBE/CONFLICT
                        # were refused by the finalize gate above, so the
                        # non-INCLUDE branch below only ever sees EXCLUDE:
                        # unresolved rows are never silently coerced.
                        if raw_dec == "INCLUDE":
                            decision = "INCLUDE"
                        elif raw_dec == "EXCLUDE":
                            decision = "EXCLUDE"
                        else:  # pragma: no cover - refused by the gate above
                            raise ValueError(
                                f"{decisions_file.name}: unresolved decision "
                                f"{raw_dec!r} cannot be finalized"
                            )
                        try:
                            confidence = float(entry.get("confidence", 0.80))
                        except (TypeError, ValueError):
                            confidence = 0.80

                        sd = ScreeningDecision(
                            workspace_id=wsid,
                            decision=decision,
                            confidence=confidence,
                            matched_inclusion_criteria=list(
                                entry.get("matched_inclusion_criteria") or []
                            ),
                            violated_exclusion_criteria=list(
                                entry.get("violated_exclusion_criteria") or []
                            ),
                            relevant_rqs=list(entry.get("relevant_rqs") or []),
                            screening_reasoning=str(
                                entry.get("screening_reasoning", "Agent screened.")
                            ),
                            document_title=doc.title if doc else entry.get("title", ""),
                            doi=doc.external_ids.doi if doc else None,
                        )
                    derived.append((entry, wsid, sd))
                check_no_unresolved_for_finalize(
                    [
                        {"workspace_id": wsid, "decision": str(item.decision)}
                        for _, wsid, item in derived
                    ]
                )
            except ScreeningIntegrityRefused as refusal:
                _refuse_single_batch(
                    workspace_dir,
                    screening_dir,
                    idx,
                    decisions_file,
                    refusal,
                    missing_batches,
                )
                continue

            contract_decisions = []
            legacy_appends = []

            for entry, wsid, sd in derived:
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
                    decisions=contract_decisions,
                )

                artifact_id = deterministic_id(
                    IdentifierKind.ARTIFACT,
                    batch_env["workspace_id"],
                    {
                        "kind": "screening-decisions",
                        "batch_id": batch_env["data"]["batch_id"],
                        "decision_ids": [
                            item.decision_id for item in contract_decisions
                        ],
                    },
                )
                dec_env = {
                    "schema_version": "1.0.0",
                    "artifact_type": "screening_decisions",
                    "artifact_id": artifact_id,
                    "created_at": max(
                        item.decided_at for item in contract_decisions
                    ).isoformat(),
                    "producer": {
                        "package": "scholar-harness",
                        "version": "1.0.0",
                        "commit": _harness_commit(),
                    },
                    "workspace_id": batch_env["workspace_id"],
                    "run_id": run_id,
                    "protocol_fingerprint": batch_env["protocol_fingerprint"],
                    "corpus_fingerprint": batch_env["corpus_fingerprint"],
                    "inputs": [
                        {
                            "artifact_id": batch_env["artifact_id"],
                            "sha256": batch_entry["sha256"],
                        }
                    ],
                    # AG-02 tamper-evidence: the exact decision-file bytes
                    # this acceptance was collected against. Recorded here
                    # (envelope lineage, preserved by the contract's
                    # forward-compatible extra fields -- no contract schema
                    # change), in the MANIFEST row, and in the journal row
                    # below. The inputs list cannot carry a raw file hash:
                    # InputArtifact admits only artifact references whose
                    # sha must equal the registered artifact sha
                    # (PARENT_HASH_MISMATCH otherwise), so a file hash is
                    # recorded alongside -- never as -- an input.
                    "decision_file_sha256": file_hash,
                    "data": dec_data.model_dump(mode="json"),
                }

                ctx = AcceptanceContext(
                    workspace_id=batch_env["workspace_id"],
                    protocol_fingerprint=batch_env["protocol_fingerprint"],
                    corpus_fingerprint=batch_env["corpus_fingerprint"],
                )

                res = accept_artifact(
                    workspace_dir, dec_env, expected=ctx, actor="agent_screen.collect"
                )
                if not res.accepted:
                    logger.error(
                        "Failed to accept decisions for batch %d: %s", idx, res.issues
                    )
                    # Archive legacy mismatching decisions
                    decisions_file.rename(
                        decisions_file.with_name(f"{decisions_file.name}.rejected")
                    )
                    missing_batches.append(idx)
                    continue
                else:
                    all_decisions.extend(legacy_appends)
                    archive_dir = screening_dir / "legacy"
                    archive_dir.mkdir(exist_ok=True)
                    shutil.copy2(decisions_file, archive_dir / decisions_file.name)
                    accepted_lineage[idx] = {
                        "decision_file_sha256": file_hash,
                        "decisions_artifact_id": artifact_id,
                        "batch_artifact_id": current_binding[0],
                        "batch_sha256": current_binding[1],
                    }
                    if not res.idempotent:
                        try:
                            log_event(
                                workspace_dir,
                                "SCREENING_DECISIONS_RECORDED",
                                f"Recorded screening decisions for batch {idx} "
                                f"from {decisions_file.name}",
                                agent="agent_screen.collect",
                                inputs=[current_binding[0]],
                                outputs=[res.published_path]
                                if res.published_path
                                else [],
                                parameters={
                                    "batch_index": idx,
                                    "batch_artifact_id": current_binding[0],
                                    "batch_sha256": current_binding[1],
                                    "decision_file_sha256": file_hash,
                                    "decisions_artifact_id": artifact_id,
                                },
                                metrics={"decision_count": len(contract_decisions)},
                                status="SUCCESS",
                            )
                        except OSError:
                            pass

    # Update manifest statuses before partition: a rejected or missing batch
    # must leave an accurate machine-readable record even when collection stops.
    for b in manifest["batches"]:
        idx = b["batch_index"]
        decisions_file = screening_dir / f"batch_{idx:03d}_decisions.json"
        lineage = accepted_lineage.get(idx)
        if decisions_file.exists():
            b["status"] = "DONE"
            if lineage is not None:
                b.update(lineage)
        else:
            b["status"] = "MISSING"
            for key in (
                "decision_file_sha256",
                "decisions_artifact_id",
                "batch_artifact_id",
                "batch_sha256",
            ):
                b.pop(key, None)
    (screening_dir / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    if missing_batches:
        logger.warning(
            "%d batch(es) had missing/broken decision files: %s",
            len(missing_batches),
            missing_batches,
        )
        raise RuntimeError(
            "screening collection blocked: missing, invalid, or rejected "
            f"decision artifacts for batches {sorted(set(missing_batches))}"
        )

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
        docs,
        all_decisions,
        total_identified=total_identified,
        duplicates_removed=duplicates_removed,
    )

    # AG-03C shared authorization gate (BEGIN)
    # AG-03C shared authorization gate: the five partition outputs below are
    # published ONLY through publish_generation, which verifies the staged
    # approval (literature/screening/publication_approval.json) against the
    # collected snapshot and binding BEFORE any of the final writes and
    # renames generation.json LAST as the commit point. On refusal this gate
    # writes none of the five partition files nor generation.json — not even
    # partial outputs — and the accepted decision files stay in place so an
    # operator can stage an approval and re-collect. (AG-02 integrity refusals
    # already raised above; the per-batch acceptances, MANIFEST status/lineage
    # rows, registry screening_decisions entries, and legacy/ archive copies
    # before the partition are review records, not publication, and are
    # untouched by this gate. No staged approval means APPROVAL_MISSING:
    # nothing is published, whatever the workspace held before.)
    from scholar_harness.authority.generations import load_publication_approval

    _staged_approval = load_publication_approval(screening_dir)
    from datetime import datetime, timezone

    from scholar_harness.authority.generations import (
        SCREENING_PUBLICATION_POLICY_VERSION,
        build_publication_snapshot,
        content_sha256,
        publication_binding,
        publication_file_bytes,
        publish_generation,
        resolve_publication_scope,
    )

    _scope = resolve_publication_scope(workspace_dir)
    # Same serialization as the retired pre-authorization writes (same
    # json.dumps args, same order), staged through the same write_text call
    # inside publish_generation: the authorized path is byte-identical to the
    # legacy path it replaces, including host newline translation.
    _content = {
        "included.json": json.dumps(
            inc_docs, indent=2, default=str, ensure_ascii=False
        ),
        "excluded.json": json.dumps(
            exc_docs, indent=2, default=str, ensure_ascii=False
        ),
        "conflicts.json": json.dumps(
            conflicts, indent=2, default=str, ensure_ascii=False
        ),
        "prisma_screening_report.md": report.to_markdown(),
        "prisma_report.json": json.dumps(asdict(report), indent=2),
    }
    _snapshot = build_publication_snapshot(
        workspace_id=_scope.workspace_id,
        run_id=_scope.run_id,
        batch_bindings=[dict(b) for b in _scope.batch_bindings],
        protocol_fingerprint=_scope.protocol_fingerprint,
        corpus_fingerprint=_scope.corpus_fingerprint,
        output_digests={
            name: content_sha256(publication_file_bytes(text))
            for name, text in _content.items()
        },
    )
    _binding = publication_binding(
        workspace_id=_scope.workspace_id,
        run_id=_scope.run_id,
        batch_bindings=[dict(b) for b in _scope.batch_bindings],
        protocol_fingerprint=_scope.protocol_fingerprint,
        corpus_fingerprint=_scope.corpus_fingerprint,
    )
    _published_at = datetime.now(timezone.utc).isoformat()

    def _audit_publish(event: dict) -> None:
        log_event(
            workspace_dir,
            event["action"],
            event["description"],
            agent="agent_screen.collect",
            inputs=[b["batch_artifact_id"] for b in _scope.batch_bindings],
            outputs=[
                f"literature/{name}"
                for name in (
                    "included.json",
                    "excluded.json",
                    "conflicts.json",
                    "prisma_screening_report.md",
                    "prisma_report.json",
                )
            ]
            + ["literature/screening/generation.json"],
            parameters={
                "generation_id": event["generation_id"],
                "generation_fingerprint": event["generation_fingerprint"],
                "approval_fingerprint": event["approval_fingerprint"],
                "operator_identity": event["operator_identity"],
                "supersedes": event["supersedes"],
            },
            metrics={"output_count": len(event["output_digests"])},
            status="SUCCESS",
        )

    def _audit_refusal(record: dict) -> None:
        log_event(
            workspace_dir,
            "SCREENING_GENERATION_REFUSED",
            f"Refused screening publication: {record['code']}",
            agent="agent_screen.collect",
            inputs=[b["batch_artifact_id"] for b in _scope.batch_bindings],
            outputs=[],
            parameters={
                "code": record["code"],
                "detail": record["message"],
                **record["details"],
            },
            metrics={},
            status="FAILED",
        )

    publish_generation(
        workspace=workspace_dir,
        snapshot_bytes=_snapshot,
        binding=_binding,
        record=_staged_approval,
        content=_content,
        published_at=_published_at,
        policy_version=SCREENING_PUBLICATION_POLICY_VERSION,
        audit_append=_audit_publish,
        refusal_sink=_audit_refusal,
    )
    # AG-03C shared authorization gate (END)

    inc_with_abs = sum(
        1 for d in inc_docs if d.get("abstract") and len(d.get("abstract", "")) > 30
    )
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
