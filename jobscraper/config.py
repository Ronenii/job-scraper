"""Configuration loading.

Reads non-secret settings from ``config.yaml`` (filters, enabled sources, schedule,
match threshold, LLM provider) and secrets from environment variables / ``.env``.

See ``config.example.yaml`` and ``.env.example`` for the full schema.

NOTE: scaffolding only — shapes are defined, loading is not implemented.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Filters:
    """User search filters. Title matching is semantic, not exact-string."""

    titles: list[str] = field(default_factory=list)        # e.g. ["mechanical engineering student", "engineering intern"]
    locations: list[str] = field(default_factory=list)     # e.g. ["Haifa", "Tel Aviv", "remote"]
    exclude_keywords: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SourceConfig:
    """One enabled source and its parameters (e.g. ATS company tokens)."""

    name: str
    enabled: bool = True
    params: dict = field(default_factory=dict)             # e.g. {"board_tokens": ["acme", "globex"]}


@dataclass(frozen=True)
class LLMConfig:
    """Provider-agnostic LLM settings. Default: Gemini Flash free tier."""

    provider: str = "gemini"                               # "gemini" | "anthropic" | "openai"
    model: str = "gemini-flash"
    # API key comes from the environment, never from config.yaml.


@dataclass(frozen=True)
class AppConfig:
    """Top-level resolved configuration for a single run."""

    filters: Filters
    sources: list[SourceConfig]
    llm: LLMConfig
    match_threshold: float = 0.6                           # borderline -> ask the LLM


def load_config(path: str = "config.yaml") -> AppConfig:
    """Load configuration from YAML into typed AppConfig."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}

    f = data.get("filters", {}) or {}
    filters = Filters(
        titles=list(f.get("titles", []) or []),
        locations=list(f.get("locations", []) or []),
        exclude_keywords=list(f.get("exclude_keywords", []) or []),
    )

    sources = [
        SourceConfig(
            name=s["name"],
            enabled=bool(s.get("enabled", True)),
            params=dict(s.get("params", {}) or {}),
        )
        for s in (data.get("sources", []) or [])
    ]

    ld = data.get("llm", {}) or {}
    llm = LLMConfig(provider=ld.get("provider", "gemini"), model=ld.get("model", "gemini-2.0-flash"))

    return AppConfig(
        filters=filters,
        sources=sources,
        llm=llm,
        match_threshold=float(data.get("match_threshold", 0.6)),
    )
