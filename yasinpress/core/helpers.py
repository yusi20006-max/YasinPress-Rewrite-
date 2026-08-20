from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import jdatetime

TEHRAN_TZ = "Asia/Tehran"

# Deterministic fallback: Tehran is UTC+3:30 year‑round in fallback mode.
# This is ONLY used when zoneinfo database is missing.
FALLBACK_TEHRAN = timezone(timedelta(hours=3, minutes=30))


def _get_timezone(tz_str: str):
    """
    Resolve timezone safely.
    - Prefer ZoneInfo when available.
    - If ZoneInfoNotFoundError occurs, use deterministic fallback.
    - Caller-provided timezones still raise if missing (tests expect this).
    """
    try:
        return ZoneInfo(tz_str)
    except ZoneInfoNotFoundError:
        if tz_str == TEHRAN_TZ:
            return FALLBACK_TEHRAN
        raise


def format_persian_datetime(dt: datetime, timezone_str: str = TEHRAN_TZ) -> str:
    """
    Convert datetime to Persian Jalali formatted string.
    Preserves existing behavior, including:
    - timezone-aware conversion
    - deterministic fallback when zoneinfo is missing
    - caller-provided timezone support
    """
    tz = _get_timezone(timezone_str)

    # Convert to target timezone
    localized = dt.astimezone(tz)

    # Convert to Jalali
    jdt = jdatetime.datetime.fromgregorian(
        year=localized.year,
        month=localized.month,
        day=localized.day,
        hour=localized.hour,
        minute=localized.minute,
        second=localized.second,
        tzinfo=tz,
    )

    # Preserve existing formatting style
    return jdt.strftime("%Y/%m/%d - %H:%M")
