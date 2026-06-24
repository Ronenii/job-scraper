# CLAUDE.md — Contributor & Agent Guide

Guidance for Claude Code (and humans) working in this repo. Read `docs/spec.md`
for the full design; this file is the day-to-day map and conventions.

## What this is
A personal-use, Israel-focused **Job Alert Bot** (Phase 1) plus a **Startup Scout**
(Phase 2). It scrapes job sources, fuzzy-matches listings semantically against
title/location filters, and pushes new matches to Telegram. The Scout later
finds startups + executive emails for **manual** outreach. Single user, runs
locally on a **Windows** PC (via Task Scheduler, or in a Docker container on that
PC). **Current state: scaffolding only — most functions raise
`NotImplementedError`.**

## Architecture map
```
jobscraper/
  models.py          JobPosting, MatchResult (shared normalized types)
  config.py          AppConfig / Filters / SourceConfig / LLMConfig + load_config
  run.py             orchestrator + CLI:  fetch -> normalize -> dedup -> match -> notify -> persist
  sources/
    base.py          JobSource ABC  (the adapter contract)
    greenhouse.py    Tier 1 example (structured ATS JSON)
    alljobs.py       Tier 2 example (best-effort HTML)
    linkedin.py      Tier 3 (disabled by default)
  matcher/
    matcher.py       two-stage Matcher (free prefilter -> LLM for borderline)
    llm_client.py    provider-agnostic LLMClient + build_llm_client factory
  notifier/telegram.py   TelegramNotifier
  store/
    seen_store.py    SeenStore (SQLite dedup -> only notify new listings)
    startup_store.py StartupStore + StartupRecord/Contact (Phase 2)
  scout/             discovery -> enrich -> people -> email (Phase 2)
```

## Conventions
- **Python**, type hints + `from __future__ import annotations`. Dataclasses for
  data; ABCs for pluggable interfaces (`JobSource`, `LLMClient`).
- **Normalize at the edge:** adapters convert raw payloads to `JobPosting`
  immediately. Nothing downstream knows which board a listing came from.
- **Secrets only from the environment** (`.env`), never from `config.yaml` or code.
- **Graceful degradation:** a failing source is logged and skipped; the run
  continues. Never let one broken adapter abort the pipeline.
- **Be polite:** rate-limit, realistic headers, respect robots.txt where
  reasonable, prefer Tier-1 feeds over scraping.
- **Cost discipline:** the prefilter must resolve obvious cases for free; only
  borderline titles hit the LLM; cache LLM verdicts.

## How to add a source adapter (the key recurring task)
1. Create `jobscraper/sources/<board>.py` with a class subclassing `JobSource`.
2. Set `name` (unique, used in dedup keys + logs) and `tier` (1/2/3).
3. Implement `fetch()`:
   - Tier 1: GET the JSON endpoint(s) from `self.params` (e.g. board tokens).
   - Tier 2: fetch HTML with `httpx`, parse with BeautifulSoup; handle missing
     fields defensively.
   - Map each item to `JobPosting(source=self.name, external_id=..., title=...,
     company=..., location=..., url=..., description=..., posted_at=..., raw=...)`.
4. Register it in `config.yaml` under `sources:` with its `params`.
5. Add an **offline** test: save a sample response to `tests/fixtures/<board>.*`
   and assert `fetch()` (with network stubbed) yields the expected postings.

## Testing
- Run: `pytest`
- Adapter tests are **offline** (use fixtures; no live network in CI).
- Matcher: table-driven prefilter cases + a fake `LLMClient` for the LLM stage.
- Store: dedup correctness against a temp SQLite DB.

## Run / debug
- One pass: `py -m jobscraper.run` (add `--dry-run` to skip sending — TODO).
- Scheduling: Windows Task Scheduler, or a scheduled Docker run; runs are
  idempotent. Run it on the home PC either way — that preserves the residential-IP
  advantage (a cloud host would get datacenter IPs blocked).
- Secrets: copy `.env.example` → `.env`; config: copy `config.example.yaml` →
  `config.yaml`.

## Gotchas
- **Scraping is fragile.** Tier-2 sites change markup and may block; expect
  breakage and keep adapters defensive. Use the `debugger` agent when one breaks.
- **LinkedIn (Tier 3)** can ban accounts/IPs — keep disabled unless explicitly
  opted in.
- **Hebrew text** is common in titles/locations; don't assume ASCII. Matching is
  **bilingual** — an English filter must be able to match a Hebrew listing (and
  vice versa). The keyword prefilter can't bridge languages, so it must defer
  cross-language/ambiguous cases to the LLM rather than rejecting them.
- **LLM free-tier rate limits** (Gemini): batch/throttle; degrade to prefilter-only
  if quota is exhausted rather than crashing.

## Development workflow — sub-agent lifecycle
Defined in `.claude/agents/`. The **main session orchestrates** the sequence;
subagents are single-shot and stateless (they do not self-chain). Each returns a
structured result the next stage consumes.

`architect` → `developer` → `tester` → `debugger` → `reviewer` → `docs-cleanup`
→ **human approval gate** (you review before anything ships).

- **architect** — turn a spec/feature into an implementation design + task list (read-only).
- **developer** — implement per the plan, following the `JobSource`/`LLMClient` contracts.
- **tester** — write/run offline tests; report pass/fail with output.
- **debugger** — root-cause failures, including broken/blocked scrapers.
- **reviewer** — correctness/security/convention review; report-only.
- **docs-cleanup** — sync `docs/spec.md` / `CLAUDE.md` / `README.md`, remove dead
  code, run linters/formatters.

All agents should read this file first for domain knowledge.

## Guardrails
- Don't commit `.env` or `config.yaml` (see `.gitignore`).
- The Scout never sends email — it only surfaces candidates for manual outreach.
- Keep changes scoped; prefer Tier-1 sources before adding fragile scrapers.
