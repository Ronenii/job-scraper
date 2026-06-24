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

NOTE: scaffolding only — the two-stage flow is described, not implemented.
"""

from __future__ import annotations

from jobscraper.config import Filters
from jobscraper.matcher.llm_client import LLMClient
from jobscraper.models import JobPosting, MatchResult


class Matcher:
    def __init__(self, filters: Filters, llm: LLMClient, threshold: float = 0.6) -> None:
        self.filters = filters
        self.llm = llm
        self.threshold = threshold

    def evaluate(self, posting: JobPosting) -> MatchResult:
        """Return a MatchResult for one posting.

        TODO:
            1. prefilter: location check + keyword/exclude check -> clear yes/no
               for SAME-language cases; defer cross-language/ambiguous to the LLM
            2. if borderline, call self.llm.judge_match(posting, self.filters)
            3. cache LLM verdicts by (normalized title, filters)
        """
        raise NotImplementedError
