# Job-Scraper & Startup-Scout Bot — Design Spec

_Last updated: 2026-06-24_

## 1. Purpose

A personal-use bot that helps a mechanical-engineering student find work in Israel.
It has two subsystems:

1. **Job Alert Bot** (Phase 1) — periodically scrapes Israeli job sources,
   fuzzy-matches listings against configurable title/location filters (semantic,
   not exact-string), and pushes new matches to a **Telegram** chat.
2. **Startup Scout** (Phase 2) — discovers relevant startups, summarizes what
   they do, and locates executive emails so the user can email them directly. It
   is a **research assistant only**: it surfaces candidates; the user sends every
   email herself.

### Why
Student/intern mechanical-engineering roles in Israel are sparse and scattered
across inconsistent titles ("engineering intern", "student – R&D", "מהנדס מכונות
סטודנט"). Manually polling many boards is tedious and easy to let slip. This bot
automates the polling and the fuzzy judgment of "is this relevant?", and pushes
results to a phone via Telegram.

## 2. Non-goals
- Not a multi-user / hosted SaaS product. Single user, run locally.
- Not an automated outreach tool. The Scout never sends email.
- Not a guarantee of total coverage — see the source-tier trade-offs.

## 3. Key decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| Market | Israel (Hebrew + English) | Where the user is job-hunting |
| Delivery | Telegram bot | Free API, trivial setup, rich messages, push to phone |
| Hosting | Local **Windows** PC — Task Scheduler, or Docker on the same PC | Free; residential IP avoids datacenter-IP blocks; missed runs self-heal next run |
| LLM | Cheap, provider-agnostic | Default Gemini Flash (free tier); Claude Haiku / gpt-4o-mini swappable |
| Sources | Tiered & pragmatic | Stability first (ATS feeds), coverage best-effort (boards) |
| Phasing | Jobs first, Scout second | Immediate value; de-risk the harder subsystem |
| Stack | Python | Best scraping ecosystem; python-telegram-bot; SQLite |
| Storage | Local SQLite | Zero-setup, matches local hosting |

## 4. Architecture

### 4.1 Pipeline (Phase 1)
```
fetch (enabled sources) -> normalize -> dedup (SeenStore)
    -> match (prefilter then LLM) -> notify (Telegram) -> persist
```
A single run is **idempotent** and safe to schedule frequently. A broken source
is logged and skipped — it never aborts the run (graceful degradation).

### 4.2 Modules
| Module | Responsibility |
|--------|----------------|
| `jobscraper/models.py` | `JobPosting`, `MatchResult` — normalized types shared across the pipeline |
| `jobscraper/config.py` | Load/validate `config.yaml` + env secrets into `AppConfig` |
| `jobscraper/sources/` | One adapter per board/ATS implementing `JobSource.fetch()` |
| `jobscraper/matcher/` | `Matcher` (prefilter → LLM) + provider-agnostic `LLMClient` |
| `jobscraper/notifier/` | `TelegramNotifier` |
| `jobscraper/store/` | `SeenStore` (dedup), `StartupStore` (Phase 2) |
| `jobscraper/run.py` | Orchestrator + CLI entry point |
| `jobscraper/scout/` | Phase-2 discovery, enrich, people, email |

### 4.3 Source tiers
- **Tier 1 — Structured ATS feeds (primary, stable).** Comeet, Greenhouse, Lever,
  Ashby. Many Israeli startups post here with clean JSON endpoints (e.g.
  `https://boards-api.greenhouse.io/v1/boards/{token}/jobs`). Low maintenance,
  ToS-friendlier. Configured with company/board tokens.
- **Tier 2 — Best-effort HTML scraping.** AllJobs, Drushim, JobMaster. No public
  API; parse search-result HTML. Must **fail gracefully**.
- **Tier 3 — Cautious / disabled by default.** LinkedIn. Aggressive bot-blocking
  and account-ban risk. Provided as a documented option, off unless the user
  opts in and accepts the risk (and only from the residential PC, heavily
  throttled).

Adding a source = one new file in `sources/` subclassing `JobSource`. See
`CLAUDE.md` → "How to add a source adapter".

## 5. Matching pipeline (the semantic core)

Requirement: title matching is **semantic**, not exact-string. A filter of
"mechanical engineering student" should match a listing titled "engineering
intern" when the description fits.

**Bilingual requirement (Hebrew + English).** Many Israeli listings are in Hebrew.
Matching must work **across languages**: a filter written in English (or Hebrew)
should match a relevant listing in the other language. Cross-language semantic
matching is the LLM stage's job — the free prefilter cannot bridge languages on
keywords alone, so it must **not hard-reject** a posting just because its language
differs from the filter; ambiguous/other-language cases are passed to the LLM
rather than dropped. Users may also list filter `titles` in both languages.

Two stages keep LLM cost near zero:
1. **Prefilter (free).** Location check + keyword/exclude check. Resolves clear
   same-language yes/no cases without any LLM call. When language differs (e.g.
   English filter vs. Hebrew title), it defers to the LLM instead of rejecting.
2. **LLM judgment (borderline + cross-language).** Such cases go to
   `LLMClient.judge_match`, which reasons across Hebrew/English and returns
   `{is_match, score in [0,1], reason}`. The `reason` is shown in the Telegram
   alert ("why it matched").

**Cost control:** verdicts are cached per (normalized title, filter-set), so
repeat/re-posted listings never re-bill. `match_threshold` in config controls how
wide the "borderline → ask LLM" band is.

## 6. Data model
- `JobPosting`: `source`, `external_id`, `title`, `company`, `location`, `url`,
  `description`, `posted_at?`, `raw`. `dedup_key = source + external_id`.
- `MatchResult`: `posting`, `is_match`, `score`, `reason`, `decided_by`
  ("prefilter" | "llm").
- Scout: `StartupRecord` (name, website, sector, summary, contacts) and `Contact`
  (name, role, email, email_confidence, linkedin_url).

## 7. Configuration
- **`config.yaml`** (non-secret): `filters` (titles, locations, exclude_keywords),
  `match_threshold`, `llm` (provider, model), `sources` (name, enabled, params).
  See `config.example.yaml`.
- **`.env`** (secrets, never committed): `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`,
  `LLM_API_KEY`, `HUNTER_API_KEY`. See `.env.example`.

## 8. Delivery (Telegram)
Each match is a message with title, company, location, link, and the match
`reason`. Created via @BotFather; the bot sends to a fixed `TELEGRAM_CHAT_ID`.
(An email digest could be added later behind the same notifier interface.)

## 9. Scheduling
Run `py -m jobscraper.run` on a schedule via **Windows Task Scheduler** (a task
that starts `.venv\Scripts\python.exe -m jobscraper.run` every 2–3 hours during
the day; see README for exact steps). Runs are idempotent; an off/asleep PC simply
catches up on the next run.

## 10. Startup Scout (Phase 2)
Pipeline: `discovery` (Startup Nation Finder by sector/region) → `enrich` (LLM
"what they do" summary) → `people` (find executives; fragile, may be
user-assisted) → `email` (Hunter.io find/verify, free tier ~25–50/mo). Output: a
reviewable digest (Telegram or file) of `{startup, summary, contacts}`.
**Nothing is auto-sent** — the user reviews and emails manually.

## 11. Cost & safety
- **Cost:** $0 (LLM free tier) to ~$1–2/month. Prefilter minimizes LLM calls;
  Telegram and local hosting are free; SQLite is local.
- **Politeness:** rate-limit requests, send realistic headers, respect robots.txt
  where reasonable, prefer official feeds (Tier 1).
- **Privacy/legal:** personal use; store minimal personal data; Hunter.io is a
  legitimate enrichment service; outreach is manual and human-initiated.
- **LinkedIn:** treated as opt-in Tier 3 due to ToS and ban risk.

## 12. Testing strategy
- **Offline adapter tests:** save a real sample response under `tests/fixtures/`
  and assert the adapter normalizes it to the expected `JobPosting` list. No live
  network in CI.
- **Matcher tests:** prefilter logic with table-driven cases; LLM stage tested via
  a fake `LLMClient`.
- **Store tests:** dedup correctness against a temp SQLite file.

## 13. Roadmap
1. **Phase 1 — Job Alert Bot:** models, config, SeenStore, one Tier-1 adapter
   (Greenhouse), Matcher (prefilter + one LLM provider), TelegramNotifier,
   orchestrator, scheduling. Then add more Tier-1/Tier-2 adapters.
2. **Phase 2 — Startup Scout:** discovery → enrich → people → email, digest output.

## 14. Development workflow (sub-agent team)
Development uses a lifecycle agent team (in `.claude/agents/`), orchestrated by
the main Claude session — subagents are single-shot and do not self-chain:

`architect` → `developer` → `tester` → `debugger` → `reviewer` → `docs-cleanup`
→ **human approval gate**.

All agents read `CLAUDE.md` for domain knowledge (Israel sources, the
`JobSource` adapter contract, scraping-fragility gotchas).
