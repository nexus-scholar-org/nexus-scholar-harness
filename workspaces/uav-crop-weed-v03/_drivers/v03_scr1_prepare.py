"""SCR1 PREP — screening batch preparation from the r3e definitive corpus.

Builds a deterministic seeded set of triage batches from the r3e deduped reps
(14,150), freezes the criteria snapshot (SHA256), and writes the Pass-1 prompt
template fingerprint log (model id, temperature 0.1, template SHA256).

Blinding/order discipline:
  - modern seeded shuffle (Fisher-Yates via random.Random(seed)) so no batch
    accidentally encodes provider/leg ordering or dedup-cluster adjacency;
  - batches are self-contained for agent consumption (no round metadata, no
    provider cross-talk beyond what each record carries).

Outputs (all new files, v03_scr1_*):
  - calibration_v03/v03_scr1_SCREENING_CRITERIA_frozen_ref.md  (copy of workspace criteria)
  - calibration_v03/screening_scr1/batch_0001.json .. batch_0283.json
  - calibration_v03/v03_scr1_prep_manifest.json  (counts, sha hashes, guardrail census)
  - _drivers/SCREEN1_pass1_prompt_template.txt
  - _drivers/v03_scr1_prep_summary.json
"""

import hashlib
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CAL = ROOT / "workspaces" / "uav-crop-weed-v03" / "calibration_v03"
DRIVERS = ROOT / "workspaces" / "uav-crop-weed-v03" / "_drivers"

DATE_TAG = "20261018"  # screening execution date
CORPUS_TAG = "20261017"  # r3 corpus creation date (artifact filenames unchanged)
SESSION = "UAV-SCREEN-SCR1-20261018"
BATCH_SIZE = 50
SEED = 20261018
MODEL_ID = "opencode/glm-5.3-flash-free"
TEMPERATURE = 0.1

UAV_TERM = re.compile(
    r"\b(uav|drone|drones|unmanned aero|aerial| remotely piloted|remote.{0,3}pilot)",
    re.I,
)
WEED_TERM = re.compile(
    r"\b(weed|weeds|weed.{0,12}(detect|map|segment|classif)|plant detection)", re.I
)


def sha256_text(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def load_reps():
    reps = json.loads(
        (CAL / f"v03_r3e_{CORPUS_TAG}_deduped.json").read_text(encoding="utf-8")
    )["documents"]
    return reps


def screen_id(rep):
    wid = rep.get("workspace_id") or ""
    if wid:
        return wid
    return f"SCR1-ASSIGNED-{rep.get('cluster_id') or 'unknown'}"


PLACEHOLDER_MARKERS = (
    "placeholder",
    "not available",
    "no abstract",
    "abstract not",
    "truncated",
    "n/a",
    "publisher's website",
    "available on the publisher",
    "no suitable abstract",
    "copyright",
    "reproduced with permission",
)
WEED_TITLE = re.compile(
    r"weed|crop|herbicid|maize|corn|wheat|rice|soybean|sorghum|cotton|potato|"
    r"vineyard|orchard|sugar beet|paddy|sunflower|barley|canola|rapeseed",
    re.I,
)
UAV_TITLE = re.compile(r"uav|uas|drone|unmanned aero|aerial|rotor|quad?rotor", re.I)


def effective_abstract_null(abstract):
    a = str(abstract or "").strip()
    if not a:
        return True
    low = a.lower()
    if any(m in low for m in PLACEHOLDER_MARKERS):
        return True
    if len(low) < 160 and not (WEED_TITLE.search(low) and UAV_TITLE.search(low)):
        return True
    return False


def compact_rep(rep):
    ext = str(rep.get("external_ids") or "")
    doi = None
    m = re.search(r"10\.\d{4,9}/[^\s',']+", ext.lower())
    if m:
        doi = m.group(0).rstrip("',")
    ax = re.search(r"arxiv_id='([^']+)'", ext)
    providers = rep.get("provider")
    if isinstance(providers, (list, tuple)):
        providers = list(providers)
    return {
        "screening_id": screen_id(rep),
        "title": rep.get("title") or "",
        "year": rep.get("year"),
        "providers": providers,
        "doi": doi,
        "arxiv_id": ax.group(1) if ax else None,
        "abstract": (rep.get("abstract") or None),
        "abstract_effectively_null": effective_abstract_null(rep.get("abstract")),
    }


def main():
    reps = load_reps()
    print(f"LOADED reps: {len(reps)}", flush=True)

    # Freeze criteria snapshot.
    crit_src = ROOT / "workspaces" / "uav-crop-weed-v03" / "SCREENING_CRITERIA.md"
    crit_text = crit_src.read_text(encoding="utf-8")
    crit_hash = sha256_text(crit_text)
    (CAL / "v03_scr1_SCREENING_CRITERIA_frozen_ref.md").write_text(
        crit_text, encoding="utf-8"
    )

    # Prompt template (fixed Pass-1;text hashed into the log).
    template = """PASS-1 TRIAGE (agent suggestions only; a human research lead will confirm every decision)

You are a PASS-1 SUGGESTION screener for a scoping review on reliability and
generalization in UAV crop-weed mapping. For each record in the supplied batch,
read TITLE (and ABSTRACT when present) and suggest exactly one decision:

  "INCLUDE"  - likely satisfies INC-01..INC-03 (primary empirical method study
               or dataset/benchmark report on UAV crop/weed detection/segmenta-
               tion/classification/spatial weed mapping, 2020-2026-in-window,
               English in scope). Examples include preprints, conference papers,
               and dataset reports. Mixed-platform studies are includable when
               UAV results are separable. Method studies evaluated on pre-2020
               UAV datasets are eligible.
  "EXCLUDE"  - identify the single best-matching criterion code:
               WRONG_PLATFORM (satellite/ground-robot/handheld/lab/pot imaging
                 without separable UAV mapping evidence),
               WRONG_TASK (UAV navigation/SLAM, yield-only, crop disease/pest,
                 wildlife, lodging, phenotyping, non-agricultural vegetation
                 such as aquatic weeds/forestry/urban turfgrass without a
                 separable agricultural crop/weed mapping task),
               WRONG_REPORT_TYPE (confirmed review/editorial/commentary/
                 protocol-only/standalone abstract; abstract=null is NEVER this
                 reason unless the title itself indicates a review/editorial),
               OUTSIDE_DATE_LANGUAGE (before 2020 or non-English).
  "PENDING"  - you cannot judge from the available signal; typically when the
               abstract is null AND the title is ambiguous, or when the record
               is UAV-adjacent and weed-adjacent but the mapping task is not
               evident from title/abstract.

HARD GUARDRAIL (never violate):
  If abstract is null/missing, you may NEVER auto-exclude on OUTSIDE_DATE_
  LANGUAGE or WRONG_PLATFORM grounds when the TITLE simultaneously contains a
  UAV/aerial term AND a weed/crop-protection term. Mark such records "PENDING"
  with reason "GUARDRAIL_TITLE_ONLY_UAV_WEED".

RULES:
  - Decide from the record's own signal only. No external knowledge about the
    corpus, no statistical priors about batch composition.
  - Do not inflate evidence; if the title carries no weed/crop-protection or
    UAV signal AND the abstract does not either, EXCLUDE with the closest code.
  - PENDING is the correct, non-cowardly answer for genuinely ambiguous
    title-only records; do not over-use it for records with rich abstracts.
  - Output STRICT JSON: {"decisions": [{"screening_id": "...", "decision":
    "INCLUDE"|"EXCLUDE"|"PENDING", "reason_code": "<CODE or inc hint INC-01/02/03>",
    "confidence": 0.0-1.0, "one_line_support": "<=25 words quoting the decisive signal"}]}
  - Return a decision line for EVERY record, in the same order.

ANTHROPIC BIAS GUARD: treat every record independently; the fact that a batch
may contain many clearly off-topic records does not make borderline records
more likely to be off-topic.

"""
    pth = DRIVERS / "v03_scr1_pass1_prompt_template.txt"
    pth.write_text(template, encoding="utf-8")
    prompt_hash = sha256_text(template)

    # Compact, shuffle, batch.
    compact = [compact_rep(r) for r in reps]
    ids = [c["screening_id"] for c in compact]
    if len({i for i in ids}) != len(ids):
        print(
            "DUPLICATE screening ids detected; de-duping by first occurrence",
            flush=True,
        )
        seen = set()
        uniq = []
        for c in compact:
            if c["screening_id"] not in seen:
                seen.add(c["screening_id"])
                uniq.append(c)
        compact = uniq
    rng = random.Random(SEED)
    rng.shuffle(compact)

    outdir = CAL / "screening_scr1"
    outdir.mkdir(exist_ok=True)
    n_batches = (len(compact) + BATCH_SIZE - 1) // BATCH_SIZE
    batch_index = {}
    guardrail_census = 0
    abstract_null_total = 0
    for b in range(n_batches):
        chunk = compact[b * BATCH_SIZE : (b + 1) * BATCH_SIZE]
        for c in chunk:
            if c["abstract_effectively_null"]:
                abstract_null_total += 1
                if UAV_TERM.search(c["title"]) and WEED_TERM.search(c["title"]):
                    guardrail_census += 1
        payload = {
            "batch_id": f"batch_{b + 1:04d}",
            "session": SESSION,
            "criteria_sha256": crit_hash,
            "prompt_template_sha256": prompt_hash,
            "model_id": MODEL_ID,
            "temperature": TEMPERATURE,
            "n_records": len(chunk),
            "records": chunk,
        }
        fp = outdir / f"batch_{b + 1:04d}.json"
        fp.write_text(
            json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        batch_index[fp.name] = {
            "records": len(chunk),
            "sha256": sha256_text(fp.read_text(encoding="utf-8")),
        }

    manifest = {
        "session": SESSION,
        "source_corpus": f"v03_r3e_{CORPUS_TAG}_deduped.json",
        "n_reps": len(reps),
        "n_compacted": len(compact),
        "batch_size": BATCH_SIZE,
        "n_batches": n_batches,
        "shuffle_seed": SEED,
        "criteria_frozen_sha256": crit_hash,
        "criteria_frozen_ref": "v03_scr1_SCREENING_CRITERIA_frozen_ref.md",
        "prompt_template_sha256": prompt_hash,
        "prompt_template_ref": str(pth.relative_to(ROOT)),
        "model_id": MODEL_ID,
        "temperature": TEMPERATURE,
        "abstract_null_total": abstract_null_total,
        "abstract_null_guardrail_titles": guardrail_census,
        "batch_format_version": "v2_effective_null_flag",
        "batch_index": batch_index,
    }
    (CAL / "v03_scr1_prep_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    summary = {
        key: manifest[key]
        for key in (
            "session",
            "n_reps",
            "n_compacted",
            "n_batches",
            "criteria_frozen_sha256",
            "prompt_template_sha256",
            "abstract_null_total",
            "abstract_null_guardrail_titles",
        )
    }
    (DRIVERS / "v03_scr1_prep_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2), flush=True)
    print(f"WROTE {n_batches} batches to {outdir}", flush=True)


if __name__ == "__main__":
    main()
