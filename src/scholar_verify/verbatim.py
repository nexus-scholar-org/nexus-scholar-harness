"""Verbatim attribution verifier for claims against extracted fulltext or abstracts.

Implements character-window and token n-gram coverage algorithms with glyph/NFKC
normalization to verify exact quotes without relying on stochastic LLM-as-a-judge.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def normalize_scientific_text(text: str) -> str:
    """Normalize text using NFKC, strip zero-width spaces, unify dashes and quotes."""
    if not text:
        return ""
    # NFKC normalizes compatibility characters, ligatures (fi -> fi), etc.
    res = unicodedata.normalize("NFKC", str(text))
    # Replace zero-width spaces and soft hyphens
    res = re.sub(r"[\u200B-\u200D\uFEFF\u00AD]", "", res)
    # Normalize bullet points and list glyphs
    res = re.sub(r"[•●○■▪◆▶►–—―−]", "-", res)
    # Normalize quotes
    res = res.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'").replace("«", '"').replace("»", '"')
    # Join hyphenated linebreaks: e.g. "sys-\n tem" -> "system"
    res = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", res)
    # Collapse multiple whitespaces into a single space
    res = re.sub(r"\s+", " ", res)
    return res.strip()


def char_window_coverage(quote: str, source_text: str, window_size: int = 8, step: int = 4) -> float:
    """Calculates fraction of sliding character windows from quote found in source."""
    norm_q = normalize_scientific_text(quote).lower()
    norm_s = normalize_scientific_text(source_text).lower()

    if not norm_q or not norm_s:
        return 0.0

    if len(norm_q) <= window_size:
        return 1.0 if norm_q in norm_s else 0.0

    windows = [
        norm_q[i : i + window_size]
        for i in range(0, len(norm_q) - window_size + 1, step)
    ]
    if not windows:
        return 0.0

    matches = sum(1 for w in windows if w in norm_s)
    return matches / len(windows)


def token_ngram_coverage(quote: str, source_text: str, n: int = 6, step: int = 3) -> float:
    """Calculates fraction of sliding token n-grams from quote found in source."""
    tokens_q = re.findall(r"\w+", normalize_scientific_text(quote).lower())
    norm_s = " " + " ".join(re.findall(r"\w+", normalize_scientific_text(source_text).lower())) + " "

    if not tokens_q:
        return 0.0

    if len(tokens_q) < n:
        sub_str = " " + " ".join(tokens_q) + " "
        return 1.0 if sub_str in norm_s else 0.0

    ngrams = [
        " " + " ".join(tokens_q[i : i + n]) + " "
        for i in range(0, len(tokens_q) - n + 1, step)
    ]
    if not ngrams:
        return 0.0

    matches = sum(1 for ng in ngrams if ng in norm_s)
    return matches / len(ngrams)


@dataclass
class VerbatimResult:
    claim_id: str
    study_id: str
    evidence_quote: str
    char_coverage: float
    token_coverage: float
    max_coverage: float
    is_verified: bool
    source_file: Optional[str] = None
    failure_reason: Optional[str] = None


class VerbatimClaimVerifier:
    """Verifies synthesis claims against extracted markdown full-texts or abstracts."""

    def __init__(self, threshold: float = 0.90, window_size: int = 8, token_n: int = 6):
        self.threshold = threshold
        self.window_size = window_size
        self.token_n = token_n

    def verify_quote(self, quote: str, source_text: str) -> Tuple[bool, float, float]:
        """Check if quote is verbatim backed by source text."""
        char_cov = char_window_coverage(quote, source_text, window_size=self.window_size)
        token_cov = token_ngram_coverage(quote, source_text, n=self.token_n)
        max_cov = max(char_cov, token_cov)
        return (max_cov >= self.threshold, char_cov, token_cov)

    def verify_claims_ledger(
        self,
        claims: List[Dict[str, Any]],
        source_texts: Dict[str, str],
    ) -> Tuple[List[VerbatimResult], Dict[str, Any]]:
        """Verify a collection of claims against mapping of study_id -> source_text."""
        results: List[VerbatimResult] = []
        verified_count = 0

        for i, claim in enumerate(claims):
            cid = str(claim.get("claim_id") or claim.get("workspace_id") or f"CLAIM-{i+1:04d}")
            sid = str(claim.get("study_id") or claim.get("workspace_id") or "")
            quote = claim.get("evidence_quote") or ""

            if not quote:
                results.append(
                    VerbatimResult(
                        claim_id=cid,
                        study_id=sid,
                        evidence_quote="",
                        char_coverage=0.0,
                        token_coverage=0.0,
                        max_coverage=0.0,
                        is_verified=False,
                        failure_reason="MISSING_QUOTE",
                    )
                )
                continue

            src = source_texts.get(sid, "")
            if not src:
                results.append(
                    VerbatimResult(
                        claim_id=cid,
                        study_id=sid,
                        evidence_quote=quote,
                        char_coverage=0.0,
                        token_coverage=0.0,
                        max_coverage=0.0,
                        is_verified=False,
                        failure_reason="SOURCE_TEXT_NOT_FOUND",
                    )
                )
                continue

            passed, c_cov, t_cov = self.verify_quote(quote, src)
            if passed:
                verified_count += 1

            results.append(
                VerbatimResult(
                    claim_id=cid,
                    study_id=sid,
                    evidence_quote=quote,
                    char_coverage=c_cov,
                    token_coverage=t_cov,
                    max_coverage=max(c_cov, t_cov),
                    is_verified=passed,
                    failure_reason=None if passed else "INSUFFICIENT_COVERAGE",
                )
            )

        total = len(claims)
        metrics = {
            "total_claims": total,
            "verified_claims": verified_count,
            "failed_claims": total - verified_count,
            "verification_rate": (verified_count / total) if total > 0 else 1.0,
            "threshold": self.threshold,
        }
        return results, metrics
