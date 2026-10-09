"""PipelineSpec fingerprinting (HCM-03 neutral core).

Moved verbatim from ``console.api.pipelines``. The fingerprint is the
canonical-JSON SHA-256 over the spec with any prior ``fingerprint`` value
excluded, so save+read round-trips are stable.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .models import PipelineSpec


def _fingerprint(spec: PipelineSpec) -> str:
    data = spec.model_dump()
    data.pop("fingerprint", None)

    def _sort(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: _sort(v) for k, v in sorted(value.items())}
        if isinstance(value, list):
            return [_sort(v) for v in value]
        return value

    canonical = json.dumps(_sort(data), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
