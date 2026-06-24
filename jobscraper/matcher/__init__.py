"""Matching subsystem: decide whether a JobPosting fits the user's filters.

Two stages keep LLM cost near zero:
    1. cheap, free **prefilter** (keyword + location) discards obvious non-matches
       and accepts obvious matches
    2. only **borderline** cases go to the LLM for a semantic verdict

See ``matcher.py`` and ``llm_client.py``.
"""
