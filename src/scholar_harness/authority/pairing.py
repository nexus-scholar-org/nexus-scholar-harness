"""Single-use pairing codes binding a browser approval act to a terminal act (UI-07).

Primary scheme of ``docs/architecture/research_ui/UI-07_ACTION_SPEC.md`` §3:
the operator act happens in their Medium terminal (the authority already
lives there); the browser only carries a short, single-use, time-bound code
that is useless to anyone who did not see the terminal.

Discipline (all floors from spec §3.1, values fixed here and pinned by
``tests/authority/test_pairing.py`` — values below these floors are refused
as a review failure, never tuned):

* the code is drawn from a server-side CSPRNG secret of ≥128-bit entropy
  (``secrets`` over a 32-symbol alphabet, 26 characters = 130 bits);
* single-use (an atomic consumed flip under a process lock; single-host
  only, documented);
* expires no later than 10 minutes after minting (default 5 minutes);
* verified with a constant-time comparison against the stored hash;
* verified behind a bounded attempt count (default cap 5).

Pending-store secrecy (spec §3.1, normative): the store holds ONLY a salted
hash of the code — never the plaintext, never a reversibly-encrypted copy.
The record carries the snapshot fingerprint, the expiry, and the attempt
counter only. Codes never appear in the audit journal, the workspace index,
or any API response: challenge creation is a terminal-side act
(:func:`begin_pairing`, the ``approve --begin`` semantics) and the code is
returned to the terminal caller only. There is deliberately NO API route
that mints or returns a code.

Authority reuse (never rewritten): the operator context and Low-integrity
gate come from :mod:`scholar_harness.authority.review`, the approval itself
is minted by ``approve_command`` (AG-03B/AG-04, including
coverage/unresolved gates, override-with-supersession, and deferral lift),
and invalidation downstream stays with the AG-03C generation gate. This
module adds only the challenge staging, the still-current revalidation, and
the atomic single-use flip around that existing path.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from scholar_harness.authority.binding import (
    APPROVAL_MISSING,
    APPROVAL_NOT_OPERATOR,
    AuthorityRefused,
    canonical_json_bytes,
    content_sha256,
)

import scholar_harness.authority.review as _review_mod

#: Sidecar identity for one staged pairing challenge.
PAIRING_SCHEMA = "harness-screening-pairing-v1"

#: Typed refusal codes owned by this layer (spec §5 rows).
PAIRING_CODE_INVALID = "PAIRING_CODE_INVALID"
STALE_VIEW = "STALE_VIEW"

#: Challenge parameters fixed at implementation review (spec OQ-A1).
#: All at or above the §3.1 floors; values below are refused, never tuned.
PAIRING_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # 32 symbols, no 0/O/1/I
PAIRING_CODE_LENGTH = 26  # 26 x 5 bits = 130 bits of CSPRNG entropy (floor: 128)
PAIRING_CODE_LIFETIME_S = 300  # 5 minutes (floor: expire no later than 10 minutes)
PAIRING_ATTEMPT_CAP = 5  # bounded verification attempts (floor: bounded)
PAIRING_PBKDF2_ITERATIONS = 210_000
PAIRING_SALT_BYTES = 16

#: Subdirectory holding staged challenges (server-side, workspace-local).
PAIRING_STORE_DIRNAME = "pairing"

#: Exact store envelope keys. The record holds ONLY the salted hash plus the
#: snapshot fingerprint, expiry, attempt counter, consumption flag, and the
#: content binding — never a plaintext or reversibly-stored code.
PAIRING_RECORD_KEYS = frozenset(
    {
        "schema",
        "batch_index",
        "salted_hash",
        "snapshot_fingerprint",
        "action_binding",
        "expires_at",
        "attempts_used",
        "attempt_cap",
        "consumed",
        "staged_at",
    }
)

#: Pairing lifecycle states reported by :func:`pairing_status`.
PAIRING_STATE_ABSENT = "ABSENT"
PAIRING_STATE_STAGED = "STAGED"
PAIRING_STATE_CONSUMED = "CONSUMED"
PAIRING_STATE_EXPIRED = "EXPIRED"
PAIRING_STATE_EXHAUSTED = "EXHAUSTED"

#: Single-host serialization for the read-modify-write of the pairing file
#: (stage, verify-and-consume, void). The in-process ``threading.Lock``
#: serializes threads; the file lock below serializes processes on one host.
#: Writers that honor this protocol on one host serialize; nothing is claimed
#: about a second host or a writer that ignores it — the same best-effort
#: scope as the AG-03C collect lock (``generations._acquire_lock`` semantics
#: mirrored here, not its code path).
_PAIRING_LOCK = threading.Lock()

#: Best-effort inter-process lock file in the pairing store directory
#: (mirrors the AG-03C ``.collect.lock`` pattern: O_CREAT|O_EXCL, pid
#: content, bounded wait, typed refusal on contention; single-host only).
PAIRING_LOCK_FILENAME = ".pairing.lock"

#: Typed refusal when the pairing file lock is held by a live writer.
PAIRING_LOCKED = "PAIRING_LOCKED"

#: Sidecar identity for one batch's redeem idempotency record (F-02).
IDEMPOTENCY_SCHEMA = "harness-screening-redeem-idempotency-v1"


def _pairing_store_dir(workspace_dir: Path) -> Path:
    return _screening_dir(Path(workspace_dir).resolve()) / PAIRING_STORE_DIRNAME


def _pairing_lock_path(workspace_dir: Path) -> Path:
    return _pairing_store_dir(workspace_dir) / PAIRING_LOCK_FILENAME


def _acquire_pairing_lock(workspace_dir: Path, timeout_s: float) -> None:
    """Best-effort single-host file lock (AG-03C ``.collect.lock`` semantics).

    Exclusive-create with the writer pid as content; waits up to
    ``timeout_s`` then refuses with ``PAIRING_LOCKED`` (a defined locked
    refusal, never a double mint). Stale files from a crashed writer block
    until removed manually once no live writer remains — same residual as
    the collect lock. Intra-process threads additionally hold
    ``_PAIRING_LOCK``; this file lock covers inter-process redemption.
    """
    import time as _time

    lock_path = _pairing_lock_path(workspace_dir)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = _time.monotonic() + max(0.0, float(timeout_s))
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, str(os.getpid()).encode("ascii"))
            finally:
                os.close(fd)
            return
        except (FileExistsError, PermissionError) as exc:
            if _time.monotonic() >= deadline:
                if isinstance(exc, PermissionError):
                    detail = (
                        "the pairing lock could not be acquired (access denied); "
                        "on Windows an existing directory or an exclusively opened "
                        "lock file reports this instead of 'already exists' — "
                        "refusing to mix redemptions; inspect the lock path and "
                        "retry once no live writer remains"
                    )
                else:
                    detail = (
                        "another redeemer holds the pairing lock; refusing to mix "
                        "redemptions (retry once no live writer remains)"
                    )
                raise _invalid(
                    PAIRING_LOCKED,
                    detail,
                    lock_path=str(lock_path),
                ) from exc
            _time.sleep(0.02)


def _release_pairing_lock(workspace_dir: Path) -> None:
    try:
        _pairing_lock_path(workspace_dir).unlink(missing_ok=True)
    except OSError:
        pass


def idempotency_path(workspace_dir: Path, batch_index: int) -> Path:
    """Server-side path of the redeem idempotency record for one batch.

    Lives alongside the pairing store (same directory, same honesty
    constraints: hashes + ids only — NO secrets, NO codes).
    """
    return (
        _screening_dir(Path(workspace_dir).resolve())
        / PAIRING_STORE_DIRNAME
        / f"batch_{batch_index:03d}_idempotency.json"
    )


def _read_idempotency(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"schema": IDEMPOTENCY_SCHEMA, "entries": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"schema": IDEMPOTENCY_SCHEMA, "entries": {}}
    if not isinstance(payload, dict):
        return {"schema": IDEMPOTENCY_SCHEMA, "entries": {}}
    entries = payload.get("entries")
    if not isinstance(entries, dict):
        return {"schema": IDEMPOTENCY_SCHEMA, "entries": {}}
    return {"schema": IDEMPOTENCY_SCHEMA, "entries": entries}


def _idempotency_key(operation: str, request_id: str) -> str:
    return f"{operation}:{request_id}"


def _store_idempotent_success(
    path: Path,
    *,
    batch_index: int,
    request_id: str,
    snapshot_fingerprint: str,
    final_decision_sha256: str,
    parent_sha256: str,
    approval_fingerprint: str,
    publication_approval_fingerprint: str,
    operator_identity: str,
    superseded: bool,
) -> None:
    """Persist the redeem success summary for idempotent retries.

    Hashes + ids only — NO secrets, NO codes. The publish path shares this
    helper shape (``operation="publish"``) rather than duplicating it; today
    publish idempotency rides the generation record, so only ``redeem``
    writes here.
    """
    payload = _read_idempotency(path)
    entries = dict(payload.get("entries", {}))
    entries[_idempotency_key("redeem", request_id)] = {
        "operation": "redeem",
        "batch_index": batch_index,
        "snapshot_fingerprint": snapshot_fingerprint,
        "final_decision_sha256": final_decision_sha256,
        "parent_sha256": parent_sha256,
        "approval_fingerprint": approval_fingerprint,
        "publication_approval_fingerprint": publication_approval_fingerprint,
        "operator_identity": operator_identity,
        "superseded": superseded,
        "stored_at": _utcnow().isoformat(),
    }
    _write_record(path, {"schema": IDEMPOTENCY_SCHEMA, "entries": entries})


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _screening_dir(workspace_dir: Path) -> Path:
    return Path(workspace_dir).resolve() / "literature" / "screening"


def pairing_path(workspace_dir: Path, batch_index: int) -> Path:
    """Server-side path of the staged challenge for one batch."""
    return (
        _screening_dir(workspace_dir)
        / PAIRING_STORE_DIRNAME
        / f"batch_{batch_index:03d}_pairing.json"
    )


def normalize_code(raw: str) -> str:
    """Normalize a transcribed code (case/dash/space-insensitive)."""
    return (
        str(raw or "")
        .strip()
        .upper()
        .replace("-", "")
        .replace(" ", "")
        .replace("_", "")
    )


def mint_code() -> str:
    """Draw one code from the server-side CSPRNG (≥128-bit entropy)."""
    alphabet = PAIRING_CODE_ALPHABET
    return "".join(secrets.choice(alphabet) for _ in range(PAIRING_CODE_LENGTH))


def hash_code(code: str, *, salt: bytes | None = None) -> str:
    """Salt and hash one code for storage (PBKDF2-HMAC-SHA256)."""
    blob = salt if salt is not None else secrets.token_bytes(PAIRING_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", normalize_code(code).encode("ascii"), blob, PAIRING_PBKDF2_ITERATIONS
    )
    return f"pbkdf2-sha256${PAIRING_PBKDF2_ITERATIONS}${blob.hex()}${digest.hex()}"


def verify_code(code: str, stored: str) -> bool:
    """Constant-time comparison of a presented code against the stored hash."""
    try:
        scheme, iterations_s, salt_hex, digest_hex = str(stored).split("$")
    except ValueError:
        return False
    if scheme != "pbkdf2-sha256":
        return False
    try:
        iterations = int(iterations_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256", normalize_code(code).encode("ascii"), salt, iterations
    )
    return hmac.compare_digest(candidate, expected)


def snapshot_content_key(payload: dict[str, Any]) -> dict[str, Any]:
    """The time-independent content a pairing challenge binds.

    A review snapshot fingerprint embeds ``captured_at``, so two snapshots of
    identical content minted a second apart fingerprint differently. The
    pairing binding must be stable across the terminal-to-browser round trip,
    so it commits to the binding plus the two content hashes only — the same
    bytes the approval hashes, without the timestamp.
    """
    return {
        "binding": dict(payload["binding"]),
        "recommendation_sha256": str(payload["recommendation_sha256"]),
        "final_decision_sha256": str(payload["final_decision_sha256"]),
    }


def snapshot_content_fingerprint(content_key: dict[str, Any]) -> str:
    """Stable fingerprint of the bound content (shown on both surfaces)."""
    return content_sha256(canonical_json_bytes(content_key))


def _parent_binding(workspace_dir: Path, batch_index: int) -> dict[str, str]:
    """The registered parent artifact the staged snapshot resolves against.

    Mirrors the registry freshness check (canonical fingerprint of the live
    envelope vs the recorded sha256): a parent envelope superseded after
    acceptance refuses instead of staging a challenge against stale parents.
    """
    from scholar_harness.contracts.canonical import canonical_fingerprint

    ws = Path(workspace_dir).resolve()
    screening_dir = ws / "literature" / "screening"
    batch_file = screening_dir / f"batch_{batch_index:03d}.json"
    try:
        batch_data = json.loads(batch_file.read_text(encoding="utf-8"))
        registry = json.loads(
            (ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8")
        )
        entry = registry.get("artifacts", {}).get(batch_data.get("artifact_id"))
        live_envelope = json.loads(
            (ws / str(entry["path"])).read_text(encoding="utf-8")
        )
        live_sha = canonical_fingerprint(live_envelope)
        if live_sha != entry.get("sha256"):
            raise AuthorityRefused(
                STALE_VIEW,
                "the batch parents were superseded after acceptance; "
                "re-resolve before staging a challenge",
                batch_index=batch_index,
                changed_element="batch_parents",
            )
        return {
            "parent_artifact_id": str(batch_data.get("artifact_id")),
            "parent_sha256": live_sha,
        }
    except AuthorityRefused:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise AuthorityRefused(
            "WORKER_PARENT_UNRESOLVED",
            f"cannot resolve accepted parent batch for index {batch_index} "
            f"({exc}); refusing to stage a challenge without parents",
            batch_index=batch_index,
        ) from exc


def _write_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp-{uuid.uuid4().hex[:8]}")
    tmp.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def _read_record(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(payload, dict) or payload.get("schema") != PAIRING_SCHEMA:
        return None
    return payload


def _is_expired(record: dict[str, Any], now: datetime) -> bool:
    try:
        return now > datetime.fromisoformat(str(record["expires_at"]))
    except ValueError:
        return True


def _invalid(code: str, message: str, **details: Any) -> AuthorityRefused:
    return AuthorityRefused(code, message, **details)


def begin_pairing(
    workspace_dir: Path,
    batch_index: int,
    *,
    lifetime_s: int = PAIRING_CODE_LIFETIME_S,
    attempt_cap: int = PAIRING_ATTEMPT_CAP,
    request_id: str | None = None,
    staged_at: str | None = None,
) -> dict[str, Any]:
    """Stage one pairing challenge (terminal-side ``approve --begin`` act).

    Freezes the exact review snapshot (AG-03B single-buffer discipline via
    :func:`review.load_review_snapshot`), binds a fresh CSPRNG code to its
    content, and stores ONLY the salted hash. The plaintext code is returned
    to the terminal caller ONLY — it never touches the workspace, the
    journal, or any API response.

    Refuses (Low-integrity caller, missing operator context, missing parents,
    nothing resolved to approve) exactly like the approval it stages for:
    AG-02/AG-04 semantics are reused, never rewritten. A second ``begin``
    for one batch supersedes the first (the old code fails verification
    afterwards and must be begun again).

    ``request_id`` is correlation-only: echoed in errors for log/journal
    tracing, never identity, never authorization, never a secret. It is not
    the idempotency key (redeem idempotency is content-keyed with the
    request id as stem — same stem with different content refuses).
    """
    if _review_mod._is_low_integrity_process():
        raise AuthorityRefused(
            APPROVAL_NOT_OPERATOR,
            "pairing begin refused: this process runs at Low integrity (worker "
            "level); the operator act requires the publisher context",
        )
    ws = Path(workspace_dir).resolve()
    _review_mod.load_operator_context(
        ws
    )  # identity verified now; approval mints it at redeem
    if lifetime_s > 600:
        # Anything above the 10-minute cap is refused, never silently
        # clamped. Non-positive lifetimes stage an already-expired challenge
        # (exercised by tests); they grant nothing.
        raise _invalid(
            PAIRING_CODE_INVALID,
            "pairing lifetime exceeds the 10-minute cap; refusing a "
            "weaker-than-floor configuration",
            lifetime_s=lifetime_s,
        )
    moment = _utcnow()
    moment_iso = staged_at if staged_at is not None else moment.isoformat()

    snapshot, _, final_bytes = _review_mod.load_review_snapshot(ws, batch_index)
    if final_bytes is None:
        raise AuthorityRefused(
            APPROVAL_MISSING,
            "nothing resolved to stage: no researcher-resolved decisions file; "
            "missing approval is never a default approval",
            batch_index=batch_index,
        )
    content_key = {
        "binding": snapshot.binding.as_dict(),
        "recommendation_sha256": snapshot.recommendation_sha256,
        "final_decision_sha256": snapshot.final_decision_sha256,
    }
    fingerprint = snapshot_content_fingerprint(content_key)
    parent = _parent_binding(ws, batch_index)
    code = mint_code()
    record = {
        "schema": PAIRING_SCHEMA,
        "batch_index": batch_index,
        "salted_hash": hash_code(code),
        "snapshot_fingerprint": fingerprint,
        "action_binding": {**content_key, **parent},
        "expires_at": (moment + timedelta(seconds=lifetime_s)).isoformat(),
        "attempts_used": 0,
        "attempt_cap": attempt_cap,
        "consumed": False,
        "staged_at": moment_iso,
    }
    with _PAIRING_LOCK:
        _write_record(pairing_path(ws, batch_index), record)
    return {
        "batch_index": batch_index,
        # Plaintext code: terminal stdout only. Never stored, never logged,
        # never returned by any API route (pinned by test).
        "code": code,
        "snapshot_fingerprint": fingerprint,
        "expires_at": record["expires_at"],
        "attempt_cap": attempt_cap,
        "request_id": request_id or f"REQ-{uuid.uuid4().hex[:12]}",
    }


def pairing_status(
    workspace_dir: Path,
    batch_index: int,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Safe status of the staged challenge (never the code or its hash)."""
    ws = Path(workspace_dir).resolve()
    moment = now if now is not None else _utcnow()
    record = _read_record(pairing_path(ws, batch_index))
    if record is None:
        return {
            "shape": "screening-action-pairing-status-v1",
            "batch_index": batch_index,
            "state": PAIRING_STATE_ABSENT,
            "expires_at": None,
            "snapshot_fingerprint": None,
            "attempts_remaining": None,
        }
    if bool(record.get("consumed")):
        state = PAIRING_STATE_CONSUMED
    elif _is_expired(record, moment):
        state = PAIRING_STATE_EXPIRED
    elif int(record.get("attempts_used", 0)) >= int(
        record.get("attempt_cap", PAIRING_ATTEMPT_CAP)
    ):
        state = PAIRING_STATE_EXHAUSTED
    else:
        state = PAIRING_STATE_STAGED
    cap = int(record.get("attempt_cap", PAIRING_ATTEMPT_CAP))
    used = int(record.get("attempts_used", 0))
    return {
        "shape": "screening-action-pairing-status-v1",
        "batch_index": batch_index,
        "state": state,
        "expires_at": str(record.get("expires_at")),
        "snapshot_fingerprint": str(record.get("snapshot_fingerprint")),
        "attempts_remaining": max(0, cap - used),
    }


def cancel_pairing(workspace_dir: Path, batch_index: int) -> bool:
    """Void the staged challenge (defer/cancel path); the code must begin again."""
    ws = Path(workspace_dir).resolve()
    path = pairing_path(ws, batch_index)
    with _PAIRING_LOCK:
        record = _read_record(path)
        if record is None or bool(record.get("consumed")):
            return False
        record["consumed"] = True
        _write_record(path, record)
        return True


def _current_content(
    ws: Path, batch_index: int
) -> tuple[dict[str, Any], dict[str, str]]:
    """Recompute the live content key plus parent binding for revalidation."""
    snapshot, _, _ = _review_mod.load_review_snapshot(ws, batch_index)
    content_key = {
        "binding": snapshot.binding.as_dict(),
        "recommendation_sha256": snapshot.recommendation_sha256,
        "final_decision_sha256": snapshot.final_decision_sha256,
    }
    return content_key, _parent_binding(ws, batch_index)


def redeem_pairing(
    workspace_dir: Path,
    batch_index: int,
    code: str,
    *,
    request_id: str | None = None,
    approved_at: str | None = None,
    lock_timeout_s: float = 10.0,
) -> dict[str, Any]:
    """Verify a transcribed code and mint the approval via the AG-03B path.

    On success the approval is minted by ``approve_command`` unchanged
    (coverage/unresolved gates, override-with-supersession, deferral lift,
    staged publication approval) and the code is marked consumed atomically.
    On any content drift the code is invalidated and the approval is refused
    with ``STALE_VIEW`` naming the changed element. Gate refusals that are
    not drift (coverage, unresolved, missing context) leave the staged
    challenge untouched so the operator can re-begin after re-review.

    ``request_id`` is correlation-only: echoed in errors and the journal
    for tracing, never identity, never authorization, never a secret. A
    retry presenting the SAME request id with IDENTICAL content hashes
    returns the stored success without re-minting (workspace-local
    idempotency record alongside the pairing store); the same stem with
    DIFFERENT content refuses instead of replaying the earlier success.
    A fresh request id proceeds normally (consumed codes still refuse).

    Concurrency: the in-process ``_PAIRING_LOCK`` plus the best-effort
    single-host file lock (``.pairing.lock``, AG-03C semantics) serialize
    the read-verify-mint-write sequence. Contention refuses with
    ``PAIRING_LOCKED``, never a double mint.
    """
    ws = Path(workspace_dir).resolve()
    moment = _utcnow()
    req = request_id or f"REQ-{uuid.uuid4().hex[:12]}"
    path = pairing_path(ws, batch_index)
    idem_path = idempotency_path(ws, batch_index)
    with _PAIRING_LOCK:
        _acquire_pairing_lock(ws, lock_timeout_s)
        try:
            record = _read_record(path)
            if record is None:
                raise _invalid(
                    PAIRING_CODE_INVALID,
                    "no staged pairing challenge for this batch; begin again in "
                    "the terminal",
                    batch_index=batch_index,
                    reason="unknown",
                    request_id=req,
                )
            if bool(record.get("consumed")):
                # Idempotent retry: same stem + identical content returns the
                # stored success without re-minting; same stem with different
                # content refuses (never replays stale success); absent key
                # proceeds to the normal consumed refusal below.
                stored = _read_idempotency(idem_path)["entries"].get(
                    _idempotency_key("redeem", req)
                )
                if isinstance(stored, dict):
                    try:
                        live_key, live_parent = _current_content(ws, batch_index)
                    except AuthorityRefused as exc:
                        raise _invalid(
                            STALE_VIEW,
                            "the content changed since the recorded success "
                            f"({exc.code}); refusing to replay it",
                            batch_index=batch_index,
                            changed_element=exc.details.get(
                                "changed_element", exc.code
                            ),
                            request_id=req,
                        ) from exc
                    live_fp = snapshot_content_fingerprint(live_key)
                    if (
                        live_fp == stored.get("snapshot_fingerprint")
                        and str(live_key.get("final_decision_sha256"))
                        == str(stored.get("final_decision_sha256"))
                        and live_parent.get("parent_sha256")
                        == stored.get("parent_sha256")
                    ):
                        return {
                            "batch_index": batch_index,
                            "snapshot_fingerprint": str(stored["snapshot_fingerprint"]),
                            "approval_fingerprint": str(stored["approval_fingerprint"]),
                            "publication_approval_fingerprint": str(
                                stored["publication_approval_fingerprint"]
                            ),
                            "operator_identity": str(stored["operator_identity"]),
                            "superseded": bool(stored["superseded"]),
                            "request_id": req,
                            "idempotent": True,
                        }
                    raise _invalid(
                        STALE_VIEW,
                        "this request was recorded for different content; "
                        "refusing to replay the earlier success",
                        batch_index=batch_index,
                        changed_element="idempotent_content",
                        request_id=req,
                    )
                raise _invalid(
                    PAIRING_CODE_INVALID,
                    "that code is already used or voided; begin again in the terminal",
                    batch_index=batch_index,
                    reason="consumed",
                    request_id=req,
                )
            if _is_expired(record, moment):
                raise _invalid(
                    PAIRING_CODE_INVALID,
                    "that code is expired; begin again in the terminal",
                    batch_index=batch_index,
                    reason="expired",
                    request_id=req,
                )
            cap = int(record.get("attempt_cap", PAIRING_ATTEMPT_CAP))
            used = int(record.get("attempts_used", 0))
            if used >= cap:
                raise _invalid(
                    PAIRING_CODE_INVALID,
                    "that challenge exhausted its verification attempts; begin "
                    "again in the terminal",
                    batch_index=batch_index,
                    reason="exhausted",
                    request_id=req,
                )
            if not verify_code(code or "", str(record.get("salted_hash", ""))):
                record["attempts_used"] = used + 1
                _write_record(path, record)
                raise _invalid(
                    PAIRING_CODE_INVALID,
                    "that code is not recognized; begin again in the terminal "
                    "if it keeps failing",
                    batch_index=batch_index,
                    reason="invalid",
                    attempts_remaining=max(0, cap - used - 1),
                    request_id=req,
                )

            # The code is genuine: revalidate that the staged snapshot is still
            # current before minting anything. Any drift voids the code.
            try:
                live_key, live_parent = _current_content(ws, batch_index)
            except AuthorityRefused as exc:
                record["consumed"] = True
                _write_record(path, record)
                raise _invalid(
                    STALE_VIEW,
                    "the content changed since review "
                    f"({exc.code}); re-review in the terminal before approving",
                    batch_index=batch_index,
                    changed_element=exc.details.get("changed_element", exc.code),
                    request_id=req,
                ) from exc
            live_fingerprint = snapshot_content_fingerprint(live_key)
            if not hmac.compare_digest(
                live_fingerprint, str(record.get("snapshot_fingerprint", ""))
            ):
                record["consumed"] = True
                _write_record(path, record)
                raise _invalid(
                    STALE_VIEW,
                    "the content changed since review; re-review in the terminal "
                    "before approving",
                    batch_index=batch_index,
                    changed_element="snapshot_content",
                    request_id=req,
                )
            stored_parent = {
                "parent_artifact_id": str(
                    record.get("action_binding", {}).get("parent_artifact_id")
                ),
                "parent_sha256": str(
                    record.get("action_binding", {}).get("parent_sha256")
                ),
            }
            if live_parent != stored_parent:
                record["consumed"] = True
                _write_record(path, record)
                raise _invalid(
                    STALE_VIEW,
                    "the batch parents changed since review; re-review in the "
                    "terminal before approving",
                    batch_index=batch_index,
                    changed_element="batch_parents",
                    request_id=req,
                )

            # Still current: mint via the existing AG-03B path, then consume.
            # Gate refusals raised here (coverage, unresolved, operator context,
            # Low integrity) propagate with the staged challenge left in place.
            result = _review_mod.approve_command(
                ws,
                batch_index,
                approved_at=approved_at
                if approved_at is not None
                else moment.isoformat(),
            )
            record["consumed"] = True
            _write_record(path, record)
            # Workspace-local idempotency record (F-02): key material is
            # hashes + ids only — NO secrets, NO codes. Identical retries
            # return this summary without re-minting; different content
            # refuses instead of replaying it.
            _store_idempotent_success(
                idem_path,
                batch_index=batch_index,
                request_id=req,
                snapshot_fingerprint=live_fingerprint,
                final_decision_sha256=str(live_key.get("final_decision_sha256", "")),
                parent_sha256=str(live_parent.get("parent_sha256", "")),
                approval_fingerprint=str(result["approval_fingerprint"]),
                publication_approval_fingerprint=str(
                    result["publication_approval_fingerprint"]
                ),
                operator_identity=str(result["operator_identity"]),
                superseded=bool(result["superseded"]),
            )
            return {
                "batch_index": batch_index,
                "snapshot_fingerprint": live_fingerprint,
                "approval_fingerprint": result["approval_fingerprint"],
                "publication_approval_fingerprint": result[
                    "publication_approval_fingerprint"
                ],
                "operator_identity": result["operator_identity"],
                "superseded": result["superseded"],
                "request_id": req,
            }
        finally:
            _release_pairing_lock(ws)
