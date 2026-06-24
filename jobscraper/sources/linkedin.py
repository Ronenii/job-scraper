"""LinkedIn adapter — Tier 3 (cautious, DISABLED by default).

LinkedIn aggressively blocks scraping and may ban accounts/IPs. This adapter is
provided as a documented option but should stay disabled in config unless you
accept that risk. Prefer Tier 1 ATS feeds and Tier 2 boards first.

If enabled, run from the residential PC (not a datacenter IP), heavily
rate-limited, and ideally via a logged-out public search only.

NOTE: scaffolding only — intentionally unimplemented. Read the spec's risk note
before building this out.
"""

from __future__ import annotations

from jobscraper.models import JobPosting
from jobscraper.sources.base import JobSource


class LinkedInSource(JobSource):
    name = "linkedin"
    tier = 3

    def fetch(self) -> list[JobPosting]:
        """Disabled by default. TODO: only implement with explicit opt-in + heavy throttling."""
        raise NotImplementedError
