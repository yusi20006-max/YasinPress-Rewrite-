from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import jdatetime
import hashlib
import json

TEHRAN_TZ = "Asia/Tehran"

# Deterministic fallback: Tehran is UTC+3:30 year‑round in fallback mode.
FALLBACK_TEHRAN = timezone(timedelta(hours=3, minutes=30))


def _get_timezone(tz_str: str):
    try:
        return ZoneInfo(tz_str)
    except ZoneInfoNotFoundError:
        if tz_str == TEHRAN_TZ:
            return FALLBACK_TEHRAN
        raise


def format_persian_datetime(dt: datetime, timezone_str: str = TEHRAN_TZ) -> str:
    tz = _get_timezone(timezone_str)
    localized = dt.astimezone(tz)

    jdt = jdatetime.datetime.fromgregorian(
        year=localized.year,
        month=localized.month,
        day=localized.day,
        hour=localized.hour,
        minute=localized.minute,
        second=localized.second,
        tzinfo=tz,
    )

    return jdt.strftime("%Y/%m/%d - %H:%M")


# -------------------------
# 🔥 stable_hash (required by pipeline)
# -------------------------

def stable_hash(value) -> str:
    """
    Stable hashing used across pipeline, dedup, normalization, scheduler, runtime.
    Must remain deterministic across Python versions and environments.
    """
    try:
        normalized = json.dumps(value, sort_keys=True, ensure_ascii=False)
    except TypeError:
        normalized = str(value)

    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
