"""Placeholder test so the suite is runnable from day one.

Real tests come with implementation. Adapter tests should be OFFLINE: save a
sample response under tests/fixtures/ and assert the adapter normalizes it to
the expected JobPosting list (no live network in CI). See CLAUDE.md.
"""


def test_package_imports():
    import jobscraper

    assert jobscraper.__version__ is not None
