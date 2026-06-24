"""Email finding/verification (Phase 2) — Hunter.io client.

Given a person + company domain, find/verify a likely email address using
Hunter.io (free tier ~25-50 lookups/month). The key is read from the
environment (``HUNTER_API_KEY``). Emails are reviewed and sent manually by the
user — this module never sends mail.

NOTE: scaffolding only — interface defined, no API calls implemented.
"""

from __future__ import annotations

from jobscraper.store.startup_store import Contact


def find_email(contact: Contact, company_domain: str) -> Contact:
    """Populate ``contact.email`` and ``contact.email_confidence`` via Hunter.io.

    TODO: call Hunter.io email-finder with name + domain; fill the fields; handle
    the free-tier quota gracefully (skip + log when exhausted).
    """
    raise NotImplementedError
