"""Record the arXiv answers of the golden cassettes again, and only those.

M10a (decision 2026-11-14, item 3a): arXiv terms are now joined with ``AND``,
so the arXiv requests recorded in
``tests/fixtures/cassettes/golden_recon_probe.yaml`` no longer matched.
M3h-c (F16, decision 2026-11-18, item 2): the arXiv leg now sends its year
range as a ``submittedDate`` clause, so the arXiv request in both golden
cassettes changes: the recon probe (``golden_recon_probe.yaml``) and the golden
search (``golden_uav_search.yaml``).

This script runs the arXiv leg of each live, once, into a scratch cassette,
then replaces the arXiv interactions of the golden cassette with the new ones.
Every other interaction (OpenAlex, Crossref, Semantic Scholar, PubMed) is kept
byte for byte: the splice works on the cassette's text, never on a
re-serialised copy. Two arXiv requests in all (one per cassette), nothing sent
to any other database.

The engine refuses to search without a contact address, and sends it to the
database. The address, API keys and the User-Agent are filtered out of the
recording, as in the cassette tests. The script refuses to write a cassette
that still contains the address, a recording whose leg is not ``ok`` or carries
no ``submittedDate`` clause, and an arXiv error feed (arXiv answers a query it
cannot parse with a feed that holds one error entry, and the leg still says
``ok``). Nothing is written unless every check passes for every cassette.

    $env:SCHOLAR_MAILTO = "<your contact address>"
    uv run python scripts/record_golden_recon_arxiv.py --dry-run
    uv run python scripts/record_golden_recon_arxiv.py

``--cassette recon|search|both`` (default ``both``). ``--dry-run`` records into
the scratch cassettes and prints what would change without writing.

    uv run python scripts/record_golden_recon_arxiv.py --check-open-ended

sends one more request, never recorded into a golden cassette: the recon probe
with a start year and no end year (``submittedDate:[2020... TO 9999...]``),
to see whether arXiv accepts an open end. It writes nothing.
"""

from __future__ import annotations

import argparse
import asyncio
import itertools
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASSETTES = {
    "recon": ROOT / "tests" / "fixtures" / "cassettes" / "golden_recon_probe.yaml",
    "search": ROOT / "tests" / "fixtures" / "cassettes" / "golden_uav_search.yaml",
}
CASSETTE = CASSETTES["recon"]  # kept for the splice tests written in M10a
GOLDEN_WORKSPACE = ROOT / "workspaces" / "golden-uav-30"
SEARCH_CAP = 100  # the run override the golden search test uses
TOPIC = "UAV crop weed mapping"
YEARS = (2020, 2026)
ARXIV_HOST = "export.arxiv.org"

SECRET_QUERY = ["mailto", "email", "tool", "api_key", "apikey"]
SECRET_HEADERS = ["user-agent", "x-api-key", "authorization", "cookie"]


def _scrub_response(response):
    headers = response.get("headers", {})
    for name in list(headers):
        if name.lower() in ("set-cookie", "cookie"):
            headers.pop(name)
    return response


def split_interactions(text: str) -> tuple[str, list[str], str]:
    """Split a VCR cassette into its header, one block per interaction, and its tail.

    A block starts at a line ``- request:`` in column 0 and runs to the next one,
    or to the ``version:`` line that ends the file.
    """
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.rstrip("\r\n") == "- request:"]
    if not starts:
        raise ValueError("no interactions found")
    end = next(
        (i for i in range(len(lines) - 1, -1, -1) if lines[i].startswith("version:")),
        len(lines),
    )
    head = "".join(lines[: starts[0]])
    bounds = [*starts, end]
    blocks = ["".join(lines[a:b]) for a, b in itertools.pairwise(bounds)]
    tail = "".join(lines[end:])
    return head, blocks, tail


def is_arxiv(block: str) -> bool:
    return re.search(r"^    uri: https://" + re.escape(ARXIV_HOST) + r"/", block, re.MULTILINE) is not None


def _read(path: Path) -> str:
    with path.open(encoding="utf-8", newline="") as fh:
        return fh.read()


def splice(golden: str, recorded: str) -> str:
    """Replace the arXiv blocks of ``golden`` with those of ``recorded``, in place of the first one.

    The new blocks take the golden cassette's line ending.
    """
    head, blocks, tail = split_interactions(golden)
    eol = "\r\n" if "\r\n" in golden else "\n"
    _h, new_blocks, _t = split_interactions(recorded.replace("\r\n", "\n").replace("\n", eol))
    new_arxiv = [b for b in new_blocks if is_arxiv(b)]
    if not new_arxiv:
        raise ValueError("the recording holds no arXiv interaction")
    if any(not is_arxiv(b) for b in new_blocks):
        raise ValueError("the recording holds a request to another database")
    out: list[str] = []
    placed = False
    for block in blocks:
        if is_arxiv(block):
            if not placed:
                out.extend(new_arxiv)
                placed = True
            continue
        out.append(block)
    if not placed:
        out.extend(new_arxiv)
    return head + "".join(out) + tail


def check_recording(recorded: str, leg: dict, address: str = "") -> list[str]:
    """What is wrong with an arXiv recording; an empty list when it can be spliced in."""
    problems: list[str] = []
    if address and address in recorded:
        problems.append("the recording still contains the contact address")
    if leg.get("status") != "ok":
        problems.append(f"the arXiv leg is {leg.get('status')!r}, not 'ok': {leg.get('error')}")
    elif not leg.get("fetched"):
        problems.append("the arXiv leg fetched no record")
    if "submittedDate" not in (leg.get("executed_query") or ""):
        problems.append("the query sent has no submittedDate clause")
    if "arxiv.org/api/errors" in recorded:
        problems.append("arXiv answered with an error feed (it could not parse the query)")
    return problems


def _recorder():
    import vcr

    return vcr.VCR(
        record_mode="all",
        match_on=["method", "scheme", "host", "path", "query"],
        filter_query_parameters=SECRET_QUERY,
        filter_headers=SECRET_HEADERS,
        before_record_response=_scrub_response,
        decode_compressed_response=True,
    )


def _quiet_settings() -> None:
    from scholar_search.config import settings

    settings.http_cache = False
    settings.openalex_key = None
    settings.s2_key = None


async def _record_recon(scratch: Path) -> dict:
    """The arXiv leg of the golden recon probe, recorded into ``scratch``."""
    from scholar_harness.recon.engine import ReconEngine

    _quiet_settings()
    with tempfile.TemporaryDirectory() as cache, _recorder().use_cassette(str(scratch)):
        pool, _path, _cached = await ReconEngine(cache_root=cache).probe_pool(
            TOPIC, ["arxiv"], year_min=YEARS[0], year_max=YEARS[1], refresh=True
        )
    return next((leg for leg in pool.get("legs", []) if leg.get("provider") == "arxiv"), {})


async def _record_search(scratch: Path) -> dict:
    """The arXiv leg of the golden search (golden protocol, cap 100), recorded into ``scratch``."""
    from scholar_harness.pipeline.discovery import run_discovery

    _quiet_settings()
    with tempfile.TemporaryDirectory() as tmp, _recorder().use_cassette(str(scratch)):
        ws = Path(tmp) / "ws"
        ws.mkdir()
        for item in ("protocol.json", "project.json"):
            shutil.copy2(GOLDEN_WORKSPACE / item, ws / item)
        outcome = await run_discovery(
            protocol_path=ws / "protocol.json",
            literature_dir=ws / "literature",
            max_search_results=SEARCH_CAP,
            providers=["arxiv"],
        )
    return next((leg for leg in outcome.legs if leg.get("provider") == "arxiv"), {})


RECORDERS = {"recon": _record_recon, "search": _record_search}


async def _record_open_ended(scratch: Path) -> dict:
    """The arXiv leg of a recon probe with a start year and no end year, into ``scratch``."""
    from scholar_harness.recon.engine import ReconEngine

    _quiet_settings()
    with tempfile.TemporaryDirectory() as cache, _recorder().use_cassette(str(scratch)):
        pool, _path, _cached = await ReconEngine(cache_root=cache).probe_pool(
            TOPIC, ["arxiv"], year_min=YEARS[0], year_max=None, refresh=True
        )
    return next((leg for leg in pool.get("legs", []) if leg.get("provider") == "arxiv"), {})


def _check_open_ended(address: str) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "arxiv.yaml"
        leg = asyncio.run(_record_open_ended(scratch))
        recorded = _read(scratch)
    problems = check_recording(recorded, leg, address)
    print(f"[open-ended] arXiv leg: status={leg.get('status')} fetched={leg.get('fetched')} reported_total={leg.get('reported_total')}")
    print(f"[open-ended] arXiv query sent: {leg.get('executed_query')}")
    for problem in problems:
        print(f"[open-ended] refused: {problem}", file=sys.stderr)
    print("nothing written")
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="record and report, do not write the golden cassettes")
    parser.add_argument("--cassette", choices=["recon", "search", "both"], default="both")
    parser.add_argument("--check-open-ended", action="store_true", help="one request with no end year; writes nothing")
    args = parser.parse_args(argv)

    address = os.environ.get("SCHOLAR_MAILTO", "").strip()
    if not address:
        print("SCHOLAR_MAILTO is not set: the engine refuses to search without a contact address.", file=sys.stderr)
        return 2
    os.environ.pop("NEXUS_RECON_ROOT", None)
    if args.check_open_ended:
        return _check_open_ended(address)

    names = ["recon", "search"] if args.cassette == "both" else [args.cassette]
    pending: dict[str, str] = {}
    refused = False
    for name in names:
        with tempfile.TemporaryDirectory() as tmp:
            scratch = Path(tmp) / "arxiv.yaml"
            leg = asyncio.run(RECORDERS[name](scratch))
            recorded = _read(scratch)
        problems = check_recording(recorded, leg, address)
        golden = _read(CASSETTES[name])
        updated = splice(golden, recorded)
        _h, old_blocks, _t = split_interactions(golden)
        _h, new_blocks, _t = split_interactions(updated)
        kept = [b for b in old_blocks if not is_arxiv(b)]
        if kept != [b for b in new_blocks if not is_arxiv(b)]:
            problems.append("another database's interaction would change")
        print(f"[{name}] arXiv leg: status={leg.get('status')} fetched={leg.get('fetched')} reported_total={leg.get('reported_total')}")
        print(f"[{name}] arXiv query sent: {leg.get('executed_query')}")
        print(f"[{name}] arXiv interactions: {sum(map(is_arxiv, old_blocks))} -> {sum(map(is_arxiv, new_blocks))}; others kept: {len(kept)}")
        for problem in problems:
            print(f"[{name}] refused: {problem}", file=sys.stderr)
        refused = refused or bool(problems)
        pending[name] = updated
    if refused:
        print("nothing written", file=sys.stderr)
        return 1
    if args.dry_run:
        print("dry run: golden cassettes not written")
        return 0
    for name, updated in pending.items():
        with CASSETTES[name].open("w", encoding="utf-8", newline="") as fh:
            fh.write(updated)
        print(f"written: {CASSETTES[name].relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
