"""Pipeline orchestrator and CLI entry point.

A single run is idempotent:

    fetch (all enabled sources) -> normalize -> dedup (SeenStore)
        -> match (prefilter then LLM) -> notify (Telegram) -> persist

Designed to be invoked on a schedule (Windows Task Scheduler, or a scheduled
Docker run on the home PC). A broken source must never abort the run — it is
logged and skipped (graceful degradation).
"""

from __future__ import annotations

import argparse
import logging
import os

from dotenv import load_dotenv

from jobscraper.config import load_config
from jobscraper.matcher.llm_client import build_llm_client
from jobscraper.matcher.matcher import Matcher
from jobscraper.models import MatchResult
from jobscraper.notifier.telegram import TelegramNotifier
from jobscraper.sources.registry import build_sources
from jobscraper.store.seen_store import SeenStore

log = logging.getLogger("jobscraper")


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def run_once(config_path: str = "config.yaml", dry_run: bool = False,
             db_path: str = "jobscraper.db") -> list[MatchResult]:
    load_dotenv()
    config = load_config(config_path)
    sources = build_sources(config)
    store = SeenStore(db_path)
    matcher = Matcher(config.filters, build_llm_client(config.llm), config.match_threshold)

    notifier: TelegramNotifier | None = None
    if not dry_run:
        notifier = TelegramNotifier(os.environ["TELEGRAM_BOT_TOKEN"], os.environ["TELEGRAM_CHAT_ID"])

    matches: list[MatchResult] = []
    try:
        for source in sources:
            try:
                postings = source.fetch()
            except Exception as exc:
                log.warning("source %s failed: %s", getattr(source, "name", "?"), exc)
                continue
            for posting in postings:
                if not store.is_new(posting):
                    continue
                result = matcher.evaluate(posting)
                if not dry_run:
                    store.record(posting)
                if result.is_match:
                    matches.append(result)
                    log.info("MATCH: %s @ %s (%s)", posting.title, posting.company, result.reason)
    finally:
        store.close()

    if matches and notifier is not None:
        notifier.send_batch(matches)
    log.info("run complete: %d new match(es)", len(matches))
    return matches


def main() -> None:
    setup_logging()
    ap = argparse.ArgumentParser(description="Run one job-scraper pass.")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--db", default="jobscraper.db")
    ap.add_argument("--dry-run", action="store_true", help="match but do not send or record")
    args = ap.parse_args()
    run_once(config_path=args.config, dry_run=args.dry_run, db_path=args.db)


if __name__ == "__main__":
    main()
