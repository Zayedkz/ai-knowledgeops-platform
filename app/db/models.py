from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def new_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("source", "content_hash", name="uq_documents_source_content_hash"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(500))
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    document_metadata: Mapped[dict[str, str]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    embedding_jobs: Mapped[list["EmbeddingJobRecord"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_document_index"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    token_estimate: Mapped[int] = mapped_column(Integer)
    chunk_metadata: Mapped[dict[str, str]] = mapped_column("metadata", JSON, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    document: Mapped[Document] = relationship(back_populates="chunks")
    embedding_job: Mapped["EmbeddingJobRecord"] = relationship(
        back_populates="chunk", cascade="all, delete-orphan", single_parent=True
    )


class EmbeddingJobRecord(Base):
    __tablename__ = "embedding_jobs"
    __table_args__ = (UniqueConstraint("chunk_id", name="uq_embedding_jobs_chunk_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_id: Mapped[str] = mapped_column(ForeignKey("document_chunks.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(50), index=True, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    document: Mapped[Document] = relationship(back_populates="embedding_jobs")
    chunk: Mapped[DocumentChunk] = relationship(back_populates="embedding_job")


class QueryEvent(Base):
    __tablename__ = "query_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    question: Mapped[str] = mapped_column(Text)
    metadata_filter: Mapped[dict[str, str] | None] = mapped_column(JSON, nullable=True)
    selected_chunk_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    citation_scores: Mapped[list[dict[str, float | str]]] = mapped_column(JSON, default=list)
    latency_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
