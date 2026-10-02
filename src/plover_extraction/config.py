"""External configuration for sentence splitting and LLM access."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .ontology import PloverCategory, validate_event_type

DEFAULT_SENTENCE_SPLIT_PATTERN = r"(?<=[.!?])\s+|\n+"


@dataclass(frozen=True, slots=True)
class LLMConfig:
    model: str
    api_base: str = "https://api.openai.com/v1"
    api_key_env: str = "OPENAI_API_KEY"
    temperature: float = 0.0
    timeout_seconds: float = 60.0
    max_retries: int = 2


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    llm: LLMConfig
    category: PloverCategory
    event_type: str | None
    system_prompt: str
    sentence_split_pattern: str = DEFAULT_SENTENCE_SPLIT_PATTERN


def load_config(path: str | Path) -> PipelineConfig:
    """Load and validate configuration from a JSON file."""
    with open(path, encoding="utf-8") as stream:
        raw: dict[str, Any] = json.load(stream)
    try:
        llm = LLMConfig(**raw["llm"])
        config = PipelineConfig(
            llm=llm,
            category=raw["category"],
            event_type=raw.get("event_type"),
            system_prompt=raw["system_prompt"],
            sentence_split_pattern=raw.get(
                "sentence_split_pattern", DEFAULT_SENTENCE_SPLIT_PATTERN
            ),
        )
    except (KeyError, TypeError) as error:
        raise ValueError(f"Invalid configuration: {error}") from error
    if not config.llm.model.strip():
        raise ValueError("llm.model must be a non-empty string")
    if not config.system_prompt.strip():
        raise ValueError("system_prompt must be a non-empty string")
    validate_event_type(config.category, config.event_type)
    if config.llm.max_retries < 0 or config.llm.timeout_seconds <= 0:
        raise ValueError("LLM retries and timeout must be non-negative/positive")
    return config
