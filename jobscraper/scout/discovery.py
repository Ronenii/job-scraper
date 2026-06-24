"""Startup discovery — Startup Nation Finder adapter (Phase 2).

Searches Startup Nation Finder by sector / stage / region to surface candidate
companies in relevant mechanical-engineering-adjacent fields.

NOTE: scaffolding only — fragile external source; treat results defensively.
"""

from __future__ import annotations

from jobscraper.store.startup_store import StartupRecord


def discover_startups(sector: str, region: str = "Israel") -> list[StartupRecord]:
    """Return candidate startups for a sector/region.

    TODO: query Startup Nation Finder, parse results into StartupRecord stubs
    (name/website/sector only — summary and contacts are filled by later stages).
    """
    raise NotImplementedError
