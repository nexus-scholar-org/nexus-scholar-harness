"""The committed ``confirmation-v1`` JSON schema, rendered from the model."""

from __future__ import annotations

import json

from .model import HumanConfirmation

SCHEMA_BASE_URI = "https://nexus-scholar.org/schemas/confirmation/v1"
SCHEMA_FILENAME = "confirmation.schema.json"


def render_confirmation_schema() -> str:
    """Render the ``HumanConfirmation@1`` JSON schema deterministically."""

    schema = HumanConfirmation.model_json_schema(mode="validation", by_alias=True)
    document = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE_URI}/{SCHEMA_FILENAME}",
        "title": "HumanConfirmation@1",
        **schema,
    }
    return json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
