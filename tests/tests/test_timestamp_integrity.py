from datetime import datetime, timezone
from yasinpress.core.helpers import format_persian_datetime


def test_timestamp_integrity_basic():
    dt = datetime(2026, 8, 11, 14, 30, tzinfo=timezone.utc)
    out = format_persian_datetime(dt)
    assert " - " in out
    assert len(out.split(" - ")) == 2
