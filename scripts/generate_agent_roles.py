"""Generate the OpenCode agent layer from the ``Role@1`` records in ``roles/``.

One record, three outputs:

* ``.opencode/agent/<id>.md`` -- generated frontmatter (``description`` plus the
  derived permission map) concatenated with the verbatim instruction body from
  ``roles/<id>.prompt.md``;
* ``.opencode/agent/_generated/permissions.json`` -- the derived capability and
  permission map consumed by the app layer;
* the drift gate itself (``--check``), which fails if either half drifts.

The generator owns only the YAML frontmatter. The instruction body is authored
prose and is never regenerated; it is copied byte-for-byte from
``roles/<id>.prompt.md``.

Generation is deterministic: no timestamps, sorted keys, LF endings, UTF-8
without a BOM.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ROLES_DIR = "roles"
AGENT_DIR = ".opencode/agent"
PERMISSIONS_FILE = f"{AGENT_DIR}/_generated/permissions.json"

ROLE_KIND = "role"
PERMISSIONS_SCHEMA = "AgentPermissions@1"

CAPABILITIES = (
    "bash",
    "edit",
    "glob",
    "grep",
    "list",
    "read",
    "skill",
    "task",
    "write",
)
READ_CAPABILITIES = ("glob", "grep", "list", "read")
WRITE_CAPABILITIES = ("edit", "write")
MODES = ("primary", "subagent")
ISOLATIONS = ("none", "directory", "redacted-input")
NETWORKS = ("deny", "allow", "allowlist")
BASH_APPROVALS = ("allow", "ask")
WRITTEN_BY = ("role", "adapter")
INPUT_ORIGINS = ("workspace", "written-input")

#: Parameters a role glob may use. ``arm`` is required by the screening output
#: globs in the governing specification (``{batch}_decisions_{arm}.json``).
#: ``repo`` resolves to the repository root, so a role can address repository
#: assets without learning where it runs (R2).
PATH_PARAMETERS = ("arm", "batch", "repo", "role", "stu", "task_id", "ws")

AUDIT_TREE = "workspaces/{ws}/audit/**"
AUDIT_JOURNAL = "workspaces/{ws}/audit/journal.jsonl"
GIT_DIR = ".git/**"

#: R2: the only literal roots a role glob may start with. Workspace artifacts
#: and run outputs are the harness's portable roots; ``{repo}`` is a parameter;
#: ``.git/**`` is the single permitted repo-relative constant; and ``**`` is the
#: whole-tree reader the dev-loop roles declare.
LITERAL_GLOB_ROOTS = ("runs/", "workspaces/")
REPO_WIDE_GLOB = "**"
REPO_PARAMETER = "{repo}"

#: R2: the segment after each literal root is fixed by the parameter it names.
ROOT_PARAMETERS = {"runs": "{task_id}", "workspaces": "{ws}"}

#: Closed refusal registry (spec ``02_envelope_and_refusals.md`` section 6).
GLOBAL_REFUSAL_CODES = frozenset(
    {
        "ABSENCE_UNCLASSIFIED",
        "BATCH_ID_MISMATCH",
        "BATCH_INCOMPLETE",
        "BLOCKED_AMBIGUOUS_TASK",
        "BLOCKED_BASELINE_DRIFT",
        "BLOCKED_CANONICAL_REPO",
        "BLOCKED_INPUT",
        "CRITERIA_HASH_MISMATCH",
        "IDENTITY_AMBIGUOUS",
        "INVALID_OUTPUT",
        "LOCATOR_UNRESOLVED",
        "PARENT_HASH_MISMATCH",
        "QUOTE_NOT_IN_SOURCE",
        "REFUSED_UNSUPPORTED",
        "REQUIREMENT_UNTRACEABLE",
        "SCOPE_VIOLATION",
        "SOURCE_MISSING",
        "TEST_GATE_FAILED",
        "VERDICT_CHANGES_REQUESTED",
    }
)

#: R1: a role contains no command and no path literal (globs are checked apart).
_SHELL_MARKERS = ("uv run", "git ", "python ", "pip ", "npm ", "```")
_PATH_LITERAL = re.compile(
    r"(?:^|[\s`'\"(])(?:src/|tools/|scripts/|tests/|workspaces/|docs/)"
    r"|\.(?:py|json|md|ya?ml|toml)\b"
    r"|[A-Za-z]:[\\/]"
)
_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
_BRACE = re.compile(r"\{([^{}]*)\}")

#: R2: a role never learns where it runs, so it may not address the harness
#: implementation it happens to be executing inside.
_SOURCE_TREES = (
    "docs/",
    "packaging/",
    "scripts/",
    "specs/",
    "src/",
    "tests/",
    "tools/",
)

#: The same trees as first path segments, so the check cannot be evaded by
#: omitting the trailing slash (``{repo}/src``) or by spelling the path
#: differently (``{repo}/./src/**``), and does not over-match ``srcs/`` (F2).
_SOURCE_TREE_SEGMENTS = tuple(tree.rstrip("/") for tree in _SOURCE_TREES)

#: RR11: the validator runs on case-insensitive hosts, so ``SRC`` names ``src``.
#: Comparison folds case; the declared spelling is never rewritten.
_SOURCE_TREE_SEGMENTS_FOLDED = frozenset(
    segment.casefold() for segment in _SOURCE_TREE_SEGMENTS
)


class RoleError(ValueError):
    """A ``roles/*.json`` record violates the Role@1 contract."""


class AgentLoadError(RoleError):
    """A file under ``.opencode/agent/`` is not a loadable role agent."""


# --------------------------------------------------------------------------- #
# text / frontmatter helpers
# --------------------------------------------------------------------------- #


def normalize_newlines(text: str) -> str:
    """Return ``text`` with LF endings so comparisons are platform independent."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def read_text(path: Path) -> str:
    return normalize_newlines(path.read_bytes().decode("utf-8"))


def split_frontmatter(text: str) -> tuple[str, str]:
    """Split an agent document into (frontmatter text, body text).

    The body starts immediately after the closing delimiter, so every blank line
    the source file has between the frontmatter and the prose is preserved.
    """
    text = normalize_newlines(text)
    if not text.startswith("---\n"):
        raise AgentLoadError("missing YAML frontmatter (expected a leading '---' line)")
    end = text.find("\n---\n", 3)
    if end == -1:
        raise AgentLoadError(
            "unterminated YAML frontmatter (missing the closing '---' line)"
        )
    return text[3:end], text[end + len("\n---\n") :]


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return json.loads(value)
    return value


def parse_frontmatter(text: str) -> dict[str, object]:
    """Parse the restricted YAML subset this generator emits."""
    fields: dict[str, object] = {}
    nested: dict[str, str] | None = None
    for raw_line in normalize_newlines(text).split("\n"):
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  "):
            if nested is None:
                raise AgentLoadError(f"nested key outside a mapping: {line.strip()!r}")
            key, separator, value = line.strip().partition(":")
            if not separator or not value.strip():
                raise AgentLoadError(
                    f"malformed nested frontmatter entry: {line.strip()!r}"
                )
            nested[key.strip()] = _unquote(value)
            continue
        key, separator, value = line.partition(":")
        if not separator:
            raise AgentLoadError(f"malformed frontmatter entry: {line.strip()!r}")
        nested = None
        if value.strip():
            fields[key.strip()] = _unquote(value)
        else:
            nested = {}
            fields[key.strip()] = nested
    return fields


def load_agent_definition(path: Path) -> dict[str, object]:
    """Load one ``.opencode/agent`` file, rejecting anything that is not a role.

    A policy document that happens to live in the agent directory (for example
    the former ``git_workflow.md``) has no frontmatter and therefore no
    ``kind: role``; it must fail here rather than silently load as an agent.
    """
    frontmatter, _body = split_frontmatter(read_text(path))
    fields = parse_frontmatter(frontmatter)
    kind = fields.get("kind")
    if kind != ROLE_KIND:
        raise AgentLoadError(
            f"{path}: rejected as an agent definition -- required 'kind: role', found kind={kind!r}"
        )
    description = fields.get("description")
    if not isinstance(description, str) or not description.strip():
        raise AgentLoadError(
            f"{path}: rejected as an agent definition -- missing a non-empty 'description'"
        )
    return fields


# --------------------------------------------------------------------------- #
# glob helpers
# --------------------------------------------------------------------------- #


def _find_brace_group(pattern: str) -> tuple[int, int] | None:
    """Return the span of the first *outermost* brace group, if balanced.

    Left-to-right scanning with a depth counter is required: a naive
    ``\\{[^{}]*\\}`` match finds the innermost group and can therefore report the
    ``{repo}`` inside ``{{repo},foo}`` as the first group, leaving the outer
    alternation unexpanded (F3).
    """
    start = pattern.find("{")
    if start == -1:
        return None
    depth = 0
    for index in range(start, len(pattern)):
        char = pattern[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return start, index + 1
    return None


def _split_alternatives(content: str) -> list[str] | None:
    """Split a group's content on top-level commas.

    ``None`` means the group is a single token -- a ``{param}`` placeholder or a
    malformed group that must survive to the structural check.
    """
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    saw_comma = False
    for char in content:
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        if char == "," and depth == 0:
            saw_comma = True
            parts.append("".join(current))
            current = []
            continue
        current.append(char)
    parts.append("".join(current))
    return parts if saw_comma else None


def expand_braces(pattern: str) -> list[str]:
    """Expand ``{a,b}`` alternations; leave ``{param}`` placeholders untouched.

    The expansion recurses into the alternatives it produces, so a nested group
    cannot hide a rule violation behind an outer one: ``{{repo},foo}/x.json``
    expands to ``{repo}/x.json`` and ``foo/x.json``, which are then validated as
    the write and the bare repo-relative path that they are.
    """
    group = _find_brace_group(pattern)
    if group is None:
        return [pattern]
    start, end = group
    head, content, tail = pattern[:start], pattern[start + 1 : end - 1], pattern[end:]
    alternatives = _split_alternatives(content)
    if alternatives is None:
        # A parameter (or a malformed group): keep it verbatim, but keep
        # scanning the tail for further alternations.
        return [head + "{" + content + "}" + rest for rest in expand_braces(tail)]
    expanded: list[str] = []
    for option in alternatives:
        expanded.extend(expand_braces(head + option + tail))
    return sorted(set(expanded))


def _segment_containing(pattern: str, offset: int) -> str:
    """Return the ``/``-delimited segment of ``pattern`` holding ``offset``."""
    start = pattern.rfind("/", 0, offset) + 1
    end = pattern.find("/", offset)
    return pattern[start:] if end == -1 else pattern[start:end]


def _malformed_brace_segment(expanded: str) -> str | None:
    """R2: every brace group must be one flat ``{token}``, never a nested group.

    A brace group that survives expansion with a brace still inside it -- or an
    unbalanced brace -- is not a parameter. It is a malformed glob, and it is
    rejected rather than read as a parameter root (F3).
    """
    index = 0
    while index < len(expanded):
        char = expanded[index]
        if char == "}":
            return _segment_containing(expanded, index)
        if char != "{":
            index += 1
            continue
        end = expanded.find("}", index)
        if end == -1:
            return _segment_containing(expanded, index)
        if "{" in expanded[index + 1 : end]:
            return _segment_containing(expanded, index)
        index = end + 1
    return None


def _path_segments(pattern: str) -> list[str]:
    """Split a glob into segments, dropping empty and ``.`` segments (R2).

    ``a/./b``, ``a//b`` and ``a/b`` name the same paths, so every intersection
    and containment check compares normalised segments. ``..`` is *not* folded
    away here: it is rejected by ``validate_glob``, and folding it would silently
    resolve a traversal instead of failing the record.
    """
    return [
        segment for segment in pattern.strip("/").split("/") if segment not in ("", ".")
    ]


def _segments_match(candidate: str, pattern: str) -> bool:
    """Match one segment against a glob segment, folding case (RR11).

    win32 and default macOS volumes compare paths case-insensitively, so
    ``audit`` and ``AUDIT`` name one directory there. Comparison folds; the
    declared spelling in the record and the generated output never does.
    """
    return fnmatch.fnmatchcase(candidate.casefold(), pattern.casefold())


def _segments_intersect(left: list[str], right: list[str]) -> bool:
    if not left and not right:
        return True
    if left and left[0] == "**":
        return _segments_intersect(left[1:], right) or (
            bool(right) and _segments_intersect(left, right[1:])
        )
    if right and right[0] == "**":
        return _segments_intersect(left, right[1:]) or (
            bool(left) and _segments_intersect(left[1:], right)
        )
    if not left or not right:
        return False
    head_left, head_right = left[0], right[0]
    if not (
        _segments_match(head_left, head_right) or _segments_match(head_right, head_left)
    ):
        return False
    return _segments_intersect(left[1:], right[1:])


def globs_intersect(first: str, second: str) -> bool:
    """Report whether one path could match both globs (conservative for ``*``)."""
    return any(
        _segments_intersect(_path_segments(left), _path_segments(right))
        for left in expand_braces(first)
        for right in expand_braces(second)
    )


def _segments_within(inner: list[str], outer: list[str]) -> bool:
    if not inner:
        return not outer or all(segment == "**" for segment in outer)
    if not outer:
        return False
    if outer[0] == "**":
        return _segments_within(inner, outer[1:]) or _segments_within(inner[1:], outer)
    if inner[0] == "**":
        return False
    if not _segments_match(inner[0], outer[0]):
        return False
    return _segments_within(inner[1:], outer[1:])


def glob_within(inner: str, outer: str) -> bool:
    """Report whether every path matched by ``inner`` is matched by ``outer``."""
    return all(
        any(
            _segments_within(
                _path_segments(inner_expanded),
                _path_segments(outer_expanded),
            )
            for outer_expanded in expand_braces(outer)
        )
        for inner_expanded in expand_braces(inner)
    )


def critic_role_ids(roles: dict[str, dict]) -> set[str]:
    """R7: derive the critic set from the records, never from a hardcoded list.

    A role is a critic when its id or purpose says so, plus ``reviewer`` whose
    purpose describes adversarial review without using the word "critic". A new
    ``synthesis-critic`` therefore becomes subject to R7 without a code change.
    """
    return {
        role_id
        for role_id, role in roles.items()
        if _is_critic(role_id, str(role.get("purpose", "")))
    }


def _is_critic(role_id: str, purpose: str) -> bool:
    return (
        role_id == "reviewer"
        or "critic" in role_id.lower()
        or "critic" in purpose.lower()
    )


def _validate_critic_denials(
    role_id: str,
    read_globs: list[str],
    write_globs: list[str],
    deny_globs: list[str],
    role_written_output: bool,
    path: Path,
) -> None:
    """R7: a critic must deny every read family outside its own write glob."""
    for family in read_globs:
        if any(glob_within(family, write_glob) for write_glob in write_globs):
            continue
        if family == "**":
            # A repo-wide reader cannot deny '**' without contradicting its own
            # output (R4). R7 is then satisfied by capability: the role has no
            # role-written output and therefore no write capability.
            if role_written_output:
                _fail(
                    path,
                    f"R7: critic {role_id!r} reads the whole tree ('**') and can write; "
                    "it cannot deny the artifacts it judges",
                )
            continue
        if not any(glob_within(family, deny_glob) for deny_glob in deny_globs):
            _fail(
                path,
                f"R7: critic {role_id!r} reads {family!r} outside its write_glob "
                "but does not deny it",
            )


# --------------------------------------------------------------------------- #
# role record validation
# --------------------------------------------------------------------------- #


def _fail(path: Path, message: str) -> None:
    raise RoleError(f"{path}: {message}")


def _require_string(role: dict, key: str, path: Path) -> str:
    value = role.get(key)
    if not isinstance(value, str) or not value.strip():
        _fail(path, f"field {key!r} must be a non-empty string")
    return value


def _require_string_list(role: dict, key: str, path: Path) -> list[str]:
    value = role.get(key)
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        _fail(path, f"field {key!r} must be a list of non-empty strings")
    return value


def _is_rooted_glob(expanded: str) -> bool:
    """R2: a glob starts at a portable root, a parameter, or a permitted constant."""
    if expanded in (REPO_WIDE_GLOB, GIT_DIR):
        return True
    if expanded.startswith("{"):
        return True
    return expanded.startswith(LITERAL_GLOB_ROOTS)


def _validate_root_parameter(
    expanded: str, path: Path, field: str, pattern: str
) -> None:
    """R2: a literal root may only be followed by the parameter it names.

    ``workspaces/uav-crop-weed-v03/x.json`` and ``runs/task-42/x.json`` are
    repo-relative paths wearing a parameter's clothes: the adapter resolves
    ``{ws}`` and ``{task_id}``, so a literal slug or task id would pin the role
    to one machine's directory.
    """
    root = expanded.split("/")[0]
    expected = ROOT_PARAMETERS.get(root)
    if expected is None:
        return
    actual = expanded.split("/")[1:2]
    if actual == [expected]:
        return
    if root == "workspaces":
        _fail(
            path,
            f"R2: {field} entry {pattern!r} has a literal where the workspace "
            f"parameter belongs; the segment after 'workspaces/' must be "
            f"'{expected}'",
        )
    _fail(
        path,
        f"R2: {field} entry {pattern!r} has a literal where the task-id "
        f"parameter belongs; the segment after 'runs/' must be '{expected}'",
    )


def _contains_repo_parameter(expanded: str) -> bool:
    """Return whether any segment of ``expanded`` names the ``{repo}`` token."""
    return any(
        match.group(1) == REPO_PARAMETER[1:-1] for match in _BRACE.finditer(expanded)
    )


def _validate_repo_parameter(
    expanded: str, path: Path, field: str, pattern: str
) -> None:
    """R2: ``{repo}`` is read-only and does not escape the source-tree exclusion.

    ``{repo}`` may only appear in a read glob. A ``write_glob`` may not carry it
    at *any* position, not only as the glob's root (R2 consequence 2): every
    legitimate output lives under ``workspaces/{ws}/`` or ``runs/{task_id}/``, so
    ``workspaces/{ws}/{repo}/x.json`` is as wrong as ``{repo}/x.json``. The
    non-root case gets its own error so the root-only branch stays pinned.
    """
    if not _contains_repo_parameter(expanded):
        return
    rooted_at_repo = expanded == REPO_PARAMETER or expanded.startswith(
        REPO_PARAMETER + "/"
    )
    if rooted_at_repo:
        # Compare the *first segment* after ``{repo}``, not a byte prefix: a
        # prefix test misses ``{repo}/src`` (no trailing slash) and cannot see
        # ``{repo}/./src/**``, while it would over-match a sibling such as
        # ``{repo}/srcs/`` (F2). Segments are normalised first (R2 consequence 4).
        relative_segments = _path_segments(expanded[len(REPO_PARAMETER) :])
        if (
            relative_segments
            and relative_segments[0].casefold() in _SOURCE_TREE_SEGMENTS_FOLDED
        ):
            _fail(
                path,
                f"R2: {field} entry {pattern!r} points into the harness source tree "
                f"through {REPO_PARAMETER}; {REPO_PARAMETER} addresses repository "
                "assets, never the implementation the role runs inside",
            )
    if field != "write_glob":
        return
    if expanded == REPO_PARAMETER:
        _fail(
            path,
            f"R2: {field} entry {pattern!r} is the repository root; "
            f"{REPO_PARAMETER} is read-only and can never be a write target",
        )
    if expanded == REPO_PARAMETER + "/" + REPO_WIDE_GLOB:
        _fail(
            path,
            f"R2: {field} entry {pattern!r} is too broad; "
            f"'{REPO_PARAMETER}/{REPO_WIDE_GLOB}' names the whole repository and "
            "is not a valid write target",
        )
    if rooted_at_repo:
        _fail(
            path,
            f"R2: {field} entry {pattern!r} is rooted at the read-only "
            f"{REPO_PARAMETER} parameter; every output lives under "
            "'workspaces/{ws}/' or 'runs/{task_id}/'",
        )
    _fail(
        path,
        f"R2: {field} entry {pattern!r} contains the read-only {REPO_PARAMETER} "
        "parameter in a non-root segment; a write target names a workspace or "
        "run path, never the repository root",
    )


def validate_glob(pattern: object, path: Path, field: str) -> str:
    if not isinstance(pattern, str) or not pattern.strip():
        _fail(path, f"{field} entries must be non-empty strings")
    if pattern != pattern.strip():
        _fail(path, f"{field} entry {pattern!r} has surrounding whitespace")
    # RR11: a control character (NUL, TAB, CR, LF, DEL, ...) is never part of a
    # canonical segment. Python's own path helpers truncate at NUL and the NTFS
    # API rejects or silently rewrites other control bytes, so a record carrying
    # one cannot be compared reliably with the paths it must not intersect.
    # Checked on the raw pattern: every brace alternative is a slice of it.
    control = sorted(
        {char for char in pattern if ord(char) < 0x20 or ord(char) == 0x7F}
    )
    if control:
        _fail(
            path,
            f"{field} entry {pattern!r} contains the control character "
            f"{control[0]!r}; control characters (including NUL) are not valid "
            "in a path segment and are truncated or rejected by path APIs",
        )
    # Every brace alternation must be validated after expansion: a raw-string
    # check cannot see that ``{..,tmp}`` hides a traversal segment.
    for expanded in expand_braces(pattern):
        if "\\" in expanded:
            _fail(path, f"{field} entry {pattern!r} uses a backslash separator")
        if expanded.startswith("/") or re.match(r"^[A-Za-z]:", expanded):
            _fail(path, f"{field} entry {pattern!r} is an absolute path")
        segments = expanded.split("/")
        if ".." in segments:
            _fail(path, f"{field} entry {pattern!r} escapes its root")
        # R2 consequence 4: ``.`` and empty segments are the same path as the one
        # a rule forbids, so they are rejected alongside ``..`` rather than being
        # silently folded away here. Intersection and containment checks normalise
        # independently, in ``_path_segments``.
        if "." in segments:
            _fail(
                path,
                f"{field} entry {pattern!r} has a '.' (current-directory) segment; "
                "paths are normalised before any rule runs",
            )
        if "" in segments:
            _fail(
                path,
                f"{field} entry {pattern!r} has an empty segment; paths are "
                "normalised before any rule runs",
            )
        # RR11: a trailing dot or space is never a legitimate filename in this
        # contract and is the spelling that silently aliases on win32 (and
        # default macOS), where the path API strips it. Rejecting the segment
        # outright keeps the journal and source-tree gates independent of how a
        # later resolver normalises.
        for segment in segments:
            if segment.endswith("."):
                _fail(
                    path,
                    f"{field} entry {pattern!r} has segment {segment!r} ending in "
                    "a trailing dot; a trailing dot is not a canonical filename "
                    "and aliases on case-insensitive hosts",
                )
            if segment != segment.rstrip():
                _fail(
                    path,
                    f"{field} entry {pattern!r} has segment {segment!r} with "
                    "trailing whitespace; a trailing space is not a canonical "
                    "filename and aliases on case-insensitive hosts",
                )
            # RR11 (T-ALP-A-r5): ``:`` opens an NTFS alternate data stream. On
            # win32 ``journal.jsonl::$DATA`` is the journal's *default* stream
            # (the file's own bytes, measured), and ``journal.jsonl:stream``
            # creates a stream inside the journal file, so either spelling
            # writes the journal while the last segment compares as
            # ``journal.jsonl::$DATA`` and the intersection check sees nothing.
            # No role glob needs a colon, so it is rejected outright rather than
            # compared.
            if ":" in segment:
                _fail(
                    path,
                    f"{field} entry {pattern!r} has segment {segment!r} "
                    "containing ':'; a colon opens an NTFS alternate data stream, "
                    "so 'name:stream' and 'name::$DATA' write into the file "
                    "'name' itself and silently alias the path they name",
                )
            # RR11 (T-ALP-A-r5): ``~`` is the NTFS 8.3 short-name marker. On a
            # volume with short-name generation enabled (measured on this host)
            # ``JOURNA~1.JSO`` is the same file as ``journal.jsonl``, so the
            # spelling writes the journal while no segment compares equal. No
            # legitimate role glob needs ``~``, so it is rejected outright.
            if "~" in segment:
                _fail(
                    path,
                    f"{field} entry {pattern!r} has segment {segment!r} "
                    "containing '~'; '~' is the NTFS 8.3 short-name marker, so "
                    "'JOURNA~1.JSO' addresses 'journal.jsonl' on a volume with "
                    "short names enabled and silently aliases the path it names",
                )
        malformed = _malformed_brace_segment(expanded)
        if malformed is not None:
            _fail(
                path,
                f"{field} entry {pattern!r} has a malformed brace group "
                f"{malformed!r}; a brace group names one parameter and may not "
                "contain another group",
            )
        _validate_repo_parameter(expanded, path, field, pattern)
        if segments[0].casefold() in _SOURCE_TREE_SEGMENTS_FOLDED:
            _fail(
                path,
                f"{field} entry {pattern!r} points into the harness source tree; "
                "a role addresses workspace artifacts and run outputs, never its own implementation",
            )
        if not _is_rooted_glob(expanded):
            _fail(
                path,
                f"R2: {field} entry {pattern!r} is a bare repo-relative path; "
                "prefix it with {repo} (or start it with "
                f"{sorted(LITERAL_GLOB_ROOTS)}, {GIT_DIR!r}, or {REPO_WIDE_GLOB!r})",
            )
        for match in _BRACE.finditer(expanded):
            for option in match.group(1).split(","):
                if option not in PATH_PARAMETERS:
                    _fail(
                        path,
                        f"{field} entry {pattern!r} uses unknown parameter {{{option}}}; "
                        f"allowed: {sorted(PATH_PARAMETERS)}",
                    )
        # Checked after the parameter loop so ``{project}`` is reported as an
        # unknown parameter rather than as a literal in the ``{ws}`` position.
        _validate_root_parameter(expanded, path, field, pattern)
    return pattern


def validate_role(role: dict, path: Path, known_ids: set[str]) -> None:
    """Validate one role record against the Role@1 contract (spec section 2-3)."""
    if role.get("kind") != ROLE_KIND:
        _fail(path, f"field 'kind' must be {ROLE_KIND!r}, found {role.get('kind')!r}")
    role_id = _require_string(role, "id", path)
    if path.stem != role_id:
        _fail(path, f"id {role_id!r} does not match the filename")
    _require_string(role, "title", path)
    purpose = _require_string(role, "purpose", path)
    version = _require_string(role, "version", path)
    if not _SEMVER.match(version):
        _fail(path, f"field 'version' must be semver, found {version!r}")
    if role.get("mode") not in MODES:
        _fail(path, f"field 'mode' must be one of {MODES}, found {role.get('mode')!r}")
    if role.get("network") not in NETWORKS:
        _fail(
            path,
            f"field 'network' must be one of {NETWORKS}, found {role.get('network')!r}",
        )

    tools = _require_string_list(role, "tools", path)
    unknown_tools = sorted(set(tools) - set(CAPABILITIES))
    if unknown_tools:
        _fail(path, f"unknown capabilities in 'tools': {unknown_tools}")
    if sorted(set(tools)) != sorted(tools):
        _fail(path, "field 'tools' must not repeat a capability")

    # Inputs declare their provenance: a workspace source, a written input, or
    # another role's artifact.
    inputs = role.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        _fail(path, "field 'inputs' must be a non-empty list")
    for item in inputs:
        if not isinstance(item, dict):
            _fail(path, "every input must be an object")
        schema = item.get("schema")
        if not isinstance(schema, str) or not schema.strip():
            _fail(path, "every input must declare a 'schema'")
        origin = item.get("from")
        if not isinstance(origin, str) or not origin.strip():
            _fail(path, f"input {schema!r} must declare a non-empty 'from'")
        if origin not in INPUT_ORIGINS and origin not in known_ids:
            _fail(
                path,
                f"input {schema!r} has unknown 'from' {origin!r}; expected one of "
                f"{sorted(INPUT_ORIGINS)} or a known role id",
            )

    # R1: a role contains no shell command and no path literal.
    for field, value in (("purpose", purpose), ("title", role["title"])):
        for marker in _SHELL_MARKERS:
            if marker in value:
                _fail(
                    path, f"R1: field {field!r} contains a command fragment {marker!r}"
                )
        if _PATH_LITERAL.search(value):
            _fail(path, f"R1: field {field!r} contains a path literal")
    for condition in _require_string_list(role, "stop_conditions", path):
        for marker in _SHELL_MARKERS:
            if marker in condition:
                _fail(
                    path, f"R1: a stop_condition contains a command fragment {marker!r}"
                )

    # Read-only claims must match the capability set.
    claims_read_only = "read-only" in purpose.lower()
    if claims_read_only and set(tools) & set(WRITE_CAPABILITIES):
        _fail(path, "description claims read-only but 'tools' grants edit or write")

    # R3: every declared output has a write_glob.
    outputs = role.get("outputs")
    if not isinstance(outputs, list) or not outputs:
        _fail(path, "field 'outputs' must be a non-empty list")
    write_globs: list[str] = []
    role_written_output = False
    for output in outputs:
        if not isinstance(output, dict):
            _fail(path, "every output must be an object")
        if not isinstance(output.get("schema"), str) or not output["schema"].strip():
            _fail(path, "every output must declare a 'schema'")
        write_glob = output.get("write_glob")
        if not isinstance(write_glob, str) or not write_glob.strip():
            _fail(path, f"output {output['schema']!r} declares no 'write_glob'")
        validate_glob(write_glob, path, "write_glob")
        if write_glob == "**":
            _fail(path, "write_glob '**' is too broad; declare the owned artifact path")
        written_by = output.get("written_by", "role")
        if written_by not in WRITTEN_BY:
            _fail(
                path,
                f"output {output['schema']!r} has written_by {written_by!r}; "
                f"expected one of {WRITTEN_BY}",
            )
        if written_by == "role":
            role_written_output = True
            if not set(tools) & set(WRITE_CAPABILITIES):
                _fail(
                    path,
                    f"output {output['schema']!r} is written by the role but 'tools' "
                    "grants no edit/write capability; declare 'written_by': 'adapter'",
                )
        write_globs.append(write_glob)

    read_globs = [
        validate_glob(item, path, "read_glob")
        for item in _require_string_list(role, "read_glob", path)
    ]
    deny_globs = [
        validate_glob(item, path, "deny_glob")
        for item in _require_string_list(role, "deny_glob", path)
    ]

    # R7: a critic denies every read family it is not allowed to write.
    if _is_critic(role_id, purpose):
        _validate_critic_denials(
            role_id,
            read_globs,
            write_globs,
            deny_globs,
            role_written_output,
            path,
        )

    # R4: no role may write the audit journal or repository history. Checked
    # before the generic intersection so the contradiction is named precisely.
    for write_glob in write_globs:
        if globs_intersect(write_glob, AUDIT_JOURNAL):
            _fail(path, f"write_glob {write_glob!r} would write the audit journal")
        if globs_intersect(write_glob, GIT_DIR):
            _fail(path, f"write_glob {write_glob!r} would write repository history")

    # R4: deny_glob always wins, so a write inside a denied glob is a contradiction.
    for write_glob in write_globs:
        for deny_glob in deny_globs:
            if globs_intersect(write_glob, deny_glob):
                _fail(
                    path,
                    f"write_glob {write_glob!r} intersects deny_glob {deny_glob!r}",
                )

    # R4/§4: every role denies the audit journal and repository history, whether
    # or not it reads the tree repo-wide. A broader audit-tree denial covers the
    # journal; ``inception-agent`` denies the journal literal because it writes
    # ``audit/recon_context.json``. Reads are governed solely by ``read_glob``.
    if not any(glob_within(AUDIT_JOURNAL, deny_glob) for deny_glob in deny_globs):
        _fail(path, f"deny_glob must deny {AUDIT_JOURNAL!r}")
    if not any(glob_within(GIT_DIR, deny_glob) for deny_glob in deny_globs):
        _fail(path, f"deny_glob must deny {GIT_DIR!r}")

    refusal_codes = _require_string_list(role, "refusal_codes", path)
    unknown_codes = sorted(set(refusal_codes) - GLOBAL_REFUSAL_CODES)
    if unknown_codes:
        _fail(path, f"refusal_codes outside the closed registry: {unknown_codes}")

    independence = role.get("independence")
    if not isinstance(independence, dict):
        _fail(path, "field 'independence' must be an object")
    blinded_from = independence.get("blinded_from")
    if not isinstance(blinded_from, list) or not all(
        isinstance(item, str) for item in blinded_from
    ):
        _fail(path, "independence.blinded_from must be a list of role ids")
    unknown_blinded = sorted(set(blinded_from) - known_ids)
    if unknown_blinded:
        _fail(path, f"independence.blinded_from names unknown roles: {unknown_blinded}")
    if role_id in blinded_from:
        _fail(path, "a role cannot be blinded from itself")
    if independence.get("isolation") not in ISOLATIONS:
        _fail(
            path,
            f"independence.isolation must be one of {ISOLATIONS}, "
            f"found {independence.get('isolation')!r}",
        )

    # R6: blinding is an adapter control, so the record may not require an input
    # whose provenance is a role the adapter hides from it. ``blinded_from``
    # hides that role's narrative/self-assessment; a diff handed over as written
    # input is therefore ``from: written-input``, not ``from: <blinded role>``.
    for item in inputs:
        origin = item.get("from")
        if item.get("required") and origin in blinded_from:
            _fail(
                path,
                f"required input {item.get('schema')!r} comes from {origin!r}, "
                "which independence.blinded_from hides; a required input cannot "
                "be sourced from a blinded role",
            )

    requires_skill = _require_string_list(role, "requires_skill", path)
    has_skill_tool = "skill" in tools
    if bool(requires_skill) != has_skill_tool:
        if requires_skill:
            _fail(path, "role requires a skill but 'tools' does not grant 'skill'")
        _fail(
            path,
            "role grants 'skill' but 'requires_skill' is empty; "
            "R5 derives 'skill' from 'requires_skill'",
        )

    bash_approval = role.get("bash_approval", "allow")
    if bash_approval not in BASH_APPROVALS:
        _fail(
            path,
            f"bash_approval must be one of {BASH_APPROVALS}, found {bash_approval!r}",
        )
    if bash_approval != "allow" and "bash" not in tools:
        _fail(path, "bash_approval is set but 'bash' is not in 'tools'")

    audit = role.get("audit")
    if not isinstance(audit, dict):
        _fail(path, "field 'audit' must be an object")
    _require_string(audit, "actor", path)
    _require_string_list(audit, "emit", path)


def load_roles(root: Path) -> dict[str, dict]:
    """Load and validate every ``roles/*.json`` record under ``root``."""
    directory = root / ROLES_DIR
    if not directory.is_dir():
        raise RoleError(f"role directory missing: {directory}")
    pending: dict[str, tuple[Path, dict]] = {}
    for path in sorted(directory.glob("*.json")):
        try:
            role = json.loads(read_text(path))
        except json.JSONDecodeError as exc:
            raise RoleError(f"{path}: invalid JSON: {exc}") from exc
        if not isinstance(role, dict):
            raise RoleError(f"{path}: role record must be a JSON object")
        role_id = role.get("id")
        if not isinstance(role_id, str) or not role_id:
            raise RoleError(f"{path}: role record is missing a string 'id'")
        if role_id in pending:
            raise RoleError(f"{path}: duplicate role id {role_id!r}")
        pending[role_id] = (path, role)
    if not pending:
        raise RoleError(f"no role records found in {directory}")
    known_ids = set(pending)
    for role_id in sorted(pending):
        path, role = pending[role_id]
        validate_role(role, path, known_ids)
    return {role_id: pending[role_id][1] for role_id in sorted(pending)}


# --------------------------------------------------------------------------- #
# derivation and rendering
# --------------------------------------------------------------------------- #


def derive_permissions(role: dict) -> dict[str, str]:
    """Derive the permission map from ``tools``, outputs and skills (R5).

    ``edit`` is granted only when the role both declares a writing capability and
    owns at least one output the role itself writes (``written_by: role``, the
    default). ``bash`` is granted only when it is in ``tools``; ``bash_approval``
    selects approval-gated shell access for roles that stay otherwise restricted.
    ``skill`` is granted only when ``requires_skill`` is non-empty, and ``task``
    follows ``tools``.
    """
    tools = set(role["tools"])
    has_role_output = any(
        output.get("written_by", "role") == "role" for output in role["outputs"]
    )
    permissions: dict[str, str] = {
        capability: ("allow" if capability in tools else "deny")
        for capability in READ_CAPABILITIES
    }
    permissions["edit"] = (
        "allow" if set(tools) & set(WRITE_CAPABILITIES) and has_role_output else "deny"
    )
    if "bash" not in tools:
        permissions["bash"] = "deny"
    else:
        permissions["bash"] = role.get("bash_approval", "allow")
    permissions["skill"] = "allow" if role.get("requires_skill") else "deny"
    permissions["task"] = "allow" if "task" in tools else "deny"
    return permissions


def render_frontmatter(role: dict) -> str:
    """Render the generated YAML frontmatter for one role."""
    permissions = derive_permissions(role)
    lines = [
        "---",
        f"description: {json.dumps(role['purpose'], ensure_ascii=False)}",
        f"kind: {ROLE_KIND}",
        f"mode: {role['mode']}",
    ]
    if all(value == "allow" for value in permissions.values()):
        lines.append("permission: allow")
    else:
        lines.append("permission:")
        lines.extend(f"  {key}: {permissions[key]}" for key in sorted(permissions))
    lines.append("---")
    return "\n".join(lines) + "\n"


def render_agent(role: dict, body: str) -> str:
    """Return the generated frontmatter followed by the untouched body."""
    return render_frontmatter(role) + body


def _role_capabilities(role: dict) -> dict[str, object]:
    return {
        "audit": role["audit"],
        "deny_glob": role["deny_glob"],
        "id": role["id"],
        "independence": role["independence"],
        "mode": role["mode"],
        "network": role["network"],
        "outputs": role["outputs"],
        "permission": derive_permissions(role),
        "read_glob": role["read_glob"],
        "refusal_codes": role["refusal_codes"],
        "requires_skill": role["requires_skill"],
        "title": role["title"],
        "version": role["version"],
        "write_glob": [output["write_glob"] for output in role["outputs"]],
    }


def render_permissions(roles: dict[str, dict]) -> str:
    """Render the derived capability/permission map consumed by the app layer."""
    payload = {
        "generated_by": "scripts/generate_agent_roles.py",
        "roles": {
            role_id: _role_capabilities(roles[role_id]) for role_id in sorted(roles)
        },
        "schema": PERMISSIONS_SCHEMA,
    }
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def expected_files(root: Path) -> dict[str, str]:
    """Return every generated file as ``{repo-relative posix path: content}``."""
    roles = load_roles(root)
    documents: dict[str, str] = {}
    for role_id in sorted(roles):
        prompt = root / ROLES_DIR / f"{role_id}.prompt.md"
        if not prompt.is_file():
            raise RoleError(f"{prompt}: missing instruction body for role {role_id!r}")
        documents[f"{AGENT_DIR}/{role_id}.md"] = render_agent(
            roles[role_id], read_text(prompt)
        )
    documents[PERMISSIONS_FILE] = render_permissions(roles)
    return documents


def check_root(root: Path) -> list[str]:
    """Return the sorted repo-relative paths that drift from ``roles/``."""
    documents = expected_files(root)
    drift: list[str] = []
    for relative in sorted(documents):
        path = root / relative
        if not path.is_file():
            drift.append(relative)
            continue
        if read_text(path) != documents[relative]:
            drift.append(relative)
            continue
        if relative.endswith(".md"):
            try:
                load_agent_definition(path)
            except AgentLoadError:
                drift.append(relative)
    agent_dir = root / AGENT_DIR
    expected_documents = {
        relative for relative in documents if relative.endswith(".md")
    }
    for path in sorted(agent_dir.rglob("*.md")):
        relative = path.relative_to(root).as_posix()
        if relative not in expected_documents:
            drift.append(relative)
    return drift


def _write_atomic(path: Path, data: bytes) -> None:
    """Write ``data`` to ``path`` through a sibling temp file and ``os.replace``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def write_root(root: Path) -> list[str]:
    """Write every generated file; return the written repo-relative paths."""
    documents = expected_files(root)
    written: list[str] = []
    for relative in sorted(documents):
        path = root / relative
        _write_atomic(path, documents[relative].encode("utf-8"))
        written.append(relative)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="report drift and exit non-zero"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="repository root to operate on (defaults to this checkout)",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.check:
            drift = check_root(root)
            if drift:
                for relative in drift:
                    print(f"drift: {relative}")
                return 1
            print(f"agent roles current: {len(load_roles(root))} roles")
            return 0
        written = write_root(root)
        print(
            f"wrote {len(written)} generated files from {len(load_roles(root))} role records"
        )
    except RoleError as exc:
        print(f"error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
