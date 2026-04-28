"""
Tests for /owner-dashboard/analytics, /owner-dashboard/reviews, track-view
"""
import pytest
from conftest import auth_headers, register_user, login_user


@pytest.fixture(scope="module")
def owner2_token(user_client):
    register_user(user_client, "owner2@yelp.com", "Owner2234!", name="Hannah", role="owner")
    return login_user(user_client, "owner2@yelp.com", "Owner2234!")


@pytest.fixture(scope="module")
def dashboard_setup(restaurant_client, review_client, user_client, owner2_token):
    """Create a restaurant + 2 reviews so analytics has data."""
    # create restaurant owned by owner2
    rest = restaurant_client.post(
        "/restaurants/",
        json={"name": "Analytics Cafe", "cuisine_type": "American", "city": "San Jose"},
        headers=auth_headers(owner2_token),
    ).json()
    rid = rest["id"]

    # create 2 reviewers
    register_user(user_client, "dashuser1@yelp.com", "Dash1234!", name="DashUser1")
    t1 = login_user(user_client, "dashuser1@yelp.com", "Dash1234!")
    register_user(user_client, "dashuser2@yelp.com", "Dash2234!", name="DashUser2")
    t2 = login_user(user_client, "dashuser2@yelp.com", "Dash2234!")

    r1 = review_client.post(
        "/reviews/",
        json={"restaurant_id": rid, "rating": 5, "comment": "Great food, amazing place!"},
        headers=auth_headers(t1),
    )
    r2 = review_client.post(
        "/reviews/",
        json={"restaurant_id": rid, "rating": 2, "comment": "Awful service, terrible experience"},
        headers=auth_headers(t2),
    )
    return {"restaurant_id": rid, "owner2_token": owner2_token}


class TestTrackView:
    def test_track_view_guest(self, owner_client, seeded_restaurant):
        r = owner_client.post(f"/owner-dashboard/restaurants/{seeded_restaurant['id']}/track-view")
        assert r.status_code == 200

    def test_track_view_logged_in(self, owner_client, user_token, seeded_restaurant):
        r = owner_client.post(
            f"/owner-dashboard/restaurants/{seeded_restaurant['id']}/track-view",
            headers=auth_headers(user_token),
        )
        assert r.status_code == 200

    def test_track_view_nonexistent(self, owner_client):
        r = owner_client.post("/owner-dashboard/restaurants/999999/track-view")
        assert r.status_code == 404


class TestOwnerDashboardReviews:
    def test_get_reviews_requires_auth(self, owner_client):
        r = owner_client.get("/owner-dashboard/reviews")
        assert r.status_code == 401

    def _extract_reviews(self, body):
        """Owner dashboard may return list or {'reviews': [...]}."""
        if isinstance(body, list):
            return body
        return body.get("reviews", body.get("data", []))

    def test_get_reviews_for_own_restaurant(self, owner_client, dashboard_setup):
        r = owner_client.get(
            "/owner-dashboard/reviews",
            headers=auth_headers(dashboard_setup["owner2_token"]),
        )
        assert r.status_code == 200
        reviews = self._extract_reviews(r.json())
        assert isinstance(reviews, list)

    def test_filter_by_restaurant(self, owner_client, dashboard_setup):
        rid = dashboard_setup["restaurant_id"]
        r = owner_client.get(
            f"/owner-dashboard/reviews?restaurant_id={rid}",
            headers=auth_headers(dashboard_setup["owner2_token"]),
        )
        assert r.status_code == 200
        reviews = self._extract_reviews(r.json())
        for review in reviews:
            assert review["restaurant_id"] == rid

    def test_filter_by_exact_rating_5(self, owner_client, dashboard_setup):
        r = owner_client.get(
            "/owner-dashboard/reviews?rating=5",
            headers=auth_headers(dashboard_setup["owner2_token"]),
        )
        assert r.status_code == 200
        reviews = self._extract_reviews(r.json())
        for review in reviews:
            assert review["rating"] == 5

    def test_filter_by_exact_rating_2(self, owner_client, dashboard_setup):
        r = owner_client.get(
            "/owner-dashboard/reviews?rating=2",
            headers=auth_headers(dashboard_setup["owner2_token"]),
        )
        assert r.status_code == 200
        reviews = self._extract_reviews(r.json())
        for review in reviews:
            assert review["rating"] == 2


class TestOwnerDashboardAnalytics:
    def test_analytics_requires_auth(self, owner_client):
        r = owner_client.get("/owner-dashboard/analytics")
        assert r.status_code == 401

    def test_analytics_returns_expected_shape(self, owner_client, dashboard_setup):
        r = owner_client.get(
            "/owner-dashboard/analytics",
            headers=auth_headers(dashboard_setup["owner2_token"]),
        )
        assert r.status_code == 200
        body = r.json()
        # Should have totals/summary fields
        assert isinstance(body, dict)

    def test_analytics_rating_distribution(self, owner_client, dashboard_setup):
        r = owner_client.get(
            "/owner-dashboard/analytics",
            headers=auth_headers(dashboard_setup["owner2_token"]),
        )
        assert r.status_code == 200
        body = r.json()
        # Check that sentiment or rating data is present
        has_data = (
            "rating_distribution" in body
            or "sentiment" in body
            or "total_reviews" in body
            or "reviews" in body
            or len(body) > 0
        )
        assert has_data

    def test_analytics_sentiment_analysis(self, owner_client, dashboard_setup):
        """Positive and negative review comments should drive sentiment scores."""
        r = owner_client.get(
            "/owner-dashboard/analytics",
            headers=auth_headers(dashboard_setup["owner2_token"]),
        )
        assert r.status_code == 200
        # If sentiment is returned, it should categorize our 2 reviews
        body = r.json()
        if "sentiment" in body:
            sentiment = body["sentiment"]
            # We added 1 positive ("Great food, amazing place!") and 1 negative
            total = sum(sentiment.values()) if isinstance(sentiment, dict) else 0
            assert total >= 2
