from jobscraper.config import AppConfig, Filters, LLMConfig
from tests.fakes import FakeLLMClient, FakeSource, make_posting


def test_run_once_matches_new_postings_and_dedups(tmp_path, monkeypatch):
    import jobscraper.run as run

    cfg = AppConfig(
        filters=Filters(titles=["engineer"], locations=[], exclude_keywords=["senior"]),
        sources=[], llm=LLMConfig("gemini", "gemini-2.0-flash"), match_threshold=0.6,
    )
    postings = [
        make_posting(external_id="1", title="Engineer"),          # prefilter accept
        make_posting(external_id="2", title="Senior Engineer"),   # excluded
    ]
    sent = []

    class _FakeNotifier:
        def send_batch(self, results):
            sent.extend(results)

    monkeypatch.setattr(run, "load_config", lambda p: cfg)
    monkeypatch.setattr(run, "build_sources", lambda c: [FakeSource("fake", postings)])
    monkeypatch.setattr(run, "build_llm_client", lambda c: FakeLLMClient())
    monkeypatch.setattr(run, "TelegramNotifier", lambda t, c: _FakeNotifier())
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "fake")

    db = str(tmp_path / "t.db")
    first = run.run_once(config_path="x", dry_run=False, db_path=db)
    assert len(first) == 1
    assert first[0].posting.external_id == "1"

    # Second run: everything already recorded -> no new matches.
    second = run.run_once(config_path="x", dry_run=False, db_path=db)
    assert second == []


def test_run_once_dry_run_does_not_record(tmp_path, monkeypatch):
    import jobscraper.run as run

    cfg = AppConfig(
        filters=Filters(titles=["engineer"], locations=[], exclude_keywords=[]),
        sources=[], llm=LLMConfig("gemini", "gemini-2.0-flash"), match_threshold=0.6,
    )
    monkeypatch.setattr(run, "load_config", lambda p: cfg)
    monkeypatch.setattr(run, "build_sources",
                        lambda c: [FakeSource("fake", [make_posting(title="Engineer")])])
    monkeypatch.setattr(run, "build_llm_client", lambda c: FakeLLMClient())

    db = str(tmp_path / "t.db")
    assert len(run.run_once(config_path="x", dry_run=True, db_path=db)) == 1
    # dry-run didn't record, so it matches again
    assert len(run.run_once(config_path="x", dry_run=True, db_path=db)) == 1
