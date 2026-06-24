# AGENTS.md — Project Guide (Codex / Copilot / cross-runtime)

This is the project instructions file for AI coding agents other than Claude Code.
Claude Code users: see `CLAUDE.md` (same content, plus agent-model pinning).

---

## What this is
A personal-use, Israel-focused **Job Alert Bot** (Phase 1) plus a **Startup Scout**
(Phase 2). Scrapes job sources, fuzzy-matches listings semantically against
title/location filters, pushes new matches to Telegram. Scout finds startups +
executive emails for **manual** outreach only.
Single user. Runs locally (Windows PC — Task Scheduler or Docker).
**Current state: scaffolding only — most functions raise `NotImplementedError`.**

## Architecture map
```
jobscraper/
  models.py          JobPosting, MatchResult (shared normalized types)
  config.py          AppConfig / Filters / SourceConfig / LLMConfig + load_config
  run.py             orchestrator: fetch -> normalize -> dedup -> match -> notify -> persist
  sources/
    base.py          JobSource ABC (the adapter contract)
    greenhouse.py    Tier 1 (structured ATS JSON)
    alljobs.py       Tier 2 (best-effort HTML)
    linkedin.py      Tier 3 (disabled by default)
  matcher/
    matcher.py       two-stage Matcher (free prefilter -> LLM for borderline/cross-language)
    llm_client.py    provider-agnostic LLMClient + build_llm_client factory
  notifier/telegram.py   TelegramNotifier
  store/
    seen_store.py    SeenStore (SQLite dedup)
    startup_store.py StartupStore + StartupRecord/Contact (Phase 2)
  scout/             discovery -> enrich -> people -> email (Phase 2)
```

## Conventions
- **Python 3.10+**, type hints, `from __future__ import annotations`.
- **Normalize at the edge:** adapters convert raw payloads to `JobPosting` immediately.
- **Secrets only from the environment** (`.env`), never from `config.yaml` or code.
- **Graceful degradation:** a failing source is logged and skipped; the run continues.
- **Be polite:** rate-limit, realistic headers, respect robots.txt; prefer Tier-1 feeds.
- **Cost discipline:** prefilter resolves obvious cases for free; only borderline/cross-language titles hit the LLM; cache LLM verdicts per normalized title.
- **Bilingual matching (Hebrew + English):** an English filter must match a relevant Hebrew listing and vice versa. The prefilter must NOT hard-reject across languages — defer to LLM.

## Source tiers
- **Tier 1 — ATS feeds (stable, preferred):** Comeet, Greenhouse, Lever, Ashby. Clean JSON.
- **Tier 2 — HTML scraping (best-effort):** AllJobs, Drushim, JobMaster. Fails gracefully.
- **Tier 3 — Cautious/disabled:** LinkedIn. Ban risk — keep off unless explicitly opted in.

## How to add a source adapter
1. Create `jobscraper/sources/<board>.py` subclassing `JobSource` from `base.py`.
2. Set `name` (unique slug used in dedup keys) and `tier` (1/2/3).
3. Implement `fetch() -> list[JobPosting]`; normalize to `JobPosting` at the edge.
4. Register in `jobscraper/sources/registry.py` → `SOURCE_REGISTRY`.
5. Add to `config.example.yaml` under `sources:`.
6. Add an **offline** test with a fixture under `tests/fixtures/`.

## Testing
- Run: `pytest` (or `py -m pytest` on Windows)
- All tests must be **offline** — no live network. Adapters are tested against saved
  fixtures; the LLM and notifier use fakes.

## Run / debug
- One pass: `py -m jobscraper.run [--dry-run] [--config config.yaml] [--db jobscraper.db]`
- Secrets: copy `.env.example` → `.env`; config: copy `config.example.yaml` → `config.yaml`.
- Schedule: Windows Task Scheduler or `docker compose run --rm bot`.

## Gotchas
- **Scraping is fragile.** Tier-2 sites change markup; keep adapters defensive.
- **LinkedIn (Tier 3)** can ban accounts/IPs — keep disabled.
- **Hebrew text** is common; don't assume ASCII; cross-language matching is the LLM's job.
- **LLM free-tier rate limits** (Gemini): degrade to prefilter-only if quota is exhausted.

## Implementation plan
Full Phase-1 plan: `docs/superpowers/plans/2026-06-24-job-alert-bot.md`
Milestones: M0 Setup → M1 Models/Config → M2 Store → M3 Greenhouse → M4 Matcher →
M5 Telegram → M6 Orchestrator → M7 Live/Schedule → M8 More adapters.
Phase 2 (Startup Scout) gets its own plan once Phase 1 ships.

---

## Workflow: Incremental commits (inlined for runtimes without skill loading)

Work in small, reviewable commits — **one plan task at a time**.

**The loop:**
1. Implement ONE plan task (failing test + implementation = one unit, one commit).
2. **Automatically present a rundown** before every commit:
   - **Task** — which plan task / what was built
   - **Files changed** — path → what changed, one bullet each
   - **Tests** — exact command run and result (must be PASS before committing)
   - **Notes** — deviations, judgment calls (omit if none)
   - **Proposed commit** — the exact message you'll use
3. **STOP and wait.** Do not commit yet.
4. On the user's OK: stage only the listed files, commit, confirm the hash.
5. **Do not proceed** to the next task until the commit is done.

Rules:
- Never batch multiple tasks into one commit.
- Never commit a broken state — tests must pass first.
- Commit style: `feat:`, `fix:`, `test:`, `chore:`, `docs:`, `refactor:` + imperative subject.

---

## Workflow: Implementation tracker (inlined for runtimes without skill loading)

Track progress using the checkboxes in `docs/superpowers/plans/2026-06-24-job-alert-bot.md`.

- Before starting any work: read the plan, report how many tasks are done vs. total,
  what was last completed, what's next.
- Mark `[x]` only when the task is fully done (tests green, committed).
- Mark in-progress work: `- [ ] Task <!-- in progress: done X, blocked on Y -->`
- Update the checkbox **immediately after the commit**, before starting the next task.

---

## Sub-agent lifecycle team

Six specialist agents handle the development lifecycle. The **main session
orchestrates** the sequence — subagents are single-shot and do not self-chain.
Always commit (via the incremental-commits workflow above) before handing off to
the next stage.

```
architect → developer → tester → debugger → reviewer → docs-cleanup → human gate
```

### How to invoke on each runtime

**Claude Code** — agents are defined in `.claude/agents/` and loaded automatically.
Invoke via the Agent tool with `subagent_type: "architect"` etc.

**Codex** — use `spawn_agent` + `wait_agent`:
```
spawn_agent(prompt="<see per-agent prompt below>", label="architect")
wait_agent(label="architect")
```

**GitHub Copilot** — use the `task` tool:
```
task(prompt="<see per-agent prompt below>", agent_type="task")   # developer/tester/debugger/docs-cleanup
task(prompt="<see per-agent prompt below>", agent_type="explore") # architect/reviewer (read-only)
```

### Per-agent prompts and roles

| Agent | Model | Role | Prompt prefix to use |
|-------|-------|------|----------------------|
| **architect** | opus | Read-only: turn a feature/spec into a design + task list | `"You are the architect for the job-scraper project. Read CLAUDE.md and docs/spec.md first. Then: <feature request>. Produce: Goal, Approach, ordered Tasks, Interfaces touched, Tests to add, Risks."` |
| **developer** | sonnet | Implement code per the architect's plan | `"You are the developer for the job-scraper project. Read CLAUDE.md first. Implement the following plan task exactly, following the JobSource/LLMClient contracts and conventions: <task from plan>"` |
| **tester** | sonnet | Write + run offline tests; report pass/fail with real output | `"You are the tester for the job-scraper project. Read CLAUDE.md first. Write and run offline pytest tests for: <what was just implemented>. Save fixtures under tests/fixtures/. Report the exact pytest output."` |
| **debugger** | sonnet | Root-cause failures; fix broken/blocked scrapers | `"You are the debugger for the job-scraper project. Read CLAUDE.md first. Diagnose and fix this failure: <error/test output>. Confirm root cause with evidence before changing code."` |
| **reviewer** | sonnet | Review diff for correctness, security, conventions; report only | `"You are the reviewer for the job-scraper project. Read CLAUDE.md first. Review the current diff for: correctness, contract adherence (JobSource/LLMClient), graceful degradation, secrets safety, offline tests, cost discipline. Report Blockers / Should-fix / Nits only."` |
| **docs-cleanup** | haiku | Sync docs, remove dead code, run linters | `"You are the docs-cleanup agent for the job-scraper project. Read CLAUDE.md first. Sync docs/spec.md, CLAUDE.md, AGENTS.md, README.md, config.example.yaml with the latest code changes. Remove dead code and run pytest to confirm green."` |

### Notes
- **Architect is read-only** — it must not edit files. On Codex/Copilot, remind it in the prompt.
- **Reviewer is report-only** — it must not edit files.
- **Human approval gate** — always review the reviewer's output and the rundown before committing.

---

## Skills (cross-platform)

Skills for this project live in `.claude/skills/` in the repo (Claude Code loads
them automatically). On Codex/Copilot, the workflows are **inlined above** in this
file — follow them directly; no skill loading needed. If you want to load them
natively on Codex/Copilot, copy or symlink the skill directories to
`~/.agents/skills/` manually (don't persist global symlinks across projects).

---

## Guardrails
- Don't commit `.env` or `config.yaml` (git-ignored).
- The Scout never sends email — it only surfaces candidates for manual outreach.
- Keep changes scoped; prefer Tier-1 sources before adding fragile scrapers.
- Run on the home PC (not a cloud host) to preserve the residential IP advantage.
