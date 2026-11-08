"""M7-method M8: a new workspace's protocol carries the method block.

Decision 2026-11-08: new workspaces are written with the block, filled with
today's values, so the signed protocol states them and the methods paragraph
reports the protocol as their source. Existing workspaces are left alone.
"""

from __future__ import annotations

import json

from scholar_harness.inception.genesis import scaffold_placeholder_workspace
from scholar_harness.screening.method import PLAYBOOK_REPORTING, effective_method
from scholar_protocol.models import MethodConfig


def test_a_new_workspace_protocol_carries_the_default_block(tmp_path):
    scaffold_placeholder_workspace(tmp_path / "new", "Method block review", agent="test", timestamp="2026-11-08T00:00:00+00:00")
    protocol = json.loads((tmp_path / "new" / "protocol.json").read_text(encoding="utf-8"))
    derived = PLAYBOOK_REPORTING[protocol["playbook_type"]]
    # M7b-guideline G3: the derived guideline is written into the signed protocol.
    assert protocol["method"] == {**MethodConfig().model_dump(mode="json"), "reporting": derived}
    method = effective_method(tmp_path / "new")
    assert method.source == "protocol"
    assert (method.reporting, method.reporting_source) == (derived, "protocol")


def test_a_scoping_review_workspace_states_prisma_scr(tmp_path):
    from scholar_harness.inception.genesis import _scaffold_only_intent, compile_protocol_files

    intent = _scaffold_only_intent("Scoping map", "scoping-map", "2026-11-08T00:00:00+00:00")
    intent["playbook_type"] = "SCOPING_REVIEW"
    ws = tmp_path / "scoping"
    ws.mkdir()
    compile_protocol_files(ws, intent)
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    assert protocol["method"]["reporting"] == "prisma-scr"
