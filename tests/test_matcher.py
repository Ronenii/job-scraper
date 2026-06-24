from jobscraper.config import Filters
from jobscraper.matcher.matcher import Matcher
from tests.fakes import FakeLLMClient, make_posting


def _filters():
    return Filters(titles=["mechanical engineering student"],
                   locations=["Tel Aviv"], exclude_keywords=["senior"])


def test_excluded_keyword_is_hard_reject_without_llm():
    llm = FakeLLMClient(score=1.0)
    m = Matcher(_filters(), llm)
    r = m.evaluate(make_posting(title="Senior Mechanical Engineer"))
    assert r.is_match is False
    assert r.decided_by == "prefilter"
    assert llm.calls == 0


def test_verbatim_title_is_accept_without_llm():
    llm = FakeLLMClient(score=0.0)
    m = Matcher(_filters(), llm)
    r = m.evaluate(make_posting(title="Mechanical Engineering Student - R&D"))
    assert r.is_match is True
    assert r.decided_by == "prefilter"
    assert llm.calls == 0


def test_gray_zone_defers_to_llm_and_uses_threshold():
    llm = FakeLLMClient(score=0.8)
    m = Matcher(_filters(), llm, threshold=0.6)
    r = m.evaluate(make_posting(title="Engineering Intern"))
    assert r.decided_by == "llm"
    assert r.is_match is True            # 0.8 >= 0.6
    assert llm.calls == 1


def test_gray_zone_below_threshold_is_no_match():
    llm = FakeLLMClient(score=0.3)
    m = Matcher(_filters(), llm, threshold=0.6)
    r = m.evaluate(make_posting(title="Marketing Manager"))
    assert r.is_match is False
    assert r.decided_by == "llm"


def test_llm_verdict_is_cached_per_title():
    llm = FakeLLMClient(score=0.8)
    m = Matcher(_filters(), llm)
    m.evaluate(make_posting(external_id="1", title="Engineering Intern"))
    m.evaluate(make_posting(external_id="2", title="Engineering Intern"))
    assert llm.calls == 1               # second evaluation hit the cache
