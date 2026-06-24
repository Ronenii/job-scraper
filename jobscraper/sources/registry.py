"""Maps source names from config to adapter classes.

Add a new adapter here to make it usable from config.yaml.
"""
from __future__ import annotations

import logging

from jobscraper.config import AppConfig
from jobscraper.sources.base import JobSource
from jobscraper.sources.greenhouse import GreenhouseSource

log = logging.getLogger(__name__)

SOURCE_REGISTRY: dict[str, type[JobSource]] = {
    "greenhouse": GreenhouseSource,
}


def build_sources(config: AppConfig) -> list[JobSource]:
    sources: list[JobSource] = []
    for sc in config.sources:
        if not sc.enabled:
            continue
        cls = SOURCE_REGISTRY.get(sc.name)
        if cls is None:
            log.warning("unknown source %r in config — skipping", sc.name)
            continue
        sources.append(cls(sc.params))
    return sources
