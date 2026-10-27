"""``SKILL.meta.json`` generation at install (spec 03 §5).

Pins belong in exactly one place: the manifest (``plugins.json``, bundled in
the wheel). A skill body never restates a version; instead the installer
emits one ``SKILL.meta.json`` per skill directory:

```json
{"skill": "scholar-graph-kit", "kit": "scholar-graph-kit",
 "rev": "<full sha from plugins.json>", "source": "plugins.json",
 "verified_at": "<ISO8601 UTC at generation>"}
```

``verified_at`` is timing metadata only — it is never part of any identity
digest (the Phase B convention). A skill whose kit has no manifest entry gets
``rev: null`` and stays equally honest; dev-loop-only skills
(e.g. ``pull-request-gate``) are not kits and that is a legitimate state.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

from scholar_harness.contracts.envelope.registry import RefusalCode

from .frontmatter import SkillContractRefusal

METADATA_FILENAME = "SKILL.meta.json"


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SkillContractRefusal(
            RefusalCode.BLOCKED_INPUT, f"plugins manifest unreadable: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise SkillContractRefusal(
            RefusalCode.INVALID_OUTPUT, f"plugins manifest is not valid JSON: {exc}"
        ) from exc


def generate_skill_meta(
    skills_root: str | Path,
    manifest_path: str | Path,
    *,
    verified_at: str | None = None,
    dry_run: bool = False,
) -> dict[str, Path]:
    """Generate one ``SKILL.meta.json`` per skill directory under the root.

    Returns ``{skill_name: meta_path}``. Deterministic given the same manifest
    and clock; ``verified_at`` is an ISO8601 UTC timestamp supplied or clocked
    at generation time.
    """

    manifest = _load_manifest(Path(manifest_path))
    plugins = manifest.get("plugins")
    if not isinstance(plugins, list) or not all(
        isinstance(entry, dict) for entry in plugins
    ):
        raise SkillContractRefusal(
            RefusalCode.INVALID_OUTPUT,
            f"{manifest_path}: expected a 'plugins' list of objects",
        )

    skills_root = Path(skills_root)
    if not skills_root.is_dir():
        raise SkillContractRefusal(
            RefusalCode.BLOCKED_INPUT, f"skills root missing: {skills_root}"
        )

    created: dict[str, Path] = {}
    stamp = verified_at or datetime.datetime.now(datetime.timezone.utc).isoformat()
    for skill_dir in sorted(p for p in skills_root.iterdir() if p.is_dir()):
        if not (skill_dir / "SKILL.md").is_file():
            continue
        name = skill_dir.name
        kit_entry = next(
            (entry for entry in plugins if entry.get("name") == name), None
        )
        rev = kit_entry.get("default_rev") if kit_entry is not None else None
        payload = {
            "skill": name,
            "kit": kit_entry.get("name", name) if kit_entry is not None else name,
            "rev": rev,
            "source": str(manifest_path),
            "verified_at": stamp,
        }
        meta_path = skill_dir / METADATA_FILENAME
        if not dry_run:
            meta_path.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        created[name] = meta_path
    return created


__all__ = ["METADATA_FILENAME", "generate_skill_meta"]
