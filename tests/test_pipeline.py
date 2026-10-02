from pathlib import Path

import pytest

from plover_extraction.config import load_config
from plover_extraction.models import ExtractionRequest
from plover_extraction.ontology import PLOVER_ONTOLOGY
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
    return load_config(Path(__file__).parents[1] / "config.example.yaml")


def test_raw_text_is_split_and_llm_output_is_normalized():
    client = FakeClient({"events": [{
        "actor_text": "Chính phủ A",
        "recipient_text": "B",
        "category": "THREATEN",
        "event_type": "Violence",
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
        "actor_text": "A", "recipient_text": "B", "category": "THREATEN",
        "event_type": "Violence", "evidence_sentence_ids": ["s9"]
    }]}
    with pytest.raises(ValueError, match="unknown sentence IDs"):
        extract_events(
            ExtractionRequest("d", "A đe dọa B."),
            config(), FakeClient(response),
        )


def test_llm_cannot_add_unexpected_fields():
    response = {"events": [{
        "actor_text": "A", "recipient_text": "B", "evidence_sentence_ids": ["s1"],
        "category": "THREATEN", "event_type": "Violence", "extra": True,
    }]}
    with pytest.raises(ValueError, match="fields must be exactly"):
        extract_events(
            ExtractionRequest("d", "A đe dọa B."),
            config(), FakeClient(response),
        )


def test_config_is_loaded_from_yaml(tmp_path):
    path = tmp_path / "config.yaml"
    text = (Path(__file__).parents[1] / "config.example.yaml").read_text(encoding="utf-8")
    path.write_text(
        text.replace("model: gpt-4.1-mini", "model: custom-model")
        .replace("temperature: 0.0", "temperature: 0.2")
        .replace('sentence_split_pattern: "(?<=[.!?])\\\\s+|\\\\n+"', 'sentence_split_pattern: "\\\\n+"'),
        encoding="utf-8",
    )
    loaded = load_config(path)
    assert loaded.llm.model == "custom-model"
    assert loaded.llm.temperature == 0.2
    assert loaded.sentence_split_pattern == "\\n+"
    assert set(loaded.ontology) == {
        "THREATEN", "PROTEST", "MOBILIZE", "COERCE", "ASSAULT", "APOLITICAL"
    }
    assert "Arrest" in loaded.ontology["COERCE"]["event_types"]


def test_sentence_split_pattern_is_configurable():
    sentences = split_sentences("One|Two|Three", r"\|")
    assert [sentence.sentence_id for sentence in sentences] == ["s1", "s2", "s3"]


def test_prompt_contains_schema_and_extraction_rules():
    client = FakeClient({"events": []})
    extract_events(ExtractionRequest("doc-1", "A đe dọa B."), config(), client)
    assert "EXTRACTION RULES" in client.user_prompt
    assert "actor_text" in client.user_prompt
    assert "recipient_text" in client.user_prompt
    assert "evidence_sentence_ids" in client.user_prompt
    assert '"category":"ASSAULT"' in client.user_prompt
    assert '"THREATEN"' in client.user_prompt
    assert '"PROTEST"' in client.user_prompt


def test_pipeline_rejects_mismatched_category_and_event_type():
    response = {"events": [{
        "actor_text": "A", "recipient_text": "B", "category": "ASSAULT",
        "event_type": "Arrest", "evidence_sentence_ids": ["s1"],
    }]}
    with pytest.raises(ValueError, match="Invalid event_type"):
        extract_events(ExtractionRequest("d", "A arrested B."), config(), FakeClient(response))


def test_example_config_describes_every_category_and_event_type():
    loaded = config()
    assert set(loaded.ontology) == set(PLOVER_ONTOLOGY)
    for category, canonical_types in PLOVER_ONTOLOGY.items():
        configured = loaded.ontology[category]
        expected = {value for value in canonical_types if value is not None}
        assert set(configured["event_types"]) == expected
        assert configured["description"].strip()
        assert all(description.strip() for description in configured["event_types"].values())


@pytest.mark.parametrize("event_type", ["natural_disaster", "epidemic"])
def test_apolitical_event_types_are_available_in_config(tmp_path, event_type):
    path = tmp_path / "config.yaml"
    text = (Path(__file__).parents[1] / "config.example.yaml").read_text(encoding="utf-8")
    path.write_text(
        text.replace("category: THREATEN", "category: APOLITICAL")
        .replace("event_type: Violence", f"event_type: {event_type}"),
        encoding="utf-8",
    )
    loaded = load_config(path)
    assert loaded.category == "APOLITICAL"
    assert loaded.event_type == event_type
    assert loaded.ontology["APOLITICAL"]["event_types"][event_type].strip()
