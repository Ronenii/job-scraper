"""SeenStore — SQLite-backed dedup so we only notify on new listings.

A posting is identified by ``JobPosting.dedup_key`` (source + external id). Once
recorded, the same listing on later runs is skipped. This is what makes runs
idempotent and safe to schedule frequently.
"""

from __future__ import annotations

import sqlite3

from jobscraper.models import JobPosting


class SeenStore:
    def __init__(self, db_path: str = "jobscraper.db") -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS seen ("
            "dedup_key TEXT PRIMARY KEY, "
            "first_seen TEXT NOT NULL DEFAULT (datetime('now')))"
        )
        self._conn.commit()

    def is_new(self, posting: JobPosting) -> bool:
        cur = self._conn.execute("SELECT 1 FROM seen WHERE dedup_key = ?", (posting.dedup_key,))
        return cur.fetchone() is None

    def record(self, posting: JobPosting) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO seen (dedup_key) VALUES (?)", (posting.dedup_key,)
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
