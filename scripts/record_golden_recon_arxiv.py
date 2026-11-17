"""Record the arXiv answers of the golden recon cassette again, and only those.

M10a (decision 2026-11-14, item 3a): arXiv terms are now joined with ``AND``,
so the arXiv requests recorded in
``tests/fixtures/cassettes/golden_recon_probe.yaml`` no longer match. This
script runs the arXiv leg of the golden recon probe live, once, into a scratch
cassette, then replaces the arXiv interactions of the golden cassette with the
new ones. Every other interaction (OpenAlex, Crossref, Semantic Scholar) is
kept byte for byte: the splice works on the cassette's text, never on a
re-serialised copy.

The engine refuses to search without a contact address, and sends it to the
database. The address, API keys and the User-Agent are filtered out of the
recording, as in the cassette test; the script refuses to write a cassette that
still contains the address.

    SCHOLAR_MAILTO=you@example.org uv run python scripts/record_golden_recon_arxiv.py

``--dry-run`` records into the scratch cassette and prints what would change
without writing the golden cassette.
"""

from __future__ import annotations

import argparse
import asyncio
import itertools
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASSETTE = ROOT / "tests" / "fixtures" / "cassettes" / "golden_recon_probe.yaml"
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


async def _record(scratch: Path) -> dict:
    import vcr

    from scholar_harness.recon.engine import ReconEngine
    from scholar_search.config import settings

    settings.http_cache = False
    settings.openalex_key = None
    settings.s2_key = None
    recorder = vcr.VCR(
        record_mode="all",
        match_on=["method", "scheme", "host", "path", "query"],
        filter_query_parameters=SECRET_QUERY,
        filter_headers=SECRET_HEADERS,
        before_record_response=_scrub_response,
        decode_compressed_response=True,
    )
    with tempfile.TemporaryDirectory() as cache, recorder.use_cassette(str(scratch)):
        pool, _path, _cached = await ReconEngine(cache_root=cache).probe_pool(
            TOPIC, ["arxiv"], year_min=YEARS[0], year_max=YEARS[1], refresh=True
        )
    return pool


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="record and report, do not write the golden cassette")
    args = parser.parse_args(argv)

    address = os.environ.get("SCHOLAR_MAILTO", "").strip()
    if not address:
        print("SCHOLAR_MAILTO is not set: the engine refuses to search without a contact address.", file=sys.stderr)
        return 2
    os.environ.pop("NEXUS_RECON_ROOT", None)

    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "arxiv.yaml"
        pool = asyncio.run(_record(scratch))
        leg = next((leg for leg in pool.get("legs", []) if leg.get("provider") == "arxiv"), {})
        recorded = _read(scratch)

    if address in recorded:
        print("refused: the recording still contains the contact address", file=sys.stderr)
        return 1
    golden = _read(CASSETTE)
    updated = splice(golden, recorded)
    _h, old_blocks, _t = split_interactions(golden)
    _h, new_blocks, _t = split_interactions(updated)
    kept = [b for b in old_blocks if not is_arxiv(b)]
    if kept != [b for b in new_blocks if not is_arxiv(b)]:
        print("refused: another database's interaction would change", file=sys.stderr)
        return 1

    print(f"arXiv leg: status={leg.get('status')} fetched={leg.get('fetched')} reported_total={leg.get('reported_total')}")
    print(f"arXiv query sent: {leg.get('executed_query')}")
    print(f"arXiv interactions: {sum(map(is_arxiv, old_blocks))} -> {sum(map(is_arxiv, new_blocks))}; others kept: {len(kept)}")
    if args.dry_run:
        print("dry run: golden cassette not written")
        return 0
    with CASSETTE.open("w", encoding="utf-8", newline="") as fh:
        fh.write(updated)
    print(f"written: {CASSETTE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
