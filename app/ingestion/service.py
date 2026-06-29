from dataclasses import dataclass
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Document, DocumentChunk, EmbeddingJobRecord
from app.ingestion.chunking import TextChunker


@dataclass(frozen=True)
class IngestDocumentCommand:
    source: str
    title: str
    text: str
    metadata: dict[str, str]


@dataclass(frozen=True)
class IngestDocumentResult:
    document: Document
    created: bool


class DocumentIngestionService:
    def __init__(self, chunker: TextChunker | None = None) -> None:
        self.chunker = chunker or TextChunker()

    def ingest(self, session: Session, command: IngestDocumentCommand) -> IngestDocumentResult:
        normalized_text = command.text.strip()
        content_hash = self._hash_content(normalized_text)

        existing = session.scalar(
            select(Document)
            .options(selectinload(Document.chunks))
            .where(Document.source == command.source, Document.content_hash == content_hash)
        )
        if existing is not None:
            return IngestDocumentResult(document=existing, created=False)

        document = Document(
            source=command.source,
            title=command.title,
            content_hash=content_hash,
            document_metadata=command.metadata,
        )

        chunks = self.chunker.split(normalized_text)
        for chunk in chunks:
            chunk_record = DocumentChunk(
                document=document,
                chunk_index=chunk.index,
                text=chunk.text,
                token_estimate=chunk.token_estimate,
                chunk_metadata={"source": command.source, **command.metadata},
            )
            document.chunks.append(chunk_record)
            document.embedding_jobs.append(
                EmbeddingJobRecord(document=document, chunk=chunk_record, status="pending")
            )

        session.add(document)
        session.commit()
        session.refresh(document)
        return IngestDocumentResult(document=document, created=True)

    @staticmethod
    def _hash_content(text: str) -> str:
        return sha256(text.encode("utf-8")).hexdigest()

