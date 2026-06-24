"""Test doubles — no network, deterministic."""
from __future__ import annotations

from jobscraper.config import Filters
from jobscraper.models import JobPosting


class FakeLLMClient:
    """Returns a fixed score; counts calls so caching can be asserted."""

    def __init__(self, score: float = 0.9, reason: str = "looks relevant"):
        self.score = score
        self.reason = reason
        self.calls = 0

    def judge_match(self, posting: JobPosting, filters: Filters) -> tuple[bool, float, str]:
        self.calls += 1
        return (self.score >= 0.5, self.score, self.reason)

    def summarize_startup(self, text: str) -> str:
        return "fake summary"


class FakeSource:
    """A JobSource-shaped object returning canned postings (or raising)."""

    def __init__(self, name: str, postings: list[JobPosting], raises: bool = False):
        self.name = name
        self.tier = 1
        self._postings = postings
        self._raises = raises

    def fetch(self) -> list[JobPosting]:
        if self._raises:
            raise RuntimeError("boom")
        return self._postings


def make_posting(**kw) -> JobPosting:
    base = dict(source="greenhouse", external_id="1", title="Engineer",
                company="Acme", location="Tel Aviv", url="http://x", description="")
    base.update(kw)
    return JobPosting(**base)
