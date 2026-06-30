import argparse

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.embeddings import get_embedding_provider
from app.jobs.embedding_processor import EmbeddingJobProcessor


def main() -> None:
    parser = argparse.ArgumentParser(description="Process pending document embedding jobs.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum pending jobs to process.")
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Attempts before a job is marked failed.",
    )
    args = parser.parse_args()

    settings = get_settings()
    provider = get_embedding_provider(settings.embedding_provider)
    processor = EmbeddingJobProcessor(provider=provider, max_attempts=args.max_attempts)

    with SessionLocal() as session:
        result = processor.process_pending(session=session, limit=args.limit)

    print(
        f"processed={result.processed} "
        f"completed={result.completed} "
        f"failed={result.failed} "
        f"skipped={result.skipped}"
    )


if __name__ == "__main__":
    main()
