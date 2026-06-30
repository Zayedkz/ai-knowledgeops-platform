from hashlib import sha256
from typing import Protocol


class EmbeddingProvider(Protocol):
    def embed(self, text: str) -> list[float]:
        """Return an embedding vector for a chunk of text."""


class LocalHashEmbeddingProvider:
    """Deterministic local embeddings for tests and offline development."""

    def __init__(self, dimensions: int = 8) -> None:
        if dimensions < 1:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        normalized = text.strip().encode("utf-8")
        digest = sha256(normalized).digest()
        values: list[float] = []

        for index in range(self.dimensions):
            byte = digest[index % len(digest)]
            values.append(round((byte / 127.5) - 1.0, 6))

        return values


def get_embedding_provider(provider_name: str) -> EmbeddingProvider:
    match provider_name:
        case "mock" | "local" | "hash":
            return LocalHashEmbeddingProvider()
        case _:
            raise ValueError(f"unsupported embedding provider: {provider_name}")
