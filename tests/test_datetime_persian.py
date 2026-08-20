import pytest
from datetime import datetime, timezone, timedelta
from yasinpress.core.helpers import format_persian_datetime, _get_timezone, TEHRAN_TZ
from zoneinfo import ZoneInfoNotFoundError


def test_normal_tehran_conversion():
    dt = datetime(2026, 8, 11, 14, 30, tzinfo=timezone.utc)
    out = format_persian_datetime(dt)
    # Jalali equivalent of 2026-08-11 is 1405-05-20
    assert out.startswith("1405/05/20")
    assert out.endswith("18:00")


def test_jalali_conversion_integrity():
    dt = datetime(2024, 3, 19, 10, 0, tzinfo=timezone.utc)
    out = format_persian_datetime(dt)
    assert "/" in out
    assert " - " in out


def test_timezone_fallback():
    tz = _get_timezone(TEHRAN_TZ)
    assert tz.utcoffset(None) == timedelta(hours=3, minutes=30)


def test_caller_provided_timezone():
    dt = datetime(2026, 8, 11, 14, 30, tzinfo=timezone.utc)
    out = format_persian_datetime(dt, "UTC")
    assert out.endswith("14:30")


def test_missing_timezone_database_behavior():
    with pytest.raises(ZoneInfoNotFoundError):
        _get_timezone("Europe/Nowhere")


def test_eitaa_timestamp_integrity():
    dt = datetime(2026, 8, 11, 14, 30, tzinfo=timezone.utc)
    out = format_persian_datetime(dt)
    assert " - " in out
