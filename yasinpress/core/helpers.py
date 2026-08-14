"""General helper functions."""

from datetime import datetime
from hashlib import sha256
from re import sub


def format_persian_datetime(dt: datetime, timezone_str: str = "Asia/Tehran") -> str:
    """Convert timezone-aware datetime to configured timezone and format in Jalali calendar."""
    from zoneinfo import ZoneInfo
    try:
        local_dt = dt.astimezone(ZoneInfo(timezone_str))
    except Exception:
        local_dt = dt.astimezone(ZoneInfo("Asia/Tehran"))

    year = local_dt.year
    month = local_dt.month
    day = local_dt.day

    # Gregorian to Jalali algorithm
    d_4 = year % 4
    g_a = [0, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    doy_g = g_a[month] + day
    if d_4 == 0 and month > 2:
        doy_g += 1
    d_33 = int(((year - 16) % 132) * 0.0305)
    a = 286 if (d_33 == 3 or d_33 < (d_4 - 1) or d_4 == 0) else 287
    if (d_33 == 1 or d_33 == 2) and (d_33 == d_4 or d_4 == 1):
        b = 78
    else:
        b = 80 if (d_33 == 3 and d_4 == 0) else 79
    if int((year - 10) / 63) == 30:
        a -= 1
        b += 1
    if doy_g > b:
        jy = year - 621
        doy_j = doy_g - b
    else:
        jy = year - 622
        doy_j = doy_g + a
    if doy_j < 187:
        jm = int((doy_j - 1) / 31)
        jd = doy_j - (31 * jm)
        jm += 1
    else:
        jm = int((doy_j - 187) / 30)
        jd = doy_j - 186 - (jm * 30)
        jm += 7

    months = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
    ]
    month_name = months[jm - 1]

    hour_str = f"{local_dt.hour:02d}"
    minute_str = f"{local_dt.minute:02d}"

    persian_digits = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    jy_p = str(jy).translate(persian_digits)
    jd_p = str(jd).translate(persian_digits)
    time_p = f"{hour_str}:{minute_str}".translate(persian_digits)

    return f"{jd_p} {month_name} {jy_p}، {time_p}"


def stable_hash(value: str) -> str:
    """Return a deterministic SHA-256 hash for a string."""
    return sha256(value.encode("utf-8")).hexdigest()


def slugify(value: str) -> str:
    """Create a conservative URL-safe slug."""
    return sub(r"-+", "-", sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())).strip("-")
