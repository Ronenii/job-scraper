import json
from pathlib import Path

from jobscraper.sources.greenhouse import GreenhouseSource

FIXTURE = json.loads(Path("tests/fixtures/greenhouse_board.json").read_text(encoding="utf-8"))


def test_parse_board_normalizes_jobs():
    postings = GreenhouseSource.parse_board(FIXTURE, token="acme")
    assert len(postings) == 2
    first = postings[0]
    assert first.source == "greenhouse"
    assert first.external_id == "123"
    assert first.title == "Mechanical Engineering Student"
    assert first.company == "acme"
    assert first.location == "Haifa, Israel"
    assert first.url == "https://boards.greenhouse.io/acme/jobs/123"
    assert first.dedup_key == "greenhouse:123"


def test_fetch_aggregates_tokens_and_skips_failures(monkeypatch):
    src = GreenhouseSource({"board_tokens": ["acme", "broken"]})

    def fake_get_json(self, url):
        if "broken" in url:
            raise RuntimeError("HTTP 500")
        return FIXTURE

    monkeypatch.setattr(GreenhouseSource, "_get_json", fake_get_json)
    postings = src.fetch()
    # "broken" raises and is skipped; "acme" yields 2
    assert len(postings) == 2
