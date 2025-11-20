import pytest
from unittest.mock import MagicMock, patch
from responses_client import (
    _managed_rag_enabled,
    _build_managed_payload,
    _extract_managed_text_fragment,
    _extract_managed_text,
    _normalize_text,
    _split_chunks,
    _score_chunk,
    _build_prompt,
    generate_rag_answer,
)
from config import (
    MANAGED_RAG_PUBLIC_URL,
    MANAGED_RAG_TOKEN,
    MANAGED_RAG_VERSION_ID,
    YC_ASSISTANT_MODEL_URI,
    YC_FOLDER_ID,
)



def test_managed_rag_enabled():
    # Test when all managed RAG variables are set (by the autouse fixture)
    assert _managed_rag_enabled()

    # Test when MANAGED_RAG_PUBLIC_URL is None
    with patch('responses_client.MANAGED_RAG_PUBLIC_URL', None):
        assert not _managed_rag_enabled()

    # Test when MANAGED_RAG_TOKEN is None
    with patch('responses_client.MANAGED_RAG_TOKEN', None):
        assert not _managed_rag_enabled()

    # Test when MANAGED_RAG_VERSION_ID is None
    with patch('responses_client.MANAGED_RAG_VERSION_ID', None):
        assert not _managed_rag_enabled()

def test_build_managed_payload():
    payload = _build_managed_payload("test query", "test prompt", retrieve_limit=1, n_chunks=2)
    assert payload == {
        "query": "test query",
        "rag_version": "test-version",
        "retrieve_limit": 1,
        "n_chunks_in_context": 2,
        "llm_settings": {
            "model_settings": {"model": "t-tech/T-lite-it-1.0"},
            "system_prompt": "test prompt",
        },
    }

@pytest.mark.parametrize("fragment, expected", [
    ("simple string", "simple string"),
    ({"text": "text value"}, "text value"),
    ({"answer": "answer value"}, "answer value"),
    ({"content": "content value"}, "content value"),
    ({"generation": "generation value"}, "generation value"),
    ({"message": "message value"}, "message value"),
    ({"candidates": [{"text": "candidate text"}]}, "candidate text"),
    ([{"text": "list text"}], "list text"),
    ({}, ""),
    (None, ""),
])
def test_extract_managed_text_fragment(fragment, expected):
    assert _extract_managed_text_fragment(fragment) == expected

def test_extract_managed_text():
    response = {
        "result": {"message": "hello world"},
        "items": [
            {"result": {"text": "item text 1"}},
            {"answer": "item text 2"}
        ]
    }
    assert _extract_managed_text(response) == "hello world"

    response_no_result = {
        "items": [
            {"result": {"text": "item text 1"}}
        ]
    }
    assert _extract_managed_text(response_no_result) == "item text 1"

    response_only_items = {
        "items": [
            {"answer": "item text 2"}
        ]
    }
    assert _extract_managed_text(response_only_items) == "item text 2"

    response_empty = {}
    assert _extract_managed_text(response_empty) == ""

def test_normalize_text():
    assert _normalize_text("  hello\x00world  ") == "hello world"
    assert _normalize_text("multi  space") == "multi space"
    assert _normalize_text("") == ""

def test_split_chunks():
    text = "a" * 1000
    chunks = _split_chunks(text, size=100, overlap=10)
    assert len(chunks) > 1
    assert chunks[0] == "a" * 100
    assert chunks[1] == "a" * 100

def test_score_chunk():
    assert _score_chunk("hello world", "hello beautiful world") == 2
    assert _score_chunk("test", "no match") == 0
    assert _score_chunk("", "any text") == 0

@pytest.mark.asyncio
@patch('responses_client._call_managed_rag')
@patch('responses_client._retrieve_top_chunks')
@patch('responses_client._build_prompt')
@patch('responses_client._call_model')
async def test_generate_rag_answer(
    mock_call_model,
    mock_build_prompt,
    mock_retrieve_top_chunks,
    mock_call_managed_rag
):
    mock_call_managed_rag.return_value = None
    mock_retrieve_top_chunks.return_value = (["chunk1", "chunk2"], ["title1"])
    mock_build_prompt.return_value = "prompt"
    mock_call_model.return_value = "model answer"

    answer, titles = generate_rag_answer("query")
    assert answer == "model answer"
    assert titles == ["title1"]

    mock_call_managed_rag.return_value = "managed answer"
    answer, titles = generate_rag_answer("query")
    assert answer == "managed answer"
    assert titles == []

# Add more tests for other generate_rag_ functions (swot, digest, nvc, po_helper, conflict)
# Similar mocking strategy will apply.
# For _call_managed_rag and _load_kb_cache, you would typically mock httpx and Yandex Cloud SDK.
# _extract_text_from_pdf_bytes would require mocking pypdf.PdfReader.
