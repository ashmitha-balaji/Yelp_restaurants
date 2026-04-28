"""
hours_utils.py — Restaurant hours parsing and open-now checking.

Stored format in MongoDB (hours_of_operation field):
    {
        "Mon": {"open": "09:00", "close": "22:00"},
        "Tue": {"open": "09:00", "close": "22:00"},
        "Wed": {"open": "09:00", "close": "22:00"},
        "Thu": {"open": "09:00", "close": "22:00"},
        "Fri": {"open": "11:00", "close": "23:30"},
        "Sat": {"open": "11:00", "close": "23:30"},
        "Sun": {"open": "12:00", "close": "21:00"},
        "closed_days": ["Mon"]           # optional list of closed days
    }

Times are 24-hour "HH:MM" strings. A restaurant is open if:
    open_minutes <= now_minutes < close_minutes

Overnight hours (e.g. open 22:00, close 02:00) are supported: if
close_minutes < open_minutes the range wraps midnight.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# Canonical day abbreviations in order Mon=0 … Sun=6
_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_DAY_ALIASES: Dict[str, str] = {
    "monday": "Mon", "tuesday": "Tue", "wednesday": "Wed",
    "thursday": "Thu", "friday": "Fri", "saturday": "Sat", "sunday": "Sun",
    "mon": "Mon", "tue": "Tue", "wed": "Wed", "thu": "Thu",
    "fri": "Fri", "sat": "Sat", "sun": "Sun",
}

# Meal-time windows (start_minute, end_minute)
MEAL_WINDOWS: Dict[str, Tuple[int, int]] = {
    "breakfast": (6 * 60, 11 * 60),       # 06:00–11:00
    "brunch":    (9 * 60, 14 * 60),        # 09:00–14:00
    "lunch":     (11 * 60, 15 * 60),       # 11:00–15:00
    "afternoon": (14 * 60, 17 * 60),       # 14:00–17:00
    "dinner":    (17 * 60, 22 * 60),       # 17:00–22:00
    "tonight":   (17 * 60, 23 * 60),       # 17:00–23:00
    "late night": (22 * 60, 26 * 60),      # 22:00–02:00 (next day)
    "late":      (21 * 60, 26 * 60),       # 21:00–02:00
    "early":     (6 * 60, 10 * 60),        # 06:00–10:00
}


def _to_minutes(time_str: str) -> int:
    """Convert 'HH:MM' to minutes since midnight. Returns -1 on parse error."""
    try:
        h, m = time_str.strip().split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return -1


def _parse_hours(hours_raw: Any) -> Optional[Dict[str, Any]]:
    """Parse hours_of_operation from string JSON or dict. Returns None on failure."""
    if not hours_raw:
        return None
    if isinstance(hours_raw, str):
        try:
            return json.loads(hours_raw)
        except Exception:
            return None
    if isinstance(hours_raw, dict):
        return hours_raw
    return None


def current_day_and_minutes(now: Optional[datetime] = None) -> Tuple[str, int]:
    """Return (day_abbrev, minutes_since_midnight) for the current moment."""
    if now is None:
        now = datetime.now()  # local time
    day_abbrev = _DAYS[now.weekday()]   # Mon=0
    minutes = now.hour * 60 + now.minute
    return day_abbrev, minutes


def is_open_at(hours_raw: Any, day: str, minutes: int) -> Optional[bool]:
    """
    Return True/False/None.
      True  → restaurant is open at `day` `minutes`
      False → restaurant is closed
      None  → no hours data available (treat as unknown)
    """
    hours = _parse_hours(hours_raw)
    if not hours:
        return None

    closed_days = hours.get("closed_days") or []
    if day in closed_days:
        return False

    day_hours = hours.get(day)
    if not day_hours:
        return None   # day not listed → no data

    open_min  = _to_minutes(str(day_hours.get("open",  "")))
    close_min = _to_minutes(str(day_hours.get("close", "")))
    if open_min < 0 or close_min < 0:
        return None

    if close_min > open_min:
        # Normal range: e.g. 09:00–22:00
        return open_min <= minutes < close_min
    else:
        # Overnight: e.g. 22:00–02:00
        return minutes >= open_min or minutes < close_min


def is_open_now(hours_raw: Any, now: Optional[datetime] = None) -> Optional[bool]:
    """Convenience wrapper: is the restaurant open right now?"""
    day, minutes = current_day_and_minutes(now)
    return is_open_at(hours_raw, day, minutes)


def is_open_for_meal(hours_raw: Any, meal: str,
                     now: Optional[datetime] = None) -> Optional[bool]:
    """
    Is the restaurant open during the given meal window?
    Meal must be a key in MEAL_WINDOWS.
    """
    meal_lower = meal.strip().lower()
    window = MEAL_WINDOWS.get(meal_lower)
    if not window:
        return None
    day, _ = current_day_and_minutes(now)
    start, end = window
    # Check if the restaurant is open during at least part of the meal window
    hours = _parse_hours(hours_raw)
    if not hours:
        return None
    closed_days = hours.get("closed_days") or []
    if day in closed_days:
        return False
    day_hours = hours.get(day)
    if not day_hours:
        return None
    open_min  = _to_minutes(str(day_hours.get("open",  "")))
    close_min = _to_minutes(str(day_hours.get("close", "")))
    if open_min < 0 or close_min < 0:
        return None
    # Overlap check: restaurant open range [open_min, close_min) ∩ [start, end)
    if close_min > open_min:
        return open_min < end and close_min > start
    else:  # overnight
        return True  # overnight restaurants cover most meal windows


def is_open_late(hours_raw: Any) -> Optional[bool]:
    """Does the restaurant close after 22:00 on at least one weekday?"""
    hours = _parse_hours(hours_raw)
    if not hours:
        return None
    for day in _DAYS:
        dh = hours.get(day)
        if not dh:
            continue
        close_min = _to_minutes(str(dh.get("close", "")))
        if close_min < 0:
            continue
        if close_min >= 22 * 60 or close_min < 4 * 60:  # >= 22:00 or past midnight
            return True
    return False


def hours_display(hours_raw: Any) -> str:
    """Return a human-readable summary, e.g. 'Mon-Thu 11:00-22:00, Fri-Sat 11:00-23:30'."""
    hours = _parse_hours(hours_raw)
    if not hours:
        return "Hours not available"
    closed = set(hours.get("closed_days") or [])
    lines = []
    for day in _DAYS:
        if day in closed:
            lines.append(f"{day}: Closed")
        elif day in hours and isinstance(hours[day], dict):
            dh = hours[day]
            lines.append(f"{day}: {dh.get('open','?')} – {dh.get('close','?')}")
    return ", ".join(lines) if lines else "Hours not available"


def make_default_hours(
    weekday_open: str = "11:00", weekday_close: str = "22:00",
    weekend_open: str = "11:00", weekend_close: str = "23:00",
    closed_days: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generate a standard hours dict — useful for seed data."""
    h: Dict[str, Any] = {}
    for day in ["Mon", "Tue", "Wed", "Thu"]:
        h[day] = {"open": weekday_open, "close": weekday_close}
    for day in ["Fri", "Sat"]:
        h[day] = {"open": weekend_open, "close": weekend_close}
    h["Sun"] = {"open": weekend_open, "close": weekday_close}
    if closed_days:
        h["closed_days"] = closed_days
    return h
