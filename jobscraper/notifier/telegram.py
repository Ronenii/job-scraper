"""Telegram notifier.

Sends each matched listing as a message: title, company, location, link, and the
*why it matched* reason from the MatchResult. Uses the Bot API via a token from
the environment (``TELEGRAM_BOT_TOKEN``) to a chat (``TELEGRAM_CHAT_ID``).
"""

from __future__ import annotations

import httpx

from jobscraper.models import MatchResult


def format_message(result: MatchResult) -> str:
    p = result.posting
    return (
        f"🔧 <b>{p.title}</b>\n"
        f"🏢 {p.company}\n"
        f"📍 {p.location}\n"
        f"✅ {result.reason}\n"
        f"{p.url}"
    )


class TelegramNotifier:
    API = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send(self, result: MatchResult) -> None:
        payload = {
            "chat_id": self.chat_id,
            "text": format_message(result),
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
        resp = httpx.post(self.API.format(token=self.bot_token), json=payload, timeout=20.0)
        resp.raise_for_status()

    def send_batch(self, results: list[MatchResult]) -> None:
        for r in results:
            self.send(r)
