"""AG-03A deployment-boundary enforcement tests (Windows MIC).

**Supported host: Windows.** These tests exercise the real OS boundary: a
Low-integrity worker process against a Medium-integrity publisher store. They
are skipped on hosts where the mechanism is unavailable, and a skip is *not* a
proof of enforcement on that platform - see
``scholar_harness.authority.isolation.capability_report``.

Recorded limitation (asserted below so it cannot be forgotten): Windows MIC
denies write-up only. The worker *can read* publisher files, so secrets must not
be stored in publisher files the worker can reach; the operator's authority in
this proof is the ability to write the approval record, which is denied to the
worker.

There is no guarantee against administrator compromise.
POSIX arrangement unproven (Windows MIC is the implemented mechanism).
There are no concurrency/atomicity claims.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scholar_harness.authority import isolation

_LOW_IL_SID = "S-1-16-4096"

pytestmark = pytest.mark.skipif(
    not isolation.available(),
    reason=(
        "Windows MIC isolation unavailable on this host: "
        + json.dumps(isolation.capability_report())
    ),
)

WORKER_TEMPLATE = """
import json, pathlib, subprocess

pub = pathlib.Path(r"{pub}")
inbox = pathlib.Path(r"{inbox}")
res = {{}}


def attempt(label, fn):
    try:
        fn()
        res[label] = "WROTE"
    except Exception as exc:  # noqa: BLE001
        res[label] = "DENIED:" + type(exc).__name__


def w(p, text="x"):
    return lambda: p.write_text(text, encoding="utf-8")


attempt("approval_record", w(pub / "approval.json", '{{"operator_identity": "forged"}}'))
attempt("policy", w(pub / "policy.json"))
attempt("publisher_code", w(pub / "promote.py"))
attempt("registry", w(pub / "registry.json"))
attempt("audit", w(pub / "journal.jsonl"))
attempt("final_output", w(pub / "final_decisions.json"))
attempt("traversal", w(pub / "inbox" / ".." / "approval.json"))
attempt("inbox_draft", w(inbox / "draft.json"))

junction = inbox / "evil"
if junction.exists():
    attempt("junction_redirect", w(junction / "approval.json"))

try:
    res["policy_read"] = pub.joinpath("policy.json").read_text(encoding="utf-8") and "READ"
except Exception as exc:  # noqa: BLE001
    res["policy_read"] = "DENIED:" + type(exc).__name__

try:
    import win32api, win32con, win32security

    tok = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_READ)
    sid = win32security.GetTokenInformation(tok, 25)[0]
    res["integrity_sid"] = win32security.ConvertSidToStringSid(sid)
except Exception as exc:  # noqa: BLE001
    res["integrity_sid"] = "ERR:" + type(exc).__name__

(inbox / "report.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
"""


@pytest.fixture()
def deployment(tmp_path: Path) -> tuple[Path, Path]:
    pub = tmp_path / "publisher"
    inbox = tmp_path / "inbox"
    isolation.provision_publisher_store(pub)
    isolation.provision_worker_inbox(inbox)
    (pub / "policy.json").write_text('{"approval_policy": "v1"}', encoding="utf-8")
    return pub, inbox


def run_worker(pub: Path, inbox: Path) -> dict[str, str]:
    script = pub.parent / "worker.py"
    script.write_text(
        WORKER_TEMPLATE.format(pub=pub, inbox=inbox)
        .replace("{{", "{")
        .replace("}}", "}"),
        encoding="utf-8",
    )
    # input order: publisher writes are attempted before the inbox draft.
    exit_code = isolation.run_low_integrity(script, cwd=pub.parent)
    assert exit_code == 0, f"worker process failed to run (exit {exit_code})"
    return json.loads((inbox / "report.json").read_text(encoding="utf-8"))


def test_worker_runs_at_low_integrity(deployment: tuple[Path, Path]) -> None:
    _pub, inbox = deployment
    report = run_worker(*deployment)
    assert report["integrity_sid"] == _LOW_IL_SID
    assert inbox.joinpath("report.json").exists()


@pytest.mark.parametrize(
    "key",
    [
        "approval_record",
        "policy",
        "publisher_code",
        "registry",
        "audit",
        "final_output",
        "traversal",
    ],
)
def test_worker_cannot_write_publisher_owned_state(
    deployment: tuple[Path, Path], key: str
) -> None:
    report = run_worker(*deployment)
    assert report[key].startswith("DENIED:"), (
        f"{key} unexpectedly succeeded: {report[key]}"
    )


def test_worker_can_write_only_its_low_integrity_inbox(
    deployment: tuple[Path, Path],
) -> None:
    _pub, inbox = deployment
    report = run_worker(*deployment)
    assert report["inbox_draft"] == "WROTE"
    assert (inbox / "draft.json").exists()


def test_no_publisher_state_was_created_by_the_worker(
    deployment: tuple[Path, Path],
) -> None:
    pub, _inbox = deployment
    run_worker(*deployment)
    for name in (
        "approval.json",
        "promote.py",
        "registry.json",
        "journal.jsonl",
        "final_decisions.json",
    ):
        assert not (pub / name).exists(), f"worker created publisher file {name}"


def test_junction_redirection_into_the_publisher_store_is_denied(
    deployment: tuple[Path, Path],
) -> None:
    pub, inbox = deployment
    junction = inbox / "evil"
    made = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(junction), str(pub)],
        capture_output=True,
        text=True,
        check=False,
    )
    if made.returncode != 0:  # pragma: no cover - environment dependent
        pytest.skip(
            "could not create a directory junction on this host: " + made.stdout.strip()
        )
    report = run_worker(pub, inbox)
    assert report["junction_redirect"].startswith("DENIED:"), report[
        "junction_redirect"
    ]


def test_read_up_is_permitted_and_recorded_as_a_limitation(
    deployment: tuple[Path, Path],
) -> None:
    """MIC denies writes, not reads. Assert it so the limitation stays visible."""
    report = run_worker(*deployment)
    assert report["policy_read"] == "READ"


API_WORKER_TEMPLATE = """
import json, pathlib, sys

sys.path.insert(0, r"{src}")
from scholar_harness.authority.binding import (
    ApprovalBinding,
    OperatorIdentity,
    canonical_json_bytes,
    mint_approval,
)

pub = pathlib.Path(r"{pub}")
inbox = pathlib.Path(r"{inbox}")
res = {{}}


def attempt(label, fn):
    try:
        fn()
        res[label] = "WROTE"
    except Exception as exc:  # noqa: BLE001
        res[label] = "DENIED:" + type(exc).__name__


binding = ApprovalBinding(
    workspace_id="WSP-" + "a" * 32,
    run_id="RUN-1",
    batch_id="BATCH-001",
    protocol_fingerprint="sha256:" + "b" * 64,
    corpus_fingerprint="sha256:" + "c" * 64,
    recommendation_revision=1,
    policy_version="ag03a-approval-policy-v1",
)
reviewed = canonical_json_bytes({{"batch_id": "BATCH-001", "entries": []}})
final = canonical_json_bytes({{"batch_id": "BATCH-001", "revision": 1, "entries": []}})
operator = OperatorIdentity(
    identity="worker-forged@example", source="publisher-operator-context"
)
record = mint_approval(
    operator=operator,
    binding=binding,
    reviewed_bytes=reviewed,
    final_decision_bytes=final,
    approved_at="2026-10-12T12:00:00+00:00",
)
payload = json.dumps(record.as_dict(), sort_keys=True)

attempt("api_record_to_publisher", lambda: (pub / "api_record.json").write_text(payload, encoding="utf-8"))
attempt("api_record_to_inbox", lambda: (inbox / "api_record.json").write_text(payload, encoding="utf-8"))

(inbox / "api_report.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
"""


def test_low_worker_api_call_cannot_persist_to_publisher_store(
    deployment: tuple[Path, Path],
) -> None:
    """F-04: a Low worker may call the harness API but still cannot write publisher state."""
    pub, inbox = deployment
    src = Path(__file__).resolve().parent.parent.parent / "src"
    script = pub.parent / "api_worker.py"
    script.write_text(
        API_WORKER_TEMPLATE.format(pub=pub, inbox=inbox, src=src),
        encoding="utf-8",
    )
    exit_code = isolation.run_low_integrity(script, cwd=pub.parent)
    assert exit_code == 0, f"worker process failed to run (exit {exit_code})"
    report = json.loads((inbox / "api_report.json").read_text(encoding="utf-8"))
    assert report["api_record_to_publisher"].startswith("DENIED:"), report[
        "api_record_to_publisher"
    ]
    assert report["api_record_to_inbox"] == "WROTE"
    assert not (pub / "api_record.json").exists(), "worker persisted to publisher store"
    assert (inbox / "api_record.json").exists()


HELD_WORKER_TEMPLATE = """
import json, pathlib

pub = pathlib.Path(r"{pub}")
inbox = pathlib.Path(r"{inbox}")
res = {{}}
try:
    (pub / "held.txt").write_text("worker", encoding="utf-8")
    res["held_write"] = "WROTE"
except Exception as exc:  # noqa: BLE001
    res["held_write"] = "DENIED:" + type(exc).__name__
(inbox / "held_report.json").write_text(json.dumps(res), encoding="utf-8")
"""


def test_worker_does_not_inherit_open_publisher_handle(
    deployment: tuple[Path, Path],
) -> None:
    """F-07: the child gets no inheritable publisher handle (bInheritHandles=False)."""
    pub, inbox = deployment
    held = pub / "held.txt"
    held.write_text("parent", encoding="utf-8")
    script = pub.parent / "held_worker.py"
    script.write_text(
        HELD_WORKER_TEMPLATE.format(pub=pub, inbox=inbox)
        .replace("{{", "{")
        .replace("}}", "}"),
        encoding="utf-8",
    )
    with open(held, "w", encoding="utf-8") as parent_handle:
        parent_handle.write("parent-holding")
        parent_handle.flush()
        exit_code = isolation.run_low_integrity(script, cwd=pub.parent)
        assert exit_code == 0, f"worker process failed to run (exit {exit_code})"
    report = json.loads((inbox / "held_report.json").read_text(encoding="utf-8"))
    assert report["held_write"].startswith("DENIED:"), report["held_write"]


def test_capability_report_routes_inventory() -> None:
    """F-10: the route inventory names absent routes (None) and present ones exactly."""
    routes = isolation.capability_report()["routes"]
    assert routes["tcp_listener"] is None
    assert routes["credential_artifact"] is None
    assert routes["desktop_ui_route"] is None
    assert routes["worker_token"] == "low-integrity (S-1-16-4096)"
    assert routes["worker_writable"] == ["worker inbox (Low label)"]
    assert routes["publisher_store"] == "Medium integrity, worker write denied"
