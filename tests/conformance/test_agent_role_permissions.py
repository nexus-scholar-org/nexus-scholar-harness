"""Conformance gate for the Role@1 agent layer.

``roles/<id>.json`` is the single source of truth for capabilities. These tests
guard against a contradiction between a role's prose, its capability record, its
generated OpenCode frontmatter and its derived permission map: the generator's
``--check`` mode is exercised both on the real tree and on mutated copies staged
in ``tmp_path`` so every negative case is hermetic.

The prose guard (``find_write_claims``) is a heuristic, not a proof: it detects
the write-claim shapes that have actually appeared in review, and relies on
human review for paraphrases it cannot see.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = ROOT / "scripts" / "generate_agent_roles.py"
AGENT_DIR = ROOT / ".opencode" / "agent"
ROLES_DIR = ROOT / "roles"
PERMISSIONS_FILE = ROOT / ".opencode" / "agent" / "_generated" / "permissions.json"
EXPECTED_PERMISSIONS = (
    ROOT / "tests" / "conformance" / "fixtures" / "expected_permissions.json"
)
SPEC_ROLE_MODEL = ROOT / "specs" / "agent-layer-portability" / "01_role_model.md"

#: R7/R5 shorthand: only the fully-autonomous dev-loop roles may render
#: ``permission: allow`` (spec section 3, "Shorthand exception").
SHORTHAND_ROLES = {"coder", "inception-agent", "orchestrator"}

#: First-person write claims a body may only make when the role itself writes
#: at least one output (``written_by: role``). An adapter-persisted role does
#: not write; it returns the artifact to the harness. These literal phrases
#: cover the pathless imperative form the original contradiction used.
WRITE_CLAIM_PHRASES = ("your only write", "write only", "you may write")

#: Declarative detector: a write verb whose subject is the role itself and which
#: names a concrete file path nearby. ``emit`` is deliberately absent -- the
#: screening critic legitimately says "Emit only the assigned critique".
WRITE_CLAIM_VERBS = (
    "write",
    "writes",
    "wrote",
    "persist",
    "persists",
    "save",
    "saves",
    "create",
    "creates",
    "produce",
    "produces",
)
WRITE_CLAIM_VERB_RE = re.compile(
    r"\b(?:" + "|".join(WRITE_CLAIM_VERBS) + r")\b", re.IGNORECASE
)

#: Subjects that make a declarative write claim a claim about the role itself.
#: The role's own id with hyphens replaced by spaces is appended per role.
ROLE_SELF_SUBJECTS = (
    "you",
    "your",
    "the critic",
    "the reviewer",
    "the role",
    "this agent",
    "the agent",
)

#: A concrete file path, never a bare word such as "files" or "code".
WRITE_CLAIM_PATH_RE = re.compile(
    r"[\w{}/.-]+\.(?:jsonl|json|md|ya?ml|csv|txt|html)\b", re.IGNORECASE
)

#: A negation suppresses a claim only when it governs that verb. The guard is
#: therefore scoped to the subject--verb span of the verb's own clause: a
#: negation in an earlier clause ("Do not edit the decisions; the critic
#: writes ...") must not mask a later genuine claim.
WRITE_CLAIM_NEGATION_RE = re.compile(
    r"\b(?:not|never|cannot|no longer|do not|does not)\b", re.IGNORECASE
)

#: Clause boundaries the negation guard and the subject search must not cross.
CLAUSE_BOUNDARY_RE = re.compile(r"[.;!?\n]")

#: Boundaries *inside* a sentence that reset the negation guard. A negation
#: before one of these does not govern the verb after it: "The critic never
#: repairs the batch but writes `x.json`" asserts a write. Treating the whole
#: sentence as one scope let every one of these shapes through (F4).
NEGATION_RESET_RE = re.compile(r"[,;]|\b(?:and|but|yet|so)\b", re.IGNORECASE)

#: Passive restatement of a write claim: "`x.json` is written by the critic".
#: The participle set is closed, so the detector reports only the shapes review
#: has actually produced.
PASSIVE_CLAIM_RE = re.compile(
    r"\b(?:is|are|was|were|be)\s+"
    r"(?:written|persisted|saved|created|produced)\s+by\s+",
    re.IGNORECASE,
)

#: A clause opening with a pronoun inherits the role subject of the clause
#: before it ("The critic never repairs the batch; it writes ...").
ANAPHOR_RE = re.compile(r"^(?:it|they)\b", re.IGNORECASE)

#: Character window after a declarative verb's claim for the path token. The
#: subject search needs no character window: it is bounded by the verb's clause,
#: and a fixed window truncated a long clause before the subject ("The critic,
#: which never edits decisions, writes ..." -- F4).
PATH_WINDOW = 40

EXPECTED_ROLES = {
    "adjudicator",
    "coder",
    "extraction-critic",
    "extractor-a",
    "extractor-b",
    "human-confirm",
    "inception-agent",
    "orchestrator",
    "reviewer",
    "screener",
    "screening-critic",
    "tester",
}

#: Positive guard (T-ALP-A-r5): every character a **shipped** glob segment may
#: contain. This is a drift alarm, not a validation rule: ``validate_glob`` is
#: deliberately stricter (``:``, ``~`` and control characters are rejected as
#: alias spellings regardless of this set). The point is that a future record
#: introducing a segment character nobody has considered fails here instead of
#: silently widening the alphabet the alias rules must reason about.
PERMITTED_GLOB_CHARACTERS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.*?[]{}~/"
)

#: Every spelling measured on win32 (2026-10-25) that addresses a protected path
#: while its segments compare unequal to the protected glob. Each entry is
#: ``(glob, expected error fragment)``; the trailing entries were found by this
#: pass's own enumeration (8.3 short name, control character), not by review.
PROTECTED_PATH_ALIASES = (
    ("workspaces/{ws}/audit/journal.jsonl:", "alternate data stream"),
    ("workspaces/{ws}/audit/journal.jsonl:stream", "alternate data stream"),
    ("workspaces/{ws}/audit/journal.jsonl::$DATA", "alternate data stream"),
    ("workspaces/{ws}/audit/JOURNAL.JSONL", "would write the audit journal"),
    ("workspaces/{ws}/audit./journal.jsonl", "trailing dot"),
    ("workspaces/{ws}/audit/journal.jsonl.", "trailing dot"),
    ("workspaces/{ws}/audit /journal.jsonl", "trailing whitespace"),
    ("workspaces/{ws}/audit/JOURNA~1.JSO", "8.3 short-name"),
    ("{repo}/SRC/**", "source tree"),
    ("workspaces/{ws}/audit/journal.jsonl\x00x", "control character"),
)


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "generate_agent_roles", GENERATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _stage(tmp_path: Path) -> Path:
    """Copy the generated agent layer into ``tmp_path`` for mutation."""
    root = tmp_path / "repo"
    shutil.copytree(ROLES_DIR, root / "roles")
    shutil.copytree(AGENT_DIR, root / ".opencode" / "agent")
    return root


def _append_to_prompt(root: Path, role_id: str, sentence: str) -> None:
    """Append one sentence to a staged prompt body, leaving the real tree alone."""
    prompt = root / "roles" / f"{role_id}.prompt.md"
    prose = prompt.read_text(encoding="utf-8")
    prompt.write_text(f"{prose}\n{sentence}\n", encoding="utf-8", newline="\n")


def _role_payload(root: Path, role_id: str) -> dict:
    return json.loads((root / "roles" / f"{role_id}.json").read_text(encoding="utf-8"))


def _write_role(root: Path, role_id: str, payload: dict) -> None:
    path = root / "roles" / f"{role_id}.json"
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _frontmatter(doc: str) -> dict:
    frontmatter, _body = gen.split_frontmatter(doc)
    return gen.parse_frontmatter(frontmatter)


def _lf(data: bytes) -> bytes:
    """Normalise a checkout to LF so the byte claim is platform independent."""
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _spec_role_example() -> dict:
    """Return the Role@1 example from the spec's section 2 JSON block."""
    text = SPEC_ROLE_MODEL.read_text(encoding="utf-8")
    examples = []
    for block in re.findall(r"```json\n(.*?)```", text, re.DOTALL):
        try:
            candidate = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and candidate.get("kind") == "role":
            examples.append(candidate)
    assert len(examples) == 1, (
        f"expected one Role@1 JSON example, found {len(examples)}"
    )
    return examples[0]


def _clause_start(body: str, position: int) -> int:
    """Return the offset where the clause containing ``position`` begins."""
    boundary = None
    for boundary in CLAUSE_BOUNDARY_RE.finditer(body, 0, position):
        pass
    return 0 if boundary is None else boundary.end()


def _negation_guard_start(body: str, subject_start: int, verb_start: int) -> int:
    """Return where the negation guard begins for a subject--verb span.

    The guard is clause-scoped, not sentence-scoped: it starts after the last
    clause boundary (``,``, ``;``, ``and``, ``but``, ``yet``, ``so``) between the
    role subject and the verb, so a negation belonging to an earlier clause
    cannot mask a later claim. When no boundary intervenes -- "The critic never
    writes ..." -- the guard starts at the subject and the negation applies.
    """
    guard_start = subject_start
    for boundary in NEGATION_RESET_RE.finditer(body, subject_start, verb_start):
        guard_start = boundary.end()
    return guard_start


def _declarative_subject(
    body: str, verb_start: int, subject_re: re.Pattern[str]
) -> tuple[int, int] | None:
    """Locate the role subject governing a write verb.

    Returns ``(subject_start, guard_start)``. The subject must belong to the
    verb's own clause, so a subject in an earlier clause cannot be borrowed to
    justify a claim it does not govern. A clause opened by ``it``/``they``
    inherits the role subject of the previous clause; the negation guard then
    starts at the pronoun's clause, so the previous clause's negation cannot
    mask the claim. Within one clause the guard additionally resets at an
    internal clause boundary (``,``, ``;``, ``and``, ``but``, ``yet``, ``so``).
    """
    clause_start = _clause_start(body, verb_start)
    clause_prefix = body[clause_start:verb_start]
    nearest = None
    for nearest in subject_re.finditer(clause_prefix):
        pass
    if nearest is not None:
        start = clause_start + nearest.start()
        return start, _negation_guard_start(body, start, verb_start)
    if not ANAPHOR_RE.match(clause_prefix.lstrip()) or clause_start == 0:
        return None
    previous_start = _clause_start(body, clause_start - 1)
    previous_clause = body[previous_start:clause_start]
    inherited = None
    for inherited in subject_re.finditer(previous_clause):
        pass
    if inherited is None:
        return None
    return previous_start + inherited.start(), clause_start


def find_write_claims(body: str, role_id: str) -> list[str]:
    """Return write-claim findings from the literal and declarative detectors.

    Detector (a) matches the pathless first-person imperatives that motivated the
    original fix. Detector (b) matches a third-person declarative claim: a write
    verb, a role-self subject in the verb's own clause, and a concrete file-path
    token within ``PATH_WINDOW`` characters after it. Detector (c) matches the
    passive restatement (``is written by <role>``), which review named as the most
    natural paraphrase.

    The negation guard is scoped to the subject--verb span and resets at the
    last clause boundary inside it (``,``, ``;``, ``and``, ``but``, ``yet``,
    ``so``), so a negation governing an earlier clause does not suppress a
    later claim. The subject search is bounded by the verb's clause rather than
    by a character window.

    This is a heuristic, not a proof: a claim paraphrased without a path token,
    or attributed to a subject other than the role, is not reported. It fails
    closed, so a legitimate sentence can be reported and must be reworded; the
    known classes are listed in D16 of the decision record.
    """
    findings = [
        f"literal phrase {phrase!r}"
        for phrase in WRITE_CLAIM_PHRASES
        if phrase in body.lower()
    ]

    subjects = (*ROLE_SELF_SUBJECTS, role_id.replace("-", " "))
    subject_re = re.compile(
        r"\b(?:" + "|".join(re.escape(subject) for subject in subjects) + r")\b",
        re.IGNORECASE,
    )
    for verb in WRITE_CLAIM_VERB_RE.finditer(body):
        claim = _declarative_subject(body, verb.start(), subject_re)
        if claim is None:
            continue
        _subject_start, guard_start = claim
        if WRITE_CLAIM_NEGATION_RE.search(body[guard_start : verb.start()]):
            continue
        suffix = body[verb.end() : verb.end() + PATH_WINDOW]
        path = WRITE_CLAIM_PATH_RE.search(suffix)
        if path is None:
            continue
        findings.append(
            f"declarative verb {verb.group(0)!r} with path {path.group(0)!r}"
        )

    for passive in PASSIVE_CLAIM_RE.finditer(body):
        subject = subject_re.match(body, passive.end())
        if subject is None:
            continue
        window = body[
            max(0, passive.start() - PATH_WINDOW) : subject.end() + PATH_WINDOW
        ]
        path = WRITE_CLAIM_PATH_RE.search(window)
        if path is None:
            continue
        findings.append(
            f"passive claim {passive.group(0).strip()!r} with path {path.group(0)!r}"
        )
    return findings


def _assert_write_claims_match_authorship(root: Path, roles: dict[str, dict]) -> None:
    """A body may claim a write only when the role itself writes an output."""
    for role_id in sorted(roles):
        body = (root / "roles" / f"{role_id}.prompt.md").read_text(encoding="utf-8")
        findings = find_write_claims(body, role_id)
        claims = bool(findings)
        writes_own = any(
            output.get("written_by", "role") == "role"
            for output in roles[role_id]["outputs"]
        )
        if claims:
            assert writes_own, (
                f"{role_id} claims it writes ({'; '.join(findings)}), but every "
                f"output is written_by: adapter"
            )
        if not writes_own:
            assert not claims, (
                f"{role_id} is entirely adapter-persisted and must not claim a write "
                f"({'; '.join(findings)})"
            )


def _synthetic_role(**overrides: object) -> dict:
    """A minimal valid Role@1 record; one derivation rule is varied at a time."""
    role: dict = {
        "audit": {"actor": "{role}@{version}", "emit": ["SYNTHETIC_COMPLETED"]},
        "deny_glob": [gen.AUDIT_TREE, gen.GIT_DIR],
        "id": "synthetic-critic",
        "independence": {"blinded_from": [], "isolation": "none"},
        "inputs": [
            {"from": "written-input", "required": True, "schema": "TaskPacket@1"}
        ],
        "kind": "role",
        "mode": "subagent",
        "network": "deny",
        "outputs": [
            {
                "required": True,
                "schema": "SyntheticReport@1",
                "write_glob": "runs/{task_id}/synthetic.json",
                "written_by": "adapter",
            }
        ],
        "purpose": "Synthetic role used to pin one derivation rule in isolation.",
        "read_glob": ["runs/{task_id}/synthetic.json"],
        "refusal_codes": ["BLOCKED_INPUT", "INVALID_OUTPUT"],
        "requires_skill": [],
        "stop_conditions": ["the assigned packet is incomplete"],
        "title": "Synthetic Critic",
        "tools": ["edit", "glob", "grep", "list", "read"],
        "version": "2.0.0",
    }
    role.update(overrides)
    return role


def _stage_synthetic(tmp_path: Path, *roles: dict) -> Path:
    """Write the given synthetic records into an otherwise empty ``roles/`` tree."""
    root = tmp_path / "repo"
    roles_dir = root / "roles"
    roles_dir.mkdir(parents=True)
    for role in roles:
        (roles_dir / f"{role['id']}.json").write_text(
            json.dumps(role, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return root


# --------------------------------------------------------------------------- #
# positive conformance: the real tree
# --------------------------------------------------------------------------- #


def test_role_catalogue_is_the_twelve_agents() -> None:
    roles = gen.load_roles(ROOT)
    assert set(roles) == EXPECTED_ROLES
    assert len(roles) == len(EXPECTED_ROLES)


def test_duplicate_role_ids_make_the_loader_raise(tmp_path: Path) -> None:
    """Two records with one ``id`` must fail the loader, not silently override."""
    root = _stage(tmp_path)
    source = root / "roles" / "screener.json"
    duplicate = root / "roles" / "screener-copy.json"
    duplicate.write_text(
        source.read_text(encoding="utf-8"), encoding="utf-8", newline="\n"
    )
    with pytest.raises(gen.RoleError, match="duplicate role id 'screener'"):
        gen.load_roles(root)


def test_every_output_declares_a_write_glob() -> None:
    for role_id, role in gen.load_roles(ROOT).items():
        assert role["outputs"], f"{role_id} declares no output"
        for output in role["outputs"]:
            assert output.get("write_glob"), (
                f"{role_id}.{output['schema']} has no write_glob"
            )


def test_all_shipped_globs_still_validate() -> None:
    """RR11 acceptance: every shipped record still validates, 95 globs in all.

    The case-folding comparison and the non-canonical-segment rejection must not
    over-reject the declared catalogue, including its upper-case filenames
    (``INDEX.md``, ``SCREENING_CRITERIA.md``) and ``extracted/A/``.
    """
    roles = gen.load_roles(ROOT)
    assert len(roles) == 12
    total = 0
    for role_id, role in roles.items():
        pairs = [
            *[("read_glob", item) for item in role["read_glob"]],
            *[("deny_glob", item) for item in role["deny_glob"]],
            *[("write_glob", output["write_glob"]) for output in role["outputs"]],
        ]
        for field, glob in pairs:
            assert (
                gen.validate_glob(glob, ROLES_DIR / f"{role_id}.json", field) == glob
            ), (role_id, field, glob)
        total += len(pairs)
    assert total == 95


def test_read_only_descriptions_exclude_write_capabilities() -> None:
    for role_id, role in gen.load_roles(ROOT).items():
        if "read-only" not in role["purpose"].lower():
            continue
        assert not set(role["tools"]) & {"edit", "write"}, (
            f"{role_id} claims read-only but grants {sorted(set(role['tools']) & {'edit', 'write'})}"
        )


def test_generated_files_match_role_records() -> None:
    assert gen.check_root(ROOT) == []


def test_cli_check_mode_is_green() -> None:
    assert gen.main(["--check", "--root", str(ROOT)]) == 0


def test_spec_section_2_example_validates_against_the_loader(tmp_path: Path) -> None:
    """The normative Role@1 example must satisfy the same validator as ``roles/``.

    Without this, the specification's own example can drift away from the rules
    it states (it previously failed R3 and R7). The example is validated
    literally, with no field patched in: ``mode`` is part of the section 2
    schema, so a missing or changed ``mode`` must fail here rather than be
    silently repaired by the test.
    """
    role = _spec_role_example()
    assert role["id"] == "screening-critic"
    assert "mode" in role, (
        "the section 2 Role@1 example must declare 'mode'; it is part of the schema"
    )
    assert role["mode"] == "subagent", (
        f"the section 2 Role@1 example must declare mode 'subagent', found "
        f"{role['mode']!r}"
    )
    path = tmp_path / "roles" / f"{role['id']}.json"
    path.parent.mkdir(parents=True)
    known_ids = {"adjudicator", "screener", role["id"]}

    # Any contract violation (including a missing field) propagates as RoleError.
    gen.validate_role(role, path, known_ids)
    assert role["outputs"][0]["written_by"] == "adapter"
    assert gen.derive_permissions(role)["edit"] == "deny"


def test_permissions_fragment_matches_derivation() -> None:
    roles = gen.load_roles(ROOT)
    payload = json.loads(PERMISSIONS_FILE.read_text(encoding="utf-8"))
    assert payload["schema"] == gen.PERMISSIONS_SCHEMA
    assert set(payload["roles"]) == set(roles)
    for role_id, role in roles.items():
        entry = payload["roles"][role_id]
        assert entry["permission"] == gen.derive_permissions(role), role_id
        assert entry["write_glob"] == [
            output["write_glob"] for output in role["outputs"]
        ]
        assert entry["independence"] == role["independence"]
        assert entry["network"] == role["network"]


def test_permissions_map_matches_independently_authored_fixture() -> None:
    """Pin the map against a hand-authored expectation, not the derivation.

    ``test_permissions_fragment_matches_derivation`` compares the generator's
    output to the generator's own function, so it cannot catch a wrong
    derivation rule. This fixture is authored from spec section 6 plus D2's
    ``bash_approval`` field and never copied from generated output.
    """
    fixture = json.loads(EXPECTED_PERMISSIONS.read_text(encoding="utf-8"))
    payload = json.loads(PERMISSIONS_FILE.read_text(encoding="utf-8"))
    actual = {
        role_id: entry["permission"] for role_id, entry in payload["roles"].items()
    }
    assert fixture["schema"] == "ExpectedAgentPermissions@1"
    assert set(actual) == EXPECTED_ROLES
    assert set(fixture["roles"]) == EXPECTED_ROLES
    for role_id in sorted(EXPECTED_ROLES):
        assert set(actual[role_id]) == set(gen.CAPABILITIES) - {"write"}
        assert actual[role_id] == fixture["roles"][role_id], role_id


def test_critic_roles_deny_every_read_family_outside_their_write_glob() -> None:
    """R7: a critic denies every read family it is not allowed to write."""
    roles = gen.load_roles(ROOT)
    critic_ids = gen.critic_role_ids(roles)
    assert critic_ids == {
        "extraction-critic",
        "reviewer",
        "screening-critic",
    }, (
        "the critic set is derived from the records (id or purpose says 'critic', "
        "plus reviewer); a new critic must appear here without a code change"
    )
    for role_id in sorted(critic_ids):
        role = roles[role_id]
        write_globs = [output["write_glob"] for output in role["outputs"]]
        role_written = any(
            output.get("written_by", "role") == "role" for output in role["outputs"]
        )
        for family in role["read_glob"]:
            if any(gen.glob_within(family, write_glob) for write_glob in write_globs):
                continue
            if family == "**":
                # A repo-wide reader cannot deny '**' without contradicting its
                # own output; R7 is satisfied by the absence of a write capability.
                assert not role_written, f"{role_id} reads '**' and can write"
                assert gen.derive_permissions(role)["edit"] == "deny"
                continue
            assert any(
                gen.glob_within(family, deny_glob) for deny_glob in role["deny_glob"]
            ), f"{role_id} reads {family!r} outside its write_glob but does not deny it"


def test_critic_set_equals_the_spec_definition() -> None:
    """R7's critic set is the definition in the specification, not a name list.

    The expectation is written from R7 itself -- a role whose ``id`` or
    ``purpose`` contains ``critic``, plus ``reviewer`` -- rather than by calling
    the generator's predicate, so a change to that predicate fails here. The
    ``reviewer`` clause is id-keyed because the specification makes it so: the
    reviewer's purpose describes adversarial review without the word "critic",
    and R7 names it explicitly (RR10).
    """
    roles = gen.load_roles(ROOT)
    expected = {
        role_id
        for role_id, role in roles.items()
        if role_id == "reviewer"
        or "critic" in role_id.lower()
        or "critic" in str(role.get("purpose", "")).lower()
    }
    assert gen.critic_role_ids(roles) == expected
    assert expected == {"extraction-critic", "reviewer", "screening-critic"}


def test_every_role_denies_the_audit_journal_and_git_history() -> None:
    """R4/§4: ``deny_glob`` always contains the journal and ``.git/**``.

    The rule is unconditional: a repo-wide ``read_glob: ["**"]`` no longer buys
    an exemption. A broader ``audit/**`` denial satisfies the journal clause for
    roles that never write under ``audit/``.
    """
    roles = gen.load_roles(ROOT)
    assert len(roles) == len(EXPECTED_ROLES) == 12
    for role_id, role in roles.items():
        assert any(
            gen.glob_within(gen.AUDIT_JOURNAL, deny_glob)
            for deny_glob in role["deny_glob"]
        ), f"{role_id} does not deny the audit journal"
        assert any(
            gen.glob_within(gen.GIT_DIR, deny_glob) for deny_glob in role["deny_glob"]
        ), f"{role_id} does not deny .git/**"


def test_role_omitting_the_journal_denial_fails(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "coder")
    payload["deny_glob"] = [
        item for item in payload["deny_glob"] if "journal" not in item
    ]
    _write_role(root, "coder", payload)
    with pytest.raises(gen.RoleError, match="deny_glob must deny"):
        gen.load_roles(root)


def test_role_omitting_the_git_denial_fails(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "tester")
    payload["deny_glob"] = [
        item for item in payload["deny_glob"] if item != gen.GIT_DIR
    ]
    _write_role(root, "tester", payload)
    with pytest.raises(gen.RoleError, match="deny_glob must deny"):
        gen.load_roles(root)


def test_required_input_from_a_blinded_role_fails(tmp_path: Path) -> None:
    """R6: a required input may not come from a role the adapter hides."""
    peer = _synthetic_role(id="synthetic-peer", title="Synthetic Peer")
    role = _synthetic_role(
        independence={"blinded_from": ["synthetic-peer"], "isolation": "directory"},
        inputs=[{"from": "synthetic-peer", "required": True, "schema": "TaskPacket@1"}],
    )
    assert role["independence"]["blinded_from"] == ["synthetic-peer"]
    root = _stage_synthetic(tmp_path, peer, role)
    with pytest.raises(gen.RoleError, match="blinded_from"):
        gen.load_roles(root)


def test_synthesis_critic_is_subject_to_r7(tmp_path: Path) -> None:
    """R7 is derived: a new critic cannot escape it with a hardcoded list."""
    role = _synthetic_role(
        id="synthesis-critic",
        title="Synthesis Critic",
        read_glob=["workspaces/{ws}/synthesis/**"],
    )
    assert gen.critic_role_ids({role["id"]: role}) == {"synthesis-critic"}
    root = _stage_synthetic(tmp_path, role)
    with pytest.raises(gen.RoleError, match="R7"):
        gen.load_roles(root)


def test_repo_parameter_addresses_repository_assets() -> None:
    roles = gen.load_roles(ROOT)
    read_glob = roles["inception-agent"]["read_glob"]
    assert "{repo}/.agents/skills/**" in read_glob
    assert "{repo}/.cache/inception_recon/**" in read_glob
    assert "{repo}/.mcp.json" in read_glob
    assert ".git/**" in roles["inception-agent"]["deny_glob"]


def test_bare_repo_relative_glob_is_rejected(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "inception-agent")
    payload["read_glob"][0] = ".agents/skills/**"
    _write_role(root, "inception-agent", payload)
    with pytest.raises(gen.RoleError, match="repo-relative"):
        gen.load_roles(root)


def test_generated_frontmatter_matches_derivation() -> None:
    for role_id, role in gen.load_roles(ROOT).items():
        fields = _frontmatter((AGENT_DIR / f"{role_id}.md").read_text(encoding="utf-8"))
        assert fields["kind"] == "role"
        assert fields["mode"] == role["mode"]
        assert fields["description"] == role["purpose"]
        if fields["permission"] == "allow":
            assert role_id in SHORTHAND_ROLES, (
                f"{role_id} uses the all-allow shorthand, reserved for "
                f"{sorted(SHORTHAND_ROLES)}"
            )
            assert all(
                value == "allow" for value in gen.derive_permissions(role).values()
            )
        else:
            assert fields["permission"] == gen.derive_permissions(role)


def test_critic_and_verifier_do_not_grant_edit() -> None:
    roles = gen.load_roles(ROOT)
    for role_id in ("screening-critic", "tester"):
        assert "edit" not in roles[role_id]["tools"]
        assert gen.derive_permissions(roles[role_id])["edit"] == "deny"
    assert gen.derive_permissions(roles["reviewer"])["edit"] == "deny"


def test_reviewer_keeps_approval_gated_shell() -> None:
    fields = _frontmatter((AGENT_DIR / "reviewer.md").read_text(encoding="utf-8"))
    assert fields["permission"]["edit"] == "deny"
    assert fields["permission"]["bash"] == "ask"
    assert fields["permission"]["read"] == "allow"


def test_refusal_codes_are_in_the_closed_registry() -> None:
    for role_id, role in gen.load_roles(ROOT).items():
        unknown = set(role["refusal_codes"]) - gen.GLOBAL_REFUSAL_CODES
        assert not unknown, (
            f"{role_id} declares unknown refusal codes {sorted(unknown)}"
        )


def test_opencode_json_carries_no_decorative_agent_block() -> None:
    """opencode.json configures the MCP server only.

    The former ``agents`` block registered four roles with a harness-internal
    ``permissionRef`` pointer that opencode never read: agents are discovered
    from ``.opencode/agent/*.md``, whose frontmatter is generated from the role
    records. Keeping the block implied a permission surface that did not exist,
    so it was removed rather than left as decoration.
    """
    config = json.loads((ROOT / "opencode.json").read_text(encoding="utf-8"))
    assert "agents" not in config
    assert "permissionRef" not in json.dumps(config)
    assert "permission" not in config
    for role_id in EXPECTED_ROLES:
        assert (AGENT_DIR / f"{role_id}.md").is_file(), (
            f"{role_id} has no discovery surface"
        )


def test_generated_bodies_are_byte_identical_to_prompt_sources() -> None:
    documents = gen.expected_files(ROOT)
    for role_id in sorted(EXPECTED_ROLES):
        relative = f".opencode/agent/{role_id}.md"
        prompt_bytes = (ROLES_DIR / f"{role_id}.prompt.md").read_bytes()

        # The generator's own output is LF-only on every platform.
        generated = documents[relative]
        assert "\r" not in generated, f"{relative} is not LF-only"
        _frontmatter_text, generated_body = gen.split_frontmatter(generated)
        assert generated_body.encode("utf-8") == _lf(prompt_bytes), (
            f"{role_id} body drifted from its prompt source"
        )

        # The checked-out file may be CRLF because git normalises on checkout
        # (core.autocrlf); compare the body exactly after newline normalisation.
        _frontmatter_text, disk_body = gen.split_frontmatter(
            (AGENT_DIR / f"{role_id}.md").read_bytes().decode("utf-8")
        )
        assert disk_body.encode("utf-8") == _lf(prompt_bytes)
        assert len(prompt_bytes) > 200, f"{role_id} prompt body is suspiciously small"


def test_body_write_claims_match_output_authorship() -> None:
    """A body may say "I write" only when the record gives it something to write.

    This guard detects the repaired ``screening-critic`` shapes: the record says
    ``written_by: adapter``, so a body that still claims the write fails. Detection
    is bounded (D16 in the decision record); review remains the control for the
    paraphrases it does not detect.
    """
    _assert_write_claims_match_authorship(ROOT, gen.load_roles(ROOT))


def test_adapter_only_role_making_a_write_claim_fails(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    prompt = root / "roles" / "reviewer.prompt.md"
    prompt.write_text(
        prompt.read_text(encoding="utf-8") + "\nWrite only the review artifact.\n",
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(AssertionError, match="written_by: adapter"):
        _assert_write_claims_match_authorship(root, gen.load_roles(root))


# --------------------------------------------------------------------------- #
# prose guard: declarative claims naming a path (probe 6)
# --------------------------------------------------------------------------- #


def test_declarative_write_claim_in_adapter_role_fails(tmp_path: Path) -> None:
    """The exact probe-6 sentence that the literal-only detector missed."""
    root = _stage(tmp_path)
    _append_to_prompt(
        root,
        "screening-critic",
        "The critic writes `critique/screening/report.md` to the workspace.",
    )
    with pytest.raises(AssertionError, match="written_by: adapter"):
        _assert_write_claims_match_authorship(root, gen.load_roles(root))


def test_declarative_persist_claim_with_a_path_fails_for_reviewer(
    tmp_path: Path,
) -> None:
    root = _stage(tmp_path)
    _append_to_prompt(
        root,
        "reviewer",
        "The reviewer persists its verdict at `review/verdict.json`.",
    )
    with pytest.raises(AssertionError, match="written_by: adapter"):
        _assert_write_claims_match_authorship(root, gen.load_roles(root))


def test_declarative_write_claim_with_negation_passes(tmp_path: Path) -> None:
    sentence = "The critic never writes `critique/x.json`."
    root = _stage(tmp_path)
    _append_to_prompt(root, "screening-critic", sentence)
    assert find_write_claims(sentence, "screening-critic") == []
    _assert_write_claims_match_authorship(root, gen.load_roles(root))


def test_declarative_write_claim_with_non_role_subject_passes(tmp_path: Path) -> None:
    sentence = "The harness writes `critique/x.json`."
    root = _stage(tmp_path)
    _append_to_prompt(root, "screening-critic", sentence)
    assert find_write_claims(sentence, "screening-critic") == []
    _assert_write_claims_match_authorship(root, gen.load_roles(root))


def test_declarative_write_claim_without_a_path_token_passes(tmp_path: Path) -> None:
    sentence = "The critic writes careful prose."
    root = _stage(tmp_path)
    _append_to_prompt(root, "screening-critic", sentence)
    assert find_write_claims(sentence, "screening-critic") == []
    _assert_write_claims_match_authorship(root, gen.load_roles(root))


def test_negation_in_an_earlier_clause_does_not_mask_a_claim(tmp_path: Path) -> None:
    """A negation governing an earlier clause must not suppress a later claim.

    This is the exact shape of the original contradiction: a prohibition and a
    genuine claim in adjacent clauses. Before T-ALP-A-r3 the negation guard
    scanned 60 characters before the subject, so ``Do not`` masked ``writes``.
    """
    sentence = (
        "Do not edit the decisions; the critic writes `critique/screening/report.md`."
    )
    root = _stage(tmp_path)
    _append_to_prompt(root, "screening-critic", sentence)
    assert find_write_claims(sentence, "screening-critic"), (
        "the negation guard must stop at the clause boundary, not scan backwards"
    )
    with pytest.raises(AssertionError, match="written_by: adapter"):
        _assert_write_claims_match_authorship(root, gen.load_roles(root))


def test_negation_before_an_anaphoric_claim_does_not_mask_it(tmp_path: Path) -> None:
    """The same shape with a pronoun subject: ``... batch; it writes ...``."""
    sentence = (
        "The critic never repairs the batch; it writes `critique/screening/report.md`."
    )
    root = _stage(tmp_path)
    _append_to_prompt(root, "screening-critic", sentence)
    assert find_write_claims(sentence, "screening-critic"), (
        "a clause-opening pronoun inherits the role subject of the previous clause"
    )
    with pytest.raises(AssertionError, match="written_by: adapter"):
        _assert_write_claims_match_authorship(root, gen.load_roles(root))


@pytest.mark.parametrize(
    "sentence",
    [
        "The critic never repairs the batch but writes `critique/x.json`.",
        "The critic does not edit decisions and writes `critique/x.json`.",
        "The critic, which never edits decisions, writes `critique/x.json`.",
    ],
)
def test_negation_before_a_clause_reset_does_not_mask_a_claim(
    tmp_path: Path, sentence: str
) -> None:
    """The negation guard resets at ``,``, ``;``, ``and``, ``but``, ``yet``, ``so``.

    These are the original defect shape with the negation in a *different*
    clause of the same sentence: through r3 the guard was sentence-scoped, so
    each returned no finding (F4). The third sentence additionally sits beyond
    the old 40-character subject window, so it pins clause-scoped attribution.
    """
    root = _stage(tmp_path)
    _append_to_prompt(root, "screening-critic", sentence)
    assert find_write_claims(sentence, "screening-critic"), (
        "a negation in an earlier clause must not mask a later claim"
    )
    with pytest.raises(AssertionError, match="written_by: adapter"):
        _assert_write_claims_match_authorship(root, gen.load_roles(root))


def test_negation_inside_the_same_clause_still_masks_the_claim(
    tmp_path: Path,
) -> None:
    """Control: a comma does not reset a negation that follows it.

    The guard starts after the last boundary *between subject and verb*, so a
    negation after that boundary is still seen and the sentence stays clean.
    """
    sentence = "The critic, when it judges a batch, never writes `critique/x.json`."
    root = _stage(tmp_path)
    _append_to_prompt(root, "screening-critic", sentence)
    assert find_write_claims(sentence, "screening-critic") == []
    _assert_write_claims_match_authorship(root, gen.load_roles(root))


def test_passive_write_claim_fails_for_an_adapter_role(tmp_path: Path) -> None:
    """The passive restatement review called the most natural paraphrase."""
    sentence = "`critique/x.json` is written by the critic."
    root = _stage(tmp_path)
    _append_to_prompt(root, "screening-critic", sentence)
    findings = find_write_claims(sentence, "screening-critic")
    assert findings and "passive" in findings[0], findings
    with pytest.raises(AssertionError, match="written_by: adapter"):
        _assert_write_claims_match_authorship(root, gen.load_roles(root))


def test_passive_claim_attributed_to_the_harness_passes(tmp_path: Path) -> None:
    """``the harness`` is not the role: the harness legitimately writes the file."""
    sentence = "`critique/x.json` is written by the harness."
    root = _stage(tmp_path)
    _append_to_prompt(root, "screening-critic", sentence)
    assert find_write_claims(sentence, "screening-critic") == []
    _assert_write_claims_match_authorship(root, gen.load_roles(root))


def test_declarative_write_claim_is_legal_for_a_role_written_output(
    tmp_path: Path,
) -> None:
    sentence = "The coder writes `runs/{task_id}/coder_report.json`."
    root = _stage(tmp_path)
    _append_to_prompt(root, "coder", sentence)
    assert find_write_claims(sentence, "coder"), (
        "the declarative detector must report the claim, not ignore it"
    )
    roles = gen.load_roles(root)
    assert any(
        output.get("written_by", "role") == "role"
        for output in roles["coder"]["outputs"]
    )
    _assert_write_claims_match_authorship(root, roles)


# --------------------------------------------------------------------------- #
# loader: only roles may load from the agent directory
# --------------------------------------------------------------------------- #


def test_loader_accepts_every_generated_agent() -> None:
    for role_id in sorted(EXPECTED_ROLES):
        fields = gen.load_agent_definition(AGENT_DIR / f"{role_id}.md")
        assert fields["kind"] == "role"
        assert fields["description"]


def test_loader_rejects_the_moved_git_workflow_policy_document() -> None:
    policy = ROOT / "docs" / "architecture" / "git_workflow.md"
    assert policy.is_file(), "git_workflow.md must live outside the agent directory"
    assert "# Git Workflow" in policy.read_text(encoding="utf-8")
    with pytest.raises(gen.AgentLoadError):
        gen.load_agent_definition(policy)


def test_loader_rejects_a_frontmatter_file_without_kind_role(tmp_path: Path) -> None:
    impostor = tmp_path / "policy.md"
    impostor.write_text(
        '---\ndescription: "A policy document that is not an agent."\nmode: subagent\n---\n\nProse.\n',
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(gen.AgentLoadError, match="kind"):
        gen.load_agent_definition(impostor)


def test_loader_rejects_kind_doc(tmp_path: Path) -> None:
    impostor = tmp_path / "doc.md"
    impostor.write_text(
        '---\ndescription: "A document."\nkind: doc\nmode: subagent\n---\n\nProse.\n',
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(gen.AgentLoadError, match="kind"):
        gen.load_agent_definition(impostor)


def test_git_workflow_is_not_left_in_the_agent_directory() -> None:
    assert not (AGENT_DIR / "git_workflow.md").exists()
    assert gen.check_root(ROOT) == []


# --------------------------------------------------------------------------- #
# negative cases: mutations must fail the gate
# --------------------------------------------------------------------------- #


def test_hand_edited_generated_file_fails_check(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    target = root / ".opencode" / "agent" / "reviewer.md"
    target.write_text(
        target.read_text(encoding="utf-8") + "\nTampered after generation.\n",
        encoding="utf-8",
        newline="\n",
    )
    assert ".opencode/agent/reviewer.md" in gen.check_root(root)
    assert gen.main(["--check", "--root", str(root)]) == 1


def test_body_drift_fails_check(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    prompt = root / "roles" / "screener.prompt.md"
    prompt.write_text(
        prompt.read_text(encoding="utf-8") + "\nExtra instruction.\n",
        encoding="utf-8",
        newline="\n",
    )
    assert "roles/screener.prompt.md" not in gen.check_root(root)
    assert ".opencode/agent/screener.md" in gen.check_root(root)


def test_adding_edit_to_screening_critic_fails(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "screening-critic")
    payload["tools"] = sorted({*payload["tools"], "edit"})
    _write_role(root, "screening-critic", payload)
    with pytest.raises(gen.RoleError, match="read-only"):
        gen.load_roles(root)


def test_role_without_write_glob_fails(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "extractor-a")
    payload["outputs"][0].pop("write_glob")
    _write_role(root, "extractor-a", payload)
    with pytest.raises(gen.RoleError, match="write_glob"):
        gen.load_roles(root)


def test_blinded_from_unknown_role_fails(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "extractor-b")
    payload["independence"]["blinded_from"] = [
        *payload["independence"]["blinded_from"],
        "ghost-role",
    ]
    _write_role(root, "extractor-b", payload)
    with pytest.raises(gen.RoleError, match="unknown roles"):
        gen.load_roles(root)


def test_write_glob_intersecting_deny_glob_fails(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "screener")
    payload["outputs"][0]["write_glob"] = "workspaces/{ws}/audit/decisions.json"
    _write_role(root, "screener", payload)
    with pytest.raises(gen.RoleError, match="deny_glob"):
        gen.load_roles(root)


def test_write_glob_never_writes_the_audit_journal(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "coder")
    payload["outputs"][0]["write_glob"] = "workspaces/{ws}/audit/journal.jsonl"
    _write_role(root, "coder", payload)
    with pytest.raises(gen.RoleError, match="audit journal"):
        gen.load_roles(root)


def test_dot_segment_cannot_hide_the_audit_journal(tmp_path: Path) -> None:
    """R2/R4: ``audit/./journal.jsonl`` is the journal path spelled differently.

    Before T-ALP-A-r4 this record was accepted, because only ``..`` was rejected
    and the intersection compared raw segments (F1).
    """
    root = _stage(tmp_path)
    payload = _role_payload(root, "coder")
    payload["outputs"][0]["write_glob"] = "workspaces/{ws}/audit/./journal.jsonl"
    _write_role(root, "coder", payload)
    with pytest.raises(gen.RoleError, match="current-directory"):
        gen.load_roles(root)


def test_empty_segment_cannot_hide_the_audit_journal(tmp_path: Path) -> None:
    """R2/R4: ``audit//journal.jsonl`` is the journal path spelled differently."""
    root = _stage(tmp_path)
    payload = _role_payload(root, "coder")
    payload["outputs"][0]["write_glob"] = "workspaces/{ws}/audit//journal.jsonl"
    _write_role(root, "coder", payload)
    with pytest.raises(gen.RoleError, match="empty segment"):
        gen.load_roles(root)


def test_glob_relations_normalise_dot_and_empty_segments() -> None:
    """R2 consequence 4: ``a/./b`` and ``a/b`` are the same path everywhere."""
    assert gen.globs_intersect(
        "workspaces/{ws}/audit/./journal.jsonl",
        "workspaces/{ws}/audit/journal.jsonl",
    )
    assert gen.globs_intersect(
        "workspaces/{ws}/audit//journal.jsonl",
        "workspaces/{ws}/audit/journal.jsonl",
    )
    assert gen.glob_within(
        "workspaces/{ws}/audit/./journal.jsonl", "workspaces/{ws}/audit/**"
    )


def test_case_folded_audit_write_glob_is_rejected_as_the_journal(
    tmp_path: Path,
) -> None:
    """RR11: win32 folds case, so ``AUDIT`` names the journal's directory.

    The segment itself is a legitimate filename (``INDEX.md`` may not be
    rejected), so R4 catches the alias through a case-folded intersection. The
    loader error proves ``validate_glob`` accepted the glob and R4 refused it.
    """
    write_glob = "workspaces/{ws}/AUDIT/journal.jsonl"
    assert gen.globs_intersect(write_glob, gen.AUDIT_JOURNAL)
    root = _stage(tmp_path)
    payload = _role_payload(root, "coder")
    payload["outputs"][0]["write_glob"] = write_glob
    _write_role(root, "coder", payload)
    with pytest.raises(gen.RoleError, match="would write the audit journal"):
        gen.load_roles(root)


def test_case_folded_intersection_and_containment() -> None:
    """RR11: comparison folds case; the declared spelling is never rewritten."""
    assert gen.globs_intersect("workspaces/{ws}/Audit/Journal.jsonl", gen.AUDIT_JOURNAL)
    assert gen.glob_within("workspaces/{ws}/AUDIT/journal.jsonl", gen.AUDIT_JOURNAL)
    assert not gen.globs_intersect(gen.AUDIT_JOURNAL, "workspaces/{ws}/INDEX.md")


@pytest.mark.parametrize(
    ("write_glob", "expected"),
    [
        ("workspaces/{ws}/audit./journal.jsonl", "trailing dot"),
        ("workspaces/{ws}/audit/journal.jsonl.", "trailing dot"),
        ("workspaces/{ws}/audit /journal.jsonl", "trailing whitespace"),
    ],
)
def test_non_canonical_segment_is_rejected(
    tmp_path: Path, write_glob: str, expected: str
) -> None:
    """RR11: win32 strips a trailing dot or space, so both alias the journal.

    ``validate_glob`` rejects the spelling outright, before any comparison: a
    resolver that normalises differently cannot reintroduce the alias.
    """
    root = _stage(tmp_path)
    payload = _role_payload(root, "coder")
    payload["outputs"][0]["write_glob"] = write_glob
    _write_role(root, "coder", payload)
    with pytest.raises(gen.RoleError, match=expected):
        gen.load_roles(root)


@pytest.mark.parametrize(
    "write_glob",
    [
        "workspaces/{ws}/audit/journal.jsonl:",
        "workspaces/{ws}/audit/journal.jsonl:stream",
        "workspaces/{ws}/audit/journal.jsonl::$DATA",
        "workspaces/{ws}/audit/journal.jsonl:$DATA/x.json",
        "workspaces/{ws}/audit/journal.jsonl:stream/x.json",
    ],
)
def test_colon_segment_is_rejected_as_an_alternate_data_stream(
    tmp_path: Path, write_glob: str
) -> None:
    """RR11: ``:`` opens an NTFS ADS, so ``journal.jsonl::$DATA`` is the journal.

    Measured on this host: ``open('<ws>/audit/journal.jsonl::$DATA', 'a')``
    appends to ``journal.jsonl`` and creates no new file, while the last segment
    compares as ``journal.jsonl::$DATA`` and ``globs_intersect`` sees nothing.
    Validation rejects the colon outright, before any comparison, so a resolver
    that normalises differently cannot reintroduce the alias.
    """
    root = _stage(tmp_path)
    payload = _role_payload(root, "coder")
    payload["outputs"][0]["write_glob"] = write_glob
    _write_role(root, "coder", payload)
    with pytest.raises(gen.RoleError, match="alternate data stream"):
        gen.load_roles(root)


@pytest.mark.parametrize(
    "write_glob",
    [
        "workspaces/{ws}/audit/JOURNA~1.JSO",
        "workspaces/{ws}/AUDIT/JOURNA~1.JSO",
        "workspaces/{ws}/audit/JOURNA~1.JS*",
        "workspaces/{ws}/audit/JOURNA~1.[J]SO",
        "workspaces/{ws}/WORKSP~1/audit/journal.jsonl",
    ],
)
def test_short_name_segment_is_rejected_as_an_83_alias(
    tmp_path: Path, write_glob: str
) -> None:
    """RR11: on a volume with 8.3 names, ``JOURNA~1.JSO`` is ``journal.jsonl``.

    Measured on this host: the short name resolves to the same inode and an
    append through it changes the journal. ``~`` is the short-name marker, so it
    is rejected in any segment; no shipped glob uses it.
    """
    root = _stage(tmp_path)
    payload = _role_payload(root, "coder")
    payload["outputs"][0]["write_glob"] = write_glob
    _write_role(root, "coder", payload)
    with pytest.raises(gen.RoleError, match="8.3 short-name"):
        gen.load_roles(root)


def test_nul_byte_in_a_segment_is_rejected(tmp_path: Path) -> None:
    """RR11: NUL truncates in path APIs, so it cannot be compared reliably."""
    root = _stage(tmp_path)
    payload = _role_payload(root, "coder")
    payload["outputs"][0]["write_glob"] = "workspaces/{ws}/audit/journal.jsonl\x00x"
    _write_role(root, "coder", payload)
    with pytest.raises(gen.RoleError, match="control character"):
        gen.load_roles(root)


@pytest.mark.parametrize(
    ("write_glob", "expected"),
    [
        ("workspaces/{ws}/{audit.,x}/journal.jsonl", "trailing dot"),
        ("workspaces/{ws}/{audit ,x}/journal.jsonl", "trailing whitespace"),
        ("workspaces/{ws}/{journal.jsonl:a,x}", "alternate data stream"),
        ("workspaces/{ws}/{JOURNA~1.JSO,x}", "8.3 short-name"),
        ("workspaces/{ws}/audit/{journal.jsonl\x00x,y}", "control character"),
    ],
)
def test_brace_hidden_non_canonical_segment_is_rejected(
    tmp_path: Path, write_glob: str, expected: str
) -> None:
    """RR11: validation runs per expanded alternative, so a group cannot hide it.

    Review found ``{audit.,x}/journal.jsonl`` untested: the rule already fired
    on expansion, but nothing pinned it. The colon and short-name variants are
    pinned with it so a future refactor to raw-string validation fails here.
    """
    root = _stage(tmp_path)
    payload = _role_payload(root, "coder")
    payload["outputs"][0]["write_glob"] = write_glob
    _write_role(root, "coder", payload)
    with pytest.raises(gen.RoleError, match=expected):
        gen.load_roles(root)


@pytest.mark.parametrize(("alias", "expected"), PROTECTED_PATH_ALIASES)
def test_every_measured_protected_path_alias_is_rejected(
    tmp_path: Path, alias: str, expected: str
) -> None:
    """Record-level matrix: no measured alias spelling reaches ``validate_role``.

    Each entry was measured on this host (win32, NTFS with 8.3 names enabled).
    The check is deliberately at ``validate_role`` — the record boundary — not at
    ``validate_glob`` alone, so a rule that passes string validation but is
    refused only by a later intersection check is still covered.
    """
    roles = gen.load_roles(ROOT)
    known_ids = set(roles)
    payload = _role_payload(ROOT, "coder")
    payload["outputs"][0]["write_glob"] = alias
    path = tmp_path / "roles" / "coder.json"
    path.parent.mkdir(parents=True)
    with pytest.raises(gen.RoleError, match=expected):
        gen.validate_role(payload, path, known_ids)


def test_ads_and_short_name_actually_alias_the_journal_on_windows(
    tmp_path: Path,
) -> None:
    """Evidence for RR11: the rejected spellings are real aliases on win32.

    Hermetic: the file lives in ``tmp_path``. Self-skipping where the host does
    not fold streams or does not generate 8.3 names, so the rule's *reason* is
    pinned without making a portable suite host-dependent.
    """
    if sys.platform != "win32":
        pytest.skip("NTFS alternate data streams are a win32 feature")
    journal = tmp_path / "journal.jsonl"
    journal.write_bytes(b"line\n")

    before = journal.read_bytes()
    with open(f"{journal}::$DATA", "a", encoding="utf-8") as stream:
        stream.write("ads\n")
    assert journal.read_bytes() != before, "::$DATA must reach the default stream"

    # 8.3 short-name generation is a per-volume option; probe instead of asserting
    # so this test skips rather than fails on a volume with it disabled.
    short = tmp_path / "JOURNA~1.JSO"
    if not short.exists():
        pytest.skip("8.3 short-name generation is disabled on this volume")
    assert short.resolve() == journal.resolve()
    before = journal.read_bytes()
    with open(short, "a", encoding="utf-8") as stream:
        stream.write("short-name\n")
    assert journal.read_bytes() != before, "the 8.3 name must reach journal.jsonl"


def test_shipped_globs_use_only_permitted_characters() -> None:
    """Positive guard: the shipped alphabet is deliberate, not accidental.

    This does not change validation. It fails if a future record introduces a
    segment character nobody has considered, which is the review question that
    let ``:`` and ``~`` reach certification in the first place. All 88 shipped
    globs currently use only letters, digits and ``_ - . * ? [ ] { } / ~``.
    """
    roles = gen.load_roles(ROOT)
    total = 0
    for role_id, role in roles.items():
        pairs = [
            *[("read_glob", item) for item in role["read_glob"]],
            *[("deny_glob", item) for item in role["deny_glob"]],
            *[("write_glob", output["write_glob"]) for output in role["outputs"]],
        ]
        for field, glob in pairs:
            unexpected = sorted(set(glob) - PERMITTED_GLOB_CHARACTERS)
            assert not unexpected, (
                f"{role_id} {field} {glob!r} uses {unexpected}; extend the "
                "documented permitted set (and the alias rules) deliberately"
            )
            total += 1
    assert total == 95


@pytest.mark.parametrize(
    ("read_glob", "expected"),
    [
        ("{repo}/SRC/**", "source tree"),
        ("{repo}/SRC/x.json", "source tree"),
        ("{repo}/src./**", "trailing dot"),
        ("{repo}/src./x.json", "trailing dot"),
    ],
)
def test_case_and_non_canonical_source_tree_read_is_rejected(
    tmp_path: Path, read_glob: str, expected: str
) -> None:
    """R2/RR11: ``{repo}/SRC/**`` and ``{repo}/src./**`` read the real ``src/``."""
    root = _stage(tmp_path)
    payload = _role_payload(root, "inception-agent")
    payload["read_glob"][0] = read_glob
    _write_role(root, "inception-agent", payload)
    with pytest.raises(gen.RoleError, match=expected):
        gen.load_roles(root)


def test_repo_source_tree_check_folds_case(tmp_path: Path) -> None:
    """R2/RR11: the source-tree comparison folds case independently of R4.

    On a case-insensitive host ``{repo}/SRC/x.json`` addresses ``src/x.json``
    even though the segment is not otherwise illegal.
    """
    path = tmp_path / "roles" / "inception-agent.json"
    with pytest.raises(gen.RoleError, match="source tree"):
        gen._validate_repo_parameter(
            "{repo}/SRC/x.json", path, "read_glob", "{repo}/SRC/x.json"
        )


@pytest.mark.parametrize(
    "artifact_glob",
    [
        "workspaces/{ws}/INDEX.md",
        "workspaces/{ws}/SCREENING_CRITERIA.md",
        "workspaces/{ws}/extracted/A/{stu}.json",
    ],
)
def test_uppercase_workspace_artifact_globs_are_accepted(
    tmp_path: Path, artifact_glob: str
) -> None:
    """RR11 must not over-reject: only comparison folds, not validation."""
    path = tmp_path / "roles" / "screener.json"
    assert gen.validate_glob(artifact_glob, path, "read_glob") == artifact_glob


def test_write_glob_may_not_be_repo_wide(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "coder")
    payload["outputs"][0]["write_glob"] = "**"
    _write_role(root, "coder", payload)
    with pytest.raises(gen.RoleError, match="too broad"):
        gen.load_roles(root)


def test_path_literal_in_a_glob_fails(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "screener")
    payload["outputs"][0]["write_glob"] = "src/scholar_harness/out.json"
    _write_role(root, "screener", payload)
    with pytest.raises(gen.RoleError, match="source tree"):
        gen.load_roles(root)


def test_unknown_path_parameter_fails(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "screener")
    payload["outputs"][0]["write_glob"] = "workspaces/{project}/decisions.json"
    _write_role(root, "screener", payload)
    with pytest.raises(gen.RoleError, match="unknown parameter"):
        gen.load_roles(root)


def test_literal_workspace_slug_in_a_write_glob_fails(tmp_path: Path) -> None:
    """R2: the segment after ``workspaces/`` must be ``{ws}``, not a slug."""
    root = _stage(tmp_path)
    payload = _role_payload(root, "screener")
    payload["outputs"][0]["write_glob"] = "workspaces/uav-crop-weed-v03/x.json"
    _write_role(root, "screener", payload)
    with pytest.raises(gen.RoleError, match="workspace parameter belongs"):
        gen.load_roles(root)


def test_literal_task_id_in_a_run_glob_fails(tmp_path: Path) -> None:
    """R2: the segment after ``runs/`` must be ``{task_id}``, not a task id."""
    root = _stage(tmp_path)
    payload = _role_payload(root, "coder")
    payload["outputs"][0]["write_glob"] = "runs/task-42/x.json"
    _write_role(root, "coder", payload)
    with pytest.raises(gen.RoleError, match="task-id parameter belongs"):
        gen.load_roles(root)


def test_repo_parameter_may_not_root_a_write_glob(tmp_path: Path) -> None:
    """R2: ``{repo}`` is read-only, so it can never be a write target."""
    root = _stage(tmp_path)
    payload = _role_payload(root, "coder")
    payload["outputs"][0]["write_glob"] = "{repo}"
    _write_role(root, "coder", payload)
    with pytest.raises(gen.RoleError, match="is the repository root"):
        gen.load_roles(root)


@pytest.mark.parametrize(
    "write_glob",
    [
        "workspaces/{ws}/{repo}/x.json",
        "workspaces/{ws}/x/{repo}.json",
    ],
)
def test_repo_parameter_is_rejected_anywhere_in_a_write_glob(
    tmp_path: Path, write_glob: str
) -> None:
    """R2 consequence 2: ``{repo}`` is read-only at every position, not only at the root.

    Both entries are ordinary-looking workspace paths with the read-only
    parameter spliced in after ``{ws}``. The rule used to inspect only position 0
    of the expanded glob, so both were accepted. The non-root branch has its own
    message, distinct from the root-only one.
    """
    root = _stage(tmp_path)
    payload = _role_payload(root, "coder")
    payload["outputs"][0]["write_glob"] = write_glob
    _write_role(root, "coder", payload)
    with pytest.raises(gen.RoleError, match="non-root segment"):
        gen.load_roles(root)


def test_repo_parameter_root_write_glob_is_still_rejected(tmp_path: Path) -> None:
    """The root case is unchanged and keeps its own message (F5)."""
    root = _stage(tmp_path)
    payload = _role_payload(root, "coder")
    payload["outputs"][0]["write_glob"] = "{repo}/x.json"
    _write_role(root, "coder", payload)
    with pytest.raises(gen.RoleError, match="rooted at the read-only"):
        gen.load_roles(root)


def test_repo_parameter_root_read_glob_is_still_accepted(tmp_path: Path) -> None:
    """The anywhere rule is write-only: ``inception-agent`` must keep its read."""
    path = tmp_path / "roles" / "inception-agent.json"
    pattern = "{repo}/.agents/skills/**"
    assert gen.validate_glob(pattern, path, "read_glob") == pattern
    assert pattern in gen.load_roles(ROOT)["inception-agent"]["read_glob"]


def test_repo_rooted_write_glob_fails_outside_a_source_tree(tmp_path: Path) -> None:
    """R2: any ``{repo}``-rooted write fails, not only the source-tree ones."""
    root = _stage(tmp_path)
    payload = _role_payload(root, "coder")
    payload["outputs"][0]["write_glob"] = "{repo}/notes/x.json"
    _write_role(root, "coder", payload)
    with pytest.raises(gen.RoleError, match="rooted at the read-only"):
        gen.load_roles(root)


def test_repo_wide_write_glob_is_not_a_valid_target(tmp_path: Path) -> None:
    """R2: ``{repo}/**`` is too broad even though its root is parameterised."""
    root = _stage(tmp_path)
    payload = _role_payload(root, "coder")
    payload["outputs"][0]["write_glob"] = "{repo}/**"
    _write_role(root, "coder", payload)
    with pytest.raises(gen.RoleError, match="not a valid write target"):
        gen.load_roles(root)


def test_repo_rooted_write_glob_still_checks_the_source_tree(tmp_path: Path) -> None:
    """R2: ``{repo}/src/**`` is rejected exactly as the bare ``src/**`` is."""
    root = _stage(tmp_path)
    payload = _role_payload(root, "coder")
    payload["outputs"][0]["write_glob"] = "{repo}/src/**"
    _write_role(root, "coder", payload)
    with pytest.raises(gen.RoleError, match="source tree"):
        gen.load_roles(root)


def test_repo_rooted_read_glob_still_checks_the_source_tree(tmp_path: Path) -> None:
    """R2 applies to reads too: ``{repo}`` does not launder a source-tree glob."""
    root = _stage(tmp_path)
    payload = _role_payload(root, "inception-agent")
    payload["read_glob"][0] = "{repo}/src/**"
    _write_role(root, "inception-agent", payload)
    with pytest.raises(gen.RoleError, match="source tree"):
        gen.load_roles(root)


def test_repo_source_tree_check_is_segment_based(tmp_path: Path) -> None:
    """R2: the first segment after ``{repo}`` is compared, not a byte prefix.

    ``{repo}/src`` (no trailing slash) was accepted by the old prefix test (F2).
    """
    root = _stage(tmp_path)
    payload = _role_payload(root, "inception-agent")
    payload["read_glob"][0] = "{repo}/src"
    _write_role(root, "inception-agent", payload)
    with pytest.raises(gen.RoleError, match="source tree"):
        gen.load_roles(root)


def test_repo_source_tree_check_does_not_over_match_a_sibling(tmp_path: Path) -> None:
    """R2: ``{repo}/srcs/`` is not ``{repo}/src/``; a prefix test must not reject it."""
    root = _stage(tmp_path)
    payload = _role_payload(root, "inception-agent")
    payload["read_glob"][0] = "{repo}/srcs/x.json"
    _write_role(root, "inception-agent", payload)
    roles = gen.load_roles(root)
    assert roles["inception-agent"]["read_glob"][0] == "{repo}/srcs/x.json"


def test_repo_source_tree_check_normalises_before_comparing(tmp_path: Path) -> None:
    """R2 consequence 4: a dot segment cannot spell the source tree differently.

    ``validate_glob`` rejects the dot segment outright, so this asserts the
    source-tree comparison itself is normalisation-safe as well (F2).
    """
    path = tmp_path / "roles" / "inception-agent.json"
    with pytest.raises(gen.RoleError, match="current-directory"):
        gen.validate_glob("{repo}/./src/**", path, "read_glob")
    with pytest.raises(gen.RoleError, match="source tree"):
        gen._validate_repo_parameter(
            "{repo}/./src/**", path, "read_glob", "{repo}/./src/**"
        )


def test_nested_brace_group_cannot_hide_the_repo_parameter(tmp_path: Path) -> None:
    """R2: ``expand_braces`` recurses, so a nested group cannot hide a rule (F3).

    Standard expansion of ``{{repo},foo}/x.json`` is ``{repo}/x.json`` -- the
    read-only write -- and ``foo/x.json`` -- the bare repo-relative path. Before
    T-ALP-A-r4 the record was accepted because the inner ``{repo}`` was taken as
    the outermost group and ``_is_rooted_glob`` read the leading ``{`` as a
    parameter root.
    """
    root = _stage(tmp_path)
    payload = _role_payload(root, "coder")
    payload["outputs"][0]["write_glob"] = "{{repo},foo}/x.json"
    _write_role(root, "coder", payload)
    assert gen.expand_braces("{{repo},foo}/x.json") == [
        "foo/x.json",
        "{repo}/x.json",
    ]
    for expanded in gen.expand_braces("{{repo},foo}/x.json"):
        with pytest.raises(gen.RoleError):
            gen.validate_glob(expanded, root / "roles" / "coder.json", "write_glob")
    with pytest.raises(gen.RoleError, match="R2"):
        gen.load_roles(root)


def test_brace_group_spanning_a_segment_boundary_is_malformed(tmp_path: Path) -> None:
    """R2: a group that survives expansion with a brace inside is malformed (F3)."""
    root = _stage(tmp_path)
    payload = _role_payload(root, "screener")
    payload["outputs"][0]["write_glob"] = "workspaces/{ws}/{{repo}/}x.json"
    _write_role(root, "screener", payload)
    with pytest.raises(gen.RoleError, match="malformed brace group"):
        gen.load_roles(root)


def test_literal_segment_alternation_is_a_legal_write_glob(tmp_path: Path) -> None:
    """A brace group of literal segments is not a parameter and stays legal.

    Decided accepted: ``{a,b}`` under ``{ws}`` expands to literal directory
    names inside the workspace, so it neither hides a parameter nor enters a
    source tree. Only a group that still contains a brace is malformed.
    """
    root = _stage(tmp_path)
    payload = _role_payload(root, "screener")
    payload["outputs"][0]["write_glob"] = "workspaces/{ws}/{a,b}/x.json"
    _write_role(root, "screener", payload)
    roles = gen.load_roles(root)
    assert roles["screener"]["outputs"][0]["write_glob"] == (
        "workspaces/{ws}/{a,b}/x.json"
    )


def test_scoped_breadth_under_a_run_is_a_legal_write_glob(tmp_path: Path) -> None:
    """``runs/{task_id}/**`` is legitimate scoped breadth, unlike bare ``**``."""
    root = _stage(tmp_path)
    payload = _role_payload(root, "coder")
    payload["outputs"][0]["write_glob"] = "runs/{task_id}/**"
    _write_role(root, "coder", payload)
    roles = gen.load_roles(root)
    assert roles["coder"]["outputs"][0]["write_glob"] == "runs/{task_id}/**"


def test_repo_parameter_is_confined_to_read_globs() -> None:
    """No shipped record needs a ``{repo}`` write, and only inception-agent reads one.

    Every write glob also keeps its root parameter in the fixed position, which is
    why the R2 enforcement needs no record change.
    """
    roles = gen.load_roles(ROOT)
    readers = {
        role_id
        for role_id, role in roles.items()
        if any("{repo}" in glob for glob in role["read_glob"])
    }
    assert readers == {"inception-agent"}, readers
    for role_id, role in roles.items():
        for output in role["outputs"]:
            write_glob = output["write_glob"]
            assert "{repo}" not in write_glob, role_id
            segments = write_glob.split("/")
            if segments[0] == "workspaces":
                assert segments[1] == "{ws}", (role_id, write_glob)
            elif segments[0] == "runs":
                assert segments[1] == "{task_id}", (role_id, write_glob)
            else:
                raise AssertionError(
                    f"{role_id} writes outside the portable roots: {write_glob!r}"
                )


def test_shell_command_in_a_role_record_fails(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "tester")
    payload["stop_conditions"] = ["run uv run pytest tests/ -q before reporting"]
    _write_role(root, "tester", payload)
    with pytest.raises(gen.RoleError, match="R1"):
        gen.load_roles(root)


def test_orphan_document_in_agent_directory_fails_check(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    (root / ".opencode" / "agent" / "git_workflow.md").write_text(
        "# Git Workflow\n\nPolicy, not an agent.\n", encoding="utf-8", newline="\n"
    )
    assert ".opencode/agent/git_workflow.md" in gen.check_root(root)
    assert gen.main(["--check", "--root", str(root)]) == 1


def test_nested_orphan_document_fails_check(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    nested = root / ".opencode" / "agent" / "nested" / "stray.md"
    nested.parent.mkdir(parents=True)
    nested.write_text("# Stray\n", encoding="utf-8", newline="\n")
    assert ".opencode/agent/nested/stray.md" in gen.check_root(root)


def test_critic_read_family_must_be_denied(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "extraction-critic")
    payload["deny_glob"] = [
        item for item in payload["deny_glob"] if item != "workspaces/{ws}/extracted/**"
    ]
    _write_role(root, "extraction-critic", payload)
    with pytest.raises(gen.RoleError, match="R7"):
        gen.load_roles(root)


def test_role_written_output_without_write_tool_fails(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "reviewer")
    payload["outputs"][0].pop("written_by")
    _write_role(root, "reviewer", payload)
    with pytest.raises(gen.RoleError, match="written_by"):
        gen.load_roles(root)


def test_invalid_written_by_value_fails(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "reviewer")
    payload["outputs"][0]["written_by"] = "harness"
    _write_role(root, "reviewer", payload)
    with pytest.raises(gen.RoleError, match="written_by"):
        gen.load_roles(root)


def test_adapter_written_outputs_do_not_grant_edit() -> None:
    roles = gen.load_roles(ROOT)
    for role_id in ("reviewer", "screening-critic", "tester"):
        assert all(
            output.get("written_by") == "adapter"
            for output in roles[role_id]["outputs"]
        ), role_id
        assert gen.derive_permissions(roles[role_id])["edit"] == "deny", role_id


def test_edit_tool_with_only_adapter_outputs_derives_deny(tmp_path: Path) -> None:
    """R5: ``edit`` in ``tools`` is not enough; a role-written output is required.

    No corpus role has this shape, so without this synthetic record a mutant
    that derives ``edit`` from ``tools`` alone (ignoring ``written_by``) would
    certify itself.
    """
    role = _synthetic_role()
    assert "edit" in role["tools"]
    assert all(output["written_by"] == "adapter" for output in role["outputs"])

    root = _stage_synthetic(tmp_path, role)
    roles = gen.load_roles(root)  # legal: the role delegates persistence
    assert gen.derive_permissions(roles["synthetic-critic"])["edit"] == "deny"


def test_skill_permission_follows_requires_skill_not_the_tool_list(
    tmp_path: Path,
) -> None:
    """R5: ``skill`` derives from ``requires_skill``; the tool list is not enough."""
    # `skill` in tools with no required skill: illegal, and the derivation denies.
    tool_only = _synthetic_role(
        tools=["edit", "glob", "grep", "list", "read", "skill"],
        requires_skill=[],
    )
    assert gen.derive_permissions(tool_only)["skill"] == "deny"
    with pytest.raises(gen.RoleError, match="requires_skill"):
        gen.load_roles(_stage_synthetic(tmp_path / "tool-only", tool_only))

    # A required skill without the tool: illegal, and the derivation allows.
    skill_only = _synthetic_role(requires_skill=["critic-contract"])
    assert gen.derive_permissions(skill_only)["skill"] == "allow"
    with pytest.raises(gen.RoleError, match="does not grant 'skill'"):
        gen.load_roles(_stage_synthetic(tmp_path / "skill-only", skill_only))


def test_brace_alternation_cannot_hide_a_traversal_in_write_glob(
    tmp_path: Path,
) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "screener")
    payload["outputs"][0]["write_glob"] = "workspaces/{ws}/{..,tmp}/x.json"
    _write_role(root, "screener", payload)
    with pytest.raises(gen.RoleError, match="escapes its root"):
        gen.load_roles(root)


def test_brace_alternation_cannot_hide_a_traversal_in_a_run_glob(
    tmp_path: Path,
) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "reviewer")
    payload["outputs"][0]["write_glob"] = "runs/{task_id}/{..,x}/review.json"
    _write_role(root, "reviewer", payload)
    with pytest.raises(gen.RoleError, match="escapes its root"):
        gen.load_roles(root)


def test_input_without_from_fails(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "screener")
    payload["inputs"][0].pop("from")
    _write_role(root, "screener", payload)
    with pytest.raises(gen.RoleError, match="non-empty 'from'"):
        gen.load_roles(root)


def test_input_from_unknown_origin_fails(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "screener")
    payload["inputs"][0]["from"] = "ghost-role"
    _write_role(root, "screener", payload)
    with pytest.raises(gen.RoleError, match="unknown 'from'"):
        gen.load_roles(root)


def test_skill_tool_without_requires_skill_fails(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "reviewer")
    payload["tools"] = sorted({*payload["tools"], "skill"})
    _write_role(root, "reviewer", payload)
    with pytest.raises(gen.RoleError, match="requires_skill"):
        gen.load_roles(root)


def test_requires_skill_without_skill_tool_fails(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "adjudicator")
    payload["tools"] = [tool for tool in payload["tools"] if tool != "skill"]
    _write_role(root, "adjudicator", payload)
    with pytest.raises(gen.RoleError, match="does not grant 'skill'"):
        gen.load_roles(root)


def test_empty_audit_action_fails(tmp_path: Path) -> None:
    root = _stage(tmp_path)
    payload = _role_payload(root, "screener")
    payload["audit"]["emit"] = ["SCREENING_COMPLETED", ""]
    _write_role(root, "screener", payload)
    with pytest.raises(gen.RoleError, match="non-empty strings"):
        gen.load_roles(root)
