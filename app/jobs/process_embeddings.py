import argparse
from datetime import timedelta

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
    parser.add_argument(
        "--lease-timeout-seconds",
        type=int,
        default=900,
        help="Recover in-progress jobs whose leases are older than this timeout.",
    )
    parser.add_argument(
        "--worker-id",
        default=None,
        help="Optional worker identifier recorded while jobs are leased.",
    )
    args = parser.parse_args()

    settings = get_settings()
    provider = get_embedding_provider(settings.embedding_provider)
    processor = EmbeddingJobProcessor(
        provider=provider,
        max_attempts=args.max_attempts,
        lease_timeout=timedelta(seconds=args.lease_timeout_seconds),
        worker_id=args.worker_id,
    )

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
