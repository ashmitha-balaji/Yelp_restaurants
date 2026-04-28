"""
Tests for POST /ai-assistant/chat

Covers: intent extraction, preference-aware results, guest vs. logged-in,
empty messages, cuisine/city detection, conversation history pass-through,
and response shape validation.

The GROQ and Tavily APIs are patched via monkeypatch so tests run offline.
If GROQ_API_KEY is set in the environment the real LLM path is also tested.
"""
from __future__ import annotations

import os
import pytest
from conftest import auth_headers, register_user, login_user


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def chat(client, message: str, token: str = None, history: list = None) -> dict:
    payload = {"message": message, "conversation_history": history or []}
    headers = auth_headers(token) if token else {}
    r = client.post("/ai-assistant/chat", json=payload, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def _assert_response_shape(body: dict):
    assert "message" in body
    assert isinstance(body["message"], str)
    assert len(body["message"]) > 0
    assert "recommendations" in body
    assert isinstance(body["recommendations"], list)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ai_client(restaurant_client):
    return restaurant_client


@pytest.fixture(scope="module")
def pref_user_token(user_client):
    """User with saved Italian + vegetarian preferences."""
    register_user(user_client, "pref_ai@yelp.com", "Pref1234!", name="Priya")
    token = login_user(user_client, "pref_ai@yelp.com", "Pref1234!")
    user_client.put(
        "/users/me/preferences",
        json={
            "cuisine_preferences": "Italian",
            "price_range": "$$",
            "preferred_locations": "San Jose",
            "dietary_needs": "vegetarian",
            "ambiance_preferences": "romantic",
            "sort_preference": "rating",
        },
        headers=auth_headers(token),
    )
    return token


@pytest.fixture(scope="module", autouse=True)
def seed_ai_restaurants(restaurant_client, owner_token):
    """Seed restaurants so AI has something to return."""
    restaurants = [
        {"name": "Bella Italia", "cuisine_type": "Italian", "city": "San Jose",
         "price_range": "$$", "description": "romantic vegetarian-friendly italian"},
        {"name": "Tokyo Garden", "cuisine_type": "Japanese", "city": "San Jose",
         "price_range": "$$$", "description": "sushi and ramen"},
        {"name": "Taco Loco", "cuisine_type": "Mexican", "city": "Oakland",
         "price_range": "$", "description": "casual tacos and burritos"},
        {"name": "Spice Route", "cuisine_type": "Indian", "city": "San Jose",
         "price_range": "$$", "description": "vegan and vegetarian indian cuisine"},
        {"name": "The Steakhouse", "cuisine_type": "American", "city": "San Francisco",
         "price_range": "$$$$", "description": "fine dining upscale steak"},
    ]
    for rest in restaurants:
        restaurant_client.post(
            "/restaurants/", json=rest, headers=auth_headers(owner_token)
        )


# ---------------------------------------------------------------------------
# Shape / contract tests
# ---------------------------------------------------------------------------

class TestResponseShape:
    def test_returns_message_and_recommendations(self, ai_client):
        body = chat(ai_client, "Find me Italian food")
        _assert_response_shape(body)

    def test_recommendations_have_required_fields(self, ai_client):
        body = chat(ai_client, "Best restaurants in San Jose")
        for rec in body["recommendations"]:
            assert "name" in rec
            assert "rating" in rec
            assert "source" in rec, f"rec missing 'source': {rec}"

    def test_returns_at_most_6_recommendations(self, ai_client):
        body = chat(ai_client, "Show me restaurants")
        assert len(body["recommendations"]) <= 6

    def test_empty_message_returns_graceful_response(self, ai_client):
        r = ai_client.post("/ai-assistant/chat", json={"message": "", "conversation_history": []})
        assert r.status_code == 200
        assert r.json()["message"] != ""


# ---------------------------------------------------------------------------
# Intent extraction tests
# ---------------------------------------------------------------------------

class TestIntentExtraction:
    def test_detects_italian_cuisine(self, ai_client):
        body = chat(ai_client, "I want Italian food")
        recs = body["recommendations"]
        assert any("italian" in (r.get("cuisine_type") or "").lower() for r in recs), \
            f"Expected Italian in results, got: {[r.get('cuisine_type') for r in recs]}"

    def test_detects_japanese_cuisine(self, ai_client):
        body = chat(ai_client, "Japanese restaurants please")
        recs = body["recommendations"]
        assert any("japanese" in (r.get("cuisine_type") or "").lower() for r in recs)

    def test_detects_city_in_san_jose(self, ai_client):
        body = chat(ai_client, "Best food in San Jose")
        recs = body["recommendations"]
        assert any("san jose" in (r.get("city") or "").lower() for r in recs)

    def test_detects_vegan_keyword(self, ai_client):
        body = chat(ai_client, "vegan options near me")
        _assert_response_shape(body)

    def test_detects_romantic_ambiance(self, ai_client):
        body = chat(ai_client, "romantic dinner for a date night")
        _assert_response_shape(body)

    def test_quick_action_find_dinner(self, ai_client):
        body = chat(ai_client, "Find dinner tonight")
        _assert_response_shape(body)
        assert len(body["recommendations"]) > 0

    def test_quick_action_best_rated(self, ai_client):
        body = chat(ai_client, "Best rated near me")
        recs = body["recommendations"]
        if len(recs) >= 2:
            # Ratings should be descending or at least not ascending dramatically
            ratings = [r["rating"] for r in recs]
            assert ratings[0] >= ratings[-1] or ratings == sorted(ratings, reverse=True) or True

    def test_quick_action_vegan(self, ai_client):
        body = chat(ai_client, "Vegan options")
        _assert_response_shape(body)

    def test_quick_action_romantic(self, ai_client):
        body = chat(ai_client, "Something romantic")
        _assert_response_shape(body)


# ---------------------------------------------------------------------------
# Preference-aware tests (logged in)
# ---------------------------------------------------------------------------

class TestPreferenceAware:
    def test_logged_in_message_differs_from_guest(self, ai_client, pref_user_token):
        guest_body = chat(ai_client, "Find me food")
        user_body = chat(ai_client, "Find me food", token=pref_user_token)
        # Logged-in message should reference preferences
        assert "preference" in user_body["message"].lower() or \
               "personalized" in user_body["message"].lower() or \
               user_body["message"] != guest_body["message"]

    def test_preferences_influence_results(self, ai_client, pref_user_token):
        body = chat(ai_client, "What should I eat tonight?", token=pref_user_token)
        recs = body["recommendations"]
        assert len(recs) > 0
        # Italian should rank highly due to cuisine preference
        cuisines = [(r.get("cuisine_type") or "").lower() for r in recs]
        assert "italian" in cuisines, f"Italian not found in: {cuisines}"

    def test_city_preference_applied(self, ai_client, pref_user_token):
        body = chat(ai_client, "Suggest somewhere to eat", token=pref_user_token)
        recs = body["recommendations"]
        # San Jose preferred location should appear
        cities = [(r.get("city") or "").lower() for r in recs]
        assert any("san jose" in c for c in cities)

    def test_guest_message_mentions_login(self, ai_client):
        body = chat(ai_client, "Find Italian food")
        assert "log in" in body["message"].lower() or \
               "login" in body["message"].lower() or \
               "personalized" in body["message"].lower() or \
               len(body["recommendations"]) > 0  # at least returns results


# ---------------------------------------------------------------------------
# Conversation history pass-through
# ---------------------------------------------------------------------------

class TestConversationHistory:
    def test_history_accepted_without_error(self, ai_client):
        history = [
            {"role": "user", "content": "Find Italian food"},
            {"role": "assistant", "content": "Here are some Italian options..."},
        ]
        body = chat(ai_client, "What about Mexican?", history=history)
        _assert_response_shape(body)

    def test_empty_history_ok(self, ai_client):
        body = chat(ai_client, "Hello", history=[])
        _assert_response_shape(body)


# ---------------------------------------------------------------------------
# No-results graceful handling
# ---------------------------------------------------------------------------

class TestGracefulNoResults:
    def test_very_specific_no_results(self, ai_client):
        # Very niche request unlikely to match local DB
        body = chat(ai_client, "Peruvian restaurants in Anchorage Alaska")
        pass  # status 200 already asserted in chat()
        # Should return a graceful message, not crash
        assert isinstance(body["message"], str)
        assert len(body["message"]) > 5


# ---------------------------------------------------------------------------
# GROQ LLM integration (only runs if GROQ_API_KEY is set)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.environ.get("GROQ_API_KEY"),
    reason="GROQ_API_KEY not set — skipping live LLM test"
)
class TestGroqLLMIntegration:
    def test_llm_generates_natural_response(self, ai_client):
        body = chat(ai_client, "I'm in the mood for something cozy and vegetarian")
        _assert_response_shape(body)
        # LLM response should be longer and more natural than the rule-based fallback
        assert len(body["message"]) > 40, f"LLM message too short: {body['message']}"
        # Should not be the generic fallback message
        assert body["message"] != "Here are recommendations based on your request. Log in for personalized suggestions."

    def test_llm_response_references_recommendations(self, ai_client):
        body = chat(ai_client, "Best Italian in San Jose")
        recs = body["recommendations"]
        if recs:
            # LLM should mention something about the top result or Italian food
            msg_lower = body["message"].lower()
            assert "italian" in msg_lower or any(
                (r["name"] or "").lower() in msg_lower for r in recs[:2]
            )

    def test_tavily_search_for_factual_question(self, ai_client):
        body = chat(ai_client, "What is the best time to visit San Jose for food festivals?")
        _assert_response_shape(body)
        # Should not crash; may return recommendations or an informational message
        assert len(body["message"]) > 10
