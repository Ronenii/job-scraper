"""Pipeline orchestrator and CLI entry point.

A single run is idempotent:

    fetch (all enabled sources) -> normalize -> dedup (SeenStore)
        -> match (prefilter then LLM) -> notify (Telegram) -> persist

Designed to be invoked on a schedule (Windows Task Scheduler, or a scheduled
Docker run on the home PC). A broken source must never abort the run — it is
logged and skipped (graceful degradation).

NOTE: scaffolding only — orchestration is described, not implemented.
"""

from __future__ import annotations


def run_once(config_path: str = "config.yaml") -> None:
    """Execute one full pipeline pass.

    TODO:
        1. load_config(config_path)
        2. instantiate enabled sources; fetch() each, catching per-source errors
        3. normalize raw listings -> JobPosting
        4. drop ones already in SeenStore
        5. Matcher.evaluate() each new posting
        6. TelegramNotifier.send() the matches
        7. record all seen postings in SeenStore
    """
    raise NotImplementedError


def main() -> None:
    """CLI entry point. TODO: arg parsing (--config, --dry-run, --once)."""
    raise NotImplementedError


if __name__ == "__main__":
    main()
