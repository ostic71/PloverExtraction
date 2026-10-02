"""End-to-end raw-text Plover extraction pipeline."""

import json

from .config import PipelineConfig
from .llm import LLMClient
from .models import EventMention, ExtractionRequest, Sentence
from .ontology import MODE_DESCRIPTIONS, PLOVER_CATEGORY_DESCRIPTIONS
from .sentences import split_sentences


def build_user_prompt(
    request: ExtractionRequest, config: PipelineConfig, sentences: list[Sentence]
) -> str:
    """Build explicit extraction rules and the machine-readable output contract."""
    mode_description = (
        MODE_DESCRIPTIONS[config.category].get(config.event_type, "Category-level event")
        if config.event_type is not None else "Category-level event"
    )
    sentence_data = [{"id": item.sentence_id, "text": item.text} for item in sentences]
    return (
        "TASK\n"
        "Find every distinct event in SENTENCES that satisfies both TARGET_CATEGORY and "
        "TARGET_EVENT_TYPE. Use the definitions below, not keyword matching alone.\n\n"
        "EXTRACTION RULES\n"
        "1. actor_text is the exact text span for the entity performing or communicating "
        "the event. recipient_text is the exact text span for its target.\n"
        "2. Copy actor_text and recipient_text verbatim from SENTENCES; never infer an "
        "unstated entity. If either role is not explicit, do not emit that event.\n"
        "3. evidence_sentence_ids contains every and only sentence needed to establish the "
        "actor, recipient, and event. Use only IDs present in SENTENCES.\n"
        "4. Emit separate array items for distinct event mentions. Do not duplicate one "
        "event merely because it has multiple evidence sentences.\n"
        "5. Ignore events belonging to another Plover category/type. Return an empty events "
        "array when no matching event is explicit.\n\n"
        "OUTPUT CONTRACT\n"
        "Return JSON only, with exactly this shape (no markdown or extra keys):\n"
        '{"events":[{"actor_text":"exact source span","recipient_text":"exact source '
        'span","evidence_sentence_ids":["s1"]}]}\n'
        "The pipeline will add doc_id, sequential mention_id, category, and event_type to "
        "produce each item in this final public schema:\n"
        '{"doc_id":"document id","mention_id":"m1","actor_text":"exact source '
        'span","recipient_text":"exact source span","category":"configured category",'
        '"event_type":"configured event type or null","evidence_sentence_ids":["s1"]}\n\n'
        f"DOCUMENT_ID: {json.dumps(request.doc_id, ensure_ascii=False)}\n"
        f"TARGET_CATEGORY: {config.category}\n"
        f"CATEGORY_DEFINITION: {PLOVER_CATEGORY_DESCRIPTIONS[config.category]}\n"
        f"TARGET_EVENT_TYPE: {json.dumps(config.event_type)}\n"
        f"EVENT_TYPE_DEFINITION: {mode_description}\n"
        f"SENTENCES: {json.dumps(sentence_data, ensure_ascii=False)}"
    )


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
