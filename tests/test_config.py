from jobscraper.config import load_config


def test_load_config_parses_filters_sources_llm(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        """
filters:
  titles: ["mechanical engineering student", "מהנדס מכונות סטודנט"]
  locations: ["Tel Aviv"]
  exclude_keywords: ["senior"]
match_threshold: 0.7
llm:
  provider: gemini
  model: gemini-2.0-flash
sources:
  - name: greenhouse
    enabled: true
    params:
      board_tokens: ["acme"]
  - name: linkedin
    enabled: false
    params: {}
""",
        encoding="utf-8",
    )
    c = load_config(str(cfg))
    assert c.filters.titles == ["mechanical engineering student", "מהנדס מכונות סטודנט"]
    assert c.filters.exclude_keywords == ["senior"]
    assert c.match_threshold == 0.7
    assert c.llm.provider == "gemini"
    assert [s.name for s in c.sources] == ["greenhouse", "linkedin"]
    assert c.sources[0].params["board_tokens"] == ["acme"]
    assert c.sources[1].enabled is False
