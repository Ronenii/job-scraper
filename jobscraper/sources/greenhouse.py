"""Greenhouse adapter — Tier 1 (structured ATS feed).

Many Israeli startups host jobs on Greenhouse, which exposes a public JSON board
per company: https://boards-api.greenhouse.io/v1/boards/{token}/jobs

Configure with ``params={"board_tokens": ["company-a", "company-b"]}``.
"""

from __future__ import annotations

import logging

import httpx

from jobscraper.models import JobPosting
from jobscraper.sources.base import JobSource

log = logging.getLogger(__name__)

BOARD_URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"


class GreenhouseSource(JobSource):
    name = "greenhouse"
    tier = 1

    def fetch(self) -> list[JobPosting]:
        postings: list[JobPosting] = []
        for token in self.params.get("board_tokens", []):
            try:
                data = self._get_json(BOARD_URL.format(token=token))
                postings.extend(self.parse_board(data, token))
            except Exception as exc:
                log.warning("greenhouse board %r failed: %s", token, exc)
        return postings

    def _get_json(self, url: str) -> dict:
        resp = httpx.get(url, timeout=20.0, headers={"User-Agent": "job-scraper/0.1"})
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def parse_board(data: dict, token: str) -> list[JobPosting]:
        out: list[JobPosting] = []
        for job in data.get("jobs", []):
            location = (job.get("location") or {}).get("name", "")
            out.append(
                JobPosting(
                    source="greenhouse",
                    external_id=str(job["id"]),
                    title=job.get("title", ""),
                    company=token,
                    location=location,
                    url=job.get("absolute_url", ""),
                    description=job.get("content", ""),
                    raw=job,
                )
            )
        return out
