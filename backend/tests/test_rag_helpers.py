from app.services.retrieval_utils import chunks, tokens


def test_chunks_overlap_and_keep_content():
    text = "x" * 2200
    result = list(chunks(text, chunk_size=1000, overlap=100))
    assert len(result) == 3
    assert result[0][1][-100:] == result[1][1][:100]


def test_tokens_removes_common_words():
    result = tokens("What does Acme offer for hospitals and clinics?")
    assert "acme" in result
    assert "hospitals" in result
    assert "what" not in result
