from app.rag.chunking import chunk_text, normalize_text


def test_normalize_text_removes_excess_blank_lines():
    assert normalize_text("a\r\n\r\n\r\nb") == "a\n\nb"


def test_chunk_text_splits_long_content():
    chunks = chunk_text("a" * 1200, max_chars=300, overlap=40)
    assert len(chunks) > 1
    assert all(chunk for chunk in chunks)
