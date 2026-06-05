"""Parse unstructured call-sheet / crew list text into structured pickups."""

from __future__ import annotations

import json
import re

from transport_ai.provider import LLMProvider

SYSTEM_PROMPT = """You extract film production crew pickup data.
Return ONLY a JSON array, no markdown, no explanation.
Each item: {"name": "...", "address": "full street address or area, city"}
Use real address strings coordinators can geocode — never invent latitude or longitude.
If address is missing, use empty string."""

USER_TEMPLATE = """Extract crew pickup list from this production text.
Return JSON array of {{name, address}} objects.

TEXT:
{text}
"""


def _extract_json_array(text: str) -> list[dict]:
    """Pull JSON array from model output (may include extra prose)."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("AI response did not contain a JSON array")

    parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, list):
        raise ValueError("AI response JSON root must be an array")

    rows = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        rows.append(
            {
                "name": name,
                "address": str(item.get("address", "")).strip(),
            }
        )
    if not rows:
        raise ValueError("No valid crew rows extracted")
    return rows


def parse_call_sheet_text(text: str, provider: LLMProvider) -> list[dict]:
    """Use local LLM to structure messy call-sheet text."""
    if not provider.available:
        raise RuntimeError("AI provider is not available")

    raw = provider.complete(
        USER_TEMPLATE.format(text=text.strip()),
        system=SYSTEM_PROMPT,
        max_tokens=2048,
    )
    return _extract_json_array(raw)
