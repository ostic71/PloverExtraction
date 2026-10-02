import uuid

import pytest

from extract import parse_requests


def test_csv_uses_available_ids_and_generates_missing_ids(tmp_path):
    path = tmp_path / "articles.csv"
    path.write_text(
        "doc_id,raw_text\nknown-id,First article.\n,Second article.\n",
        encoding="utf-8",
    )

    requests = list(parse_requests(path, None, None))

    assert requests[0].doc_id == "known-id"
    assert requests[0].raw_text == "First article."
    assert uuid.UUID(requests[1].doc_id)


def test_csv_accepts_article_dataset_columns(tmp_path):
    path = tmp_path / "articles.csv"
    path.write_text(
        "article_id,raw_article\narticle-1,Article body.\n",
        encoding="utf-8",
    )

    request = next(parse_requests(path, None, None))

    assert request.doc_id == "article-1"
    assert request.raw_text == "Article body."


def test_raw_text_uses_explicit_id_or_uuid():
    assert next(parse_requests(None, "Text", "doc-1")).doc_id == "doc-1"
    assert uuid.UUID(next(parse_requests(None, "Text", None)).doc_id)


def test_csv_rejects_doc_id_override(tmp_path):
    path = tmp_path / "articles.csv"
    path.write_text("raw_text\nArticle body.\n", encoding="utf-8")

    with pytest.raises(ValueError, match="cannot override"):
        next(parse_requests(path, None, "doc-1"))
