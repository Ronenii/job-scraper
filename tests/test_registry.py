from jobscraper.config import AppConfig, Filters, LLMConfig, SourceConfig
from jobscraper.sources.greenhouse import GreenhouseSource
from jobscraper.sources.registry import build_sources


def _cfg(sources):
    return AppConfig(filters=Filters([], [], []), sources=sources,
                     llm=LLMConfig("gemini", "gemini-2.0-flash"), match_threshold=0.6)


def test_build_sources_instantiates_enabled_known_sources():
    cfg = _cfg([
        SourceConfig("greenhouse", True, {"board_tokens": ["acme"]}),
        SourceConfig("greenhouse", False, {}),          # disabled -> skipped
        SourceConfig("does-not-exist", True, {}),        # unknown -> skipped
    ])
    sources = build_sources(cfg)
    assert len(sources) == 1
    assert isinstance(sources[0], GreenhouseSource)
    assert sources[0].params["board_tokens"] == ["acme"]
