"""Dependency-free loading for the project's deliberately small YAML subset."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .ontology import PloverCategory, validate_event_type

DEFAULT_SENTENCE_SPLIT_PATTERN = r"(?<=[.!?])\s+|\n+"


def _scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value in {"null", "~"}:
        return None
    if value in {"true", "false"}:
        return value == "true"
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _load_simple_yaml(path: str | Path) -> dict[str, Any]:
    """Parse top-level scalars, JSON-style lists, and ``|`` block strings."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    result: dict[str, Any] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[:1].isspace() or ":" not in line:
            raise ValueError(f"Invalid top-level YAML at line {index}: {line!r}")
        key, value = line.split(":", 1)
        key = key.strip()
        if value.strip() in {"|", "|-", ">", ">-"}:
            block: list[str] = []
            while index < len(lines) and (not lines[index] or lines[index][:1].isspace()):
                block_line = lines[index]
                index += 1
                block.append(block_line[2:] if block_line.startswith("  ") else block_line)
            result[key] = "\n".join(block).rstrip()
        else:
            result[key] = _scalar(value)
    return result


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
    allowed_event_types: tuple[str | None, ...]
    category_description: str
    event_type_description: str
    system_prompt: str
    user_prompt_template: str
    sentence_split_pattern: str = DEFAULT_SENTENCE_SPLIT_PATTERN


def load_config(path: str | Path) -> PipelineConfig:
    """Load model settings, label definitions, and prompts from YAML."""
    raw = _load_simple_yaml(path)
    try:
        llm = LLMConfig(**{key: raw[key] for key in (
            "model", "api_base", "api_key_env", "temperature",
            "timeout_seconds", "max_retries",
        )})
        config = PipelineConfig(
            llm=llm,
            category=raw["category"],
            event_type=raw.get("event_type"),
            allowed_event_types=tuple(raw["allowed_event_types"]),
            category_description=raw["category_description"],
            event_type_description=raw["event_type_description"],
            system_prompt=raw["system_prompt"],
            user_prompt_template=raw["user_prompt_template"],
            sentence_split_pattern=raw.get(
                "sentence_split_pattern", DEFAULT_SENTENCE_SPLIT_PATTERN
            ),
        )
    except (KeyError, TypeError) as error:
        raise ValueError(f"Invalid configuration: {error}") from error
    validate_event_type(config.category, config.event_type)
    if config.event_type not in config.allowed_event_types:
        raise ValueError("event_type must be included in allowed_event_types")
    for name in ("model", "category_description", "event_type_description", "system_prompt", "user_prompt_template"):
        if not getattr(config.llm, name, None) and not getattr(config, name, None):
            raise ValueError(f"{name} must be a non-empty string")
    if config.llm.max_retries < 0 or config.llm.timeout_seconds <= 0:
        raise ValueError("LLM retries and timeout must be non-negative/positive")
    return config
