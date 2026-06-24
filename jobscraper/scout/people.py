"""Executive lookup (Phase 2) — find decision-maker names for a startup.

Locates likely executives (founder/CEO/CTO/VP R&D/engineering lead) to target.
This step is fragile (LinkedIn is hostile to automation) and may be
semi-manual-assisted: the tool proposes names/roles, the user confirms.

NOTE: scaffolding only. Store minimal personal data; personal use only.
"""

from __future__ import annotations

from jobscraper.store.startup_store import Contact, StartupRecord


def find_executives(record: StartupRecord) -> list[Contact]:
    """Return candidate executive contacts (name + role; email filled later).

    TODO: derive likely execs (public sources / user-assisted LinkedIn search),
    return Contact stubs without emails yet.
    """
    raise NotImplementedError
