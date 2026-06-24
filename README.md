# Job-Scraper & Startup-Scout Bot

A personal bot that helps a mechanical-engineering student find **student jobs and
internships in Israel**. It scrapes job sources, fuzzy-matches listings against
your title/location filters (semantic — "engineering intern" can match "mechanical
engineering student"), and pushes new matches to **Telegram**. A second phase
helps scout startups and find executive emails for you to contact directly.

> **Status:** scaffolding only. The structure, docs, and config templates exist;
> the logic is not implemented yet. See `docs/spec.md` for the design and
> `CLAUDE.md` for the build plan.

## Features (planned)
- 🔎 Scrapes Israeli job sources (ATS feeds first, then major boards).
- 🧠 Semantic title matching via a cheap LLM — no exact-string brittleness, and
  it works **across Hebrew and English** (English filters can match Hebrew listings).
- 📱 Telegram alerts with title, company, location, link, and *why it matched*.
- 🔁 Dedup so you're only pinged about genuinely new listings.
- 🏢 (Phase 2) Startup scout: summaries + executive emails for manual outreach.
- 💸 Designed to cost **$0–2/month** and run on your own PC.

## Requirements
- A **Windows** PC that's on during the day (runs locally — your home IP avoids
  the datacenter-IP blocks that hit cloud scrapers).
- Python 3.10+ (install from python.org; check "Add python.exe to PATH").
- A Telegram account.
- An LLM API key (Google Gemini free tier by default).
- (Phase 2) A Hunter.io account (free tier) for email finding.

## Setup
1. **Install dependencies** (PowerShell)
   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. **Create a Telegram bot**
   - In Telegram, message **@BotFather** → `/newbot` → follow prompts → copy the
     **bot token**.
   - Get your **chat id**: message your new bot once, then open
     `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` and read `chat.id`.
3. **Configure secrets**
   ```bash
   cp .env.example .env      # fill TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, LLM_API_KEY
   ```
4. **Configure filters & sources**
   ```bash
   cp config.example.yaml config.yaml   # edit titles, locations, enabled sources
   ```
   For Tier-1 sources (Greenhouse/Comeet/Lever/Ashby), add the company board
   tokens of startups you care about under `sources[].params`.

## Run
```bash
python -m jobscraper.run        # one pass (once implemented)
```

## Schedule (so it runs automatically)
Use **Windows Task Scheduler**:
1. Open Task Scheduler → **Create Task…**
2. **Triggers** → New → "Daily", then under *Advanced* set **Repeat task every
   2–3 hours** for a duration of "1 day" (e.g. active 08:00–22:00).
3. **Actions** → New → *Start a program*:
   - Program/script: `C:\path\to\job-scraper\.venv\Scripts\python.exe`
   - Arguments: `-m jobscraper.run`
   - Start in: `C:\path\to\job-scraper`
4. (Optional) **Conditions** → uncheck "Start only on AC power" so it runs anytime
   the PC is on.

Runs are idempotent — if the PC is off/asleep, the next run simply catches up.

## Alternative: run in Docker
If you prefer containers, a `Dockerfile` and `docker-compose.yml` are included.
The container runs one pass and exits; schedule repeated runs from the host.
```powershell
docker compose run --rm bot          # one pass
```
Mount your `config.yaml` and `.env` (compose already does this) and keep the
SQLite dedup DB on the `./data` volume so it survives restarts. **Run it on your
home PC** either way — that keeps the residential-IP advantage; a cloud host would
get datacenter IPs blocked by the boards.

## How it works
```
fetch (sources) -> normalize -> dedup -> match (prefilter, then LLM) -> Telegram
```
See `docs/spec.md` for the full architecture, source-tier strategy, and Phase-2
Startup Scout design.

## Privacy & etiquette
Personal use. The bot rate-limits politely and prefers official job feeds. The
Startup Scout **never sends email** — it only surfaces candidates so you can reach
out yourself.
