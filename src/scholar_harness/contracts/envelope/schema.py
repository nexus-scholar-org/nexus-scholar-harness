"""The committed ``envelope-v1`` JSON schema, rendered from the model."""

from __future__ import annotations

import json

from .model import Envelope

SCHEMA_BASE_URI = "https://nexus-scholar.org/schemas/envelope/v1"
SCHEMA_FILENAME = "envelope.schema.json"


def render_envelope_schema() -> str:
    """Render the ``envelope-v1`` JSON schema deterministically."""

    schema = Envelope.model_json_schema(mode="validation", by_alias=True)
    document = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE_URI}/{SCHEMA_FILENAME}",
        "title": "Envelope@1",
        **schema,
    }
    return json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
