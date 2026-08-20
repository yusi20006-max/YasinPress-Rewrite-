from datetime import datetime, timezone, timedelta
from yasinpress.core.helpers import _get_timezone, TEHRAN_TZ


def test_termux_fallback_offset():
    tz = _get_timezone(TEHRAN_TZ)
    assert tz.utcoffset(None) == timedelta(hours=3, minutes=30)
