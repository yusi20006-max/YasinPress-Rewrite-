import hashlib
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import jdatetime

TEHRAN_TZ = "Asia/Tehran"

FALLBACK_TEHRAN = timezone(timedelta(hours=3, minutes=30))


def _get_timezone(tz_str: str):
    try:
        tz = ZoneInfo(tz_str)
        if tz_str == TEHRAN_TZ and tz.utcoffset(None) is None:
            return FALLBACK_TEHRAN
        return tz
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


def stable_hash(value) -> str:
    try:
        normalized = json.dumps(value, sort_keys=True, ensure_ascii=False)
    except TypeError:
        normalized = str(value)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


PERSIAN_MONTHS = [
    "فروردین",
    "اردیبهشت",
    "خرداد",
    "تیر",
    "مرداد",
    "شهریور",
    "مهر",
    "آبان",
    "آذر",
    "دی",
    "بهمن",
    "اسفند",
]


# تبدیل اعداد انگلیسی به فارسی
def to_persian_digits(s: str) -> str:
    english = "0123456789"
    persian = "۰۱۲۳۴۵۶۷۸۹"
    table = str.maketrans(english, persian)
    return s.translate(table)


def format_persian_pretty(dt: datetime, timezone_str: str = TEHRAN_TZ) -> str:
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

    year = str(jdt.year)
    month_name = PERSIAN_MONTHS[jdt.month - 1]
    day = str(jdt.day)
    time_str = f"{jdt.hour:02d}:{jdt.minute:02d}"

    pretty = f"{day} {month_name} {year}، {time_str}"
    return to_persian_digits(pretty)
