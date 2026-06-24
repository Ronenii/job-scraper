"""Provider-agnostic LLM wrapper.

A thin interface so the provider (Gemini Flash free tier by default, Claude Haiku
or gpt-4o-mini as alternatives) can be swapped without touching the matcher or
scout. The API key is read from the environment, never from config.yaml.

NOTE: scaffolding only — interface defined, no provider calls implemented.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from jobscraper.config import Filters, LLMConfig
from jobscraper.models import JobPosting


class LLMClient(ABC):
    """Minimal capability surface the rest of the app depends on."""

    @abstractmethod
    def judge_match(self, posting: JobPosting, filters: Filters) -> tuple[bool, float, str]:
        """Semantic, bilingual match verdict: (is_match, score in [0,1], reason).

        Must reason across Hebrew and English: an English filter can match a
        Hebrew listing and vice versa.

        TODO (per provider): prompt the model with the posting + filters
        (instructing cross-language matching), parse a structured
        {match, score, reason} response.
        """
        raise NotImplementedError

    @abstractmethod
    def summarize_startup(self, text: str) -> str:
        """Return a short plain-language rundown of what a startup does (Scout phase)."""
        raise NotImplementedError


def build_llm_client(config: LLMConfig) -> LLMClient:
    """Factory: return the LLMClient implementation for config.provider."""
    if config.provider == "gemini":
        from jobscraper.matcher.gemini_client import GeminiClient

        return GeminiClient(model=config.model)
    raise ValueError(f"unsupported LLM provider: {config.provider!r}")
