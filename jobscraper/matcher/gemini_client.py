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
