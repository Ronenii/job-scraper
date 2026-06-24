import pytest

from jobscraper.config import Filters, LLMConfig
from jobscraper.matcher.gemini_client import build_match_prompt, parse_match_response
from jobscraper.matcher.llm_client import build_llm_client
from tests.fakes import make_posting


def test_prompt_includes_titles_and_bilingual_instruction():
    f = Filters(titles=["mechanical engineering student"], locations=["Haifa"], exclude_keywords=[])
    prompt = build_match_prompt(make_posting(title="מתמחה הנדסה"), f)
    assert "mechanical engineering student" in prompt
    assert "Hebrew" in prompt or "hebrew" in prompt.lower()
    assert "מתמחה הנדסה" in prompt


def test_parse_match_response_extracts_json():
    text = 'Sure!\n{"match": true, "score": 0.82, "reason": "student R&D role"}'
    is_match, score, reason = parse_match_response(text)
    assert is_match is True
    assert score == 0.82
    assert reason == "student R&D role"


def test_parse_match_response_handles_garbage():
    is_match, score, reason = parse_match_response("no json here")
    assert is_match is False
    assert score == 0.0


def test_build_llm_client_rejects_unknown_provider():
    with pytest.raises(ValueError):
        build_llm_client(LLMConfig(provider="nope", model="x"))
