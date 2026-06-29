# AI KnowledgeOps Platform

AI KnowledgeOps Platform is a production-style retrieval-augmented generation system for ingesting internal documents, indexing searchable chunks, and answering questions with citations.

The project is intentionally designed like an engineering portfolio piece: clear architecture, local infrastructure, tests, observability hooks, and room for realistic scaling work.

## Problem Statement

Engineering and operations teams often store critical knowledge across PDFs, Markdown files, runbooks, tickets, and internal docs. Search alone does not answer operational questions well, while naive LLM chat over documents tends to lack traceability. This platform demonstrates how to build a reliable RAG service with ingestion, retrieval, citations, evaluation, and production-minded boundaries.

## Architecture

```mermaid
flowchart LR
    User[User or API Client] --> API[FastAPI API]
    API --> RateLimit[Rate Limiting]
    API --> Query[Query Service]
    API --> Ingest[Document Ingestion API]
    Ingest --> Queue[Redis Job Queue]
    Queue --> Worker[Embedding Worker]
    Worker --> Embed[Embedding Provider]
    Worker --> DB[(PostgreSQL + pgvector)]
    Query --> Cache[Redis Cache]
    Query --> DB
    Query --> LLM[LLM Provider]
    Query --> Citations[Citation Formatter]
    API --> OTel[OpenTelemetry Logs and Traces]
```

## Features

- FastAPI backend skeleton with health checks
- Environment-based configuration with safe local defaults
- Document chunking service with unit tests
- Document ingestion persistence with idempotent content hashing
- SQLAlchemy models and Alembic migrations for documents, chunks, and embedding jobs
- Retrieval and answer response contracts
- Docker Compose for PostgreSQL/pgvector and Redis
- GitHub Actions CI for linting and tests
- System design documentation with scaling, reliability, and security notes

## Tech Stack

- Python 3.12
- FastAPI
- Pydantic Settings
- SQLAlchemy
- Alembic
- PostgreSQL with pgvector
- Redis
- pytest
- Ruff
- Docker Compose
- GitHub Actions

## Local Setup

Create an environment file:

```bash
cp .env.example .env
```

Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Start local infrastructure once Docker is installed:

```bash
docker compose up -d
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

## Environment Variables

| Variable | Purpose | Example |
| --- | --- | --- |
| `APP_ENV` | Runtime environment label | `local` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://...` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `LLM_PROVIDER` | LLM provider selector | `mock` |
| `EMBEDDING_PROVIDER` | Embedding provider selector | `mock` |
| `RATE_LIMIT_PER_MINUTE` | API rate limit target | `60` |

## API Examples

```bash
curl http://localhost:8000/health
```

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"What does this platform do?","metadata_filter":{"source":"sample"}}'
```

```bash
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{
    "source": "sample/platform-overview.md",
    "title": "Platform Overview",
    "text": "AI KnowledgeOps indexes internal documents for retrieval.",
    "metadata": {"team": "ai-platform"}
  }'
```

## Database Migrations

Run migrations after PostgreSQL is available:

```bash
alembic upgrade head
```

The test suite uses SQLite to validate ingestion behavior without Docker. PostgreSQL/pgvector integration tests will be added once a Docker-capable or external Postgres environment is available.

## Testing

```bash
pytest
ruff check .
```

## Scaling Considerations

- Split ingestion workers from API replicas.
- Use Redis-backed queues with retries and dead-letter handling.
- Partition document chunks by tenant or corpus for larger deployments.
- Add approximate nearest-neighbor indexes through pgvector once data volume warrants it.
- Cache high-frequency retrieval results with invalidation tied to document versions.

## Reliability Considerations

- Ingestion should be idempotent by document checksum and source ID.
- Failed embedding jobs should retry with exponential backoff.
- Query responses should include citation metadata for auditability.
- Provider failures should degrade to clear errors rather than uncited answers.

## Security Considerations

- No secrets are committed; use `.env` locally and managed secrets in CI or hosting.
- Uploaded documents should be scanned and size-limited before processing.
- Future auth should enforce corpus-level access control before retrieval.
- Logs should avoid storing full prompts or sensitive document content by default.

## Future Improvements

- Database migrations with Alembic
- Real embedding provider implementation
- RAG evaluation runner and sample benchmark set
- Frontend document browser and query UI
- OpenTelemetry exporter configuration
- Integration tests against PostgreSQL and Redis
