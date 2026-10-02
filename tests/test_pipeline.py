import json

import pytest

from plover_extraction.config import LLMConfig, PipelineConfig, load_config
from plover_extraction.models import ExtractionRequest
from plover_extraction.pipeline import extract_events
from plover_extraction.sentences import split_sentences


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.user_prompt = ""

    def generate_json(self, system_prompt, user_prompt):
        self.user_prompt = user_prompt
        return self.response


def config():
    return PipelineConfig(LLMConfig("test-model"), "THREATEN", "Violence", "Extract events")


def test_raw_text_is_split_and_llm_output_is_normalized():
    client = FakeClient({"events": [{
        "actor_text": "Chính phủ A",
        "recipient_text": "B",
        "evidence_sentence_ids": ["s1", "s2"],
    }]})
    request = ExtractionRequest("doc-1", "A đe dọa B. B đã phản đối.")
    events = extract_events(request, config(), client)
    assert events[0].mention_id == "m1"
    assert events[0].evidence_sentence_ids == ("s1", "s2")
    assert '"id": "s1"' in client.user_prompt
    assert '"id": "s2"' in client.user_prompt


def test_empty_event_list_is_supported():
    assert extract_events(
        ExtractionRequest("d", "Không có sự kiện."),
        config(), FakeClient({"events": []}),
    ) == []


def test_unknown_evidence_id_is_rejected():
    response = {"events": [{
        "actor_text": "A", "recipient_text": "B", "evidence_sentence_ids": ["s9"]
    }]}
    with pytest.raises(ValueError, match="unknown sentence IDs"):
        extract_events(
            ExtractionRequest("d", "A đe dọa B."),
            config(), FakeClient(response),
        )


def test_llm_cannot_add_unexpected_fields():
    response = {"events": [{
        "actor_text": "A", "recipient_text": "B", "evidence_sentence_ids": ["s1"],
        "category": "PROTEST",
    }]}
    with pytest.raises(ValueError, match="fields must be exactly"):
        extract_events(
            ExtractionRequest("d", "A đe dọa B."),
            config(), FakeClient(response),
        )


def test_config_is_loaded_from_json(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({
        "llm": {"model": "custom-model", "temperature": 0.2},
        "category": "COERCE",
        "event_type": "Arrest",
        "system_prompt": "Custom prompt",
        "sentence_split_pattern": "\\n+",
    }), encoding="utf-8")
    loaded = load_config(path)
    assert loaded.llm.model == "custom-model"
    assert loaded.llm.temperature == 0.2
    assert loaded.category == "COERCE"
    assert loaded.event_type == "Arrest"
    assert loaded.sentence_split_pattern == "\\n+"


def test_sentence_split_pattern_is_configurable():
    sentences = split_sentences("d", "One|Two|Three", r"\|")
    assert [sentence.sentence_id for sentence in sentences] == ["s1", "s2", "s3"]


def test_prompt_contains_schema_and_extraction_rules():
    client = FakeClient({"events": []})
    extract_events(ExtractionRequest("doc-1", "A đe dọa B."), config(), client)
    assert "EXTRACTION RULES" in client.user_prompt
    assert "actor_text" in client.user_prompt
    assert "recipient_text" in client.user_prompt
    assert "evidence_sentence_ids" in client.user_prompt
    assert '"mention_id":"m1"' in client.user_prompt
    assert '"category":"configured category"' in client.user_prompt
    assert "TARGET_CATEGORY: THREATEN" in client.user_prompt
    assert "TARGET_EVENT_TYPE: \"Violence\"" in client.user_prompt


def test_config_rejects_mismatched_category_and_event_type(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({
        "llm": {"model": "test"},
        "category": "ASSAULT",
        "event_type": "Arrest",
        "system_prompt": "Extract",
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid event_type"):
        load_config(path)
