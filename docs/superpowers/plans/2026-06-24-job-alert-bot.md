# Job Alert Bot (Phase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a working bot that scrapes Israeli job sources, semantically matches listings against the user's filters, and pushes new matches to Telegram — runnable on a Windows PC.

**Architecture:** A linear, idempotent pipeline — `fetch (sources) → normalize → dedup (SQLite) → match (free prefilter, then LLM for the gray zone) → notify (Telegram) → persist`. Each stage is a small, independently testable unit behind a clear interface; sources and the LLM provider are pluggable. A single run is safe to re-run and safe to schedule.

**Tech Stack:** Python 3.10+, httpx (HTTP), PyYAML (config), python-dotenv (secrets), google-generativeai (default LLM), SQLite (stdlib), pytest. Telegram Bot API for delivery.

## Global Constraints

These apply to **every task** below:

- **Python 3.10+**, type hints, `from __future__ import annotations` at the top of every module.
- **Secrets only from the environment** (`.env` via python-dotenv) — never read secrets from `config.yaml`, never hard-code, never log them.
- **Graceful degradation:** a source that raises must be logged and skipped; it must never abort the run.
- **Bilingual matching (Hebrew + English):** an English filter must be able to match a Hebrew listing and vice versa. The free keyword prefilter must NOT reject across languages — ambiguous/cross-language cases are deferred to the LLM.
- **Cost discipline:** the prefilter resolves only *obvious* cases for free (verbatim title hit = accept; excluded keyword = reject); everything else goes to the LLM. The pipeline dedups **before** matching, so the LLM is called at most once per listing, ever.
- **Offline tests only:** no test makes a live network call. Adapters are tested against saved fixtures; the LLM and notifier are tested via fakes / pure helper functions.
- **Frequent commits:** every task ends with a commit.
- **Run on the home PC** (Task Scheduler or Docker) to keep the residential IP.

## Interfaces Reference (locked — keep names/types identical across tasks)

```python
# jobscraper/models.py
JobPosting(source, external_id, title, company, location, url, description="", posted_at=None, raw={})
JobPosting.dedup_key -> str                      # f"{source}:{external_id}"
MatchResult(posting, is_match, score, reason, decided_by)

# jobscraper/config.py
Filters(titles: list[str], locations: list[str], exclude_keywords: list[str])
SourceConfig(name: str, enabled: bool, params: dict)
LLMConfig(provider: str, model: str)
AppConfig(filters, sources: list[SourceConfig], llm: LLMConfig, match_threshold: float)
load_config(path: str = "config.yaml") -> AppConfig

# jobscraper/sources/base.py
JobSource.name: str ; JobSource.tier: int ; JobSource(params: dict|None) ; fetch() -> list[JobPosting]

# jobscraper/matcher/llm_client.py
LLMClient.judge_match(posting, filters) -> tuple[bool, float, str]   # (is_match_advisory, score, reason)
LLMClient.summarize_startup(text: str) -> str
build_llm_client(config: LLMConfig) -> LLMClient

# jobscraper/matcher/matcher.py
Matcher(filters: Filters, llm: LLMClient, threshold: float = 0.6).evaluate(posting) -> MatchResult

# jobscraper/store/seen_store.py
SeenStore(db_path: str).is_new(posting) -> bool ; .record(posting) -> None ; .close() -> None

# jobscraper/notifier/telegram.py
format_message(result: MatchResult) -> str
TelegramNotifier(bot_token: str, chat_id: str).send(result) -> None ; .send_batch(results) -> None

# jobscraper/sources/registry.py
SOURCE_REGISTRY: dict[str, type[JobSource]] ; build_sources(config: AppConfig) -> list[JobSource]

# jobscraper/run.py
run_once(config_path="config.yaml", dry_run=False, db_path="jobscraper.db") -> list[MatchResult]
main() -> None
```

---

## Milestone 0 — Project setup & green test harness

*Goal: deps installed, pytest configured and green, shared test fakes in place.*

### Task 0.1: Pytest config + verify the placeholder test runs

**Files:**
- Create: `pyproject.toml`
- Test: `tests/test_placeholder.py` (already exists)

- [x] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "jobscraper"
version = "0.0.0"
requires-python = ">=3.10"

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
addopts = "-q"
```

- [x] **Step 2: Install dependencies**

Run: `py -m venv .venv && .venv\Scripts\Activate.ps1 && pip install -r requirements.txt`
Expected: installs httpx, beautifulsoup4, lxml, python-telegram-bot, PyYAML, python-dotenv, google-generativeai, pytest.

- [x] **Step 3: Run the existing placeholder test**

Run: `pytest tests/test_placeholder.py -v`
Expected: PASS (`test_package_imports`).

- [x] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add pyproject with pytest config"
```

### Task 0.2: Shared test fakes

**Files:**
- Create: `tests/fakes.py`

- [x] **Step 1: Write the fakes** (used by later matcher/run tests)

```python
"""Test doubles — no network, deterministic."""
from __future__ import annotations

from jobscraper.config import Filters
from jobscraper.models import JobPosting


class FakeLLMClient:
    """Returns a fixed score; counts calls so caching can be asserted."""

    def __init__(self, score: float = 0.9, reason: str = "looks relevant"):
        self.score = score
        self.reason = reason
        self.calls = 0

    def judge_match(self, posting: JobPosting, filters: Filters) -> tuple[bool, float, str]:
        self.calls += 1
        return (self.score >= 0.5, self.score, self.reason)

    def summarize_startup(self, text: str) -> str:
        return "fake summary"


class FakeSource:
    """A JobSource-shaped object returning canned postings (or raising)."""

    def __init__(self, name: str, postings: list[JobPosting], raises: bool = False):
        self.name = name
        self.tier = 1
        self._postings = postings
        self._raises = raises

    def fetch(self) -> list[JobPosting]:
        if self._raises:
            raise RuntimeError("boom")
        return self._postings


def make_posting(**kw) -> JobPosting:
    base = dict(source="greenhouse", external_id="1", title="Engineer",
                company="Acme", location="Tel Aviv", url="http://x", description="")
    base.update(kw)
    return JobPosting(**base)
```

- [x] **Step 2: Verify it imports**

Run: `python -c "import tests.fakes"`
Expected: no error.

- [x] **Step 3: Commit**

```bash
git add tests/fakes.py
git commit -m "test: add shared fakes (FakeLLMClient, FakeSource, make_posting)"
```

---

## Milestone 1 — Domain models & config loading

*Goal: `JobPosting.dedup_key` works; `load_config` parses `config.yaml` into typed objects.*

### Task 1.1: Implement `JobPosting.dedup_key`

**Files:**
- Modify: `jobscraper/models.py` (the `dedup_key` property)
- Test: `tests/test_models.py`

- [x] **Step 1: Write the failing test**

```python
from jobscraper.models import JobPosting


def test_dedup_key_combines_source_and_id():
    p = JobPosting(source="greenhouse", external_id="42", title="t",
                   company="c", location="l", url="u")
    assert p.dedup_key == "greenhouse:42"
```

- [x] **Step 2: Run it — verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL (`NotImplementedError`).

- [x] **Step 3: Implement** — replace the body of `dedup_key` in `jobscraper/models.py`:

```python
    @property
    def dedup_key(self) -> str:
        """Stable key for the SeenStore: source + external id."""
        return f"{self.source}:{self.external_id}"
```

- [x] **Step 4: Run it — verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add jobscraper/models.py tests/test_models.py
git commit -m "feat: implement JobPosting.dedup_key"
```

### Task 1.2: Implement `load_config`

**Files:**
- Modify: `jobscraper/config.py` (`load_config`)
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `load_config(path) -> AppConfig` consumed by `run_once` (Task 6.1) and `build_sources` (Task 3.3).

- [x] **Step 1: Write the failing test**

```python
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
```

- [x] **Step 2: Run it — verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL (`NotImplementedError`).

- [x] **Step 3: Implement** — replace `load_config` in `jobscraper/config.py` and add the imports at the top:

```python
from pathlib import Path

import yaml


def load_config(path: str = "config.yaml") -> AppConfig:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}

    f = data.get("filters", {}) or {}
    filters = Filters(
        titles=list(f.get("titles", []) or []),
        locations=list(f.get("locations", []) or []),
        exclude_keywords=list(f.get("exclude_keywords", []) or []),
    )

    sources = [
        SourceConfig(
            name=s["name"],
            enabled=bool(s.get("enabled", True)),
            params=dict(s.get("params", {}) or {}),
        )
        for s in (data.get("sources", []) or [])
    ]

    ld = data.get("llm", {}) or {}
    llm = LLMConfig(provider=ld.get("provider", "gemini"), model=ld.get("model", "gemini-2.0-flash"))

    return AppConfig(
        filters=filters,
        sources=sources,
        llm=llm,
        match_threshold=float(data.get("match_threshold", 0.6)),
    )
```

- [x] **Step 4: Run it — verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS.

- [x] **Step 5: Update the example default model** — in `config.example.yaml`, set `model: "gemini-2.0-flash"` (a real Gemini id) so the default works out of the box.

- [x] **Step 6: Commit**

```bash
git add jobscraper/config.py tests/test_config.py config.example.yaml
git commit -m "feat: implement load_config (YAML -> AppConfig)"
```

---

## Milestone 2 — Persistence (dedup)

*Goal: `SeenStore` remembers listings in SQLite so only new ones flow downstream.*

### Task 2.1: Implement `SeenStore`

**Files:**
- Modify: `jobscraper/store/seen_store.py`
- Test: `tests/test_seen_store.py`

**Interfaces:**
- Consumes: `JobPosting.dedup_key` (Task 1.1).
- Produces: `SeenStore(db_path).is_new(posting)`, `.record(posting)`, `.close()` — used by `run_once` (Task 6.1).

- [x] **Step 1: Write the failing test**

```python
from jobscraper.store.seen_store import SeenStore
from tests.fakes import make_posting


def test_is_new_then_record_then_not_new(tmp_path):
    store = SeenStore(str(tmp_path / "t.db"))
    p = make_posting(external_id="100")
    assert store.is_new(p) is True
    store.record(p)
    assert store.is_new(p) is False
    store.close()


def test_record_is_idempotent(tmp_path):
    store = SeenStore(str(tmp_path / "t.db"))
    p = make_posting(external_id="200")
    store.record(p)
    store.record(p)  # must not raise
    assert store.is_new(p) is False
    store.close()
```

- [x] **Step 2: Run it — verify it fails**

Run: `pytest tests/test_seen_store.py -v`
Expected: FAIL (`NotImplementedError`).

- [x] **Step 3: Implement** — replace the body of `jobscraper/store/seen_store.py` (keep the module docstring):

```python
from __future__ import annotations

import sqlite3

from jobscraper.models import JobPosting


class SeenStore:
    def __init__(self, db_path: str = "jobscraper.db") -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS seen ("
            "dedup_key TEXT PRIMARY KEY, "
            "first_seen TEXT NOT NULL DEFAULT (datetime('now')))"
        )
        self._conn.commit()

    def is_new(self, posting: JobPosting) -> bool:
        cur = self._conn.execute("SELECT 1 FROM seen WHERE dedup_key = ?", (posting.dedup_key,))
        return cur.fetchone() is None

    def record(self, posting: JobPosting) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO seen (dedup_key) VALUES (?)", (posting.dedup_key,)
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
```

- [x] **Step 4: Run it — verify it passes**

Run: `pytest tests/test_seen_store.py -v`
Expected: PASS (both tests).

- [x] **Step 5: Commit**

```bash
git add jobscraper/store/seen_store.py tests/test_seen_store.py
git commit -m "feat: implement SQLite-backed SeenStore for dedup"
```

---

## Milestone 3 — First source: Greenhouse (Tier 1)

*Goal: a real ATS adapter that parses the public Greenhouse board JSON into `JobPosting`s, tested fully offline, plus the source registry.*

### Task 3.1: Save a Greenhouse fixture

**Files:**
- Create: `tests/fixtures/greenhouse_board.json`

- [x] **Step 1: Create the fixture** (trimmed shape of the real `boards-api.greenhouse.io` response)

```json
{
  "jobs": [
    {
      "id": 123,
      "title": "Mechanical Engineering Student",
      "absolute_url": "https://boards.greenhouse.io/acme/jobs/123",
      "location": {"name": "Haifa, Israel"},
      "content": "&lt;p&gt;Part-time role for an engineering student.&lt;/p&gt;",
      "updated_at": "2026-06-20T10:00:00-04:00"
    },
    {
      "id": 456,
      "title": "Senior Backend Engineer",
      "absolute_url": "https://boards.greenhouse.io/acme/jobs/456",
      "location": {"name": "Tel Aviv, Israel"},
      "content": "&lt;p&gt;10+ years experience.&lt;/p&gt;",
      "updated_at": "2026-06-19T10:00:00-04:00"
    }
  ]
}
```

- [x] **Step 2: Commit**

```bash
git add tests/fixtures/greenhouse_board.json
git commit -m "test: add Greenhouse board fixture"
```

### Task 3.2: Implement `GreenhouseSource`

**Files:**
- Modify: `jobscraper/sources/greenhouse.py`
- Test: `tests/test_greenhouse.py`

**Interfaces:**
- Produces: `GreenhouseSource(params).fetch() -> list[JobPosting]`; pure `GreenhouseSource.parse_board(data: dict, token: str) -> list[JobPosting]`. Registered in Task 3.3.

- [x] **Step 1: Write the failing tests**

```python
import json
from pathlib import Path

import pytest

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
```

- [x] **Step 2: Run them — verify they fail**

Run: `pytest tests/test_greenhouse.py -v`
Expected: FAIL (`NotImplementedError`).

- [x] **Step 3: Implement** — replace the body of `jobscraper/sources/greenhouse.py` (keep the module docstring):

```python
from __future__ import annotations

import logging

import httpx

from jobscraper.models import JobPosting
from jobscraper.sources.base import JobSource

log = logging.getLogger(__name__)

BOARD_URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"


class GreenhouseSource(JobSource):
    name = "greenhouse"
    tier = 1

    def fetch(self) -> list[JobPosting]:
        postings: list[JobPosting] = []
        for token in self.params.get("board_tokens", []):
            try:
                data = self._get_json(BOARD_URL.format(token=token))
                postings.extend(self.parse_board(data, token))
            except Exception as exc:  # graceful degradation per source
                log.warning("greenhouse board %r failed: %s", token, exc)
        return postings

    def _get_json(self, url: str) -> dict:
        resp = httpx.get(url, timeout=20.0, headers={"User-Agent": "job-scraper/0.1"})
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def parse_board(data: dict, token: str) -> list[JobPosting]:
        out: list[JobPosting] = []
        for job in data.get("jobs", []):
            location = (job.get("location") or {}).get("name", "")
            out.append(
                JobPosting(
                    source="greenhouse",
                    external_id=str(job["id"]),
                    title=job.get("title", ""),
                    company=token,
                    location=location,
                    url=job.get("absolute_url", ""),
                    description=job.get("content", ""),
                    raw=job,
                )
            )
        return out
```

- [x] **Step 4: Run them — verify they pass**

Run: `pytest tests/test_greenhouse.py -v`
Expected: PASS (both tests).

- [x] **Step 5: Commit**

```bash
git add jobscraper/sources/greenhouse.py tests/test_greenhouse.py
git commit -m "feat: implement GreenhouseSource adapter (Tier 1)"
```

### Task 3.3: Source registry

**Files:**
- Create: `jobscraper/sources/registry.py`
- Test: `tests/test_registry.py`

**Interfaces:**
- Consumes: `AppConfig.sources` (Task 1.2), `GreenhouseSource` (Task 3.2).
- Produces: `build_sources(config) -> list[JobSource]`; `SOURCE_REGISTRY` dict (extended in Milestone 8).

- [x] **Step 1: Write the failing test**

```python
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
```

- [x] **Step 2: Run it — verify it fails**

Run: `pytest tests/test_registry.py -v`
Expected: FAIL (`ModuleNotFoundError: jobscraper.sources.registry`).

- [x] **Step 3: Implement** `jobscraper/sources/registry.py`

```python
"""Maps source names from config to adapter classes.

Add a new adapter here to make it usable from config.yaml.
"""
from __future__ import annotations

import logging

from jobscraper.config import AppConfig
from jobscraper.sources.base import JobSource
from jobscraper.sources.greenhouse import GreenhouseSource

log = logging.getLogger(__name__)

SOURCE_REGISTRY: dict[str, type[JobSource]] = {
    "greenhouse": GreenhouseSource,
}


def build_sources(config: AppConfig) -> list[JobSource]:
    sources: list[JobSource] = []
    for sc in config.sources:
        if not sc.enabled:
            continue
        cls = SOURCE_REGISTRY.get(sc.name)
        if cls is None:
            log.warning("unknown source %r in config — skipping", sc.name)
            continue
        sources.append(cls(sc.params))
    return sources
```

- [x] **Step 4: Run it — verify it passes**

Run: `pytest tests/test_registry.py -v`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add jobscraper/sources/registry.py tests/test_registry.py
git commit -m "feat: add source registry + build_sources"
```

---

## Milestone 4 — Matching (prefilter + LLM)

*Goal: the semantic, bilingual matcher. Free prefilter handles obvious accept/reject; the LLM handles the gray zone. Default provider = Gemini, behind a swappable client.*

### Task 4.1: Implement `Matcher` (prefilter + deferral + cache)

**Files:**
- Modify: `jobscraper/matcher/matcher.py`
- Test: `tests/test_matcher.py`

**Interfaces:**
- Consumes: `Filters` (Task 1.2), `LLMClient.judge_match` (stub interface; fake in tests), `MatchResult` / `JobPosting` (Task 1.1).
- Produces: `Matcher(filters, llm, threshold).evaluate(posting) -> MatchResult` — used by `run_once` (Task 6.1).

- [x] **Step 1: Write the failing tests**

```python
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
```

- [x] **Step 2: Run them — verify they fail**

Run: `pytest tests/test_matcher.py -v`
Expected: FAIL (`NotImplementedError`).

- [x] **Step 3: Implement** — replace the `evaluate` body in `jobscraper/matcher/matcher.py` and add a module-level helper + cache init. Full class body:

```python
from __future__ import annotations

from jobscraper.config import Filters
from jobscraper.matcher.llm_client import LLMClient
from jobscraper.models import JobPosting, MatchResult


def _contains(haystack: str, needle: str) -> bool:
    return needle.strip().casefold() in haystack.casefold()


class Matcher:
    def __init__(self, filters: Filters, llm: LLMClient, threshold: float = 0.6) -> None:
        self.filters = filters
        self.llm = llm
        self.threshold = threshold
        self._cache: dict[str, tuple[float, str]] = {}

    def evaluate(self, posting: JobPosting) -> MatchResult:
        text = f"{posting.title}\n{posting.description}"

        # 1. Hard exclude (free): user explicitly listed these.
        for kw in self.filters.exclude_keywords:
            if kw and _contains(text, kw):
                return MatchResult(posting, False, 0.0, f"excluded keyword: {kw}", "prefilter")

        # 2. Obvious accept (free): a filter title appears verbatim in the title.
        for title in self.filters.titles:
            if title and _contains(posting.title, title):
                return MatchResult(posting, True, 1.0, f"title matches '{title}'", "prefilter")

        # 3. Gray zone (semantic + cross-language): defer to the LLM, cached by title.
        key = posting.title.strip().casefold()
        if key in self._cache:
            score, reason = self._cache[key]
        else:
            _, score, reason = self.llm.judge_match(posting, self.filters)
            self._cache[key] = (score, reason)
        return MatchResult(posting, score >= self.threshold, score, reason, "llm")
```

- [x] **Step 4: Run them — verify they pass**

Run: `pytest tests/test_matcher.py -v`
Expected: PASS (all five).

- [x] **Step 5: Commit**

```bash
git add jobscraper/matcher/matcher.py tests/test_matcher.py
git commit -m "feat: implement two-stage Matcher (prefilter + cached LLM deferral)"
```

### Task 4.2: Gemini LLM client (pure helpers tested; API call thin)

**Files:**
- Create: `jobscraper/matcher/gemini_client.py`
- Modify: `jobscraper/matcher/llm_client.py` (`build_llm_client`)
- Test: `tests/test_gemini_client.py`

**Interfaces:**
- Consumes: `Filters`, `JobPosting`, `LLMConfig`.
- Produces: `GeminiClient(LLMClient)`; pure `build_match_prompt(posting, filters) -> str`, `parse_match_response(text) -> tuple[bool, float, str]`; `build_llm_client(config)` returns a `GeminiClient` for `provider == "gemini"`.

- [x] **Step 1: Write the failing tests** (pure helpers only — no API)

```python
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
    import pytest
    with pytest.raises(ValueError):
        build_llm_client(LLMConfig(provider="nope", model="x"))
```

- [x] **Step 2: Run them — verify they fail**

Run: `pytest tests/test_gemini_client.py -v`
Expected: FAIL (`ModuleNotFoundError`).

- [x] **Step 3: Implement** `jobscraper/matcher/gemini_client.py`

```python
"""Gemini implementation of LLMClient. Pure prompt/parse helpers are unit-tested;
the network call is intentionally thin."""
from __future__ import annotations

import json
import os
import re

from jobscraper.config import Filters
from jobscraper.matcher.llm_client import LLMClient
from jobscraper.models import JobPosting


def build_match_prompt(posting: JobPosting, filters: Filters) -> str:
    titles = "\n".join(f"- {t}" for t in filters.titles)
    locations = ", ".join(filters.locations) or "any"
    return (
        "You match job listings for a mechanical engineering student in Israel.\n"
        "Roles she wants (semantic, not exact):\n"
        f"{titles}\n"
        f"Preferred locations: {locations}.\n\n"
        "Listings may be in Hebrew or English — match across languages by meaning.\n\n"
        f"Listing title: {posting.title}\n"
        f"Location: {posting.location}\n"
        f"Description: {posting.description[:1500]}\n\n"
        'Reply with ONLY JSON: {"match": true|false, "score": 0..1, '
        '"reason": "one short sentence"}'
    )


def parse_match_response(text: str) -> tuple[bool, float, str]:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return (False, 0.0, "could not parse model response")
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return (False, 0.0, "invalid JSON from model")
    score = float(data.get("score", 0.0))
    return (bool(data.get("match", score >= 0.5)), score, str(data.get("reason", "")))


class GeminiClient(LLMClient):
    def __init__(self, model: str = "gemini-2.0-flash", api_key: str | None = None) -> None:
        import google.generativeai as genai

        genai.configure(api_key=api_key or os.environ["LLM_API_KEY"])
        self._model = genai.GenerativeModel(model)

    def judge_match(self, posting: JobPosting, filters: Filters) -> tuple[bool, float, str]:
        resp = self._model.generate_content(build_match_prompt(posting, filters))
        return parse_match_response(resp.text)

    def summarize_startup(self, text: str) -> str:
        resp = self._model.generate_content(
            "Summarize what this company does in 2 plain sentences:\n" + text
        )
        return resp.text.strip()
```

- [x] **Step 4: Implement** `build_llm_client` — replace its body in `jobscraper/matcher/llm_client.py`:

```python
def build_llm_client(config: LLMConfig) -> LLMClient:
    if config.provider == "gemini":
        from jobscraper.matcher.gemini_client import GeminiClient

        return GeminiClient(model=config.model)
    raise ValueError(f"unsupported LLM provider: {config.provider!r}")
```

- [x] **Step 5: Run the tests — verify they pass**

Run: `pytest tests/test_gemini_client.py -v`
Expected: PASS (all four). (Note: these import `gemini_client` but only call the pure helpers and the error path, so `google.generativeai` is not invoked.)

- [x] **Step 6: Commit**

```bash
git add jobscraper/matcher/gemini_client.py jobscraper/matcher/llm_client.py tests/test_gemini_client.py
git commit -m "feat: add Gemini LLM client + build_llm_client factory"
```

---

## Milestone 5 — Notification (Telegram)

*Goal: format a match into a readable message and send it via the Telegram Bot API.*

### Task 5.1: Implement `format_message` + `TelegramNotifier`

**Files:**
- Modify: `jobscraper/notifier/telegram.py`
- Test: `tests/test_telegram.py`

**Interfaces:**
- Consumes: `MatchResult` (Task 1.1).
- Produces: `format_message(result) -> str`; `TelegramNotifier(token, chat_id).send(result)`, `.send_batch(results)` — used by `run_once` (Task 6.1).

- [x] **Step 1: Write the failing tests** (pure formatter + injected sender)

```python
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
```

- [x] **Step 2: Run them — verify they fail**

Run: `pytest tests/test_telegram.py -v`
Expected: FAIL (`NotImplementedError`).

- [x] **Step 3: Implement** — replace the body of `jobscraper/notifier/telegram.py` (keep the module docstring):

```python
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
```

- [x] **Step 4: Run them — verify they pass**

Run: `pytest tests/test_telegram.py -v`
Expected: PASS (both).

- [x] **Step 5: Commit**

```bash
git add jobscraper/notifier/telegram.py tests/test_telegram.py
git commit -m "feat: implement Telegram notifier + message formatter"
```

---

## Milestone 6 — Orchestration (wire it together end-to-end)

*Goal: `run.py` runs the whole pipeline once, idempotently, with `--dry-run`, logging, and a CLI.*

### Task 6.1: Implement `run_once` + `main`

**Files:**
- Modify: `jobscraper/run.py`
- Test: `tests/test_run.py`

**Interfaces:**
- Consumes: `load_config` (1.2), `build_sources` (3.3), `build_llm_client` (4.2), `Matcher` (4.1), `SeenStore` (2.1), `TelegramNotifier` (5.1).
- Produces: `run_once(config_path, dry_run, db_path) -> list[MatchResult]`; `main()`.

- [x] **Step 1: Write the failing test** (monkeypatch the heavy pieces; dry-run avoids Telegram)

```python
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
    monkeypatch.setattr(run, "load_config", lambda p: cfg)
    monkeypatch.setattr(run, "build_sources", lambda c: [FakeSource("fake", postings)])
    monkeypatch.setattr(run, "build_llm_client", lambda c: FakeLLMClient())

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
```

- [x] **Step 2: Run it — verify it fails**

Run: `pytest tests/test_run.py -v`
Expected: FAIL (`NotImplementedError`).

- [x] **Step 3: Implement** — replace the body of `jobscraper/run.py` (keep the module docstring):

```python
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
            except Exception as exc:  # one bad source never aborts the run
                log.warning("source %s failed: %s", getattr(source, "name", "?"), exc)
                continue
            for posting in postings:
                if not store.is_new(posting):
                    continue
                result = matcher.evaluate(posting)
                if not dry_run:
                    store.record(posting)  # record all seen -> LLM runs once per listing
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
```

- [x] **Step 4: Run it — verify it passes**

Run: `pytest tests/test_run.py -v`
Expected: PASS (both).

- [x] **Step 5: Run the whole suite**

Run: `pytest`
Expected: all green.

- [x] **Step 6: Commit**

```bash
git add jobscraper/run.py tests/test_run.py
git commit -m "feat: implement run_once pipeline orchestrator + CLI"
```

---

## Milestone 7 — First real end-to-end run & scheduling

*Goal: prove it works against the real world with the user's own bot, then schedule it. (Manual verification — no new tests.)*

### Task 7.1: Live smoke test (dry-run, then real)

**Files:** none (uses real `config.yaml` + `.env`).

- [ ] **Step 1: Create real config + secrets**

```powershell
cp config.example.yaml config.yaml
cp .env.example .env
```
Edit `config.yaml`: set `filters.titles`/`locations` and add real Greenhouse `board_tokens` for Israeli companies your wife cares about (find them at `boards.greenhouse.io/<token>`). Edit `.env`: `LLM_API_KEY` (Gemini), and `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` (see README BotFather steps).

- [ ] **Step 2: Dry run (no send, no record)**

Run: `py -m jobscraper.run --dry-run`
Expected: logs `MATCH: ...` lines for relevant roles; ends with `run complete: N new match(es)`. No Telegram message.

- [ ] **Step 3: Real run**

Run: `py -m jobscraper.run`
Expected: a Telegram message arrives for each match. Re-running immediately yields `0 new match(es)` (dedup works).

- [ ] **Step 4: Commit any config tweaks** (NOT `.env`/`config.yaml` — they're git-ignored)

```bash
git add -A
git commit -m "chore: phase-1 live smoke test complete" --allow-empty
```

### Task 7.2: Schedule it

**Files:** none (OS-level).

- [ ] **Step 1 (Option A — Task Scheduler):** Create a task per the README "Schedule" section: action `…\.venv\Scripts\python.exe -m jobscraper.run`, "Start in" = project dir, trigger repeating every 2–3 hours during the day, uncheck "Start only on AC power".

- [ ] **Step 2 (Option B — Docker, optional):** `docker compose run --rm bot` works; schedule that same command from Task Scheduler. Confirm the SQLite DB persists under `./data` between runs (set `db_path` to `data/jobscraper.db` via `--db` or config wiring).

- [ ] **Step 3: Verify a scheduled run fired** — check Task Scheduler history / that a Telegram message arrived at the scheduled time.

---

## Milestone 8 — Self-Discovering ATS Scout + Israeli Aggregators

> **Supersedes the original M8 "Expand coverage" sketch.** Approved 2026-06-24.
> Full design: `~/.claude/plans/ticklish-leaping-babbage.md`.

*Goal: the bot reaches the employers a candidate actually wants — international
high-tech and funded Israeli startups — **without a hand-maintained company list**.
Those companies post on their careers pages, which are almost always a skin over a
known ATS (Greenhouse/Ashby/Workday/Lever/…) that exposes a **public, no-auth JSON
API** including location + description. The bot **discovers** those companies itself
(Common Crawl CDX + GitHub seed lists → probe → keep Israel jobs → self-populating
registry), then fetches via the ATS APIs. Israeli HTML boards (AllJobs/Indeed/
Drushim/JobMaster) add Hebrew-first SMB coverage the ATS path misses.*

**Architecture — two cadences, one shared registry + dedup store:**
```
DISCOVERY (heavy; weekly, separate CLI: python -m jobscraper.discovery.discover)
  Common Crawl CDX + GitHub seeds -> candidate (ats_type, token) pairs
    -> probe public ATS API -> keep tokens with Israel jobs
    -> upsert into CompanyStore (SQLite registry)            [self-populating]

JOB RUN (light; hourly: python -m jobscraper.run)
  active tokens from CompanyStore -> ATS adapters (greenhouse, ashby, workday)
  + HTML aggregators (alljobs, indeed, drushim, jobmaster)
    -> normalize -> dedup (SeenStore) -> match (prefilter + LLM)
    -> notify (Telegram) -> persist
```
Discovery is **never** run inside the job run (probing thousands of tokens is expensive).

**Decisions (locked):** Discovery = **free** (Common Crawl + seeds, no API keys);
ATS adapters this iteration = **greenhouse (exists) + ashby + workday**; HTML aggregators
= **all four**; Lever = recommended follow-up (8L). Out of reach (documented, not built):
Google/Meta/Amazon/Apple Israel (proprietary in-house ATS).

**Global conventions for every task below:** mirror `GreenhouseSource` — defensive
`fetch()` with per-unit `try/except` logging a warning, plus a pure static `parse_*`
method tested offline against a real fixture; normalize to `JobPosting`; secrets from
`.env`; offline tests only; realistic UA + polite delays; honor robots.txt where
reasonable. **Bilingual Israel regex** (prober + aggregators):
`Israel|Tel Aviv|Haifa|Herzliya|Jerusalem|…|ישראל|תל אביב|חיפה|הרצליה|ירושלים|…`.

### Task 8A: Shared Tier-2 HTTP helper
**Files:** Create `jobscraper/sources/_http.py`; Test `tests/sources/test_http.py`.
- [ ] `get_html(url, *, params=None, delay=1.5, timeout=20.0) -> str` (realistic UA, polite `time.sleep`, `raise_for_status`).
- [ ] Test with httpx stubbed (asserts UA header, returns text). Commit: `feat: add shared Tier-2 HTML fetch helper`.

### Task 8B: Company registry store
**Files:** Create `jobscraper/store/company_store.py`; Test `tests/test_company_store.py`.
- [ ] `CompanyStore(db_path)` over SQLite: table `companies(ats_type, token, name, careers_url, location_sample, has_israel_jobs, first_seen, last_checked, active)`, PK `(ats_type, token)`.
- [ ] Methods: `upsert(record)`, `active_tokens(ats_type) -> list[str]`, `all_active() -> list[CompanyRecord]`, `mark_checked(...)`, `close()`.
- [ ] Offline test (temp DB): upsert idempotency, `active_tokens` filtering. Commit: `feat: add CompanyStore registry (SQLite)`.

### Task 8C: Discovery subsystem (free: Common Crawl + seeds)
**Files:** Create `jobscraper/discovery/{__init__,common_crawl,seeds,prober,discover}.py`, `data/seeds/{greenhouse,ashby,workday}.txt`; Tests under `tests/discovery/`.
- [ ] **8C.1 Common Crawl CDX client** — `common_crawl.enumerate_tokens(ats_type, *, limit)` queries `https://index.commoncrawl.org/CC-MAIN-<latest>-index?url=<pattern>&output=json`; extract tokens per rule (greenhouse: seg after `boards.greenhouse.io/`; ashby: seg after `jobs.ashbyhq.com/`; workday: parse `{tenant}.{wdN}.myworkdayjobs.com/...` → tenant+wd+site). Offline test against a saved CDX JSONL fixture.
- [ ] **8C.2 Seed loader** — `seeds.load(ats_type)` reads bundled `data/seeds/<ats>.txt` (+ optional pinned GitHub dataset with graceful fallback). Ship curated Israeli seeds (snyk, jfrog, lightricks, gongio, riskified, taboola, deel, …). Test: bundled loads; missing → empty, no raise.
- [ ] **8C.3 Prober + Israel filter** — `prober.probe(ats_type, token) -> CompanyRecord|None`: instantiate the ATS adapter for one token, `fetch()`, keep if any location matches the Israel regex; capture `location_sample`. Errors → `None`. Test with stubbed adapter.
- [ ] **8C.4 Orchestrator + CLI** — `discover.run_discovery(db_path, *, ats_types, limit, delay)`: union seeds + CDX candidates, probe (throttled), upsert keepers, `mark_checked` rest; `main()` argparse (`--db`, `--ats`, `--limit`); log summary. Test orchestrator with stubbed enumerate/probe. Commit per sub-task (8C.1–8C.4).

### Task 8D: Wire ATS adapters to the registry
**Files:** Modify `jobscraper/sources/greenhouse.py`, `registry.py`, `run.py`; update `tests/test_registry.py`, `tests/test_run.py`.
- [ ] `GreenhouseSource` reads `params["board_tokens"]` (manual override) **merged with** registry tokens injected by `build_sources`.
- [ ] `build_sources(config, company_store=None)` merges config tokens with `company_store.active_tokens(ats_type)` for each ATS source; aggregators unchanged. `run_once` opens `CompanyStore` and passes it in.
- [ ] Update tests for the registry-injection path (fake store). Commit: `feat: drive ATS adapters from the company registry`.

### Task 8E: Workday adapter (enterprise giants)
**Files:** Create `jobscraper/sources/workday.py`, `tests/fixtures/workday_jobs.json`, `tests/test_workday.py`; register in `SOURCE_REGISTRY`.
- [ ] `WorkdaySource` (Tier 1): `https://{tenant}.{wdN}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs` (POST JSON, `appliedFacets` location). Pure `parse_jobs(json)`.
- [ ] Fixture + offline parse + `fetch()` (stubbed) tests; add CDX pattern + seeds. **Risk:** tenant/URL shape is fiddly — keep parsing defensive; route breakage to the `debugger` agent. Commit per task.

### Task 8E2: Ashby adapter (funded startups — clean JSON)
**Files:** Create `jobscraper/sources/ashby.py`, `tests/fixtures/ashby_board.json`, `tests/test_ashby.py`; register.
- [ ] `AshbySource` (Tier 1): `https://api.ashbyhq.com/posting-api/job-board/{token}` (no auth; location + description). Token = `jobs.ashbyhq.com/{token}` slug. Pure `parse_board(json, token)`.
- [ ] Fixture + offline parse + `fetch()` tests; add CDX pattern (`jobs.ashbyhq.com/*`) + seeds (e.g. `deel`). Reaches Deel + newer startups. Commit per task.

### Task 8F: AllJobs adapter (Hebrew SMB coverage)
**Files:** Rewrite `jobscraper/sources/alljobs.py`; Create `tests/fixtures/alljobs_search.html`, `tests/sources/test_alljobs.py`; register.
- [ ] Capture fixture from `SearchResultsGuest.aspx?freetxt=mechanical&page=1`; read REAL selectors (don't guess class names).
- [ ] Pure `parse_search_html`; `external_id` = `JobID` from `UploadSingle.aspx?JobID=` href; `url` absolute. `fetch()` from `params` (`queries`, `region`, `max_pages`), dedupe within run. Offline tests (incl. missing-field card). Commit per task.

### Task 8G: Indeed IL adapter (throttled)
**Files:** Create `jobscraper/sources/indeed.py`, `tests/fixtures/indeed_search.html`, `tests/sources/test_indeed.py`; register.
- [ ] URL `il.indeed.com/jobs?q=<kw>&l=Israel&start=<n>`. **Heavy throttle (~3s), back off on 403/429** (robots gray-area, user-accepted personal use). Fixture + parse + fetch tests. Commit per task.

### Task 8H: Drushim adapter (best-effort, first-page only)
**Files:** Create `jobscraper/sources/drushim.py`, `tests/fixtures/drushim_search.html`, `tests/sources/test_drushim.py`; register.
- [ ] URL `drushim.co.il/jobs/search/<kw>/`. Parse only the server-rendered first batch; **do NOT** hit robots-disallowed `/api/jobs/search`; no pagination. reCAPTCHA block → log+skip. Note Playwright path as deferred. Fixture + tests. Commit per task.

### Task 8I: JobMaster adapter (page-1 snippets only)
**Files:** Create `jobscraper/sources/jobmaster.py`, `tests/fixtures/jobmaster_search.html`, `tests/sources/test_jobmaster.py`; register.
- [ ] URL `jobmaster.co.il/jobs/?q=<kw>` — page 1 only; respect robots (no `currPage`, no `checknum.asp` detail). Fixture + tests. Commit per task.

### Task 8J: Docs & config sync
- [ ] `config.example.yaml`/`config.yaml`: aggregators with `queries`; ATS sources note registry-driven tokens (+ optional manual `board_tokens`); add a `discovery:` section. Document the weekly `discovery.discover` vs hourly `run` cadence in `CLAUDE.md`/`docs/spec.md`. Run `pytest`; commit `docs: sync source list and discovery cadence`.

### Task 8L: RECOMMENDED follow-up — Lever adapter (low effort, high yield)
*Discovery already surfaces Lever tokens; without the adapter they're dead weight.*
- [ ] `LeverSource`: `https://api.lever.co/v0/postings/{token}?mode=json` (has location). Add CDX pattern (`jobs.lever.co/*`) + seeds (e.g. `mobileye`); register; fixture + offline tests. Reaches Mobileye + many scale-ups. Commit per task.

> LinkedIn (Tier 3) stays disabled (proprietary giants + ban-risk are future, discovery-only work — see roadmap below and the spec risk note).

**Future roadmap (documented, not built):** (1) Serper.dev fresh-token refresh; (2) more
ATS — SmartRecruiters/Workable/Comeet/Recruitee/Teamtailor/Personio; (3) proprietary
giants via bespoke scrapers or LinkedIn discovery-only; (4) preferences/prioritization
(company type, sector, follow/boost specific companies) in `Filters` + matcher;
(5) more Israeli aggregators (Nisha, Gotfriends), Glassdoor via paid service;
(6) Drushim full coverage via Playwright.

---

## Phase 2 — Startup Scout (separate plan, to be written after Phase 1 ships)

Phase 2 is an independent subsystem (per the spec). It will get its own detailed TDD plan once Phase 1 is running, because its design depends on Phase 1's `LLMClient` and on hands-on behavior of the external tools. Milestone roadmap:

- **M9 — Discovery:** `scout/discovery.py` — query Startup Nation Finder by sector/region → `StartupRecord` stubs. Offline fixture test.
- **M10 — Enrich:** `scout/enrich.py` — fill `StartupRecord.summary` via `LLMClient.summarize_startup`. (Reuses Phase-1 LLM client.)
- **M11 — People:** `scout/people.py` — propose executive names/roles (semi-manual-assisted; LinkedIn is hostile).
- **M12 — Email:** `scout/email.py` — Hunter.io find/verify (free tier quota handling) → fill `Contact.email`/`email_confidence`.
- **M13 — Digest + persistence:** `StartupStore` upsert + a reviewable Telegram/file digest of `{startup, summary, contacts}`. **Nothing auto-sent** — manual outreach only.

---

## Self-Review (completed)

- **Spec coverage (Phase 1):** sources/tiers → M3 + M8; semantic+bilingual matching → M4; dedup → M2; Telegram delivery → M5; config schema → M1; orchestration/idempotency → M6; Windows/Docker scheduling → M7; cost discipline (prefilter + dedup-before-match) → M4 + M6. Phase 2 spec sections → M9–M13 roadmap (own plan).
- **Placeholders:** none — every code step shows complete code; the only "repeat per item" block (M8) is a deliberate, fully-specified template with concrete endpoints and a worked reference (M3) to copy.
- **Type consistency:** names/signatures match the Interfaces Reference throughout — `dedup_key`, `judge_match(...) -> (bool, float, str)`, `evaluate -> MatchResult`, `build_sources`, `run_once(config_path, dry_run, db_path)`, `format_message`. `judge_match`'s first tuple element is advisory; `Matcher` decides via `score >= threshold` (documented in Task 4.1).
