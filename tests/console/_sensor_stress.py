"""A generated workspace of the sensor-stress review's size (H-screening-read-performance).

The researcher's own review is never read: this builds a stand-in of the same
shape through the engine's own paths. Five database exports are staged (2,181
records, 1,062 works after de-duplication) and accepted, 54 batches of 20 are
prepared, every record is decided by an intake event (1,062 events, then 38
changed decisions that supersede earlier ones: 1,100 events), the decision
files are projected, the publication is approved and published.

``build(root)`` writes the workspace to ``root / "ws"`` and returns its path.
Deterministic (seeded); about half a minute on a desktop PC.
"""

from __future__ import annotations

import importlib.util
import json
import random
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "tests" / "kits" / "protocol" / "fixtures" / "canonical" / "identity_base.json"
WS_ID = "WSP-" + "5" * 32
SCREENER = "researcher:local"

WORKS = 1_062
RECORDS = 2_181
BATCH_SIZE = 20
CHANGED = 38
DATABASES = ("Scopus", "Web of Science", "IEEE Xplore", "PubMed", "ACM Digital Library")

_WORDS = (
    "sensor stress fault drift calibration bridge strain fatigue crack vibration modal damage acoustic emission "
    "thermal load wireless network node energy harvesting embedded monitoring structural health concrete steel "
    "composite aircraft wing turbine blade pipeline corrosion ultrasonic guided wave piezoelectric fibre optic "
    "bragg grating temperature humidity compensation machine learning neural anomaly detection baseline "
    "uncertainty bayesian kalman filter estimation localisation imaging tomography field trial laboratory "
    "specimen benchmark dataset survey review framework prognosis lifetime reliability degradation"
).split()


def _helpers():
    spec = importlib.util.spec_from_file_location(
        "_sensor_stress_events_helpers", ROOT / "tests" / "test_screening_events.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _works(rng: random.Random) -> list[dict[str, str]]:
    works = []
    seen: set[str] = set()
    while len(works) < WORKS:
        title = " ".join(rng.choice(_WORDS) for _ in range(rng.randint(7, 12))).capitalize()
        if title.lower() in seen:
            continue
        seen.add(title.lower())
        i = len(works)
        works.append({
            "title": title,
            "doi": f"10.5555/sensor-stress.{i:05d}",
            "year": str(2005 + i % 20),
            "author": f"Author{i % 97}, {chr(65 + i % 26)}.",
            "journal": f"Journal of {rng.choice(_WORDS).capitalize()} {rng.choice(_WORDS).capitalize()}",
            "abstract": " ".join(rng.choice(_WORDS) for _ in range(rng.randint(150, 230))).capitalize() + ".",
        })
    return works


def _ris(records: list[tuple[dict[str, str], bool, bool]]) -> bytes:
    lines = []
    for work, upper, with_doi in records:
        lines += ["TY  - JOUR", f"AU  - {work['author']}", f"TI  - {work['title'].upper() if upper else work['title']}",
                  f"PY  - {work['year']}", f"JO  - {work['journal']}", f"AB  - {work['abstract']}"]
        if with_doi:
            lines.append(f"DO  - {work['doi'].upper() if upper else work['doi']}")
        lines.append("ER  - ")
    return ("\n".join(lines) + "\n").encode("utf-8")


def _exports(works: list[dict[str, str]]) -> list[list[tuple[dict[str, str], bool, bool]]]:
    """Every work in two exports, 57 in a third: 2,181 records, 1,119 of them duplicates."""
    files: list[list[tuple[dict[str, str], bool, bool]]] = [[] for _ in DATABASES]
    third = RECORDS - 2 * WORKS
    for i, work in enumerate(works):
        files[i % 5].append((work, False, True))
        # The second copy differs in case; one in ten has no DOI (matched by its title).
        files[(i + 1) % 5].append((work, i % 3 == 0, i % 10 != 0))
        if i < third:
            files[(i + 2) % 5].append((work, False, True))
    return files


def build(root: Path) -> Path:
    from scholar_harness.corpus_accept import accept_corpus, stage_ris_source
    from scholar_harness.screening import events as ev
    from scholar_harness.screening.batcher import cmd_prepare
    from scholar_harness.screening.collector import cmd_collect

    se = _helpers()
    se.WS_ID = WS_ID  # the approval helper binds the workspace id it is given
    rng = random.Random(20261120)
    ws = Path(root) / "ws"
    (ws / "literature").mkdir(parents=True)
    (ws / "audit").mkdir()
    (ws / "audit" / "journal.jsonl").write_text("", encoding="utf-8")
    (ws / "project.json").write_text(
        json.dumps({"project_id": "sensor-stress-fixture", "registered_workspace_id": WS_ID}), encoding="utf-8"
    )
    (ws / "protocol.json").write_text(PROTOCOL.read_text(encoding="utf-8"), encoding="utf-8")

    works = _works(rng)
    for label, records in zip(DATABASES, _exports(works), strict=True):
        stage_ris_source(ws, label, _ris(records), file_name=f"{label.lower().replace(' ', '_')}.ris",
                         searched_on="2026-11-20", query="(sensor OR strain) AND stress")
    accept_corpus(ws, now=datetime(2026, 11, 20, 9, tzinfo=UTC))
    cmd_prepare(ws, batch_size=BATCH_SIZE)

    context = ev.load_context(ws)
    exclusion = min(context.exclusion_ids)
    inclusion = min(context.inclusion_ids)
    start = datetime(2026, 11, 20, 10, tzinfo=UTC)
    clock = 0

    def event(study: str, outcome: str, **extra) -> dict:
        nonlocal clock
        clock += 1
        batch = context.batches[context.study_batch[study]]
        reason = None
        if outcome == "EXCLUDE":
            reason = exclusion if clock % 3 else f"FAILS-{inclusion}"
        return {
            "event_id": str(uuid.UUID(int=rng.getrandbits(128), version=4)),
            "study_id": study,
            "screener_id": SCREENER,
            "method": "HUMAN",
            "outcome": outcome,
            "reason_code": reason,
            "note": (f"Read the abstract: {' '.join(rng.choice(_WORDS) for _ in range(30))}." if clock % 3 == 0 else None),
            "criteria": [{"id": inclusion, "answer": "no" if reason == f"FAILS-{inclusion}" else "yes"}],
            "decided_at": (start + timedelta(seconds=40 * clock)).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "device": "desktop",
            "supersedes": None,
            "proposal_shown": None,
            "binding": {
                "protocol_fingerprint": context.protocol_fingerprint,
                "batch_id": batch.batch_id,
                "batch_sha256": batch.batch_sha256,
                "criteria_version": context.criteria_version,
            },
            **extra,
        }

    def outcome(i: int) -> str:
        return "INCLUDE" if i % 10 == 0 else ("MAYBE" if i % 10 == 1 else "EXCLUDE")

    first: dict[str, dict] = {}
    for index in sorted(context.batches):
        sent = []
        for study in context.batches[index].candidates:
            sent.append(event(study, outcome(len(first))))
            first[study] = sent[-1]
        results = se._intake(ws, sent)
        assert set(results) == {"accepted"}, results
    studies = sorted(first)
    for j in range(CHANGED):
        study = studies[(j * 27) % len(studies)]
        before = first[study]["outcome"]
        after = "INCLUDE" if before != "INCLUDE" else "MAYBE"
        results = se._intake(ws, [event(study, after, supersedes=first[study]["event_id"])])
        assert results == ["accepted"], results
    for index in context.batches:
        ev.write_projection(ws, index, SCREENER, workspace_id=WS_ID)
    se._stage_approval(ws)
    cmd_collect(ws)
    return ws


if __name__ == "__main__":  # pragma: no cover - a manual run for the measurement record
    import sys
    import time

    t0 = time.perf_counter()
    print(build(Path(sys.argv[1])), f"{time.perf_counter() - t0:.1f} s")
