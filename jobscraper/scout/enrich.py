"""Startup enrichment — LLM "what they do" rundown (Phase 2).

Given a startup's site/description text, produce a short plain-language summary
so my wife can quickly judge fit before reaching out.

NOTE: scaffolding only — delegates to LLMClient.summarize_startup.
"""

from __future__ import annotations

from jobscraper.matcher.llm_client import LLMClient
from jobscraper.store.startup_store import StartupRecord


def enrich_startup(record: StartupRecord, llm: LLMClient) -> StartupRecord:
    """Fill ``record.summary`` using the LLM.

    TODO: gather source text (website/about), call llm.summarize_startup, return
    an updated record.
    """
    raise NotImplementedError
