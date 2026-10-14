"""Researcher review and operator approval for one screening worker (AG-04).

Smallest supported interface (CLI only) on the proven AG-03 publisher:

* ``review`` displays the exact immutable snapshot bytes used for parsing,
  hashing and approval (AG-03B single-buffer discipline: parse, hash and
  display all read the identical buffer).
* ``approve`` diffs the researcher-resolved file against the snapshot:
  identical content approves as-is; different content creates a superseding
  revision preserving the original (AG-03B ``supersede``) and requires a
  fresh approval bound to the new revision. Stale approvals never authorize
  changed revisions. The staged publication approval
  (``literature/screening/publication_approval.json``) is minted over the
  exact partition content the existing ``cmd_collect`` gate will verify, so
  collection reuses the AG-03C gate unchanged.
* ``defer`` records a deferred/cancelled state with reason and publishes
  nothing (any staged approval is voided).

Authority comes ONLY from the publisher-owned operator context
(``literature/screening/operator_context.json``). A typed name, reviewer
string, or editable approval file is never trusted identity, and identity is
never taken from CLI args. On Windows, ``approve`` refuses when its own
process token is Low integrity — the worker cannot invoke the operator
action. MAYBE/CONFLICT (and worker-pending rows) stay unresolved until the
researcher resolves them or defers publication.

Single-screener flow only. Dual-screening and checklist-derived inputs
refuse with typed errors (out of pilot scope). Synthetic ``tmp_path``
batches plus disposable state; no real-workspace audit events are emitted
here (residual: wire the workspace-manager audit logger before any real
workspace use).
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scholar_harness.authority.binding import (
    APPROVAL_MISSING,
    APPROVAL_NOT_OPERATOR,
    ApprovalBinding,
    AuthorityRefused,
    OperatorIdentity,
    content_sha256,
    mint_approval,
)
from scholar_harness.authority.generations import (
    build_publication_snapshot,
    mint_publication_approval,
    publication_binding,
    publication_file_bytes,
    resolve_publication_scope,
    write_publication_approval,
)
from scholar_harness.authority.lifecycle import (
    ReviewSnapshot,
    capture_snapshot,
    supersede,
)
from scholar_harness.screening.batcher import _load_decisions, _rebuild_doc
from scholar_harness.screening.integrity import (
    ScreeningIntegrityRefused,
    UNRESOLVED_FINALIZE_REFUSED,
    check_exact_coverage,
    check_no_unresolved_for_finalize,
)
from scholar_harness.screening.worker import (
    WORKER_BATCH_MISSING,
    WORKER_PARENT_UNRESOLVED,
    WorkerRefused,
    recommendation_path,
)
from scholar_harness.verification_identity import (
    VERIFICATION_IDENTITY_BRIDGE_MISS,
    VERIFICATION_IDENTITY_MISSING_DOI,
    VerificationIdentityRefused,
)

#: Sidecar identity for one researcher review record.
REVIEW_SCHEMA = "harness-screening-review-v1"

#: Sidecar identity for one staged per-batch operator approval.
BATCH_APPROVAL_SCHEMA = "harness-screening-batch-approval-v1"

#: Sidecar identity for one deferral/cancellation record.
DEFERRAL_SCHEMA = "harness-screening-deferral-v1"

#: Policy version per-batch review approvals are minted and verified under.
#: Distinct from the publication policy: batch scope and publication scope
#: never share an approval.
REVIEW_POLICY_VERSION = "screening-review-v1"

#: Deferral reason that marks an explicit cancellation.
CANCELLED_REASON = "CANCELLED"

#: Publisher-owned operator context filename (worker-unwritable in deployment).
OPERATOR_CONTEXT_FILENAME = "operator_context.json"

# --- typed refusal codes (review layer) ------------------------------------ #
OPERATOR_CONTEXT_MISSING = "OPERATOR_CONTEXT_MISSING"
REVIEW_INVALID_DECISIONS = "REVIEW_INVALID_DECISIONS"
REVIEW_CHECKLIST_UNSUPPORTED = "REVIEW_CHECKLIST_UNSUPPORTED"
REVIEW_DUAL_UNSUPPORTED = "REVIEW_DUAL_UNSUPPORTED"
REVIEW_NOT_PREPARED = "REVIEW_NOT_PREPARED"
REVIEW_REASON_MISSING = "REVIEW_REASON_MISSING"
#: --begin takes no staged note: decisions/message would be silently dropped.
REVIEW_BEGIN_ARGS_REFUSED = "REVIEW_BEGIN_ARGS_REFUSED"

#: Decisions that count as final (anything else refuses as unresolved).
TERMINAL_DECISIONS = frozenset({"INCLUDE", "EXCLUDE"})


class ReviewRefused(RuntimeError):
    """Typed recoverable refusal from the review interaction layer.

    Same shape as the authority/integrity/worker errors (stable ``code``,
    human ``message``, machine-readable ``details``). Raised for interaction
    problems owned by this layer (missing context, unreadable decisions,
    out-of-scope inputs); approval, integrity, and worker problems reuse
    their own layer errors.
    """

    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.details: dict[str, Any] = dict(details)

    def as_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "details": self.details}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- operator identity (publisher-owned context only) ----------------------- #


def operator_context_path(workspace_dir: Path) -> Path:
    return (
        Path(workspace_dir).resolve()
        / "literature"
        / "screening"
        / OPERATOR_CONTEXT_FILENAME
    )


def load_operator_context(workspace_dir: Path) -> OperatorIdentity:
    """Load the verified operator identity from the publisher-owned context.

    Identity NEVER comes from CLI args, worker output, or editable approval
    files. A missing/unreadable context refuses with
    ``OPERATOR_CONTEXT_MISSING``; a forged or empty identity refuses with
    ``APPROVAL_NOT_OPERATOR`` via the :class:`OperatorIdentity` constructor.
    """
    path = operator_context_path(workspace_dir)
    if not path.is_file():
        raise ReviewRefused(
            OPERATOR_CONTEXT_MISSING,
            f"publisher operator context {OPERATOR_CONTEXT_FILENAME} is absent; "
            "no verified operator identity exists, so approval is refused",
            context_path=str(path),
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise ReviewRefused(
            OPERATOR_CONTEXT_MISSING,
            f"publisher operator context is unreadable ({exc}); approval is refused",
            context_path=str(path),
        ) from exc
    if not isinstance(payload, dict):
        raise ReviewRefused(
            OPERATOR_CONTEXT_MISSING,
            "publisher operator context is not a JSON object; approval is refused",
            context_path=str(path),
        )
    identity = payload.get("operator_identity")
    if not isinstance(identity, str) or not identity.strip():
        raise ReviewRefused(
            OPERATOR_CONTEXT_MISSING,
            "publisher operator context carries no operator identity; "
            "approval is refused",
            context_path=str(path),
        )
    # The constructor refuses any source but "publisher-operator-context" and
    # any untrusted identity string (APPROVAL_NOT_OPERATOR): a forged
    # actor/method label can never become the approver.
    return OperatorIdentity(
        identity=identity.strip(), source="publisher-operator-context"
    )


def _is_low_integrity_process() -> bool:
    """Whether this process runs at Windows Low integrity (the worker level).

    Non-Windows hosts return False: POSIX has no proven arrangement (packet
    section 1), so no enforcement is claimed there. Any query failure also
    returns False (documented residual: the OS-level MIC boundary in
    ``authority.isolation`` remains the proven mechanism on Windows).
    Monkeypatched in tests to exercise the refusal cross-platform.
    """
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        advapi32 = ctypes.windll.advapi32
        # Exact signatures: without argtypes/restype the pseudo-handle (-1)
        # truncates to 32 bits and the token query fails closed-open.
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        kernel32.GetCurrentProcess.argtypes = []
        advapi32.OpenProcessToken.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.HANDLE),
        ]
        advapi32.OpenProcessToken.restype = wintypes.BOOL
        advapi32.GetTokenInformation.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            wintypes.LPVOID,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
        ]
        advapi32.GetTokenInformation.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        TOKEN_QUERY = 0x0008
        TOKEN_INTEGRITY_LEVEL = 25
        token = wintypes.HANDLE()
        proc = kernel32.GetCurrentProcess()
        if not advapi32.OpenProcessToken(proc, TOKEN_QUERY, ctypes.byref(token)):
            return False
        try:
            size = wintypes.DWORD(0)
            advapi32.GetTokenInformation(
                token, TOKEN_INTEGRITY_LEVEL, None, 0, ctypes.byref(size)
            )
            if not size.value:
                return False
            buf = ctypes.create_string_buffer(size.value)
            if not advapi32.GetTokenInformation(
                token, TOKEN_INTEGRITY_LEVEL, buf, size, ctypes.byref(size)
            ):
                return False
            import struct

            (sid_ptr,) = struct.unpack("P", buf.raw[: struct.calcsize("P")])
            if not sid_ptr:
                return False
            sid = ctypes.cast(sid_ptr, ctypes.POINTER(ctypes.c_ubyte))
            count = int(sid[1])
            raw = bytes(int(sid[i]) for i in range(8 + 4 * count))
            # S-1-16-4096 (Low): revision 1, 1 subauthority, authority 16,
            # subauthority 4096 (0x1000, little-endian).
            return raw == bytes([1, 1, 0, 0, 0, 0, 0, 16, 0x00, 0x10, 0x00, 0x00])
        finally:
            kernel32.CloseHandle(token)
    except Exception:  # noqa: BLE001 - query failure is not enforcement
        return False


# --- review paths ----------------------------------------------------------- #


def _screening_dir(workspace_dir: Path) -> Path:
    return Path(workspace_dir).resolve() / "literature" / "screening"


def _reviews_dir(workspace_dir: Path) -> Path:
    return _screening_dir(workspace_dir) / "reviews"


def _approvals_dir(workspace_dir: Path) -> Path:
    return _screening_dir(workspace_dir) / "approvals"


def _deferrals_dir(workspace_dir: Path) -> Path:
    return _screening_dir(workspace_dir) / "deferrals"


def review_path(workspace_dir: Path, batch_index: int) -> Path:
    return _reviews_dir(workspace_dir) / f"batch_{batch_index:03d}_review.json"


def batch_approval_path(workspace_dir: Path, batch_index: int) -> Path:
    return _approvals_dir(workspace_dir) / f"batch_{batch_index:03d}_approval.json"


def deferral_path(workspace_dir: Path, batch_index: int) -> Path:
    return _deferrals_dir(workspace_dir) / f"batch_{batch_index:03d}_deferral.json"


def default_decisions_path(workspace_dir: Path, batch_index: int) -> Path:
    return _screening_dir(workspace_dir) / f"batch_{batch_index:03d}_decisions.json"


def _resolve_batch_env(workspace_dir: Path, batch_index: int) -> dict[str, Any]:
    """Resolve the accepted parent batch envelope for one batch index."""
    ws = Path(workspace_dir).resolve()
    screening_dir = ws / "literature" / "screening"
    batch_file = screening_dir / f"batch_{batch_index:03d}.json"
    if not batch_file.is_file():
        raise WorkerRefused(
            WORKER_BATCH_MISSING,
            f"assigned batch file {batch_file.name} is absent",
            batch_index=batch_index,
        )
    try:
        batch_data = json.loads(batch_file.read_text(encoding="utf-8"))
        registry = json.loads(
            (ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8")
        )
        entry = registry.get("artifacts", {}).get(batch_data.get("artifact_id"))
        return json.loads((ws / entry["path"]).read_text(encoding="utf-8"))
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise WorkerRefused(
            WORKER_PARENT_UNRESOLVED,
            f"cannot resolve accepted parent batch for index {batch_index} "
            f"({exc}); refusing to invent parents",
            batch_index=batch_index,
        ) from exc


def _review_binding(batch_env: dict[str, Any], revision: int) -> ApprovalBinding:
    data = batch_env.get("data", {})
    return ApprovalBinding(
        workspace_id=str(batch_env.get("workspace_id")),
        run_id=str(batch_env.get("run_id")),
        batch_id=str(data.get("batch_id")),
        protocol_fingerprint=str(batch_env.get("protocol_fingerprint")),
        corpus_fingerprint=str(batch_env.get("corpus_fingerprint")),
        recommendation_revision=revision,
        policy_version=REVIEW_POLICY_VERSION,
    )


def _read_recommendation_bytes(workspace_dir: Path, batch_index: int) -> bytes:
    path = recommendation_path(workspace_dir, batch_index)
    if not path.is_file():
        raise WorkerRefused(
            WORKER_BATCH_MISSING,
            f"no worker recommendation {path.name}; run the recommend step first",
            batch_index=batch_index,
            recommendation_path=str(path),
        )
    return path.read_bytes()


def _parse_decisions(path: Path) -> list[dict[str, Any]]:
    try:
        entries = _load_decisions(path)
    except (OSError, ValueError) as exc:
        raise ReviewRefused(
            REVIEW_INVALID_DECISIONS,
            f"researcher-resolved file {path.name} is unreadable ({exc})",
            decisions_file=str(path),
        ) from exc
    if not isinstance(entries, list) or not all(
        isinstance(entry, dict) for entry in entries
    ):
        raise ReviewRefused(
            REVIEW_INVALID_DECISIONS,
            f"researcher-resolved file {path.name} is not a list of decision objects",
            decisions_file=str(path),
        )
    return entries


def _require_resolved(entries: list[dict[str, Any]]) -> None:
    """Refuse any non-terminal decision presented for approval.

    AG-02 MAYBE/CONFLICT stay unresolved (never coerced); worker-pending
    rows and any other non-terminal value refuse under the same code instead
    of being coerced into terminal exclusions.
    """
    check_no_unresolved_for_finalize(entries)
    pending = sorted(
        {
            str(entry.get("workspace_id") or entry.get("study_id") or "")
            for entry in entries
            if str(entry.get("decision", "")).strip().upper() not in TERMINAL_DECISIONS
        }
    )
    if pending:
        raise ScreeningIntegrityRefused(
            UNRESOLVED_FINALIZE_REFUSED,
            "decision file carries non-terminal row(s) presented for "
            f"approval; resolve them or defer publication (studies={pending})",
            unresolved_rows=pending,
        )


def load_review_snapshot(
    workspace_dir: Path,
    batch_index: int,
    decisions_file: Path | None = None,
) -> tuple[ReviewSnapshot, bytes, bytes | None]:
    """Freeze the worker submission plus current researcher resolutions.

    Returns ``(snapshot, recommendation_bytes, final_bytes_or_None)``. The
    snapshot is the single source for parse/hash/display; the caller must
    use :meth:`ReviewSnapshot.bytes_for` rather than re-reading files. A
    missing decisions file yields ``None`` final bytes (nothing resolved yet:
    displayable, never approvable).
    """
    ws = Path(workspace_dir).resolve()
    recommendation_bytes = _read_recommendation_bytes(ws, batch_index)
    batch_env = _resolve_batch_env(ws, batch_index)
    decisions_path = (
        Path(decisions_file)
        if decisions_file is not None
        else default_decisions_path(ws, batch_index)
    )
    final_bytes = decisions_path.read_bytes() if decisions_path.is_file() else None
    snapshot = capture_snapshot(
        recommendation_bytes,
        final_bytes if final_bytes is not None else b"",
        _review_binding(batch_env, 1),
    )
    return snapshot, recommendation_bytes, final_bytes


# --- researcher display ------------------------------------------------------ #


def _as_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        for key in ("rows", "decisions", "entries"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def show_review(snapshot: ReviewSnapshot) -> str:
    """Render the exact snapshot bytes as researcher-readable text.

    Displays decision, supporting reasons, uncertainty, source/criterion
    references, and parent hashes from the single display buffer
    (``bytes_for("display")``) — the identical bytes the approval hashes.
    Protocol/batch identity is inspectable from the binding. Instructions
    and errors use researcher language.
    """
    try:
        recommended = json.loads(snapshot.bytes_for("display").decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        recommended = None
    try:
        final_raw = snapshot.final_bytes_for("display").decode("utf-8")
        final = json.loads(final_raw) if final_raw.strip() else None
    except (ValueError, UnicodeDecodeError):
        final = None

    binding = snapshot.binding
    lines = [
        "Screening review — please check the worker draft below.",
        "",
        f"Batch: {binding.batch_id}  (recommendation revision "
        f"{binding.recommendation_revision})",
        f"Workspace: {binding.workspace_id}",
        f"Run: {binding.run_id}",
        f"Protocol parents: {binding.protocol_fingerprint}",
        f"Corpus parents: {binding.corpus_fingerprint}",
        f"Recommendation content: {snapshot.recommendation_sha256}",
        f"Resolved content: {snapshot.final_decision_sha256}",
        f"Review snapshot: {snapshot.fingerprint()}",
    ]
    if snapshot.supersedes is not None:
        lines.append(f"Supersedes: {snapshot.supersedes} (original preserved)")
        lines.append(f"Overridden by: {snapshot.superseded_by}")
    else:
        lines.append("Supersedes: nothing (this is the original worker submission)")
    lines.append("")

    rec_rows = _as_rows(recommended)
    if rec_rows:
        lines.append("Worker draft rows (the worker makes no scientific judgments):")
        for row in rec_rows:
            study = row.get("study_id") or row.get("workspace_id") or "?"
            decision = row.get("decision", "?")
            lines.append(f"- [{decision}] {study}")
            refs = row.get("criterion_refs") or {}
            if isinstance(refs, dict):
                inc = refs.get("inclusion", [])
                exc = refs.get("exclusion", [])
                lines.append(f"    Criteria: inclusion={inc} exclusion={exc}")
            loc = row.get("source_locators") or {}
            if isinstance(loc, dict):
                lines.append(
                    "    Sources: "
                    + ", ".join(
                        f"{key}={loc.get(key)}"
                        for key in ("doi", "url", "venue", "year")
                    )
                )
            if row.get("uncertainty"):
                lines.append(f"    Uncertainty: {row['uncertainty']}")
            reasons = row.get("reasons") or []
            lines.append(
                "    Reasons: "
                + (
                    "; ".join(str(reason) for reason in reasons)
                    if reasons
                    else "(none recorded)"
                )
            )
        lines.append("")

    final_rows = _as_rows(final)
    if final_rows:
        lines.append("Researcher-resolved final decisions:")
        for row in final_rows:
            study = row.get("study_id") or row.get("workspace_id") or "?"
            decision = row.get("decision", "?")
            reason = (
                row.get("screening_reasoning")
                or row.get("reason")
                or "(no reason recorded)"
            )
            lines.append(f"- [{decision}] {study}: {reason}")
        lines.append("")
    else:
        lines.append("Researcher-resolved final decisions: none yet.")
        lines.append("")

    lines.append(
        "To finish: resolve every pending row to INCLUDE or EXCLUDE with a "
        "reason (or run defer with a reason to postpone publication). "
        "Approving binds your identity to exactly the content shown above; "
        "any later change needs a fresh review."
    )
    return "\n".join(lines)


def cmd_review(workspace_dir: Path, batch_index: int) -> None:
    """CLI entry: read-only display of the current review snapshot."""
    snapshot, _, _ = load_review_snapshot(Path(workspace_dir), batch_index)
    print(show_review(snapshot))


# --- operator approval -------------------------------------------------------- #


def _compute_single_screener_content(
    workspace_dir: Path,
    *,
    decisions_overrides: dict[int, list[dict[str, Any]]] | None = None,
) -> dict[str, str]:
    """Recompute the exact partition content ``cmd_collect`` would publish.

    Bounded mirror of the single-screener legacy path in
    ``screening.collector.cmd_collect`` (same inputs, same partition call,
    same serialization, including host newline handling via
    ``publication_file_bytes`` at digest time). Dual-screening and
    checklist-derived inputs refuse as out of pilot scope instead of being
    silently mishandled. Any drift between this mirror and the collector is
    pinned by the byte-identity publication test: the staged approval only
    verifies when both compute identical bytes.

    ``decisions_overrides`` carries already-validated in-memory entries per
    batch index (used by ``approve_command`` so the staged approval binds
    exactly the entries the AG-02 gates accepted — including a custom
    ``--decisions-file`` — rather than re-reading the files).
    """
    from scholar_search.screening import ScreeningDecision, partition_screening_results

    ws = Path(workspace_dir).resolve()
    screening_dir = ws / "literature" / "screening"
    manifest_path = screening_dir / "MANIFEST.json"
    verified_path = ws / "literature" / "verified.json"
    if not manifest_path.is_file() or not verified_path.is_file():
        raise ReviewRefused(
            REVIEW_NOT_PREPARED,
            "workspace has no prepared screening batches or verified material; "
            "run prepare before approval",
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw_verified: list[dict] = json.loads(verified_path.read_text(encoding="utf-8"))

    registry_path = ws / "audit" / "artifact_registry.json"
    registry = (
        json.loads(registry_path.read_text(encoding="utf-8"))
        if registry_path.exists()
        else {"artifacts": {}}
    )

    if sorted(screening_dir.glob("batch_*_decisions_screener2.json")) or sorted(
        screening_dir.glob("_adjudication_resolved_group_*.json")
    ):
        raise ReviewRefused(
            REVIEW_DUAL_UNSUPPORTED,
            "dual-screening inputs are present; the AG-04 pilot supports the "
            "single-screener flow only",
        )

    alias_to_stu: dict[str, str] = {}
    corpus_items = [
        (aid, entry)
        for aid, entry in registry.get("artifacts", {}).items()
        if entry.get("artifact_type") == "corpus_snapshot"
    ]
    corpus_env: dict | None = None
    if corpus_items:
        _, corpus_entry = max(
            corpus_items, key=lambda item: item[1].get("accepted_at", "")
        )
        corpus_env = json.loads((ws / corpus_entry["path"]).read_text(encoding="utf-8"))
        for study in corpus_env.get("data", {}).get("studies", []):
            stu_id = study["study_id"]
            alias_to_stu[stu_id] = stu_id
            for alias in study.get("alias_ids", []):
                alias_to_stu[alias] = stu_id

    docs = []
    for i, raw in enumerate(raw_verified):
        wid = raw.get("workspace_id")
        if not wid:
            eids = raw.get("external_ids") or {}
            doi = eids.get("doi") or raw.get("doi")
            if not doi:
                raise VerificationIdentityRefused(
                    VERIFICATION_IDENTITY_MISSING_DOI,
                    "screening review blocked: verified record at position "
                    f"{i} has no workspace_id (no DOI to bridge); "
                    "refusing positional mint",
                    position=i,
                )
            raise VerificationIdentityRefused(
                VERIFICATION_IDENTITY_BRIDGE_MISS,
                "screening review blocked: verified record at position "
                f"{i} has no workspace_id; DOI {doi!r} has no recorded identity",
                position=i,
                doi=doi,
            )
        if wid in alias_to_stu:
            wid = alias_to_stu[wid]
            raw["workspace_id"] = wid
        docs.append(_rebuild_doc(raw, fallback_id=wid))

    protocol_data = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    doc_by_wsid = {d.workspace_id: d for d in docs if d.workspace_id}

    all_decisions: list[ScreeningDecision] = []
    for batch in manifest["batches"]:
        idx = batch["batch_index"]
        decisions_file = screening_dir / f"batch_{idx:03d}_decisions.json"
        batch_file = screening_dir / f"batch_{idx:03d}.json"
        if decisions_overrides is not None and idx in decisions_overrides:
            raw_decisions = decisions_overrides[idx]
        else:
            if not decisions_file.is_file():
                raise ReviewRefused(
                    REVIEW_NOT_PREPARED,
                    f"batch {idx} has no researcher-resolved decisions file; "
                    "resolve every batch or defer publication",
                    batch_index=idx,
                )
            raw_decisions = _parse_decisions(decisions_file)
        batch_data = json.loads(batch_file.read_text(encoding="utf-8"))
        batch_entry = registry.get("artifacts", {}).get(batch_data.get("artifact_id"))
        if not batch_entry:
            raise WorkerRefused(
                WORKER_PARENT_UNRESOLVED,
                f"batch {idx} parent artifact is not registered",
                batch_index=idx,
            )
        batch_env = json.loads((ws / batch_entry["path"]).read_text(encoding="utf-8"))
        batch_candidate_ids = {
            str(candidate.get("study_id"))
            for candidate in batch_env.get("data", {}).get("candidates", [])
        }
        check_exact_coverage(batch_candidate_ids, raw_decisions)
        _require_resolved(raw_decisions)

        for entry in raw_decisions:
            if any(key.startswith(("inc_", "exc_")) for key in entry):
                raise ReviewRefused(
                    REVIEW_CHECKLIST_UNSUPPORTED,
                    f"batch {idx} carries checklist-derived rows; the AG-04 "
                    "pilot supports legacy INCLUDE/EXCLUDE rows only",
                    batch_index=idx,
                )
            wsid = str(entry.get("workspace_id") or entry.get("study_id") or "")
            doc = doc_by_wsid.get(wsid)
            raw_dec = str(entry.get("decision", "")).strip().upper()
            if raw_dec not in ("INCLUDE", "EXCLUDE"):
                raise ReviewRefused(
                    REVIEW_INVALID_DECISIONS,
                    f"batch {idx} carries non-terminal decision {raw_dec!r}",
                    batch_index=idx,
                )
            try:
                confidence = float(entry.get("confidence", 0.80))
            except (TypeError, ValueError):
                confidence = 0.80
            all_decisions.append(
                ScreeningDecision(
                    workspace_id=wsid,
                    decision=raw_dec,
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
            )

    manifest_raw = ws / "literature" / "raw" / "provenance_manifest.json"
    total_identified = len(docs)
    duplicates_removed = 0
    if manifest_raw.exists():
        try:
            harvest = json.loads(manifest_raw.read_text(encoding="utf-8"))
            total_identified = harvest.get("total_raw_harvested", len(docs))
            duplicates_removed = max(0, total_identified - len(docs))
        except (OSError, ValueError):
            pass

    inc_docs, exc_docs, conflicts, report = partition_screening_results(
        docs,
        all_decisions,
        total_identified=total_identified,
        duplicates_removed=duplicates_removed,
    )
    # Identical serialization to cmd_collect (same dumps args, same order).
    return {
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


def approve_command(
    workspace_dir: Path,
    batch_index: int,
    *,
    decisions_file: Path | None = None,
    message: str | None = None,
    approved_at: str | None = None,
) -> dict[str, Any]:
    """Approve the exact reviewed content for one batch (operator action).

    Refuses when this process runs at Low integrity on Windows (the worker
    cannot invoke the operator action), when no publisher operator context
    exists, and while any row is unresolved. A reviewed file that differs
    from the worker recommendation becomes a superseding revision preserving
    the original; the fresh approval binds the new revision only. The
    publication approval for the existing collect gate is staged from the
    exact partition content, so ``collect`` verifies without modification.
    """
    if _is_low_integrity_process():
        raise AuthorityRefused(
            APPROVAL_NOT_OPERATOR,
            "approve refused: this process runs at Low integrity (worker "
            "level); the operator action requires the publisher context",
        )
    ws = Path(workspace_dir).resolve()
    operator = load_operator_context(ws)
    moment = approved_at if approved_at is not None else _utcnow_iso()

    recommendation_bytes = _read_recommendation_bytes(ws, batch_index)
    decisions_path = (
        Path(decisions_file)
        if decisions_file is not None
        else default_decisions_path(ws, batch_index)
    )
    if not decisions_path.is_file():
        raise AuthorityRefused(
            APPROVAL_MISSING,
            f"no researcher-resolved file {decisions_path.name}; refusing to "
            "approve pending worker output (missing approval is never a "
            "default approval)",
            batch_index=batch_index,
        )
    final_bytes = decisions_path.read_bytes()
    entries = _parse_decisions(decisions_path)

    batch_env = _resolve_batch_env(ws, batch_index)
    batch_candidate_ids = {
        str(candidate.get("study_id"))
        for candidate in batch_env.get("data", {}).get("candidates", [])
    }
    check_exact_coverage(batch_candidate_ids, entries)
    _require_resolved(entries)

    snapshot = capture_snapshot(
        recommendation_bytes,
        recommendation_bytes,
        _review_binding(batch_env, 1),
        captured_at=moment,
    )
    superseded = final_bytes != recommendation_bytes
    if superseded:
        # Researcher override: preserve the original recommendation bytes
        # verbatim in revision 1, burn a new revision carrying the resolved
        # final content, and bind the fresh approval to the new revision
        # only.
        snapshot = supersede(snapshot, final_bytes, operator, captured_at=moment)

    record = mint_approval(
        operator=operator,
        binding=snapshot.binding,
        reviewed_bytes=snapshot.bytes_for("hash"),
        final_decision_bytes=snapshot.final_bytes_for("hash"),
        approved_at=moment,
    )

    screening_dir = _screening_dir(ws)
    reviews_dir = _reviews_dir(ws)
    approvals_dir = _approvals_dir(ws)
    reviews_dir.mkdir(parents=True, exist_ok=True)
    approvals_dir.mkdir(parents=True, exist_ok=True)
    review_record = {
        "schema": REVIEW_SCHEMA,
        "batch_index": batch_index,
        "binding": snapshot.binding.as_dict(),
        "recommendation_sha256": snapshot.recommendation_sha256,
        "final_decision_sha256": snapshot.final_decision_sha256,
        "snapshot_fingerprint": snapshot.fingerprint(),
        "supersedes": snapshot.supersedes,
        "superseded_by": snapshot.superseded_by,
        "superseded": superseded,
        "approval_fingerprint": record.fingerprint(),
        "operator_identity": record.operator_identity,
        "message": message,
        "reviewed_at": moment,
    }
    review_out = review_path(ws, batch_index)
    review_out.write_text(
        json.dumps(review_record, indent=2, sort_keys=True), encoding="utf-8"
    )
    approval_out = batch_approval_path(ws, batch_index)
    approval_out.write_text(
        json.dumps(
            {
                "schema": BATCH_APPROVAL_SCHEMA,
                "approval": record.as_dict(),
                "policy_version": REVIEW_POLICY_VERSION,
                "staged_at": moment,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    # Stage the publication approval the existing collect gate verifies:
    # same scope resolution, same content, same snapshot construction. The
    # staged approval binds the validated in-memory entries (not a re-read),
    # so a custom --decisions-file stays fail-closed: collect over different
    # default-path bytes refuses until those bytes are delivered.
    content = _compute_single_screener_content(
        ws, decisions_overrides={batch_index: entries}
    )
    scope = resolve_publication_scope(ws)
    digests = {
        name: content_sha256(publication_file_bytes(text))
        for name, text in content.items()
    }
    snapshot_bytes = build_publication_snapshot(
        workspace_id=scope.workspace_id,
        run_id=scope.run_id,
        batch_bindings=[dict(b) for b in scope.batch_bindings],
        protocol_fingerprint=scope.protocol_fingerprint,
        corpus_fingerprint=scope.corpus_fingerprint,
        output_digests=digests,
    )
    binding = publication_binding(
        workspace_id=scope.workspace_id,
        run_id=scope.run_id,
        batch_bindings=[dict(b) for b in scope.batch_bindings],
        protocol_fingerprint=scope.protocol_fingerprint,
        corpus_fingerprint=scope.corpus_fingerprint,
    )
    publication_record = mint_publication_approval(
        operator=operator,
        binding=binding,
        snapshot_bytes=snapshot_bytes,
        approved_at=moment,
    )
    publication_out = write_publication_approval(
        screening_dir, publication_record, staged_at=moment
    )

    # A successful approval lifts any prior deferral for this batch.
    deferral_file = deferral_path(ws, batch_index)
    deferral_lifted = deferral_file.is_file()
    if deferral_lifted:
        deferral_file.unlink()

    return {
        "batch_index": batch_index,
        "review_path": str(review_out),
        "approval_path": str(approval_out),
        "publication_approval_path": str(publication_out),
        "binding": snapshot.binding.as_dict(),
        "superseded": superseded,
        "recommendation_sha256": snapshot.recommendation_sha256,
        "final_decision_sha256": snapshot.final_decision_sha256,
        "approval_fingerprint": record.fingerprint(),
        "publication_approval_fingerprint": publication_record.fingerprint(),
        "operator_identity": record.operator_identity,
        "deferral_lifted": deferral_lifted,
    }


def cmd_approve(
    workspace_dir: Path,
    batch_index: int,
    decisions_file: str | None = None,
    message: str | None = None,
    begin: bool = False,
) -> None:
    """CLI entry: approve the reviewed content and stage the publication approval.

    When ``begin`` is True, stage a single-use pairing challenge via the
    existing :func:`pairing.begin_pairing` path and print the code exactly
    once to stdout with its expiry and snapshot fingerprint (the operator
    compares the fingerprint with the browser view). The code is terminal
    stdout only: it is never logged, never written to any file, and never
    appears in exception messages. ``message``/``decisions_file`` are not
    staged with the challenge (the pairing store is hash-only by contract);
    the approval note is minted at redeem. Refusals propagate unchanged
    (Low-IL ``APPROVAL_NOT_OPERATOR``, missing context
    ``OPERATOR_CONTEXT_MISSING``, unresolved ``APPROVAL_MISSING``).
    """
    if begin:
        # Staged binding must equal operator intent: silently dropping a
        # supplied note/file would be a bypass-shaped surprise (the operator
        # would believe the note was staged when it was not), so refuse
        # before staging anything (no challenge staged, nothing minted).
        if decisions_file is not None or message is not None:
            raise ReviewRefused(
                REVIEW_BEGIN_ARGS_REFUSED,
                "approve --begin stages the live review snapshot only; "
                "--decisions-file/--message are not staged with the challenge "
                "(re-run without --begin to approve with a note/file)",
                batch_index=batch_index,
            )
        from scholar_harness.authority.pairing import begin_pairing

        staged = begin_pairing(Path(workspace_dir), batch_index)
        print(f"Pairing code for batch {batch_index}: {staged['code']}")
        print(f"  expires: {staged['expires_at']}")
        print(f"  snapshot: {staged['snapshot_fingerprint']}")
        print(
            "  (single-use; type this code into the browser dialog "
            "— it is shown only here)"
        )
        return
    result = approve_command(
        Path(workspace_dir),
        batch_index,
        decisions_file=Path(decisions_file) if decisions_file else None,
        message=message,
    )
    print(f"Approved batch {batch_index} as {result['operator_identity']}")
    print(f"  review record: {result['review_path']}")
    print(f"  batch approval: {result['approval_path']}")
    print(f"  publication approval: {result['publication_approval_path']}")
    print(f"  approval: {result['approval_fingerprint']}")
    if result["superseded"]:
        print("  (superseding revision: researcher override preserved the original)")


# --- deferral ----------------------------------------------------------------- #


def defer_command(
    workspace_dir: Path,
    batch_index: int,
    *,
    reason: str,
    recorded_at: str | None = None,
) -> Path:
    """Record a deferred/cancelled state with reason; publish nothing.

    A reason of ``CANCELLED`` marks an explicit cancellation. Any staged
    batch or publication approval for this batch is voided (fingerprints are
    preserved in the deferral record), so a deferred batch leaves nothing
    publishable until a fresh approval is minted. The staged pairing
    challenge is voided alongside (F-01: defer-then-redeem must not mint —
    the genuine code refuses ``PAIRING_CODE_INVALID/reason=consumed``
    afterwards and must begin again); the ``pairing_voided`` outcome is
    recorded beside ``voided_approvals``.
    """
    if not isinstance(reason, str) or not reason.strip():
        raise ReviewRefused(
            REVIEW_REASON_MISSING,
            "defer requires a reason (use CANCELLED for an explicit cancellation)",
            batch_index=batch_index,
        )
    ws = Path(workspace_dir).resolve()
    moment = recorded_at if recorded_at is not None else _utcnow_iso()
    screening_dir = _screening_dir(ws)

    voided: list[dict[str, str]] = []
    for candidate in (
        batch_approval_path(ws, batch_index),
        screening_dir / "publication_approval.json",
    ):
        if candidate.is_file():
            try:
                prior = json.loads(candidate.read_text(encoding="utf-8"))
                fingerprint = str(
                    prior.get("approval", {}).get("operator_identity", "")
                )
            except (OSError, ValueError, AttributeError):
                fingerprint = ""
            candidate.unlink()
            voided.append({"path": candidate.name, "prior_operator": fingerprint})

    batch_file = screening_dir / f"batch_{batch_index:03d}.json"
    batch_id = f"batch-{batch_index:03d}"
    if batch_file.is_file():
        try:
            batch_id = str(
                json.loads(batch_file.read_text(encoding="utf-8")).get(
                    "artifact_id", batch_id
                )
            )
        except (OSError, ValueError, AttributeError):
            pass

    cancelled = reason.strip().upper() == CANCELLED_REASON
    # F-01: void the staged pairing challenge here (this function owns
    # staged-state teardown) so CLI defer closes the defer-then-redeem path.
    # Lazy import: pairing imports this module at load; calling back at
    # teardown time avoids the cycle.
    from scholar_harness.authority.pairing import cancel_pairing as _void_pairing

    pairing_voided = bool(_void_pairing(ws, batch_index))
    record = {
        "schema": DEFERRAL_SCHEMA,
        "batch_index": batch_index,
        "batch_id": batch_id,
        "reason": reason.strip(),
        "cancelled": cancelled,
        "voided_approvals": voided,
        "pairing_voided": pairing_voided,
        "recorded_at": moment,
    }
    out = deferral_path(ws, batch_index)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return out


def cmd_defer(workspace_dir: Path, batch_index: int, reason: str) -> None:
    """CLI entry: defer (or cancel) publication for one batch."""
    out = defer_command(Path(workspace_dir), batch_index, reason=reason)
    record = json.loads(out.read_text(encoding="utf-8"))
    state = "cancelled" if record["cancelled"] else "deferred"
    print(f"Batch {batch_index} {state}: {record['reason']} (nothing published)")
    print(f"  pairing voided: {bool(record.get('pairing_voided', False))}")
