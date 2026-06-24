from jobscraper.store.seen_store import SeenStore
from tests.fakes import make_posting


def test_is_new_then_record_then_not_new(tmp_path):
    store = SeenStore(str(tmp_path / "t.db"))
    p = make_posting(external_id="100")
    assert store.is_new(p) is True
    store.record(p)
    assert store.is_new(p) is False
    store.close()


def test_record_is_idempotent(tmp_path):
    store = SeenStore(str(tmp_path / "t.db"))
    p = make_posting(external_id="200")
    store.record(p)
    store.record(p)  # must not raise
    assert store.is_new(p) is False
    store.close()
