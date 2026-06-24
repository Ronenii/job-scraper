from jobscraper.models import MatchResult
from jobscraper.notifier.telegram import TelegramNotifier, format_message
from tests.fakes import make_posting


def _result():
    p = make_posting(title="Engineering Intern", company="Acme",
                     location="Haifa", url="https://x/job/1")
    return MatchResult(p, True, 0.8, "student R&D role", "llm")


def test_format_message_contains_key_fields():
    msg = format_message(_result())
    assert "Engineering Intern" in msg
    assert "Acme" in msg
    assert "Haifa" in msg
    assert "student R&D role" in msg
    assert "https://x/job/1" in msg


def test_send_batch_posts_each(monkeypatch):
    sent = []
    monkeypatch.setattr(
        "jobscraper.notifier.telegram.httpx.post",
        lambda url, json, timeout: _Resp(sent, json),
    )
    TelegramNotifier("TOKEN", "CHAT").send_batch([_result(), _result()])
    assert len(sent) == 2
    assert sent[0]["chat_id"] == "CHAT"


class _Resp:
    def __init__(self, sink, payload):
        sink.append(payload)

    def raise_for_status(self):
        return None
