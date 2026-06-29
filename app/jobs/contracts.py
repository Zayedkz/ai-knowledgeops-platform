from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddingJob:
    document_id: str
    chunk_id: str
    text: str

