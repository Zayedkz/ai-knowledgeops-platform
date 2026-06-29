from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentChunk:
    index: int
    text: str
    token_estimate: int


class TextChunker:
    def __init__(self, max_words: int = 250, overlap_words: int = 40) -> None:
        if max_words <= 0:
            raise ValueError("max_words must be positive")
        if overlap_words < 0:
            raise ValueError("overlap_words cannot be negative")
        if overlap_words >= max_words:
            raise ValueError("overlap_words must be smaller than max_words")

        self.max_words = max_words
        self.overlap_words = overlap_words

    def split(self, text: str) -> list[DocumentChunk]:
        words = text.split()
        if not words:
            return []

        chunks: list[DocumentChunk] = []
        start = 0
        while start < len(words):
            end = min(start + self.max_words, len(words))
            chunk_words = words[start:end]
            chunks.append(
                DocumentChunk(
                    index=len(chunks),
                    text=" ".join(chunk_words),
                    token_estimate=self._estimate_tokens(chunk_words),
                )
            )
            if end == len(words):
                break
            start = end - self.overlap_words

        return chunks

    @staticmethod
    def _estimate_tokens(words: list[str]) -> int:
        return max(1, round(len(words) * 1.3))

