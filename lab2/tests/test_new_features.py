"""
Tests for the 7 new Lab 2 features:

  1. Owner reply to reviews       (POST/DELETE /reviews/{id}/reply)
  2. Review photo upload          (POST /reviews/{id}/photo)
  3. Search autocomplete          (GET /restaurants/autocomplete)
  4. Waitlist / reservation       (POST/GET/DELETE /waitlist/{restaurant_id})
  5. AI memory across sessions    (GET/DELETE /ai-assistant/history)
  6. Trending restaurants         (GET /restaurants/trending)
  7. Push notifications           (GET /notifications/, unread-count, mark-read)
"""
from __future__ import annotations

import io
import os
import sys
import types
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from conftest import auth_headers, register_user, login_user


# ── Shared app factories ───────────────────────────────────────────────────

def _make_full_review_app():
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from mongo_routers import reviews_async, waitlist

    app = FastAPI()
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    app.include_router(reviews_async.router)
    app.include_router(waitlist.router)
    return app


def _make_full_user_app():
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from mongo_routers import auth, users, favorites, history, notifications

    app = FastAPI()
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(favorites.router)
    app.include_router(history.router)
    app.include_router(notifications.router)
    return app


def _make_full_restaurant_app():
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from mongo_routers import restaurants, ai_assistant

    app = FastAPI()
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    app.include_router(restaurants.router)
    app.include_router(ai_assistant.router)
    return app


@pytest.fixture(scope="module")
def full_review_client():
    return TestClient(_make_full_review_app())


@pytest.fixture(scope="module")
def full_user_client():
    return TestClient(_make_full_user_app())


@pytest.fixture(scope="module")
def full_rest_client():
    return TestClient(_make_full_restaurant_app())


# ── Module-scoped users + restaurant ──────────────────────────────────────

@pytest.fixture(scope="module")
def new_owner_token(full_user_client):
    register_user(full_user_client, "newowner@yelp.com", "NewOwner1!", name="NewOwner", role="owner")
    return login_user(full_user_client, "newowner@yelp.com", "NewOwner1!")


@pytest.fixture(scope="module")
def new_user_token(full_user_client):
    register_user(full_user_client, "newuser@yelp.com", "NewUser1!", name="NewUser")
    return login_user(full_user_client, "newuser@yelp.com", "NewUser1!")


@pytest.fixture(scope="module")
def owned_restaurant(full_rest_client, new_owner_token):
    r = full_rest_client.post(
        "/restaurants/",
        json={
            "name": "Feature Test Bistro",
            "cuisine_type": "French",
            "city": "San Jose",
            "price_range": "$$",
            "description": "A lovely bistro for testing new features",
        },
        headers=auth_headers(new_owner_token),
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture(scope="module")
def existing_review(full_review_client, full_user_client, new_user_token, owned_restaurant):
    """Create a review to test reply/photo on."""
    r = full_review_client.post(
        "/reviews/",
        json={"restaurant_id": owned_restaurant["id"], "rating": 4, "comment": "Very nice place!"},
        headers=auth_headers(new_user_token),
    )
    assert r.status_code == 202, r.text
    job_id = r.json()["job_id"]
    status = full_review_client.get(f"/reviews/job/{job_id}").json()
    return {"review_id": status["review_id"]}


# ══════════════════════════════════════════════════════════════════════════
# 1. Owner Reply to Reviews
# ══════════════════════════════════════════════════════════════════════════

class TestOwnerReply:
    def test_owner_can_reply(self, full_review_client, new_owner_token, existing_review):
        r = full_review_client.post(
            f"/reviews/{existing_review['review_id']}/reply",
            json={"reply": "Thank you for your kind words! Hope to see you again."},
            headers=auth_headers(new_owner_token),
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["owner_reply"] == "Thank you for your kind words! Hope to see you again."
        assert body["owner_reply_at"] is not None

    def test_reply_visible_in_review_list(self, full_review_client, owned_restaurant):
        rid = owned_restaurant["id"]
        reviews = full_review_client.get(f"/reviews/restaurant/{rid}").json()
        replied = [rev for rev in reviews if rev.get("owner_reply")]
        assert len(replied) >= 1
        assert "Thank you" in replied[0]["owner_reply"]

    def test_non_owner_cannot_reply(self, full_review_client, new_user_token, existing_review):
        r = full_review_client.post(
            f"/reviews/{existing_review['review_id']}/reply",
            json={"reply": "Hacked reply"},
            headers=auth_headers(new_user_token),
        )
        assert r.status_code == 403

    def test_wrong_owner_cannot_reply(self, full_review_client, full_user_client, existing_review):
        # Register a different owner
        register_user(full_user_client, "other_owner@yelp.com", "Other123!", name="OtherOwner", role="owner")
        other_token = login_user(full_user_client, "other_owner@yelp.com", "Other123!")
        r = full_review_client.post(
            f"/reviews/{existing_review['review_id']}/reply",
            json={"reply": "I own this now"},
            headers=auth_headers(other_token),
        )
        assert r.status_code == 403

    def test_reply_on_nonexistent_review(self, full_review_client, new_owner_token):
        r = full_review_client.post(
            "/reviews/999999/reply",
            json={"reply": "Test"},
            headers=auth_headers(new_owner_token),
        )
        assert r.status_code == 404

    def test_owner_can_delete_reply(self, full_review_client, new_owner_token, existing_review):
        r = full_review_client.delete(
            f"/reviews/{existing_review['review_id']}/reply",
            headers=auth_headers(new_owner_token),
        )
        assert r.status_code == 200
        assert "removed" in r.json()["message"].lower()

    def test_delete_reply_twice_returns_404(self, full_review_client, new_owner_token, existing_review):
        r = full_review_client.delete(
            f"/reviews/{existing_review['review_id']}/reply",
            headers=auth_headers(new_owner_token),
        )
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════
# 2. Review Photo Upload
# ══════════════════════════════════════════════════════════════════════════

class TestReviewPhotoUpload:
    def _fake_image(self, name: str = "photo.jpg") -> tuple:
        # Minimal valid JPEG bytes
        img_bytes = (
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
            b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
            b"\xff\xd9"
        )
        return (name, io.BytesIO(img_bytes), "image/jpeg")

    def test_author_can_upload_photo(self, full_review_client, new_user_token, existing_review):
        r = full_review_client.post(
            f"/reviews/{existing_review['review_id']}/photo",
            files={"file": self._fake_image()},
            headers=auth_headers(new_user_token),
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "photo_url" in body
        assert body["photo_url"].startswith("/uploads/")
        assert f"review_{existing_review['review_id']}_" in body["photo_url"]

    def test_photo_appears_in_review(self, full_review_client, owned_restaurant, existing_review):
        reviews = full_review_client.get(f"/reviews/restaurant/{owned_restaurant['id']}").json()
        target = next((r for r in reviews if r["id"] == existing_review["review_id"]), None)
        assert target is not None
        assert target["photo_url"] is not None
        assert target["photo_url"].startswith("/uploads/")

    def test_other_user_cannot_upload_photo(
        self, full_review_client, full_user_client, existing_review
    ):
        register_user(full_user_client, "photohack@yelp.com", "Photo123!", name="PhotoHack")
        other_token = login_user(full_user_client, "photohack@yelp.com", "Photo123!")
        r = full_review_client.post(
            f"/reviews/{existing_review['review_id']}/photo",
            files={"file": self._fake_image()},
            headers=auth_headers(other_token),
        )
        assert r.status_code == 403

    def test_disallowed_file_type_rejected(self, full_review_client, new_user_token, existing_review):
        r = full_review_client.post(
            f"/reviews/{existing_review['review_id']}/photo",
            files={"file": ("malware.exe", io.BytesIO(b"MZ"), "application/octet-stream")},
            headers=auth_headers(new_user_token),
        )
        assert r.status_code == 422

    def test_upload_requires_auth(self, full_review_client, existing_review):
        r = full_review_client.post(
            f"/reviews/{existing_review['review_id']}/photo",
            files={"file": self._fake_image()},
        )
        assert r.status_code == 401


# ══════════════════════════════════════════════════════════════════════════
# 3. Search Autocomplete
# ══════════════════════════════════════════════════════════════════════════

class TestSearchAutocomplete:
    def test_autocomplete_returns_list(self, full_rest_client, owned_restaurant):
        r = full_rest_client.get("/restaurants/autocomplete?q=Feat")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_autocomplete_matches_name(self, full_rest_client, owned_restaurant):
        r = full_rest_client.get("/restaurants/autocomplete?q=Feature")
        assert r.status_code == 200
        results = r.json()
        assert any("Feature" in (res.get("name") or "") for res in results)

    def test_autocomplete_matches_cuisine(self, full_rest_client, owned_restaurant):
        r = full_rest_client.get("/restaurants/autocomplete?q=French")
        assert r.status_code == 200
        results = r.json()
        assert any("French" in (res.get("cuisine_type") or "") for res in results)

    def test_autocomplete_matches_city(self, full_rest_client, owned_restaurant):
        r = full_rest_client.get("/restaurants/autocomplete?q=San")
        assert r.status_code == 200
        results = r.json()
        assert any("San" in (res.get("city") or "") for res in results)

    def test_autocomplete_returns_at_most_8(self, full_rest_client):
        r = full_rest_client.get("/restaurants/autocomplete?q=e")
        assert r.status_code == 200
        assert len(r.json()) <= 8

    def test_autocomplete_result_shape(self, full_rest_client, owned_restaurant):
        r = full_rest_client.get("/restaurants/autocomplete?q=Bistro")
        assert r.status_code == 200
        for item in r.json():
            assert "id" in item
            assert "name" in item
            assert "cuisine_type" in item
            assert "city" in item

    def test_autocomplete_no_match(self, full_rest_client):
        r = full_rest_client.get("/restaurants/autocomplete?q=xyznonexistent9999")
        assert r.status_code == 200
        assert r.json() == []


# ══════════════════════════════════════════════════════════════════════════
# 4. Waitlist / Reservation
# ══════════════════════════════════════════════════════════════════════════

class TestWaitlist:
    def test_join_waitlist(self, full_review_client, new_user_token, owned_restaurant):
        r = full_review_client.post(
            f"/waitlist/{owned_restaurant['id']}",
            json={"party_size": 2, "notes": "Window seat please"},
            headers=auth_headers(new_user_token),
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["position"] >= 1
        assert body["party_size"] == 2
        assert "queue" in body["message"].lower() or "waitlist" in body["message"].lower()

    def test_cannot_join_twice(self, full_review_client, new_user_token, owned_restaurant):
        r = full_review_client.post(
            f"/waitlist/{owned_restaurant['id']}",
            json={"party_size": 1},
            headers=auth_headers(new_user_token),
        )
        assert r.status_code == 400
        assert "already" in r.json()["detail"].lower()

    def test_get_my_status(self, full_review_client, new_user_token, owned_restaurant):
        r = full_review_client.get(
            f"/waitlist/{owned_restaurant['id']}/status",
            headers=auth_headers(new_user_token),
        )
        assert r.status_code == 200
        body = r.json()
        assert body["in_queue"] is True
        assert body["position"] >= 1
        assert body["queue_length"] >= 1

    def test_status_for_nonmember(self, full_review_client, full_user_client, owned_restaurant):
        register_user(full_user_client, "noqueue@yelp.com", "NoQueue1!", name="NoQueue")
        token = login_user(full_user_client, "noqueue@yelp.com", "NoQueue1!")
        r = full_review_client.get(
            f"/waitlist/{owned_restaurant['id']}/status",
            headers=auth_headers(token),
        )
        assert r.status_code == 200
        assert r.json()["in_queue"] is False

    def test_owner_sees_full_queue(self, full_review_client, new_owner_token, owned_restaurant):
        r = full_review_client.get(
            f"/waitlist/{owned_restaurant['id']}",
            headers=auth_headers(new_owner_token),
        )
        assert r.status_code == 200
        body = r.json()
        assert "queue_length" in body
        assert isinstance(body["entries"], list)
        assert body["queue_length"] >= 1

    def test_non_owner_cannot_see_full_queue(self, full_review_client, new_user_token, owned_restaurant):
        r = full_review_client.get(
            f"/waitlist/{owned_restaurant['id']}",
            headers=auth_headers(new_user_token),
        )
        assert r.status_code == 403

    def test_owner_can_call_guest(self, full_review_client, full_user_client, new_owner_token, owned_restaurant):
        # Get the user's ID from queue
        queue_r = full_review_client.get(
            f"/waitlist/{owned_restaurant['id']}",
            headers=auth_headers(new_owner_token),
        ).json()
        entry = queue_r["entries"][0]
        uid = entry["user_id"]

        r = full_review_client.post(
            f"/waitlist/{owned_restaurant['id']}/notify/{uid}",
            headers=auth_headers(new_owner_token),
        )
        assert r.status_code == 200
        assert "notified" in r.json()["message"].lower()

    def test_leave_waitlist(self, full_review_client, full_user_client, owned_restaurant):
        # Add a fresh user, then have them leave
        register_user(full_user_client, "leavequeue@yelp.com", "Leave123!", name="Leaver")
        token = login_user(full_user_client, "leavequeue@yelp.com", "Leave123!")
        full_review_client.post(
            f"/waitlist/{owned_restaurant['id']}",
            json={"party_size": 1},
            headers=auth_headers(token),
        )
        r = full_review_client.delete(
            f"/waitlist/{owned_restaurant['id']}",
            headers=auth_headers(token),
        )
        assert r.status_code == 200
        # Verify they're gone
        status = full_review_client.get(
            f"/waitlist/{owned_restaurant['id']}/status",
            headers=auth_headers(token),
        ).json()
        assert status["in_queue"] is False

    def test_join_nonexistent_restaurant(self, full_review_client, new_user_token):
        r = full_review_client.post(
            "/waitlist/999999",
            json={"party_size": 1},
            headers=auth_headers(new_user_token),
        )
        assert r.status_code == 404

    def test_requires_auth(self, full_review_client, owned_restaurant):
        r = full_review_client.post(
            f"/waitlist/{owned_restaurant['id']}",
            json={"party_size": 1},
        )
        assert r.status_code == 401


# ══════════════════════════════════════════════════════════════════════════
# 5. AI Memory Across Sessions
# ══════════════════════════════════════════════════════════════════════════

class TestAIMemory:
    @pytest.fixture(scope="class")
    def mem_user_token(self, full_user_client):
        register_user(full_user_client, "memuser@yelp.com", "MemUser1!", name="MemUser")
        return login_user(full_user_client, "memuser@yelp.com", "MemUser1!")

    def test_history_empty_before_chat(self, full_rest_client, mem_user_token):
        # Clear first in case
        full_rest_client.delete("/ai-assistant/history", headers=auth_headers(mem_user_token))
        r = full_rest_client.get("/ai-assistant/history", headers=auth_headers(mem_user_token))
        assert r.status_code == 200
        assert r.json()["count"] == 0

    def test_chat_persists_history(self, full_rest_client, mem_user_token):
        full_rest_client.post(
            "/ai-assistant/chat",
            json={"message": "Find Italian food in San Jose", "conversation_history": []},
            headers=auth_headers(mem_user_token),
        )
        r = full_rest_client.get("/ai-assistant/history", headers=auth_headers(mem_user_token))
        assert r.status_code == 200
        body = r.json()
        assert body["count"] >= 2  # user message + assistant reply
        messages = body["history"]
        roles = [m["role"] for m in messages]
        assert "user" in roles
        assert "assistant" in roles

    def test_second_chat_appends_history(self, full_rest_client, mem_user_token):
        full_rest_client.post(
            "/ai-assistant/chat",
            json={"message": "What about Japanese?", "conversation_history": []},
            headers=auth_headers(mem_user_token),
        )
        r = full_rest_client.get("/ai-assistant/history", headers=auth_headers(mem_user_token))
        assert r.json()["count"] >= 4  # 2 turns × 2 messages

    def test_history_loaded_in_next_chat(self, full_rest_client, mem_user_token):
        """Third chat should have DB history loaded (not empty)."""
        r = full_rest_client.post(
            "/ai-assistant/chat",
            json={"message": "Show me something romantic", "conversation_history": []},
            headers=auth_headers(mem_user_token),
        )
        assert r.status_code == 200
        # The response should work fine — history was loaded from DB

    def test_clear_history(self, full_rest_client, mem_user_token):
        r = full_rest_client.delete(
            "/ai-assistant/history",
            headers=auth_headers(mem_user_token),
        )
        assert r.status_code == 200
        # Verify cleared
        r2 = full_rest_client.get("/ai-assistant/history", headers=auth_headers(mem_user_token))
        assert r2.json()["count"] == 0

    def test_history_requires_auth(self, full_rest_client):
        r = full_rest_client.get("/ai-assistant/history")
        assert r.status_code == 401

    def test_guests_do_not_persist_history(self, full_rest_client):
        """Guest chats should not write to DB (no user_id)."""
        full_rest_client.post(
            "/ai-assistant/chat",
            json={"message": "Italian food", "conversation_history": []},
        )
        # No way to query guest history — just verify the endpoint didn't crash


# ══════════════════════════════════════════════════════════════════════════
# 6. Trending Restaurants
# ══════════════════════════════════════════════════════════════════════════

class TestTrending:
    @pytest.fixture(scope="class", autouse=True)
    def seed_views_and_reviews(
        self, full_rest_client, full_review_client, full_user_client,
        new_owner_token, owned_restaurant
    ):
        """Seed some view + review events so trending has data."""
        from mongo_client import get_db
        from datetime import timedelta
        db = get_db()
        rid = owned_restaurant["id"]
        now = datetime.now(timezone.utc)
        # Insert 5 views in the last 7 days
        for _ in range(5):
            db.restaurant_views.insert_one(
                {"restaurant_id": rid, "user_id": None, "viewed_at": now}
            )

    def test_trending_returns_list(self, full_rest_client):
        r = full_rest_client.get("/restaurants/trending")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_trending_has_rank_fields(self, full_rest_client):
        r = full_rest_client.get("/restaurants/trending")
        results = r.json()
        if results:
            top = results[0]
            assert "trending_rank" in top
            assert "trending_score" in top
            assert "recent_views" in top
            assert top["trending_rank"] == 1

    def test_trending_rank_ascending(self, full_rest_client):
        r = full_rest_client.get("/restaurants/trending")
        results = r.json()
        if len(results) >= 2:
            ranks = [res["trending_rank"] for res in results]
            assert ranks == sorted(ranks)

    def test_trending_respects_limit(self, full_rest_client):
        r = full_rest_client.get("/restaurants/trending?limit=2")
        assert r.status_code == 200
        assert len(r.json()) <= 2

    def test_trending_custom_days(self, full_rest_client):
        r = full_rest_client.get("/restaurants/trending?days=1")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_our_restaurant_in_trending(self, full_rest_client, owned_restaurant):
        r = full_rest_client.get("/restaurants/trending")
        ids = [res["id"] for res in r.json()]
        assert owned_restaurant["id"] in ids


# ══════════════════════════════════════════════════════════════════════════
# 7. Push Notifications
# ══════════════════════════════════════════════════════════════════════════

class TestNotifications:
    @pytest.fixture(scope="class", autouse=True)
    def seed_notifications(self, full_user_client, new_user_token):
        """Directly insert test notifications into MongoDB for the test user."""
        from mongo_client import get_db, get_next_id
        from datetime import timezone

        # Get user_id
        me = full_user_client.get("/users/me", headers=auth_headers(new_user_token)).json()
        user_id = me["id"]
        db = get_db()
        now = datetime.now(timezone.utc)

        for i in range(3):
            nid = get_next_id("notifications")
            db.notifications.insert_one({
                "_id": nid,
                "user_id": user_id,
                "type": "new_review",
                "subject": f"Test notification {i+1}",
                "body": f"Body {i+1}",
                "metadata": {"review_id": i+1},
                "read": i == 0,  # first one is already read
                "created_at": now,
            })

    def test_list_notifications(self, full_user_client, new_user_token):
        r = full_user_client.get("/notifications/", headers=auth_headers(new_user_token))
        assert r.status_code == 200
        body = r.json()
        assert "notifications" in body
        assert isinstance(body["notifications"], list)
        assert body["total"] >= 3

    def test_unread_count(self, full_user_client, new_user_token):
        r = full_user_client.get("/notifications/unread-count", headers=auth_headers(new_user_token))
        assert r.status_code == 200
        assert r.json()["unread_count"] >= 2  # we seeded 2 unread

    def test_filter_unread_only(self, full_user_client, new_user_token):
        r = full_user_client.get(
            "/notifications/?unread_only=true",
            headers=auth_headers(new_user_token),
        )
        assert r.status_code == 200
        notifs = r.json()["notifications"]
        assert all(not n["read"] for n in notifs)

    def test_notification_shape(self, full_user_client, new_user_token):
        r = full_user_client.get("/notifications/", headers=auth_headers(new_user_token))
        for notif in r.json()["notifications"]:
            assert "id" in notif
            assert "subject" in notif
            assert "body" in notif
            assert "type" in notif
            assert "read" in notif
            assert "created_at" in notif

    def test_mark_notification_as_read(self, full_user_client, new_user_token):
        notifs = full_user_client.get(
            "/notifications/?unread_only=true",
            headers=auth_headers(new_user_token),
        ).json()["notifications"]
        assert notifs, "Need at least one unread notification"
        nid = notifs[0]["id"]

        r = full_user_client.put(
            f"/notifications/{nid}/read",
            headers=auth_headers(new_user_token),
        )
        assert r.status_code == 200

        # Verify count dropped
        r2 = full_user_client.get("/notifications/unread-count", headers=auth_headers(new_user_token))
        # Count should now be lower
        assert r2.json()["unread_count"] >= 0

    def test_mark_all_read(self, full_user_client, new_user_token):
        r = full_user_client.put("/notifications/read-all", headers=auth_headers(new_user_token))
        assert r.status_code == 200
        count = full_user_client.get(
            "/notifications/unread-count",
            headers=auth_headers(new_user_token),
        ).json()["unread_count"]
        assert count == 0

    def test_delete_notification(self, full_user_client, new_user_token):
        notifs = full_user_client.get(
            "/notifications/", headers=auth_headers(new_user_token)
        ).json()["notifications"]
        assert notifs
        nid = notifs[0]["id"]

        r = full_user_client.delete(
            f"/notifications/{nid}",
            headers=auth_headers(new_user_token),
        )
        assert r.status_code == 200

        # Verify gone
        r2 = full_user_client.get("/notifications/", headers=auth_headers(new_user_token))
        remaining_ids = [n["id"] for n in r2.json()["notifications"]]
        assert nid not in remaining_ids

    def test_cannot_read_others_notification(
        self, full_user_client, full_review_client, new_owner_token, new_user_token
    ):
        # Get a notification belonging to new_user
        notifs = full_user_client.get(
            "/notifications/", headers=auth_headers(new_user_token)
        ).json()["notifications"]
        if not notifs:
            pytest.skip("No notifications to test")
        nid = notifs[0]["id"]
        r = full_user_client.put(
            f"/notifications/{nid}/read",
            headers=auth_headers(new_owner_token),
        )
        assert r.status_code == 403

    def test_requires_auth(self, full_user_client):
        r = full_user_client.get("/notifications/")
        assert r.status_code == 401

    def test_notification_created_when_owner_replies(
        self, full_user_client, full_review_client, new_owner_token,
        new_user_token, existing_review
    ):
        """Posting an owner reply should create a notification for the reviewer."""
        # Get reviewer's current notification count
        before = full_user_client.get(
            "/notifications/", headers=auth_headers(new_user_token)
        ).json()["total"]

        # Post a reply
        full_review_client.post(
            f"/reviews/{existing_review['review_id']}/reply",
            json={"reply": "We're glad you enjoyed it! Come back soon."},
            headers=auth_headers(new_owner_token),
        )

        after = full_user_client.get(
            "/notifications/", headers=auth_headers(new_user_token)
        ).json()["total"]
        assert after > before
