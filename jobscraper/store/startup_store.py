"""StartupStore — SQLite persistence for the Startup Scout (Phase 2).

Stores discovered startups, their summaries, and located contacts so the scout
doesn't re-research the same company and my wife can track who she's reviewed.

NOTE: scaffolding only — Phase 2 surface, no SQL implemented.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Contact:
    """An executive contact located for outreach (email sent manually by the user)."""

    name: str
    role: str = ""
    email: str = ""
    email_confidence: float = 0.0          # from the email-finder (e.g. Hunter.io)
    linkedin_url: str = ""


@dataclass
class StartupRecord:
    """A scouted startup with summary and contacts."""

    name: str
    website: str = ""
    sector: str = ""
    summary: str = ""                      # LLM rundown of what they do
    contacts: list[Contact] = field(default_factory=list)


class StartupStore:
    def __init__(self, db_path: str = "jobscraper.db") -> None:
        self.db_path = db_path

    def upsert(self, record: StartupRecord) -> None:
        """Persist or update a startup record. TODO: SQL upsert."""
        raise NotImplementedError

    def already_scouted(self, name: str) -> bool:
        """True if we've already researched this startup. TODO: SQL lookup."""
        raise NotImplementedError
