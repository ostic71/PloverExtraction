"""Turn raw documents into stable, addressable sentences."""

import re

from .models import Sentence


def split_sentences(doc_id: str, raw_text: str, pattern: str) -> list[Sentence]:
    """Split raw text with a configurable regex and assign ``s1``, ``s2``, ... IDs."""
    if not raw_text or not raw_text.strip():
        raise ValueError("raw_text must be a non-empty string")
    try:
        parts = re.split(pattern, raw_text.strip())
    except re.error as error:
        raise ValueError(f"Invalid sentence_split_pattern: {error}") from error
    cleaned = [part.strip() for part in parts if part.strip()]
    return [Sentence(doc_id, f"s{index}", text) for index, text in enumerate(cleaned, 1)]
