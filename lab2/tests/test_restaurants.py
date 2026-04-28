"""
Tests for /restaurants/ CRUD, search, claim, and permissions.
"""
import pytest
from conftest import auth_headers


class TestCreateRestaurant:
    def test_create_restaurant_success(self, restaurant_client, owner_token):
        r = restaurant_client.post(
            "/restaurants/",
            json={
                "name": "Mario's Pizza",
                "cuisine_type": "Italian",
                "city": "San Francisco",
                "state": "CA",
                "price_range": "$",
                "description": "Authentic Neapolitan pizza",
            },
            headers=auth_headers(owner_token),
        )
        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "Mario's Pizza"
        assert body["cuisine_type"] == "Italian"
        assert body["average_rating"] == 0.0
        assert body["review_count"] == 0
        assert isinstance(body["id"], int)

    def test_create_restaurant_requires_auth(self, restaurant_client):
        r = restaurant_client.post("/restaurants/", json={"name": "Ghost"})
        assert r.status_code == 401

    def test_create_restaurant_missing_name(self, restaurant_client, owner_token):
        r = restaurant_client.post(
            "/restaurants/",
            json={"cuisine_type": "Thai"},
            headers=auth_headers(owner_token),
        )
        assert r.status_code == 422


class TestGetRestaurant:
    def test_get_restaurant_by_id(self, restaurant_client, seeded_restaurant):
        rid = seeded_restaurant["id"]
        r = restaurant_client.get(f"/restaurants/{rid}")
        assert r.status_code == 200
        assert r.json()["id"] == rid
        assert r.json()["name"] == "Test Bistro"

    def test_get_nonexistent_restaurant(self, restaurant_client):
        r = restaurant_client.get("/restaurants/99999")
        assert r.status_code == 404


class TestSearchRestaurants:
    def test_search_all(self, restaurant_client, seeded_restaurant):
        r = restaurant_client.get("/restaurants/")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 1

    def test_search_by_cuisine(self, restaurant_client, seeded_restaurant):
        r = restaurant_client.get("/restaurants/?cuisine_type=Italian")
        assert r.status_code == 200
        results = r.json()
        assert any(rest["cuisine_type"] and "italian" in rest["cuisine_type"].lower()
                   for rest in results)

    def test_search_by_city(self, restaurant_client, seeded_restaurant):
        r = restaurant_client.get("/restaurants/?city=San Jose")
        assert r.status_code == 200
        results = r.json()
        assert any("san jose" in (rest.get("city") or "").lower() for rest in results)

    def test_search_by_name(self, restaurant_client, seeded_restaurant):
        r = restaurant_client.get("/restaurants/?name=Bistro")
        assert r.status_code == 200
        results = r.json()
        assert any("bistro" in (rest["name"] or "").lower() for rest in results)

    def test_search_by_price_range(self, restaurant_client, seeded_restaurant):
        r = restaurant_client.get("/restaurants/?price_range=$$")
        assert r.status_code == 200

    def test_search_pagination(self, restaurant_client, seeded_restaurant):
        r = restaurant_client.get("/restaurants/?page=1&limit=1")
        assert r.status_code == 200
        assert len(r.json()) <= 1

    def test_search_no_results(self, restaurant_client):
        r = restaurant_client.get("/restaurants/?name=xyznonexistentxyz99")
        assert r.status_code == 200
        assert r.json() == []

    def test_search_by_keyword(self, restaurant_client, seeded_restaurant):
        r = restaurant_client.get("/restaurants/?keyword=vegetarian")
        assert r.status_code == 200


class TestUpdateRestaurant:
    def test_owner_can_update(self, restaurant_client, owner_token, seeded_restaurant):
        rid = seeded_restaurant["id"]
        r = restaurant_client.put(
            f"/restaurants/{rid}",
            json={"description": "Updated description"},
            headers=auth_headers(owner_token),
        )
        assert r.status_code == 200
        assert r.json()["description"] == "Updated description"

    def test_other_user_cannot_update(self, restaurant_client, user_token, seeded_restaurant):
        rid = seeded_restaurant["id"]
        r = restaurant_client.put(
            f"/restaurants/{rid}",
            json={"name": "Hacked Name"},
            headers=auth_headers(user_token),
        )
        assert r.status_code == 403

    def test_update_requires_auth(self, restaurant_client, seeded_restaurant):
        r = restaurant_client.put(f"/restaurants/{seeded_restaurant['id']}", json={"name": "x"})
        assert r.status_code == 401


class TestClaimRestaurant:
    def test_user_cannot_claim(self, restaurant_client, user_token, seeded_restaurant):
        r = restaurant_client.post(
            f"/restaurants/{seeded_restaurant['id']}/claim",
            headers=auth_headers(user_token),
        )
        assert r.status_code == 403

    def test_claim_unclaimed_restaurant(self, restaurant_client, owner_token):
        # create an unclaimed restaurant without owner
        from mongo_client import get_db, get_next_id
        from datetime import datetime, timezone
        db = get_db()
        rid = get_next_id("restaurants")
        db.restaurants.insert_one({
            "_id": rid, "name": "Unclaimed Spot", "is_claimed": False,
            "owner_id": None, "average_rating": 0.0, "review_count": 0,
            "photos": [], "created_at": datetime.now(timezone.utc),
        })

        r = restaurant_client.post(
            f"/restaurants/{rid}/claim",
            headers=auth_headers(owner_token),
        )
        assert r.status_code == 200
        assert r.json()["is_claimed"] is True

    def test_cannot_claim_already_claimed(self, restaurant_client, owner_token):
        # Create + immediately claim a restaurant, then try to claim again
        from mongo_client import get_db, get_next_id
        from datetime import datetime, timezone
        db = get_db()
        rid = get_next_id("restaurants")
        db.restaurants.insert_one({
            "_id": rid, "name": "Already Claimed", "is_claimed": True,
            "owner_id": 999, "average_rating": 0.0, "review_count": 0,
            "photos": [], "created_at": datetime.now(timezone.utc),
        })
        r = restaurant_client.post(
            f"/restaurants/{rid}/claim",
            headers=auth_headers(owner_token),
        )
        assert r.status_code == 400


class TestMyRestaurants:
    def test_owner_sees_own_restaurants(self, restaurant_client, owner_token, seeded_restaurant):
        r = restaurant_client.get(
            "/restaurants/owner/my-restaurants",
            headers=auth_headers(owner_token),
        )
        assert r.status_code == 200
        ids = [rest["id"] for rest in r.json()]
        assert seeded_restaurant["id"] in ids

    def test_requires_auth(self, restaurant_client):
        r = restaurant_client.get("/restaurants/owner/my-restaurants")
        assert r.status_code == 401
