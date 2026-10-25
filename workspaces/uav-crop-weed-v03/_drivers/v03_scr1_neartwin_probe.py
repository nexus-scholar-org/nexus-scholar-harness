# Task #5: near-twin dedup gap probe for v03_r3e calibration corpus.
# Pass 1: exact normalized-title equality. Pass 2: token-set Jaccard >= 0.9
# (excluding pass-1-linked docs). Family map from A1/A2 screener lanes.
import json
import re
import string
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]  # workspaces/uav-crop-weed-v03
CAL = BASE / "calibration_v03"
CORPUS = CAL / "v03_r3e_20261017_deduped.json"
DECISIONS_DIR = CAL / "screening_scr1" / "decisions"
OUT = CAL / "v03_scr1_neartwin_probe.json"

_SCI_RE = re.compile(r"SCI-(\d+)")
_TRANS = str.maketrans("", "", string.punctuation)


def normalize_title(t: str) -> str:
    t = (t or "").lower().translate(_TRANS)
    return re.sub(r"\s+", " ", t).strip()


def norm_tokens(t: str):
    return set(normalize_title(t).split())


def main() -> None:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    docs = corpus["documents"]
    n = len(docs)
    titles = [d.get("title") or "" for d in docs]
    norm_titles = [normalize_title(t) for t in titles]
    tokens = [norm_tokens(t) for t in titles]
    clusters = [d.get("cluster_id") for d in docs]
    providers = [d.get("provider") or "?" for d in docs]

    # ---- lanes from A1/A2 decision files ----
    screens: dict[str, dict[str, str]] = {}  # screening_id -> {"A1": dec, "A2": dec}
    for path in sorted(DECISIONS_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        sid = payload.get("screener_id")
        if sid not in ("A1", "A2"):
            continue
        for row in payload.get("decisions") or []:
            scr = row.get("screening_id") or ""
            m = _SCI_RE.fullmatch(scr.strip())
            if not m:
                continue
            screens.setdefault(scr, {})[sid] = (row.get("decision") or "").upper()

    lang = {}  # doc index -> lane
    for idx in range(n):
        scr = f"SCI-{idx + 1:06d}"
        pair = screens.get(scr, {})
        a1, a2 = pair.get("A1"), pair.get("A2")
        if a1 == "INCLUDE" and a2 == "INCLUDE":
            lang[idx] = "mutual-incl"
        elif a1 == "EXCLUDE" and a2 == "EXCLUDE":
            lang[idx] = "mutual-exc"
        else:
            lang[idx] = "other"

    # ---- pass 1: exact normalized-title equality ----
    by_norm: dict[str, list[int]] = {}
    for i, nt in enumerate(norm_titles):
        if nt:
            by_norm.setdefault(nt, []).append(i)

    def pairs_from_groups(groups: list[list[int]]) -> list[tuple[int, int]]:
        out = []
        for g in groups:
            for x in range(len(g)):
                for y in range(x + 1, len(g)):
                    out.append((g[x], g[y]))
        return out

    all_pairs = set(pairs_from_groups(list(by_norm.values())))
    pass1_pairs = sorted(all_pairs)

    # ---- pass 2: token-set Jaccard >= 0.9, excluding pass-1 pairs ----
    # blocking by 3-token prefix signature of sorted tokens to keep O(n~) sane
    from itertools import combinations

    sig: dict[int, set[int]] = {}
    for i, toks in enumerate(tokens):
        sig[i] = set()
        for t in sorted(toks)[:3] if toks else []:
            sig[i].add(hash(t))

    pass2_pairs: list[tuple[int, int]] = []
    seen2 = set()
    # block on shared rare-ish tokens: use each token minus stopwordsless trivial filter;
    # simple inverted index on tokens length>=4
    inv: dict[str, list[int]] = {}
    for i, toks in enumerate(tokens):
        for t in toks:
            if len(t) >= 4:
                inv.setdefault(t, []).append(i)
    cand = set()
    for posting in inv.values():
        if len(posting) < 2 or len(posting) > 60:
            continue  # skip ultra-common tokens
        for a, b in combinations(sorted(posting), 2):
            cand.add((a, b))
    for a, b in sorted(cand):
        ta, tb = tokens[a], tokens[b]
        if not ta or not tb:
            continue
        inter = len(ta & tb)
        if inter == 0:
            continue
        jac = inter / len(ta | tb)
        if jac >= 0.9 and (a, b) not in all_pairs:
            seen2.add((a, b))
    pass2_pairs = sorted(seen2)

    # ---- pair analysis ----
    def cluster_key(i: int) -> object:
        cid = clusters[i]
        # null-safe: use sentinel for missing
        return cid if cid is not None else ("__none__", i)

    analysis = []
    for lane_pairs, tag in ((pass1_pairs, 1), (pass2_pairs, 2)):
        for a, b in lane_pairs:
            ca, cb = clusters[a], clusters[b]
            status = (
                "shared-cluster"
                if (ca is not None and ca == cb)
                else (
                    "missing-cluster-id"
                    if (ca is None or cb is None)
                    else "different-clusters"
                )
            )
            la, lb = lang[a], lang[b]
            if {la, lb} <= {"mutual-incl", "mutual-exc"} and la != lb:
                lane_cat = "INCLUDE-split"
            elif la == "mutual-exc" and lb == "mutual-exc":
                lane_cat = "both-mutual-EXCLUDE"
            elif la == "mutual-incl" and lb == "mutual-incl":
                lane_cat = "both-mutual-INCLUDE"
            else:
                lane_cat = "other"
            analysis.append(
                {
                    "pass": tag,
                    "a": a,
                    "b": b,
                    "jaccard": round(
                        len(tokens[a] & tokens[b]) / len(tokens[a] | tokens[b]), 4
                    ),
                    "cluster_status": status,
                    "lane": lane_cat,
                    "cluster_a": ca,
                    "cluster_b": cb,
                }
            )

    cov = [x for x in analysis if x["cluster_status"] != "missing-cluster-id"]
    missed = [x for x in cov if x["cluster_status"] == "different-clusters"]

    stats = {
        "corpus_docs": n,
        "pairs_pass1_exact": len(pass1_pairs),
        "pairs_pass2_jaccard": len(pass2_pairs),
        "pairs_total": len(analysis),
        "cluster_coverage": {
            "already_shared_cluster": sum(
                1 for x in cov if x["cluster_status"] == "shared-cluster"
            ),
            "different_clusters_dedup_missed": len(missed),
            "missing_cluster_id": sum(
                1 for x in analysis if x["cluster_status"] == "missing-cluster-id"
            ),
        },
        "missed_lane_distribution": dict(Counter(x["lane"] for x in missed)),
        "missed_by_pass": dict(Counter(x["pass"] for x in missed)),
        "provider_pair_labels_missed": {
            " | ".join(sorted(k)): v
            for k, v in Counter(
                tuple(sorted((providers[x2["a"]], providers[x2["b"]]))) for x2 in missed
            ).items()
        },
    }

    # provider labels of all pair members
    prov_counter = Counter()
    for x in analysis:
        prov_counter[tuple(sorted((providers[x["a"]], providers[x["b"]])))] += 1
    stats["provider_pair_labels_all"] = {
        " | ".join(sorted(k)): v for k, v in prov_counter.items()
    }

    examples = []
    for x in sorted(missed, key=lambda z: (-z["pass"], z["lane"] != "INCLUDE-split"))[
        :20
    ]:
        a, b = x["a"], x["b"]
        da, db = docs[a].get("doi"), docs[b].get("doi")
        examples.append(
            {
                "pass": x["pass"],
                "jaccard": x["jaccard"],
                "title_a": titles[a],
                "title_b": titles[b],
                "doi_a": da,
                "doi_b": db,
                "lanes": f"{lang[a]} | {lang[b]}",
                "cluster_a": x["cluster_a"],
                "cluster_b": x["cluster_b"],
                "providers": f"{providers[a]} | {providers[b]}",
            }
        )
    # dangerous split pairs
    split_pairs = [x for x in missed if x["lane"] == "INCLUDE-split"]
    impact = {
        "include_split_missed_pairs": len(split_pairs),
        "note": "INCLUDE-split pairs = one member on mutual-INCLUDE lane, other on mutual-EXCLUDE lane; if both are the same work and dedup failed to merge them, PRISMA include/exclude counts are corrupted (same work double-counted on opposite sides).",
        "include_split_examples": [
            {
                "pass": x["pass"],
                "title_a": titles[x["a"]],
                "title_b": titles[x["b"]],
                "cluster_a": x["cluster_a"],
                "cluster_b": x["cluster_b"],
            }
            for x in split_pairs[:10]
        ],
    }

    out = {
        "task": "v03 scr1 near-twin dedup gap probe (#5)",
        "stats": stats,
        "examples_up_to_20": examples,
        "include_split_impact": impact,
    }
    OUT.write_text(
        json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(
        f"docs={n} pass1_exact={len(pass1_pairs)} pass2_jaccard={len(pass2_pairs)} total={len(analysis)}"
    )
    print(
        f"shared_cluster={stats['cluster_coverage']['already_shared_cluster']} "
        f"missed_diff_clusters={len(missed)} missing_cid={stats['cluster_coverage']['missing_cluster_id']}"
    )
    print("missed lanes:", stats["missed_lane_distribution"])
    print("missed by pass:", stats["missed_by_pass"])
    print("missed provider pairs:", stats["provider_pair_labels_missed"])
    print(f"INCLUDE-split (dangerous) missed pairs: {len(split_pairs)}")
    print(f"out -> {OUT}")


if __name__ == "__main__":
    main()
