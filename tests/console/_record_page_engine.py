"""Record the engine's answers to every GET the screens send on load (H-screening-read-performance).

The web app's request-count tests (``apps/research-ui/tests/page-requests.test.tsx``)
answer each page from these recorded answers of a real engine, so the pages reach
the state they reach on a published review and send what they send there.

usage: uv run python tests/console/_record_page_engine.py
writes apps/research-ui/tests/fixtures/page-engine.json
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
# ``tests/``, for ``support.workspaces`` (H-faster-python-tests); pytest adds it through the conftest.
sys.path.insert(0, str(HERE.parent))

from test_export_api import published_workspace  # noqa: E402

from scholar_harness.console import create_app  # noqa: E402

OUT = HERE.parents[1] / "apps" / "research-ui" / "tests" / "fixtures" / "page-engine.json"

SCREENING = [
    "summary", "ui/batches", "ui/batches/review", "decisions/conflicts", "settings", "corpus", "proposals/setup",
    "criteria", "agreement", "prisma/preview", "approver", "methods",
    "queue?view=needs_you&limit=50", "queue?view=needs_you&limit=200", "queue?view=decided&limit=30",
    "queue?view=decided&limit=50", "queue?view=pilot&limit=200",
]


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "root"
        root.mkdir()
        ws, ids = published_workspace(root)
        client = TestClient(
            create_app(ws, token="t", workspaces_root=root),
            base_url="http://127.0.0.1",
            headers={"Authorization": "Bearer t"},
        )
        study = ids["included"]
        paths = [
            "/api/v1/review/next-step", "/api/v1/workspaces", "/api/v1/ui/publication-status",
            *[f"/api/v1/screening/{p}" for p in SCREENING],
            f"/api/v1/screening/records/{study}", f"/api/v1/screening/records/{study}/proposal",
            "/api/v1/charting", "/api/v1/charting/fetch", f"/api/v1/charting/records/{study}",
        ]
        answers = {}
        for path in paths:
            response = client.get(path)
            body = response.json()
            if isinstance(body, dict):
                body.pop("computed_at", None)
            answers[path] = {"status": response.status_code, "body": body}
        fixture = {
            "_source": "tests/console/_record_page_engine.py: a published three-record workspace (test_export_api)",
            "study": study,
            "answers": answers,
        }
        text = json.dumps(fixture, indent=1, sort_keys=True, ensure_ascii=False)
        # Paths of the temporary folder are not kept.
        text = text.replace(str(root).replace("\\", "\\\\"), "C:\\\\ws-root").replace(str(root), "/ws-root")
        OUT.write_text(text + "\n", encoding="utf-8")
        print(OUT, len(text), {p: a["status"] for p, a in answers.items()})


if __name__ == "__main__":
    main()
