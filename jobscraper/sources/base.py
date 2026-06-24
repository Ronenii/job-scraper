"""The JobSource interface that every adapter implements.

Contract:
    * ``fetch()`` returns normalized ``JobPosting`` objects (or raises, which the
      orchestrator catches and logs — one broken source never aborts the run).
    * Adapters are constructed with their ``SourceConfig.params`` (e.g. ATS tokens).
    * Adapters must be polite: respect rate limits and robots.txt where reasonable.

NOTE: scaffolding only — the interface is defined, no adapter logic lives here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from jobscraper.models import JobPosting


class JobSource(ABC):
    """Abstract base for all job-board / ATS adapters."""

    #: Short, unique adapter name used in dedup keys and logs (e.g. "greenhouse").
    name: str = "base"

    #: Source tier, for logging/strategy: 1 = ATS feed, 2 = HTML scrape, 3 = cautious.
    tier: int = 0

    def __init__(self, params: dict | None = None) -> None:
        self.params = params or {}

    @abstractmethod
    def fetch(self) -> list[JobPosting]:
        """Return current listings for this source, normalized to JobPosting.

        TODO (per adapter): call the endpoint / fetch HTML, parse, normalize.
        """
        raise NotImplementedError
