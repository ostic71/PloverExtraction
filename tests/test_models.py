import pytest

from plover_extraction import EventMention
from plover_extraction.ontology import validate_event_type


def test_event_mention_serializes_exact_schema():
    mention = EventMention(
        "doc-1", "m1", "Chính phủ A", "B", "THREATEN", "Violence", ("s1", "s3")
    )
    assert mention.to_dict() == {
        "doc_id": "doc-1",
        "mention_id": "m1",
        "actor_text": "Chính phủ A",
        "recipient_text": "B",
        "category": "THREATEN",
        "event_type": "Violence",
        "evidence_sentence_ids": ["s1", "s3"],
    }


def test_category_only_event_is_valid():
    validate_event_type("ASSAULT", None)


def test_event_type_must_belong_to_category():
    with pytest.raises(ValueError, match="Invalid event_type"):
        validate_event_type("ASSAULT", "Arrest")


@pytest.mark.parametrize("event_type", ["natural_disaster", "epidemic"])
def test_apolitical_event_type_is_valid(event_type):
    validate_event_type("APOLITICAL", event_type)


def test_apolitical_requires_a_specific_event_type():
    with pytest.raises(ValueError, match="Invalid event_type"):
        validate_event_type("APOLITICAL", None)


@pytest.mark.parametrize("field", ["doc_id", "mention_id", "actor_text", "recipient_text"])
def test_required_text_fields(field):
    values = dict(
        doc_id="doc-1", mention_id="m1", actor_text="A", recipient_text="B",
        category="COERCE", event_type="Arrest", evidence_sentence_ids=("s1",),
    )
    values[field] = " "
    with pytest.raises(ValueError, match=field):
        EventMention(**values)


def test_evidence_ids_must_be_unique():
    with pytest.raises(ValueError, match="duplicates"):
        EventMention("d", "m1", "A", "B", "PROTEST", "Demo", ("s1", "s1"))
