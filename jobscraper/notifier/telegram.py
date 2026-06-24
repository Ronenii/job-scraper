"""Telegram notifier.

Sends each matched listing as a message: title, company, location, link, and the
*why it matched* reason from the MatchResult. Uses the Bot API via a token from
the environment (``TELEGRAM_BOT_TOKEN``) to a chat (``TELEGRAM_CHAT_ID``).

NOTE: scaffolding only — message shape is described, sending is not implemented.
"""

from __future__ import annotations

from jobscraper.models import MatchResult


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send(self, result: MatchResult) -> None:
        """Send one matched listing to the configured chat.

        TODO: format a message (title/company/location/link/reason) and POST it
        via the Telegram Bot API; handle rate limits and transient errors.
        """
        raise NotImplementedError

    def send_batch(self, results: list[MatchResult]) -> None:
        """Send several matches (e.g. one run's worth). TODO: iterate + throttle."""
        raise NotImplementedError
