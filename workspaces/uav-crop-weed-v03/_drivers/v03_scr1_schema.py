"""SCR1 decision-row schema contract — FROZEN TEMPLATE is normative.

The frozen PASS-1 template (v03_scr1_pass1_prompt_template.txt, sha 0c7f129d...)
defines the canonical per-record output schema as exactly:

    screening_id, decision, reason_code, confidence, one_line_support

Later waves added extra conventions (reason, criterion_refs, moderation_*
annotations). Extras are ALLOWED but never required. Variant key names that
carry canonical payloads are RECOGNIZED via ALIASES and TAGGED — downstream
readers call normalize_row(); evidence files are never rewritten to coerce
them (detect explicitly, never silently coerce).

Genuinely absent canonical fields classify as schema DEBT (value None + tag);
they are never fabricated. Non-numeric confidence strings ("high"/"medium")
are returned as None with a tag — no numeric value is invented for them.
"""

import json
import re
from pathlib import Path

CANONICAL_FIELDS = (
    "screening_id",
    "decision",
    "reason_code",
    "confidence",
    "one_line_support",
)
ALLOWED_EXTRAS = (
    "reason",
    "criterion_refs",
    "moderation_status",
    "moderation_redacted",
    "moderation_terms",
    "abstract_effectively_null",
)
DECISION_VOCAB = {"INCLUDE", "EXCLUDE", "PENDING"}

CRITERIA_SHA_PREFIX = "9ae1f97d"
PROMPT_SHA_PREFIX = "0c7f129d"

# variant key -> canonical field (payload copied verbatim; usage tagged)
REASON_CODE_ALIASES = {
    "exclusion_reason_code": "reason_code",
    "pending_reason_code": "reason_code",
    "inclusion_hint": "reason_code",
    "reason_CODE": "reason_code",  # observed key typo (1 row)
}

# embedded-code extraction from rationale text the screener wrote verbatim
_CODE_RE = re.compile(
    r"\s*((?:INC|EXC)-\d{2}|MODERATION_[A-Z_]+|GUARDRAIL_[A-Z_]+|"
    r"PENDING_[A-Z_]+|AMBIGUOUS_[A-Z_]+|WRONG_[A-Z_]+|OUTSIDE_[A-Z_]+|"
    r"OTHER_[A-Z_]+)"
)

# debt = template-conformance gap worth triage (severity ranked in reports)
DEBT_PREFIXES = (
    "CONFIDENCE_ABSENT",
    "CONFIDENCE_NON_NUMERIC",
    "CONFIDENCE_OUT_OF_RANGE",
    "RATIONALE_IN_REASON_ONLY",
    "REASON_CODE_ABSENT",
    "REASON_CODE_EMBEDDED_IN_TEXT",
    "ALIAS_REASON_CODE",
)
ADVISORY_PREFIXES = ("SUPPORT_OVER_25_WORDS", "UNKNOWN_KEYS")


def is_debt(tag: str) -> bool:
    return tag.split(":")[0] in DEBT_PREFIXES


def _wc(s) -> int:
    return len(re.findall(r"\S+", s or ""))


def normalize_row(row: dict):
    """Return (canonical_row, tags). Canonical values verbatim or None."""
    tags = []
    canon = {f: row.get(f) for f in CANONICAL_FIELDS}

    if canon["reason_code"] is None:
        for akey, cfield in REASON_CODE_ALIASES.items():
            if akey in row and row[akey] is not None:
                canon[cfield] = row[akey]
                tags.append(f"ALIAS_REASON_CODE:{akey}")
                break

    if canon["reason_code"] is None:
        rt = row.get("reason") or row.get("one_line_support") or ""
        m = _CODE_RE.match(str(rt))
        if m:
            canon["reason_code"] = m.group(1)
            tags.append("REASON_CODE_EMBEDDED_IN_TEXT")
        else:
            tags.append("REASON_CODE_ABSENT")

    if (
        canon["one_line_support"] is None
        and isinstance(row.get("reason"), str)
        and row["reason"].strip()
    ):
        tags.append("RATIONALE_IN_REASON_ONLY")

    if canon["one_line_support"] is not None and _wc(canon["one_line_support"]) > 25:
        tags.append(f"SUPPORT_OVER_25_WORDS:{_wc(canon['one_line_support'])}")

    c = canon["confidence"]
    if c is None:
        tags.append("CONFIDENCE_ABSENT")
    elif isinstance(c, bool) or not isinstance(c, (int, float)):
        tags.append(f"CONFIDENCE_NON_NUMERIC:{c!r}")
        canon["confidence"] = None
    elif not (0.0 <= float(c) <= 1.0):
        tags.append(f"CONFIDENCE_OUT_OF_RANGE:{c!r}")
        canon["confidence"] = None

    if canon["decision"] not in DECISION_VOCAB:
        tags.append(f"DECISION_OUT_OF_VOCAB:{canon['decision']!r}")

    unknown = sorted(
        set(row)
        - set(CANONICAL_FIELDS)
        - set(ALLOWED_EXTRAS)
        - set(REASON_CODE_ALIASES)
    )
    if unknown:
        tags.append("UNKNOWN_KEYS:" + ",".join(unknown))

    return canon, tags


def load_and_classify(n: int, fam: str, dec_dir) -> dict:
    """Classify one decision file. Tiers: VALID | DEBT | BAD.

    BAD     = structural: unparseable, header unattested, wrong row count,
              ID/order mismatch vs view, missing screening_id/decision,
              decision out of vocabulary (reconcile cannot proceed).
    DEBT    = decision-complete but canonical field absent / alias-named /
              non-numeric confidence / rationale only in `reason`.
    VALID   = every canonical field present and well-formed, no debt tags.
    prompt_template_sha256 absence in pre-pinning waves is era provenance
    debt (reported via header_info), never a validity failure.
    """
    dec_dir = Path(dec_dir)
    scr = dec_dir.parent
    views_dir = scr / "moderation_views"
    fp = dec_dir / f"batch_{n:04d}_decisions_{fam}.json"
    out = {
        "file": fp.name,
        "tier": "BAD",
        "structural": [],
        "debt": [],
        "advisory": [],
        "header": {},
        "prompt_sha_attested": False,
        "rows": 0,
    }
    if not fp.is_file():
        out["structural"].append("FILE_MISSING")
        return out
    try:
        doc = json.loads(fp.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001 - report, do not crash the sweep
        out["structural"].append(f"JSON_PARSE:{str(e)[:80]}")
        return out

    hdr = {
        "screener_id": doc.get("screener_id"),
        "criteria_sha256": str(doc.get("criteria_sha256", "")),
        "prompt_template_sha256": str(doc.get("prompt_template_sha256", "")),
    }
    out["header"] = hdr
    out["prompt_sha_attested"] = hdr["prompt_template_sha256"].startswith(
        PROMPT_SHA_PREFIX
    )
    if hdr["screener_id"] != fam:
        out["structural"].append(
            f"HEADER_UNATTESTED:screener_id={hdr['screener_id']!r}"
        )
    if not hdr["criteria_sha256"].startswith(CRITERIA_SHA_PREFIX):
        out["structural"].append("CRITERIA_SHA_MISSING_OR_BAD")

    rows = doc.get("decisions") or doc.get("rows")
    if not isinstance(rows, list):
        out["structural"].append("NO_ROWS_KEY")
        return out
    out["rows"] = len(rows)

    expected = None
    batch_fp = scr / f"batch_{n:04d}.json"
    try:
        expected = json.loads(batch_fp.read_text(encoding="utf-8"))["n_records"]
    except Exception:  # noqa: BLE001
        vp0 = views_dir / f"batch_{n:04d}.view.json"
        if vp0.is_file():
            expected = len(json.loads(vp0.read_text(encoding="utf-8"))["records"])
    if expected is not None and len(rows) != expected:
        out["structural"].append(f"ROW_COUNT:{len(rows)}!={expected}")

    vp = views_dir / f"batch_{n:04d}.view.json"
    if vp.is_file():
        view = json.loads(vp.read_text(encoding="utf-8"))
        ids = [r["screening_id"] for r in view["records"]]
        got = [r.get("screening_id") for r in rows]
        if got != ids:
            out["structural"].append("ID_ORDER_MISMATCH_VS_VIEW")

    for i, r in enumerate(rows):
        if not isinstance(r, dict) or not r.get("screening_id"):
            out["structural"].append(f"ROW_{i}_MISSING_SCREENING_ID")
            continue
        _canon, tags = normalize_row(r)
        hard = [t for t in tags if t.startswith("DECISION_OUT_OF_VOCAB")]
        if hard:
            out["structural"].append(f"ROW_{i}_{hard[0]}")
        debt_tags = [t for t in tags if is_debt(t)]
        adv = [t for t in tags if t.startswith(ADVISORY_PREFIXES)]
        if debt_tags or adv:
            out["debt"].append(
                {
                    "row": i,
                    "screening_id": r.get("screening_id"),
                    "debt": debt_tags,
                    "advisory": adv,
                }
            )

    if out["structural"]:
        out["tier"] = "BAD"
    elif out["debt"]:
        out["tier"] = "DEBT"
    else:
        out["tier"] = "VALID"
    return out
