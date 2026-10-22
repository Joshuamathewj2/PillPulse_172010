"""Local-time helpers.

Servers run in UTC but doses happen on the patient's wall clock. Every
"today" / "already missed" decision goes through here so it uses APP_TIMEZONE
(default Asia/Kolkata). Timestamps are stored as naive local datetimes.
"""
import os
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo


def tz() -> ZoneInfo:
    return ZoneInfo(os.getenv("APP_TIMEZONE", "Asia/Kolkata"))


def now() -> datetime:
    return datetime.now(tz()).replace(tzinfo=None)


def today() -> date:
    return now().date()


_TIME = re.compile(r"(\d{1,2})[:.](\d{2})\s*([AaPp][Mm])?")


def to_24h(value: str) -> str | None:
    """'8:00 AM' / '08:00' / '8.30 pm' / '08:15 AM — After breakfast' -> 'HH:MM'."""
    m = _TIME.search(value or "")
    if not m:
        return None
    h, mins, period = int(m.group(1)), int(m.group(2)), (m.group(3) or "").upper()
    if period == "PM" and h != 12:
        h += 12
    if period == "AM" and h == 12:
        h = 0
    if h > 23 or mins > 59:
        return None
    return f"{h:02d}:{mins:02d}"
