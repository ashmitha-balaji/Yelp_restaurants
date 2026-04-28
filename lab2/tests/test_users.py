"""
Tests for /users/me, /users/me/preferences, /users/{id}
"""
from conftest import auth_headers


class TestGetMe:
    def test_get_me(self, user_client, user_token):
        r = user_client.get("/users/me", headers=auth_headers(user_token))
        assert r.status_code == 200
        body = r.json()
        assert body["email"] == "testuser@yelp.com"
        assert body["name"] == "Alice"
        assert "password_hash" not in body

    def test_get_me_unauthenticated(self, user_client):
        r = user_client.get("/users/me")
        assert r.status_code == 401


class TestUpdateMe:
    def test_update_name_and_city(self, user_client, user_token):
        r = user_client.put(
            "/users/me",
            json={"name": "Alice Updated", "city": "San Jose", "state": "CA"},
            headers=auth_headers(user_token),
        )
        assert r.status_code == 200
        body = r.json()
        assert body["name"] == "Alice Updated"
        assert body["city"] == "San Jose"

    def test_update_about_me(self, user_client, user_token):
        r = user_client.put(
            "/users/me",
            json={"about_me": "I love food!"},
            headers=auth_headers(user_token),
        )
        assert r.status_code == 200
        assert r.json()["about_me"] == "I love food!"

    def test_update_requires_auth(self, user_client):
        r = user_client.put("/users/me", json={"name": "Hacker"})
        assert r.status_code == 401


class TestUserPreferences:
    def test_get_preferences_default_empty(self, user_client, user_token):
        r = user_client.get("/users/me/preferences", headers=auth_headers(user_token))
        assert r.status_code == 200
        # Should return something (empty dict or nulls) — not 404

    def test_set_and_get_preferences(self, user_client, user_token):
        prefs = {
            "cuisine_preferences": "Italian, Japanese",
            "price_range": "$$",
            "preferred_locations": "San Jose, CA",
            "dietary_needs": "vegetarian",
            "ambiance_preferences": "casual",
            "sort_preference": "rating",
        }
        r = user_client.put(
            "/users/me/preferences",
            json=prefs,
            headers=auth_headers(user_token),
        )
        assert r.status_code == 200

        r2 = user_client.get("/users/me/preferences", headers=auth_headers(user_token))
        assert r2.status_code == 200
        body = r2.json()
        assert body["cuisine_preferences"] == "Italian, Japanese"
        assert body["price_range"] == "$$"
        assert body["dietary_needs"] == "vegetarian"

    def test_preferences_require_auth(self, user_client):
        r = user_client.get("/users/me/preferences")
        assert r.status_code == 401


class TestGetUserById:
    def test_get_other_user(self, user_client, user_token):
        # First get own ID
        me = user_client.get("/users/me", headers=auth_headers(user_token)).json()
        user_id = me["id"]
        r = user_client.get(f"/users/{user_id}", headers=auth_headers(user_token))
        assert r.status_code == 200
        assert r.json()["id"] == user_id

    def test_get_nonexistent_user(self, user_client, user_token):
        r = user_client.get("/users/99999", headers=auth_headers(user_token))
        assert r.status_code == 404
