"""Run the M10c critic test set through the assistant's MCP path, and score it.

``prepare <dir>`` makes one workspace folder per document of
``tests/fixtures/critic_protocols`` (40 variants and 2 bases): ``intent.json``
and the compiled ``protocol.json``, the files genesis writes; a protocol-format
variant gets its ``protocol.json`` only, and an intent the compiler refuses
gets its ``intent.json`` only. Point the researcher's MCP client at these
folders (``scholar-agent -w <dir>``) and ask it to criticise each one with
``nexus_assistant_read_workspace`` and ``nexus_assistant_report_finding``.

``score <dir>`` reads each folder's ``audit/assistant_findings.jsonl`` and
scores it by the set's README: rule 1(a), the locator, is computed (a finding
*locates* a defect when its pointer is one of the defect's ``fields`` or
``accepted_locators`` or contains one); rule 1(b), "states the same problem",
is a judgement this script does not make, so a located defect is not called
caught. Rule 3: a major or critical finding on a base is a false alarm.

No model and no network is used here (M10c, decision item 13).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
SET_DIR = REPO / "tests" / "fixtures" / "critic_protocols"
FINDINGS_FILE = "audit/assistant_findings.jsonl"
PROTOCOL_PREFIX = "protocol:"


def manifest(set_dir: Path = SET_DIR) -> dict[str, Any]:
    return json.loads((set_dir / "manifest.json").read_text(encoding="utf-8"))


def documents(set_dir: Path = SET_DIR) -> list[dict[str, Any]]:
    """The 42 documents: each base (its intent) and each variant, with its format and defects."""
    m = manifest(set_dir)
    docs = [
        {"id": f"{name}-base", "base": name, "format": "intent", "file": f"bases/{name}-base.intent.json", "defects": []}
        for name in ("scoping", "sr")
    ]
    for v in m["variants"]:
        docs.append({"id": v["id"], "base": v["base"], "format": v["format"], "file": v["file"], "defects": v["defects"]})
    return docs


def prepare(out: Path, set_dir: Path = SET_DIR) -> list[dict[str, Any]]:
    """Write one workspace folder per document; answer what each holds."""
    from scholar_protocol.canonical import canonical_json
    from scholar_protocol.compiler import compile_protocol
    from scholar_protocol.intent import IntentPacket

    out.mkdir(parents=True, exist_ok=True)
    made = []
    for doc in documents(set_dir):
        folder = out / doc["id"]
        folder.mkdir(parents=True, exist_ok=True)
        data = json.loads((set_dir / doc["file"]).read_text(encoding="utf-8"))
        files = []
        if doc["format"] == "protocol":
            (folder / "protocol.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            files.append("protocol.json")
        else:
            (folder / "intent.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            files.append("intent.json")
            try:
                compiled = json.loads(canonical_json(compile_protocol(IntentPacket.model_validate(data))))
            except Exception:  # noqa: BLE001 - the set holds an intent the model refuses; it keeps its intent only
                compiled = None
            if compiled is not None:
                (folder / "protocol.json").write_text(json.dumps(compiled, indent=2, ensure_ascii=False), encoding="utf-8")
                files.append("protocol.json")
        made.append({"id": doc["id"], "files": files})
    return made


def findings(folder: Path) -> list[dict[str, Any]]:
    try:
        lines = (folder / FINDINGS_FILE).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if isinstance(entry, dict) and entry.get("event") == "reported":
            out.append(entry)
    return out


def _pointer(locator: str, fmt: str) -> str | None:
    """The finding's pointer in the document's own space, or ``None`` when it points elsewhere."""
    if locator.startswith(PROTOCOL_PREFIX):
        return locator[len(PROTOCOL_PREFIX):] if fmt == "protocol" else None
    if ":" in locator.split("/", 1)[0]:
        return None  # draft: or another space
    return locator if fmt == "intent" else None


def locates(pointer: str, targets: list[str]) -> bool:
    """README rule 1(a): the pointer is a target or contains one (never the whole document)."""
    if not pointer:
        return False
    return any(t == pointer or t.startswith(pointer.rstrip("/") + "/") for t in targets)


def score(out: Path, set_dir: Path = SET_DIR) -> dict[str, Any]:
    rows = []
    false_alarms, base_minor = [], 0
    for doc in documents(set_dir):
        found = findings(out / doc["id"])
        pointers = [p for p in (_pointer(f["locator"], doc["format"]) for f in found) if p is not None]
        if not doc["defects"]:
            for f in found:
                if f["severity"] in ("major", "critical"):
                    false_alarms.append({"document": doc["id"], "locator": f["locator"], "finding": f["finding"]})
                else:
                    base_minor += 1
        for d in doc["defects"]:
            targets = list(d["fields"]) + list(d.get("accepted_locators") or [])
            rows.append({
                "variant": doc["id"], "severity": d["severity"], "category": d["category"],
                "critic_only": d["catching_check"] == "none: critic only",
                "located": any(locates(p, targets) for p in pointers),
            })

    def share(items: list[dict[str, Any]]) -> dict[str, int]:
        return {"located": sum(r["located"] for r in items), "defects": len(items)}

    by = lambda key: {k: share([r for r in rows if r[key] == k]) for k in sorted({r[key] for r in rows})}
    return {
        "shape": "critic-score-v1",
        "rule": "located = README rule 1(a) only; whether the finding states the same problem (rule 1(b)) is not judged here",
        "defects": share(rows),
        "critic_only": share([r for r in rows if r["critic_only"]]),
        "with_fixed_check": share([r for r in rows if not r["critic_only"]]),
        "by_severity": by("severity"),
        "by_category": by("category"),
        "base_false_alarms": false_alarms,
        "base_minor_findings": base_minor,
        "missed": [{k: r[k] for k in ("variant", "severity", "category", "critic_only")} for r in rows if not r["located"]],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="critic_set", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare", help="write one workspace folder per document").add_argument("dir", type=Path)
    sub.add_parser("score", help="score the findings stored in the folders").add_argument("dir", type=Path)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        made = prepare(args.dir)
        print(json.dumps({"prepared": len(made), "dir": str(args.dir)}, indent=2))
    else:
        print(json.dumps(score(args.dir), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
