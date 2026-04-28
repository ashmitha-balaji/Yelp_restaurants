"""
test_hours.py — Tests for restaurant hours / open-now feature.

Covers:
  1. hours_utils unit tests (is_open_at, is_open_now, is_open_for_meal,
     is_open_late, hours_display, make_default_hours)
  2. REST: GET /restaurants/open-now endpoint
  3. REST: open_now / for_meal / at_time params on GET /restaurants/
  4. AI chatbot: _extract_time_intent (isolated)
  5. AI chatbot: full chat with "open now" query
"""
from __future__ import annotations

import sys
import types
from datetime import datetime
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# hours_utils unit tests
# ---------------------------------------------------------------------------
sys.path.insert(0, "lab2/python")

from hours_utils import (
    MEAL_WINDOWS,
    _to_minutes,
    _parse_hours,
    current_day_and_minutes,
    hours_display,
    is_open_at,
    is_open_for_meal,
    is_open_late,
    is_open_now,
    make_default_hours,
)

_SAMPLE = {
    "Mon": {"open": "09:00", "close": "22:00"},
    "Tue": {"open": "09:00", "close": "22:00"},
    "Wed": {"open": "09:00", "close": "22:00"},
    "Thu": {"open": "09:00", "close": "22:00"},
    "Fri": {"open": "11:00", "close": "23:30"},
    "Sat": {"open": "11:00", "close": "23:30"},
    "Sun": {"open": "12:00", "close": "21:00"},
}

_OVERNIGHT = {
    "Mon": {"open": "22:00", "close": "02:00"},
    "Tue": {"open": "22:00", "close": "02:00"},
    "Wed": {"open": "22:00", "close": "02:00"},
    "Thu": {"open": "22:00", "close": "02:00"},
    "Fri": {"open": "22:00", "close": "03:00"},
    "Sat": {"open": "22:00", "close": "03:00"},
    "Sun": {"open": "20:00", "close": "01:00"},
}


class TestToMinutes:
    def test_standard(self):
        assert _to_minutes("09:00") == 9 * 60
        assert _to_minutes("22:30") == 22 * 60 + 30

    def test_midnight(self):
        assert _to_minutes("00:00") == 0

    def test_invalid(self):
        assert _to_minutes("bad") == -1
        assert _to_minutes("") == -1


class TestIsOpenAt:
    def test_open_during_hours(self):
        assert is_open_at(_SAMPLE, "Mon", 12 * 60) is True   # noon on Mon

    def test_before_open(self):
        assert is_open_at(_SAMPLE, "Mon", 8 * 60) is False    # 08:00, opens 09:00

    def test_after_close(self):
        assert is_open_at(_SAMPLE, "Mon", 22 * 60 + 1) is False  # 22:01, closes 22:00

    def test_exactly_at_open(self):
        assert is_open_at(_SAMPLE, "Mon", 9 * 60) is True

    def test_exactly_at_close_is_closed(self):
        assert is_open_at(_SAMPLE, "Mon", 22 * 60) is False

    def test_closed_day(self):
        hours = dict(_SAMPLE)
        hours["closed_days"] = ["Mon"]
        assert is_open_at(hours, "Mon", 12 * 60) is False

    def test_overnight_open(self):
        assert is_open_at(_OVERNIGHT, "Mon", 23 * 60) is True   # 23:00 → open

    def test_overnight_past_midnight(self):
        assert is_open_at(_OVERNIGHT, "Mon", 1 * 60) is True    # 01:00 → still open

    def test_overnight_after_close(self):
        assert is_open_at(_OVERNIGHT, "Mon", 3 * 60) is False   # 03:00 → closed

    def test_no_hours_returns_none(self):
        assert is_open_at(None, "Mon", 12 * 60) is None
        assert is_open_at({}, "Mon", 12 * 60) is None


class TestIsOpenForMeal:
    def test_open_for_lunch(self):
        # _SAMPLE Mon opens 09:00, closes 22:00 → covers lunch (11:00–15:00)
        assert is_open_for_meal(_SAMPLE, "lunch") is True

    def test_open_for_dinner(self):
        assert is_open_for_meal(_SAMPLE, "dinner") is True

    def test_lunch_only_not_open_for_dinner(self):
        lunch_only = {d: {"open": "11:00", "close": "15:00"}
                      for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}
        # Simulate checking on any day; dinner window is 17–22, no overlap
        # We need to fake the current day — use now parameter trick by passing
        # a datetime that falls on the same day the dict covers
        assert is_open_for_meal(lunch_only, "dinner") is False

    def test_unknown_meal(self):
        assert is_open_for_meal(_SAMPLE, "supper") is None

    def test_no_hours(self):
        assert is_open_for_meal(None, "lunch") is None


class TestIsOpenLate:
    def test_late_night_bar(self):
        assert is_open_late(_OVERNIGHT) is True

    def test_lunch_only_not_late(self):
        lunch_only = {d: {"open": "11:00", "close": "14:00"}
                      for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}
        assert is_open_late(lunch_only) is False

    def test_closes_at_2230(self):
        hours = {"Mon": {"open": "11:00", "close": "22:30"}}
        assert is_open_late(hours) is True

    def test_no_hours(self):
        assert is_open_late(None) is None


class TestHoursDisplay:
    def test_returns_string(self):
        result = hours_display(_SAMPLE)
        assert isinstance(result, str)
        assert "Mon" in result

    def test_no_hours_fallback(self):
        assert hours_display(None) == "Hours not available"
        assert hours_display({}) == "Hours not available"

    def test_closed_day_shown(self):
        hours = dict(_SAMPLE)
        hours["closed_days"] = ["Mon"]
        result = hours_display(hours)
        assert "Closed" in result


class TestMakeDefaultHours:
    def test_structure(self):
        h = make_default_hours()
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            assert day in h
            assert "open" in h[day]
            assert "close" in h[day]

    def test_closed_days(self):
        h = make_default_hours(closed_days=["Mon"])
        assert "Mon" in h["closed_days"]


# ---------------------------------------------------------------------------
# REST endpoint tests
# ---------------------------------------------------------------------------

# We need to import the restaurant app and seed a test restaurant with hours
# Reuse conftest fixtures via pytest

@pytest.fixture(scope="module")
def rest_client(seeded_restaurant):
    """TestClient for the restaurant service."""
    from conftest import _make_restaurant_app
    from fastapi.testclient import TestClient
    return TestClient(_make_restaurant_app())


@pytest.fixture(scope="module")
def hours_restaurant(rest_client, user_token):
    """Create a restaurant with known hours_of_operation."""
    from mongo_client import get_db
    db = get_db()
    hours = {
        "Mon": {"open": "09:00", "close": "22:00"},
        "Tue": {"open": "09:00", "close": "22:00"},
        "Wed": {"open": "09:00", "close": "22:00"},
        "Thu": {"open": "09:00", "close": "22:00"},
        "Fri": {"open": "11:00", "close": "23:30"},
        "Sat": {"open": "11:00", "close": "23:30"},
        "Sun": {"open": "12:00", "close": "21:00"},
    }
    payload = {
        "name": "The Open Now Bistro",
        "address": "1 Test St, San Jose, CA 95101",
        "cuisine_type": "Italian",
        "description": "Open now test restaurant",
        "phone": "408-555-0001",
        "price_range": "$$",
        "city": "San Jose",
        "hours_of_operation": hours,
    }
    resp = rest_client.post(
        "/restaurants/",
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code in (200, 201)
    return resp.json()


class TestOpenNowEndpoint:
    def test_returns_list(self, rest_client, hours_restaurant):
        r = rest_client.get("/restaurants/open-now")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)

    def test_result_has_is_open_now(self, rest_client, hours_restaurant):
        r = rest_client.get("/restaurants/open-now")
        assert r.status_code == 200
        for item in r.json():
            assert item.get("is_open_now") is True

    def test_limit_param(self, rest_client, hours_restaurant):
        r = rest_client.get("/restaurants/open-now?limit=2")
        assert r.status_code == 200
        assert len(r.json()) <= 2

    def test_city_filter(self, rest_client, hours_restaurant):
        r = rest_client.get("/restaurants/open-now?city=San+Jose")
        assert r.status_code == 200
        for item in r.json():
            assert "San Jose" in item.get("city", "")

    def test_for_meal_param(self, rest_client, hours_restaurant):
        r = rest_client.get("/restaurants/open-now?for_meal=lunch")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_at_time_param(self, rest_client, hours_restaurant):
        # 12:00 — should include restaurants open at noon
        r = rest_client.get("/restaurants/open-now?at_time=12:00")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


class TestSearchWithHoursFilter:
    def test_open_now_param_on_search(self, rest_client, hours_restaurant):
        r = rest_client.get("/restaurants/?open_now=true")
        assert r.status_code == 200
        data = r.json()
        items = data if isinstance(data, list) else data.get("restaurants", [])
        assert isinstance(items, list)

    def test_open_for_param_on_search(self, rest_client, hours_restaurant):
        r = rest_client.get("/restaurants/?open_for=dinner")
        assert r.status_code == 200

    def test_at_time_param_on_search(self, rest_client, hours_restaurant):
        r = rest_client.get("/restaurants/?at_time=19:00")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# AI chatbot: time intent extraction (unit)
# ---------------------------------------------------------------------------

sys.path.insert(0, "lab2/mongo_routers")

from ai_assistant import _extract_time_intent


class TestExtractTimeIntent:
    def test_open_now(self):
        result = _extract_time_intent("find restaurants open right now")
        assert result["open_now"] is True

    def test_currently_open(self):
        result = _extract_time_intent("which places are currently open?")
        assert result["open_now"] is True

    def test_open_today(self):
        result = _extract_time_intent("show me restaurants open today")
        assert result["open_now"] is True

    def test_meal_dinner(self):
        result = _extract_time_intent("italian restaurants open for dinner")
        assert result["open_for"] == "dinner"
        assert result["open_now"] is True

    def test_meal_lunch(self):
        result = _extract_time_intent("cheap lunch spots near me")
        assert result["open_for"] == "lunch"

    def test_meal_breakfast(self):
        result = _extract_time_intent("best breakfast places")
        assert result["open_for"] == "breakfast"

    def test_late_night(self):
        result = _extract_time_intent("open late night bars")
        assert result["open_late"] is True
        assert result["open_now"] is True

    def test_open_late(self):
        result = _extract_time_intent("restaurants open late on Friday")
        assert result["open_late"] is True

    def test_explicit_time_pm(self):
        result = _extract_time_intent("open at 8pm")
        assert result["at_time"] == "20:00"
        assert result["open_now"] is True

    def test_explicit_time_am(self):
        result = _extract_time_intent("breakfast places open at 8am")
        assert result["at_time"] == "08:00"

    def test_no_time_intent(self):
        result = _extract_time_intent("best italian restaurants in San Jose")
        assert result["open_now"] is None
        assert result["open_for"] is None
        assert result["at_time"] is None
        assert result["open_late"] is None

    def test_after_midnight(self):
        result = _extract_time_intent("open past midnight")
        assert result["open_late"] is True


# ---------------------------------------------------------------------------
# AI chatbot: full chat integration
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ai_client():
    from conftest import _make_restaurant_app
    from fastapi.testclient import TestClient
    return TestClient(_make_restaurant_app())


class TestAIChatHours:
    def test_open_now_chat_response(self, ai_client):
        """AI should respond to 'restaurants open now' without crashing."""
        r = ai_client.post(
            "/ai-assistant/chat",
            json={"message": "show me restaurants open right now"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "message" in data
        assert isinstance(data["recommendations"], list)

    def test_open_for_dinner_chat(self, ai_client):
        r = ai_client.post(
            "/ai-assistant/chat",
            json={"message": "find me a good Italian restaurant open for dinner"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "message" in data

    def test_open_late_chat(self, ai_client):
        r = ai_client.post(
            "/ai-assistant/chat",
            json={"message": "where can I eat open late night?"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "message" in data

    def test_open_at_time_chat(self, ai_client):
        r = ai_client.post(
            "/ai-assistant/chat",
            json={"message": "restaurants open at 8pm"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "message" in data

    def test_recommendations_have_hours_display(self, ai_client, hours_restaurant):
        """Recommendations from local DB should include hours_display field."""
        r = ai_client.post(
            "/ai-assistant/chat",
            json={"message": "italian restaurants open now"},
        )
        assert r.status_code == 200
        recs = r.json().get("recommendations", [])
        # At least one local rec should have hours_display (when hours data exists)
        local_recs = [rec for rec in recs if rec.get("source") == "local"]
        for rec in local_recs:
            assert "hours_display" in rec
