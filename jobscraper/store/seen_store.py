"""SeenStore — SQLite-backed dedup so we only notify on new listings.

A posting is identified by ``JobPosting.dedup_key`` (source + external id). Once
recorded, the same listing on later runs is skipped. This is what makes runs
idempotent and safe to schedule frequently.

NOTE: scaffolding only — interface defined, no SQL implemented.
"""

from __future__ import annotations

from jobscraper.models import JobPosting


class SeenStore:
    def __init__(self, db_path: str = "jobscraper.db") -> None:
        self.db_path = db_path

    def is_new(self, posting: JobPosting) -> bool:
        """True if this posting has not been recorded before. TODO: SQL lookup."""
        raise NotImplementedError

    def record(self, posting: JobPosting) -> None:
        """Persist a posting's dedup key (+ timestamp). TODO: upsert."""
        raise NotImplementedError
