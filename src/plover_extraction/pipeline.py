"""End-to-end raw-text Plover extraction pipeline."""

import json
from string import Template

from .config import PipelineConfig
from .llm import LLMClient
from .models import EventMention, ExtractionRequest, Sentence
from .sentences import split_sentences


def build_user_prompt(
    request: ExtractionRequest, config: PipelineConfig, sentences: list[Sentence]
) -> str:
    """Render the externally configured extraction prompt."""
    sentence_data = [{"id": item.sentence_id, "text": item.text} for item in sentences]
    try:
        return Template(config.user_prompt_template).substitute(
            doc_id=json.dumps(request.doc_id, ensure_ascii=False),
            category=config.category,
            category_description=config.category_description,
            event_type=json.dumps(config.event_type),
            event_type_description=config.event_type_description,
            sentences=json.dumps(sentence_data, ensure_ascii=False),
        )
    except (KeyError, ValueError) as error:
        raise ValueError(f"Invalid user_prompt_template placeholder: {error}") from error


def extract_events(
    request: ExtractionRequest, config: PipelineConfig, client: LLMClient
) -> list[EventMention]:
    """Split raw text, query the LLM, and validate its output against the request."""
    sentences = split_sentences(request.doc_id, request.raw_text, config.sentence_split_pattern)
    result = client.generate_json(
        config.system_prompt, build_user_prompt(request, config, sentences)
    )
    if not isinstance(result, dict) or not isinstance(result.get("events"), list):
        raise ValueError("LLM output must be an object containing an events array")
    known_ids = {sentence.sentence_id for sentence in sentences}
    mentions: list[EventMention] = []
    for index, raw in enumerate(result["events"], 1):
        if not isinstance(raw, dict):
            raise ValueError("Each LLM event must be an object")
        allowed = {"actor_text", "recipient_text", "evidence_sentence_ids"}
        if set(raw) != allowed:
            raise ValueError(f"LLM event fields must be exactly: {', '.join(sorted(allowed))}")
        evidence_value = raw["evidence_sentence_ids"]
        if not isinstance(evidence_value, list) or not all(
            isinstance(value, str) for value in evidence_value
        ):
            raise ValueError("evidence_sentence_ids must be an array of strings")
        evidence = tuple(evidence_value)
        unknown = set(evidence) - known_ids
        if unknown:
            raise ValueError(f"LLM returned unknown sentence IDs: {', '.join(sorted(unknown))}")
        mentions.append(EventMention(
            doc_id=request.doc_id,
            mention_id=f"m{index}",
            actor_text=raw["actor_text"],
            recipient_text=raw["recipient_text"],
            category=config.category,
            event_type=config.event_type,
            evidence_sentence_ids=evidence,
        ))
    return mentions
