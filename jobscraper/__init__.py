"""jobscraper — Israel-focused job-alert bot and startup scout.

Two subsystems share this package:

* **Job Alert Bot** (Phase 1): scrape Israeli job sources, fuzzy-match listings
  against title/location filters, push new matches to Telegram.
* **Startup Scout** (Phase 2): discover startups, summarize them, and locate
  executive emails for *manual* outreach.

See ``docs/spec.md`` for the full design and ``CLAUDE.md`` for contributor guidance.
"""

__version__ = "0.0.0"
