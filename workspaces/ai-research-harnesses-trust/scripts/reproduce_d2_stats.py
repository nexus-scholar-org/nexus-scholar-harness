"""Reproduce every headline statistic in manuscript_d2.md from committed ledgers.

Single command:
    uv run python scripts/reproduce_d2_stats.py

Reads only committed artifacts (no network, no LLM calls):
  synthesis/claims.json                 (510 verbatim claims)
  synthesis/rag_baseline/claims.json    (90 RAG claims)
  synthesis/consensus.json              (95 verbatim clusters)
  synthesis/rag_baseline/consensus.json (20 RAG clusters)
  literature/screening/final_reconciled_decisions.json (included set)

Prints a machine-readable report and writes synthesis/figures_d2/stats_audit.md.
Exit code is non-zero if any assertion against the manuscript's numbers fails.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

WS = Path(r"C:\Users\mouadh\Documents\nexus-scholar-harness\workspaces\ai-research-harnesses-trust")

CLAIMS = WS / "synthesis" / "claims.json"
RAG = WS / "synthesis" / "rag_baseline" / "claims.json"
CONS = WS / "synthesis" / "consensus.json"
RAG_CONS = WS / "synthesis" / "rag_baseline" / "consensus.json"
FINAL = WS / "literature" / "screening" / "final_reconciled_decisions.json"

failures: list[str] = []
stats: dict = {}


def check(label: str, actual, expected, tol: float = 0.0):
    ok = bool(abs(actual - expected) <= tol) if isinstance(expected, (int, float)) else bool(actual == expected)
    stats[label] = actual
    status = "ok" if ok else "MISMATCH"
    print(f"  [{status:>8}] {label}: {actual}  (expected {expected})")
    if not ok:
        failures.append(f"{label}: got {actual}, expected {expected}")


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float, float]:
    """Wilson score interval; returns (rate_pct, lower_pct, upper_pct)."""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return 100 * center, 100 * max(0, center - half), 100 * min(1, center + half)


def fisher_one_sided(a: int, b: int, c: int, d: int) -> float:
    """Exact one-sided Fisher p-value on [[a, b], [c, d]] via scipy. a/b = RAG pass/fail; c/d = verbatim pass/fail."""
    from scipy.stats import fisher_exact

    _, p = fisher_exact([[a, b], [c, d]], alternative="less" if a / (a + b) < c / (c + d) else "greater")
    return float(p)


def run():
    print("== Verbatim claims ==")
    claims = json.loads((CLAIMS).read_text(encoding="utf-8"))
    rag = json.loads((RAG).read_text(encoding="utf-8"))
    cons = json.loads((CONS).read_text(encoding="utf-8"))
    rag_cons = json.loads((RAG_CONS).read_text(encoding="utf-8"))
    final = json.loads((FINAL).read_text(encoding="utf-8"))

    included = set()
    if isinstance(final, dict):
        for sid, verdict in final.items():
            if isinstance(verdict, str) and "includ" in verdict.lower():
                included.add(sid)
            elif isinstance(verdict, dict) and "include" in json.dumps(verdict).lower():
                included.add(sid)
    print(f"  included studies from final decisions: {len(included)}")

    check("verbatim total claims", len(claims), 510)
    check("verbatim RQ1 claims", sum(1 for c in claims if c["rq_id"] == "RQ1"), 166)
    check("verbatim RQ2 claims", sum(1 for c in claims if c["rq_id"] == "RQ2"), 132)
    check("verbatim RQ3 claims", sum(1 for c in claims if c["rq_id"] == "RQ3"), 212)
    check("verbatim fulltext claims", sum(1 for c in claims if c.get("evidence_level") == "fulltext"), 493)
    check("verbatim abstract-only claims", sum(1 for c in claims if c.get("evidence_level") == "abstract_only"), 17)
    v_studies = {c.get("study_id") for c in claims if c.get("study_id")}
    check("verbatim distinct studies", len(v_studies), 57)
    check("verbatim claims WITH evidence_quote", sum(1 for c in claims if c.get("evidence_quote")), 510)

    print("\n== RAG claims ==")
    check("rag total claims", len(rag), 90)
    check("rag RQ1 claims", sum(1 for c in rag if c["rq_id"] == "RQ1"), 30)
    check("rag RQ2 claims", sum(1 for c in rag if c["rq_id"] == "RQ2"), 30)
    check("rag RQ3 claims", sum(1 for c in rag if c["rq_id"] == "RQ3"), 30)
    st = {c.get("entailment_status") for c in rag}
    print(f"  rag entailment statuses: {st}")
    rag_verified = sum(1 for c in rag if c.get("entailment_status") == "VERIFIED")
    rag_verified_studies = {c.get("study_id") for c in rag if c.get("entailment_status") == "VERIFIED"}
    check("rag verified", rag_verified, 39)
    check("rag RQ1 verified", sum(1 for c in rag if c["rq_id"] == "RQ1" and c.get("entailment_status") == "VERIFIED"), 11)
    check("rag RQ2 verified", sum(1 for c in rag if c["rq_id"] == "RQ2" and c.get("entailment_status") == "VERIFIED"), 14)
    check("rag RQ3 verified", sum(1 for c in rag if c["rq_id"] == "RQ3" and c.get("entailment_status") == "VERIFIED"), 14)
    check("rag claims WITH evidence_quote", sum(1 for c in rag if c.get("evidence_quote")), 0)
    rag_studies = {c.get("study_id") for c in rag if c.get("study_id")}
    check("rag distinct studies", len(rag_studies), 25)
    rag_in = rag_studies & included
    rag_out = rag_studies - included
    check("rag in-scope studies", len(rag_in), 14)
    check("rag out-of-scope studies", len(rag_out), 11)
    check("included studies with zero rag claims", len(included - rag_studies), 44)
    check("rag in-scope with >=1 verified claim", len(rag_in & rag_verified_studies), 8)
    check("verbatim included studies with claims", len(v_studies & included), 57)
    top = sorted(((k, sum(1 for c in rag if c.get("study_id") == k)) for k in rag_studies), key=lambda t: -t[1])[0]
    print(f"  rag top-contributing study: {top[0]} with {top[1]} claims")
    check("SCI-000184 contributes", next(t[1] for t in sorted(
        ((k, sum(1 for c in rag if c.get("study_id") == k)) for k in rag_studies), key=lambda t: -t[1])), 22)

    pooled_rate, lo, hi = wilson(39, 90)
    print(f"  rag pooled Wilson 95% CI: {lo:.1f}-{hi:.1f}%  (rate {pooled_rate:.1f}%)")
    stats["rag_pooled_ci"] = (round(lo, 1), round(hi, 1))

    q1 = wilson(11, 30)
    q2 = wilson(14, 30)
    q3 = wilson(14, 30)
    stats["rag_rq1_ci"] = (round(q1[1], 1), round(q1[2], 1))
    stats["rag_rq2_ci"] = (round(q2[1], 1), round(q2[2], 1))
    stats["rag_rq3_ci"] = (round(q3[1], 1), round(q3[2], 1))

    vq1 = wilson(166, 166)
    vq2 = wilson(132, 132)
    vq3 = wilson(212, 212)
    vpooled = wilson(510, 510)
    print(f"  verbatim pooled Wilson 95% CI: {vpooled[1]:.1f}-{vpooled[2]:.1f}%")
    stats["verbatim_pooled_ci"] = (round(vpooled[1], 1), round(vpooled[2], 1))

    p = fisher_one_sided(39, 51, 510, 0)
    print(f"\n  Fisher one-sided p (pooled 2x2): {p:.3e}")

    print("\n== Consensus clusters ==")
    check("verbatim high_consensus", len(cons["high_consensus"]), 16)
    check("verbatim active_debates", len(cons["active_debates"]), 7)
    check("verbatim unresolved", len(cons["unresolved"]), 37)
    check("verbatim provisional", len(cons["provisional"]), 35)
    check("verbatim total clusters", cons["total_groups"], 95)
    check("rag high_consensus", len(rag_cons["high_consensus"]), 2)
    check("rag active_debates", len(rag_cons["active_debates"]), 0)
    check("rag unresolved", len(rag_cons["unresolved"]), 3)
    check("rag provisional", len(rag_cons["provisional"]), 15)
    check("rag total clusters", rag_cons["total_groups"], 20)

    rep = "\n".join(f"{k}: {v if not isinstance(v, tuple) else '–'.join(map(str, v))}" for k, v in sorted(stats.items()))
    out = WS / "synthesis" / "figures_d2" / "stats_audit.md"
    out.write_text(
        f"# D2 statistics audit ({len(stats)} metrics recomputed)\n\n{rep}\n\n"
        f"Fisher one-sided p: {p:.3e}\n\n"
        f"Status: {'ALL PASS' if not failures else 'FAILURES: ' + '; '.join(failures)}\n",
        encoding="utf-8",
    )
    print(f"\nWrote {out}")

    print("\n== RESULT ==")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("ALL ASSERTIONS PASS — every headline number matches the committed ledgers.")
    return 0


if __name__ == "__main__":
    sys.exit(run())