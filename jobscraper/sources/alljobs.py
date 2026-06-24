"""AllJobs adapter — Tier 2 (best-effort HTML scraping).

AllJobs (alljobs.co.il) is a major Israeli consumer board with no public API, so
this adapter parses HTML search-result pages. It MUST fail gracefully: if the
markup changes or the site blocks us, raise/return cleanly so the orchestrator
logs and skips it without aborting the run.

Configure with search params, e.g. ``params={"query": "...", "region": "..."}``.

NOTE: scaffolding only — strategy is documented, scraping is not implemented.
Keep requests polite (rate-limited, realistic headers); respect robots.txt.
"""

from __future__ import annotations

from jobscraper.models import JobPosting
from jobscraper.sources.base import JobSource


class AllJobsSource(JobSource):
    name = "alljobs"
    tier = 2

    def fetch(self) -> list[JobPosting]:
        """Fetch + parse AllJobs search results into JobPosting objects.

        TODO:
            - build the search URL from self.params
            - fetch HTML (httpx); parse listing cards (BeautifulSoup)
            - normalize each card -> JobPosting; handle missing fields defensively
        """
        raise NotImplementedError
