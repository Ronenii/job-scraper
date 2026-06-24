from jobscraper.models import JobPosting


def test_dedup_key_combines_source_and_id():
    p = JobPosting(source="greenhouse", external_id="42", title="t",
                   company="c", location="l", url="u")
    assert p.dedup_key == "greenhouse:42"
