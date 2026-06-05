import pytest

from transport_ai.callsheet import _extract_json_array, parse_call_sheet_text


class FakeProvider:
    def __init__(self, response: str, *, available: bool = True) -> None:
        self.response = response
        self._available = available

    @property
    def available(self) -> bool:
        return self._available

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 2048) -> str:
        return self.response


def test_extract_json_array_plain():
    rows = _extract_json_array('[{"name": "Anna", "address": "Drottninggatan 1, Stockholm"}]')
    assert rows == [{"name": "Anna", "address": "Drottninggatan 1, Stockholm"}]


def test_extract_json_array_markdown_fence():
    raw = """```json
[{"name": "Grip", "address": "Sveavägen 44"}]
```"""
    rows = _extract_json_array(raw)
    assert rows[0]["name"] == "Grip"


def test_extract_json_array_with_prose():
    raw = 'Here is the list:\n[{"name": "AD", "address": "Storgatan 1"}]\nDone.'
    rows = _extract_json_array(raw)
    assert rows[0]["name"] == "AD"


def test_extract_json_array_skips_invalid_rows():
    raw = '[{"name": ""}, {"name": "Sound", "address": "Hornstull"}]'
    rows = _extract_json_array(raw)
    assert len(rows) == 1
    assert rows[0]["name"] == "Sound"


def test_parse_call_sheet_text():
    provider = FakeProvider(
        '[{"name": "Camera", "address": "Drottninggatan 1, Stockholm"}]'
    )
    rows = parse_call_sheet_text("Camera - Drottninggatan 1", provider)
    assert rows[0]["name"] == "Camera"
    assert "Drottninggatan" in rows[0]["address"]


def test_parse_call_sheet_unavailable_provider():
    provider = FakeProvider("", available=False)
    with pytest.raises(RuntimeError, match="not available"):
        parse_call_sheet_text("text", provider)
