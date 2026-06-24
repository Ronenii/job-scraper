"""Source adapters.

Each adapter wraps one job board / ATS and implements the ``JobSource`` interface
in ``base.py``. Adding a source = adding one file here that subclasses ``JobSource``.

Tiers (see docs/spec.md):
    Tier 1 — structured ATS feeds (stable JSON): comeet, greenhouse, lever, ashby
    Tier 2 — best-effort HTML scraping (fails gracefully): alljobs, drushim, jobmaster
    Tier 3 — cautious / disabled by default: linkedin

Representative stubs are provided for greenhouse (Tier 1), alljobs (Tier 2), and
linkedin (Tier 3). The remaining adapters follow the same pattern — see CLAUDE.md
"How to add a source adapter".
"""
