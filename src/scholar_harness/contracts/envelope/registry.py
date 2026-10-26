"""Closed refusal registry for ``Envelope@1`` (spec 02 §6).

The registry is a frozen string enum. Adding a code requires editing this
module, the governing spec table, and the roles that may emit it *in the same
change* — the conformance test enforces enum/docs/role-record agreement both
ways.

``VERDICT_CHANGES_REQUESTED`` is deliberately **not** a refusal: it is reviewer
payload (a review verdict), so it never lives on this enum. It still appears in
the generated docs table as an annotated payload row so consumers can find it.
"""

from __future__ import annotations

from enum import StrEnum


class RefusalCode(StrEnum):
    """Closed refusal vocabulary for ``Envelope@1``."""

    BLOCKED_INPUT = "BLOCKED_INPUT"
    BLOCKED_AMBIGUOUS_TASK = "BLOCKED_AMBIGUOUS_TASK"
    BLOCKED_CANONICAL_REPO = "BLOCKED_CANONICAL_REPO"
    BLOCKED_BASELINE_DRIFT = "BLOCKED_BASELINE_DRIFT"
    REFUSED_UNSUPPORTED = "REFUSED_UNSUPPORTED"
    PROVIDER_TRANSIENT = "PROVIDER_TRANSIENT"
    INVALID_OUTPUT = "INVALID_OUTPUT"
    PARENT_HASH_MISMATCH = "PARENT_HASH_MISMATCH"
    SCOPE_VIOLATION = "SCOPE_VIOLATION"
    CRITERIA_HASH_MISMATCH = "CRITERIA_HASH_MISMATCH"
    BATCH_INCOMPLETE = "BATCH_INCOMPLETE"
    IDENTITY_AMBIGUOUS = "IDENTITY_AMBIGUOUS"
    BATCH_ID_MISMATCH = "BATCH_ID_MISMATCH"
    SOURCE_MISSING = "SOURCE_MISSING"
    LOCATOR_UNRESOLVED = "LOCATOR_UNRESOLVED"
    QUOTE_NOT_IN_SOURCE = "QUOTE_NOT_IN_SOURCE"
    ABSENCE_UNCLASSIFIED = "ABSENCE_UNCLASSIFIED"
    REQUIREMENT_UNTRACEABLE = "REQUIREMENT_UNTRACEABLE"
    TEST_GATE_FAILED = "TEST_GATE_FAILED"


#: Codes the registry tables list as emittable by any role (or by the adapter
#: on behalf of any role).
ANY_EMITTER_CODES = frozenset(
    {
        RefusalCode.BLOCKED_INPUT,
        RefusalCode.REFUSED_UNSUPPORTED,
        RefusalCode.PROVIDER_TRANSIENT,
        RefusalCode.INVALID_OUTPUT,
        RefusalCode.PARENT_HASH_MISMATCH,
        RefusalCode.SCOPE_VIOLATION,
    }
)

#: Roles allowed to *emit* each non-global code (spec 02 §6 "Emitted by").
#: ``None`` means any role.
_EMITTER_ROLES: dict[RefusalCode, frozenset[str] | None] = {
    RefusalCode.BLOCKED_INPUT: None,
    RefusalCode.BLOCKED_AMBIGUOUS_TASK: frozenset({"coder", "orchestrator"}),
    RefusalCode.BLOCKED_CANONICAL_REPO: frozenset({"coder", "orchestrator"}),
    RefusalCode.BLOCKED_BASELINE_DRIFT: frozenset(
        {"coder", "orchestrator", "reviewer"}
    ),
    RefusalCode.REFUSED_UNSUPPORTED: None,
    RefusalCode.PROVIDER_TRANSIENT: None,
    RefusalCode.INVALID_OUTPUT: None,
    RefusalCode.PARENT_HASH_MISMATCH: None,
    RefusalCode.SCOPE_VIOLATION: None,
    RefusalCode.CRITERIA_HASH_MISMATCH: frozenset({"screener", "screening-critic"}),
    RefusalCode.BATCH_INCOMPLETE: frozenset({"screener", "screening-critic"}),
    RefusalCode.IDENTITY_AMBIGUOUS: frozenset({"screener", "screening-critic"}),
    RefusalCode.BATCH_ID_MISMATCH: frozenset({"screener", "screening-critic"}),
    RefusalCode.SOURCE_MISSING: frozenset(
        {"extractor-a", "extractor-b", "extraction-critic"}
    ),
    RefusalCode.LOCATOR_UNRESOLVED: frozenset(
        {"extractor-a", "extractor-b", "extraction-critic"}
    ),
    RefusalCode.QUOTE_NOT_IN_SOURCE: frozenset(
        {"extractor-a", "extractor-b", "extraction-critic"}
    ),
    RefusalCode.ABSENCE_UNCLASSIFIED: frozenset(
        {"extractor-a", "extractor-b", "extraction-critic"}
    ),
    # Review/test codes carry no "Emitted by" column in the spec; the envelope
    # cross-checks them against the roles that plausibly host those duties.
    RefusalCode.REQUIREMENT_UNTRACEABLE: frozenset({"reviewer"}),
    RefusalCode.TEST_GATE_FAILED: frozenset({"tester", "orchestrator", "coder"}),
}


def allowed_emitter_roles(code: RefusalCode) -> frozenset[str] | None:
    """Return the roles allowed to emit ``code``; ``None`` means any role."""

    return _EMITTER_ROLES[code]


def render_refusals_doc() -> str:
    """Render ``docs/architecture/refusals.md``; kept in test-enforced parity."""

    registry_rows = {
        RefusalCode.BLOCKED_INPUT: ("any", "Required artifact missing/unreadable"),
        RefusalCode.BLOCKED_AMBIGUOUS_TASK: (
            "coder, orchestrator",
            "Task under-specified",
        ),
        RefusalCode.BLOCKED_CANONICAL_REPO: (
            "coder, orchestrator",
            "Toolkit sync obligation unmet",
        ),
        RefusalCode.BLOCKED_BASELINE_DRIFT: (
            "coder, orchestrator, reviewer",
            "Frozen baseline check failed",
        ),
        RefusalCode.REFUSED_UNSUPPORTED: (
            "any",
            "Declared-unsupported operation (E1/E2/E3)",
        ),
        RefusalCode.PROVIDER_TRANSIENT: (
            "adapter (any role)",
            (
                "Model/data provider unreachable, rate-limited, timed out, or "
                "context overflow. Retried by the adapter, never by the role; "
                "retry exhaustion surfaces to the human with the attempt count"
            ),
        ),
        RefusalCode.INVALID_OUTPUT: ("any", "Schema or invariant violation"),
        RefusalCode.PARENT_HASH_MISMATCH: ("any consumer", "Lineage broken"),
        RefusalCode.SCOPE_VIOLATION: (
            "any",
            "Attempted read/write outside read_glob/write_glob",
        ),
    }
    screening_rows = {
        RefusalCode.CRITERIA_HASH_MISMATCH: "criteria_sha256 ≠ protocol fingerprint",
        RefusalCode.BATCH_INCOMPLETE: "Decision coverage < 100%",
        RefusalCode.IDENTITY_AMBIGUOUS: (
            "Record identity unresolvable (title collision, DOI conflict)"
        ),
        RefusalCode.BATCH_ID_MISMATCH: "batch_id disagrees between batch and decisions",
    }
    extraction_rows = {
        RefusalCode.SOURCE_MISSING: "Required source text absent",
        RefusalCode.LOCATOR_UNRESOLVED: "Locator does not resolve in the source",
        RefusalCode.QUOTE_NOT_IN_SOURCE: "Quotation fails verbatim check",
        RefusalCode.ABSENCE_UNCLASSIFIED: (
            "A required field is absent without an absence state"
        ),
    }
    review_rows = {
        RefusalCode.REQUIREMENT_UNTRACEABLE: (
            "Diff contradicts or omits a governing requirement"
        ),
        RefusalCode.TEST_GATE_FAILED: "Declared gate command failed",
    }

    def table(rows: list[tuple[str, str, str | None]]) -> list[str]:
        if rows[0][2] is None:
            lines = ["| Code | Meaning |", "|---|---|"]
        else:
            lines = ["| Code | Emitted by | Meaning |", "|---|---|---|"]
        for code, meaning, emitted_by in rows:
            if emitted_by is None:
                lines.append(f"| `{code}` | {meaning} |")
            else:
                lines.append(f"| `{code}` | {emitted_by} | {meaning} |")
        return lines

    lines: list[str] = [
        "# Refusal registry (generated)",
        "",
        "<!-- GENERATED FILE — do not hand-edit; render via",
        f"     {render_refusals_doc.__module__}.render_refusals_doc().",
        "     Parity with the enum and the roles/ records is enforced by",
        "     tests/conformance/test_envelope.py -->",
        "",
        "Closed set of `Envelope@1` refusal codes (spec `02_envelope_and_refusals.md`",
        "§6). Adding a code requires editing the spec, the enum, and the roles that",
        "may emit it *in the same change*.",
        "",
        "## Policy: transient provider failures",
        "",
        "**The principle: provider failure is not empty success.** A rate limit, a",
        "timeout, a dropped connection, or a context overflow means the role's",
        "records are exactly as unresolved as before the call. Nothing is written,",
        "nothing is counted, and no batch decision silently moves from `PENDING` to",
        "`EXCLUDED`.",
        "",
        "- Provider failure is `PROVIDER_TRANSIENT`, never `BLOCKED_INPUT` (no",
        "  artifact is missing) and never `REFUSED` (nothing prohibited happened).",
        "- **The role never retries.** Backoff policy, budget ceilings, and",
        "  per-provider limits are adapter concerns. Retry exhaustion surfaces one",
        "  final envelope whose refusal detail carries the attempt count.",
        "- **Retries preserve identity.** `envelope_id` excludes timing, so the",
        "  same request against the same inputs produces the same logical envelope",
        "  whether it succeeded on the first attempt or the fourth.",
        "- **Partially completed batches are `PARTIAL`, not `PROVIDER_TRANSIENT`;**",
        "  the unfinished records keep their payload-neutral `PENDING` state.",
        "- **Other codes are never auto-retried.** `BLOCKED_INPUT`, `REFUSED`,",
        "  `SCOPE_VIOLATION`, and hash mismatches re-produce themselves.",
        "",
        "## Global",
        "",
        *table(
            [
                (code.value, registry_rows[code][1], registry_rows[code][0])
                for code in RefusalCode
                if code in registry_rows
            ]
        ),
        "",
        "## Screening",
        "",
        *table(
            [
                (code.value, screening_rows[code], None)
                for code in [
                    RefusalCode.CRITERIA_HASH_MISMATCH,
                    RefusalCode.BATCH_INCOMPLETE,
                    RefusalCode.IDENTITY_AMBIGUOUS,
                    RefusalCode.BATCH_ID_MISMATCH,
                ]
            ]
        ),
        "",
        "## Extraction",
        "",
        *table(
            [
                (code.value, extraction_rows[code], None)
                for code in [
                    RefusalCode.SOURCE_MISSING,
                    RefusalCode.LOCATOR_UNRESOLVED,
                    RefusalCode.QUOTE_NOT_IN_SOURCE,
                    RefusalCode.ABSENCE_UNCLASSIFIED,
                ]
            ]
        ),
        "",
        "## Review / test",
        "",
        *table(
            [
                (code.value, review_rows[code], None)
                for code in [
                    RefusalCode.REQUIREMENT_UNTRACEABLE,
                    RefusalCode.TEST_GATE_FAILED,
                ]
            ]
        ),
        "",
        "## Not a refusal — reviewed payload",
        "",
        "The review table below is *payload*, not part of this refusal registry:",
        "",
        "| Code | Meaning |",
        "|---|---|",
        "| `VERDICT_CHANGES_REQUESTED` | Reviewer requests repairs (payload, not a refusal) |",
        "",
        "`VERDICT_CHANGES_REQUESTED` is deliberately absent from the",
        "`RefusalCode` enum: a review verdict is data the consumer parses, not a",
        "transport refusal. It may never appear in an `envelope.refusal.code`; the",
        "validator rejects any attempt.",
        "",
        f"Registry revision: {len(RefusalCode)} codes.",
        "",
    ]
    return "\n".join(lines)
