import logging
import time
from typing import Protocol

import httpx

logger = logging.getLogger(__name__)

from app.config import get_settings

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
RETRYABLE_STATUS_CODES = {400, 429, 500, 503}


class LLMClient(Protocol):
    def generate_content(
        self, system_instruction: str, contents: list[dict], tools: list[dict]
    ) -> dict:
        """Returns the raw provider response as a dict."""
        ...


class LLMNotConfiguredError(Exception):
    pass


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.5-flash",
        timeout: float = 45.0,
        max_retries: int = 3,
    ):
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._max_retries = max_retries

    def generate_content(
        self, system_instruction: str, contents: list[dict], tools: list[dict]
    ) -> dict:
        url = f"{GEMINI_API_BASE}/models/{self._model}:generateContent"
        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": contents,
            "tools": tools,
        }

        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = httpx.post(
                    url, params={"key": self._api_key}, json=payload, timeout=self._timeout
                )
                if response.status_code in RETRYABLE_STATUS_CODES and attempt < self._max_retries:
                    time.sleep(2**attempt)
                    continue
                if response.status_code >= 400:
                    logger.warning("Gemini API error %s: %s", response.status_code, response.text[:2000])
                response.raise_for_status()
                return response.json()
            except httpx.TransportError as exc:
                last_error = exc
                if attempt < self._max_retries:
                    time.sleep(2**attempt)
                    continue
                raise

        raise last_error or RuntimeError("Gemini request failed with no response")


def get_llm_client() -> LLMClient:
    settings = get_settings()
    if not settings.llm_api_key:
        raise LLMNotConfiguredError("LLM_API_KEY is not set")

    if settings.llm_provider == "gemini":
        return GeminiClient(api_key=settings.llm_api_key)

    raise LLMNotConfiguredError(f"Unsupported LLM_PROVIDER: {settings.llm_provider!r}")
