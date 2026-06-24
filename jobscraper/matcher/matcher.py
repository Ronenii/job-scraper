"""Two-stage matcher: free prefilter, then LLM for borderline cases.

The key product requirement: title matching is **semantic**, not exact-string,
and **bilingual** (Hebrew + English). "engineering intern" should match a filter
of "mechanical engineering student" when the description fits, and an English
filter should match a Hebrew listing (and vice versa). The keyword prefilter
cannot bridge languages, so cross-language/ambiguous cases are deferred to the
LLM rather than rejected.

Cost control: the prefilter resolves most postings for free; the LLM is only
consulted for the ambiguous middle, and its verdicts are cached per
(normalized title, filter-set) so repeat listings cost nothing.
"""

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

        # 2. Obvious accept (free): a filter title appears verbatim in the posting title.
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
