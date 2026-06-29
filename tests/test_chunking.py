import pytest

from app.ingestion.chunking import TextChunker


def test_chunker_splits_text_with_overlap() -> None:
    text = " ".join(f"word{i}" for i in range(10))
    chunks = TextChunker(max_words=4, overlap_words=1).split(text)

    assert [chunk.index for chunk in chunks] == [0, 1, 2]
    assert chunks[0].text == "word0 word1 word2 word3"
    assert chunks[1].text == "word3 word4 word5 word6"
    assert chunks[2].text == "word6 word7 word8 word9"


def test_chunker_returns_empty_list_for_blank_text() -> None:
    assert TextChunker().split("   ") == []


def test_chunker_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError, match="overlap_words must be smaller"):
        TextChunker(max_words=10, overlap_words=10)

