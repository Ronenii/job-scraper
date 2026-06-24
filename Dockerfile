# Job-Scraper container image.
# Runs ONE pipeline pass and exits (idempotent) — schedule repeated runs from the
# host (Task Scheduler invoking `docker compose run`) so runs stay independent.
# Run it on the home PC so outbound requests use the residential IP.
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code. config.yaml and .env are mounted at runtime, not baked in (secrets).
COPY jobscraper ./jobscraper

# Default: one pass. Override CMD for --dry-run, etc.
CMD ["python", "-m", "jobscraper.run"]
