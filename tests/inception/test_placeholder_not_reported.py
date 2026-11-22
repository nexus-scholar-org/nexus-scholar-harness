"""M11b follow-up: a placeholder workspace does not sign the not-reported rule silently.

M11b part D (answer 8, 2026-11-21) gave the rule no default: an Inception draft
leaves it unchosen and ``METHOD_RULE_UNCHOSEN`` blocks step 5, Review and
genesis; the terminal wizard asks it, and a scripted run needs ``--not-reported``.
The placeholder scaffold (``nexus-scholar init --scaffold-only`` and the
Workspaces "Create", one function) asks no question, so its protocol states no
method block unless ``--not-reported`` names the rule. The rule is chosen when
the placeholder is replaced (New review or the wizard), where part D asks it.
"""

from __future__ import annotations

import json
import sys
import unittest.mock as mock
from pathlib import Path

import pytest
import typer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "console"))
from test_inception_api import _draft  # noqa: E402

from scholar_harness.inception import steps, wizard  # noqa: E402
from scholar_harness.inception.genesis import scaffold_placeholder_workspace  # noqa: E402
from scholar_harness.screening.method import PLAYBOOK_REPORTING, effective_method  # noqa: E402

STAMP = "2026-11-22T00:00:00+00:00"


def _read(ws: Path, name: str) -> dict:
    return json.loads((ws / name).read_text(encoding="utf-8"))


def test_a_placeholder_states_no_rule_and_the_screen_reads_the_defaults(tmp_path):
    ws = tmp_path / "new"
    scaffold_placeholder_workspace(ws, "Placeholder review", agent="test", timestamp=STAMP)
    assert "method" not in _read(ws, "protocol.json")  # nothing signed for the researcher
    assert "method" not in _read(ws, "intent.json")
    method = effective_method(ws)
    # The screens say "defaults", never "protocol", for a rule nobody chose.
    assert (method.config.not_reported, method.source_of("not_reported")) == ("unclear", "defaults")
    assert method.reporting_source == "playbook"


def test_an_explicit_rule_is_signed_with_the_guideline(tmp_path):
    ws = tmp_path / "new"
    scaffold_placeholder_workspace(ws, "Placeholder review", agent="test", timestamp=STAMP, not_reported="decisive_first")
    protocol = _read(ws, "protocol.json")
    assert protocol["method"]["not_reported"] == "decisive_first"
    assert protocol["method"]["blinding"] == "reveal_after_decision"
    assert protocol["method"]["reporting"] == PLAYBOOK_REPORTING[protocol["playbook_type"]]
    # As part D's genesis: the choice travels in the intent, so a recompile keeps it (E21).
    assert _read(ws, "intent.json")["method"] == {"blinding": "reveal_after_decision", "not_reported": "decisive_first"}
    assert effective_method(ws).source_of("not_reported") == "protocol"


def test_a_rule_outside_the_three_is_refused_before_anything_is_written(tmp_path):
    from scholar_harness.inception.genesis import WorkspaceScaffoldRefused

    with pytest.raises(WorkspaceScaffoldRefused) as refused:
        scaffold_placeholder_workspace(tmp_path / "new", "Placeholder review", agent="test", not_reported="include")
    assert refused.value.code == "METHOD_RULE_INVALID"
    assert not (tmp_path / "new").exists()


def test_init_scaffold_only_takes_the_rule_from_the_option(tmp_path):
    target = tmp_path / "given"
    wizard.init_command("Given rule", target, scaffold_only=True, not_reported="exclude")
    assert _read(target, "protocol.json")["method"]["not_reported"] == "exclude"


def test_init_scaffold_only_without_the_option_signs_no_rule_also_when_scripted(tmp_path, capsys):
    # Nothing is signed, so nothing needs refusing: the placeholder states no rule.
    target = tmp_path / "scripted"
    with mock.patch.object(wizard, "_scripted", return_value=True):
        wizard.init_command("No rule", target, scaffold_only=True, not_reported=None)
    assert "method" not in _read(target, "protocol.json")
    said = " ".join(capsys.readouterr().out.split())
    # Review finding 3: init cannot run again on the folder, so the hint never sends the researcher there.
    assert "It states no not-reported rule: choose it with New review in the app" in said
    assert "replace the placeholder (or give" not in said


def test_init_scaffold_only_refuses_a_rule_outside_the_three_before_writing(tmp_path):
    target = tmp_path / "bad"
    with pytest.raises(typer.Exit) as refused:
        wizard.init_command("Bad rule", target, scaffold_only=True, not_reported="include")
    assert refused.value.exit_code == 2
    assert not target.exists()


def test_the_workspaces_create_signs_no_rule(tmp_path):
    from scholar_harness.workspace import catalog

    root = tmp_path / "root"
    root.mkdir()
    made = catalog.create(root, "Created in the app")
    assert "method" not in _read(Path(made["path"]), "protocol.json")


def test_an_imported_placeholder_leaves_the_rule_unchosen(tmp_path):
    """Starting a New review from the placeholder's protocol: part D's blocker applies, no "imported" rule."""
    import base64

    from scholar_harness.inception import importer

    ws = tmp_path / "new"
    scaffold_placeholder_workspace(ws, "Placeholder review", agent="test", timestamp=STAMP)
    source = {"kind": "file", "file_name": "protocol.json",
              "content_base64": base64.b64encode((ws / "protocol.json").read_bytes()).decode("ascii")}
    built = importer.map_source(importer.read_source(source, tmp_path))
    assert built["draft"].get("method_not_reported") is None
    assert "method_not_reported_source" not in built["draft"]


def test_a_search_amendment_of_a_placeholder_is_not_refused_for_the_method(tmp_path):
    """A recompile of the placeholder's intent states no method either (it would otherwise be refused outside_search)."""
    from scholar_harness import workspace_proposals as wp

    ws = tmp_path / "new"
    scaffold_placeholder_workspace(ws, "Placeholder review", agent="test", timestamp=STAMP)
    intent, protocol = _read(ws, "intent.json"), _read(ws, "protocol.json")
    concept = intent["core_concepts"][0]["concept"]
    new = wp.apply_op(intent, protocol, f"core_concepts[{concept}].synonyms", "add", "a new synonym")
    answer = wp.compile_amendment(protocol, new)
    assert answer["changed"] and all(p.startswith("search_strategy") for p in answer["changed"])
    assert "method" not in json.loads(answer["protocol_bytes"])


def test_a_review_written_at_step_5_still_states_its_block(tmp_path):
    """The change is the placeholder's only: genesis from a draft keeps part D's block."""
    from scholar_harness.inception.genesis import compile_intent

    draft = steps.parse_draft({**_draft(), "method_not_reported": "unclear"})
    protocol = json.loads(compile_intent(steps.build_intent(draft, STAMP))["protocol_bytes"])
    assert protocol["method"]["not_reported"] == "unclear"
