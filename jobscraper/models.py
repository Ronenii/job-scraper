"""Normalized data models shared across the pipeline.

Every source adapter converts its raw payload into these types, so the matcher,
notifier, and store never need to know which board a listing came from.

NOTE: scaffolding only — fields are defined, behavior is not implemented.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class JobPosting:
    """A single job/internship listing, normalized across all sources.

    Attributes:
        source: Adapter name that produced this posting (e.g. "greenhouse").
        external_id: Stable id from the source; used with ``source`` for dedup.
        title: Job title as published.
        company: Hiring company name.
        location: Free-text location string (may be Hebrew or English).
        url: Canonical link to the listing.
        description: Full or truncated job description text.
        posted_at: When the listing was posted, if the source exposes it.
        raw: The untouched source payload, kept for debugging adapters.
    """

    source: str
    external_id: str
    title: str
    company: str
    location: str
    url: str
    description: str = ""
    posted_at: datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def dedup_key(self) -> str:
        """Stable key for the SeenStore. TODO: implement (e.g. f\"{source}:{external_id}\")."""
        raise NotImplementedError


@dataclass(frozen=True)
class MatchResult:
    """Outcome of evaluating a JobPosting against the user's filters.

    Attributes:
        posting: The listing that was evaluated.
        is_match: Whether it should be sent to the user.
        score: Confidence in [0, 1].
        reason: Short human-readable explanation (shown in the alert).
        decided_by: "prefilter" or "llm" — which stage produced the verdict.
    """

    posting: JobPosting
    is_match: bool
    score: float
    reason: str
    decided_by: str
