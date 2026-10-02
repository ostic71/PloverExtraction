"""Small OpenAI-compatible chat client used by the extraction pipeline."""

import json
import os
import time
import urllib.error
import urllib.request
from typing import Protocol

from .config import LLMConfig


class LLMClient(Protocol):
    def generate_json(self, system_prompt: str, user_prompt: str) -> object:
        """Return the decoded JSON value produced by an LLM."""


class OpenAICompatibleClient:
    """Call an OpenAI-compatible ``/chat/completions`` JSON endpoint."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    def generate_json(self, system_prompt: str, user_prompt: str) -> object:
        api_key = os.environ.get(self.config.api_key_env)
        if not api_key:
            raise RuntimeError(f"Missing API key environment variable: {self.config.api_key_env}")
        payload = json.dumps({
            "model": self.config.model,
            "temperature": self.config.temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }).encode("utf-8")
        request = urllib.request.Request(
            f"{self.config.api_base.rstrip('/')}/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(self.config.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                    body = json.load(response)
                content = body["choices"][0]["message"]["content"]
                return json.loads(content)
            except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError) as error:
                if attempt >= self.config.max_retries:
                    raise RuntimeError(f"LLM request failed: {error}") from error
                time.sleep(2**attempt)
        raise AssertionError("unreachable")
