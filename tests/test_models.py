import pytest

from plover_extraction import EventMention
from plover_extraction.ontology import validate_event_type


def test_event_mention_serializes_exact_schema():
    mention = EventMention(
        "doc-1", "Chính phủ A", "B", "THREATEN", "Violence", ("s1", "s3"),
        {"s1": "A đe dọa B.", "s3": "B phản hồi."},
    )
    assert mention.to_dict() == {
        "doc_id": "doc-1",
        "actor_text": "Chính phủ A",
        "recipient_text": "B",
        "category": "THREATEN",
        "event_type": "Violence",
        "evidence_sentence_ids": ["s1", "s3"],
        "evidence": {"s1": "A đe dọa B.", "s3": "B phản hồi."},
    }


def test_category_only_event_is_valid():
    validate_event_type("ASSAULT", None)


def test_event_type_must_belong_to_category():
    with pytest.raises(ValueError, match="Invalid event_type"):
        validate_event_type("ASSAULT", "Arrest")


@pytest.mark.parametrize("field", ["doc_id", "actor_text", "recipient_text"])
def test_required_text_fields(field):
    values = dict(
        doc_id="doc-1", actor_text="A", recipient_text="B",
        category="COERCE", event_type="Arrest", evidence_sentence_ids=("s1",),
        evidence={"s1": "A arrested B."},
    )
    values[field] = " "
    with pytest.raises(ValueError, match=field):
        EventMention(**values)


def test_evidence_ids_must_be_unique():
    with pytest.raises(ValueError, match="duplicates"):
        EventMention(
            "d", "A", "B", "PROTEST", "Demo", ("s1", "s1"),
            {"s1": "A protested B."},
        )
