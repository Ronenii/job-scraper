"""Greenhouse adapter — Tier 1 (structured ATS feed).

Many Israeli startups host jobs on Greenhouse, which exposes a public JSON board
per company: https://boards-api.greenhouse.io/v1/boards/{token}/jobs

Configure with ``params={"board_tokens": ["company-a", "company-b"]}``.

NOTE: scaffolding only — endpoint shape is documented, parsing is not implemented.
"""

from __future__ import annotations

from jobscraper.models import JobPosting
from jobscraper.sources.base import JobSource


class GreenhouseSource(JobSource):
    name = "greenhouse"
    tier = 1

    def fetch(self) -> list[JobPosting]:
        """Fetch + normalize Greenhouse listings for each configured board token.

        TODO:
            - for token in self.params["board_tokens"]: GET the board JSON
            - map each job -> JobPosting(source=self.name, external_id=str(job["id"]), ...)
        """
        raise NotImplementedError
