"""Pluggable LLM provider — Ollama (Gemma) default, degrades gracefully."""

from __future__ import annotations

from typing import Protocol

import httpx


class LLMProvider(Protocol):
    @property
    def available(self) -> bool: ...

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 2048) -> str: ...


class DisabledProvider:
    @property
    def available(self) -> bool:
        return False

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 2048) -> str:
        raise RuntimeError("AI is disabled (AI_ENABLED=false)")


class OllamaProvider:
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "gemma2:2b",
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._available: bool | None = None

    @property
    def available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            self._available = response.status_code == 200
        except Exception:
            self._available = False
        return self._available

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 2048) -> str:
        if not self.available:
            raise RuntimeError(f"Ollama not reachable at {self.base_url}")

        payload: dict = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.1,
            },
        }
        if system:
            payload["system"] = system

        response = httpx.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()


def get_provider(
    *,
    enabled: bool,
    base_url: str = "http://localhost:11434",
    model: str = "gemma2:2b",
) -> LLMProvider:
    if not enabled:
        return DisabledProvider()
    return OllamaProvider(base_url=base_url, model=model)
