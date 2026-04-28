"""
Tests for /reviews/ — async Kafka path is synchronously stubbed in conftest.

Covers: create, update, delete, job polling, listing, validation, permissions.
"""
import time
import pytest
from conftest import auth_headers, register_user, login_user


@pytest.fixture(scope="module")
def second_user_token(user_client):
    register_user(user_client, "reviewer2@yelp.com", "Rev12345!", name="Greg")
    return login_user(user_client, "reviewer2@yelp.com", "Rev12345!")


class TestCreateReview:
    def test_create_review_returns_202(self, review_client, user_token, seeded_restaurant):
        r = review_client.post(
            "/reviews/",
            json={"restaurant_id": seeded_restaurant["id"], "rating": 5, "comment": "Amazing food!"},
            headers=auth_headers(user_token),
        )
        assert r.status_code == 202
        body = r.json()
        assert body["status"] == "accepted"
        assert "job_id" in body

    def test_create_review_updates_restaurant_rating(
        self, review_client, restaurant_client, seeded_restaurant
    ):
        # Give the stub a moment (sync stub writes immediately)
        rest = restaurant_client.get(f"/restaurants/{seeded_restaurant['id']}").json()
        assert rest["average_rating"] > 0
        assert rest["review_count"] >= 1

    def test_duplicate_review_rejected(self, review_client, user_token, seeded_restaurant):
        r = review_client.post(
            "/reviews/",
            json={"restaurant_id": seeded_restaurant["id"], "rating": 4, "comment": "Again"},
            headers=auth_headers(user_token),
        )
        assert r.status_code == 400
        assert "already reviewed" in r.json()["detail"].lower()

    def test_create_requires_auth(self, review_client, seeded_restaurant):
        r = review_client.post(
            "/reviews/",
            json={"restaurant_id": seeded_restaurant["id"], "rating": 3},
        )
        assert r.status_code == 401

    def test_rating_must_be_1_to_5(self, review_client, second_user_token, seeded_restaurant):
        for bad_rating in [0, 6, -1]:
            r = review_client.post(
                "/reviews/",
                json={"restaurant_id": seeded_restaurant["id"], "rating": bad_rating},
                headers=auth_headers(second_user_token),
            )
            assert r.status_code == 422, f"Expected 422 for rating={bad_rating}"

    def test_nonexistent_restaurant_returns_404(self, review_client, user_token):
        r = review_client.post(
            "/reviews/",
            json={"restaurant_id": 999999, "rating": 3},
            headers=auth_headers(user_token),
        )
        assert r.status_code == 404


class TestJobPolling:
    def test_job_status_done_after_create(self, review_client, second_user_token, seeded_restaurant):
        r = review_client.post(
            "/reviews/",
            json={"restaurant_id": seeded_restaurant["id"], "rating": 4, "comment": "Good place"},
            headers=auth_headers(second_user_token),
        )
        assert r.status_code == 202
        job_id = r.json()["job_id"]

        status_r = review_client.get(f"/reviews/job/{job_id}")
        assert status_r.status_code == 200
        assert status_r.json()["status"] == "done"
        assert status_r.json()["review_id"] is not None

    def test_unknown_job_returns_404(self, review_client):
        r = review_client.get("/reviews/job/nonexistent-uuid-1234")
        assert r.status_code == 404


class TestListReviews:
    def test_get_restaurant_reviews(self, review_client, seeded_restaurant):
        r = review_client.get(f"/reviews/restaurant/{seeded_restaurant['id']}")
        assert r.status_code == 200
        results = r.json()
        assert isinstance(results, list)
        assert len(results) >= 1
        for rev in results:
            assert rev["restaurant_id"] == seeded_restaurant["id"]
            assert "rating" in rev
            assert "user_name" in rev

    def test_get_recent_reviews(self, review_client):
        r = review_client.get("/reviews/recent")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_my_reviews(self, review_client, user_token):
        r = review_client.get("/reviews/my-reviews", headers=auth_headers(user_token))
        assert r.status_code == 200
        results = r.json()
        assert isinstance(results, list)
        assert len(results) >= 1

    def test_my_reviews_requires_auth(self, review_client):
        r = review_client.get("/reviews/my-reviews")
        assert r.status_code == 401


class TestUpdateReview:
    @pytest.fixture(scope="class")
    def review_to_edit(self, review_client, second_user_token, restaurant_client, owner_token):
        # Create a fresh restaurant for editing tests
        rest = restaurant_client.post(
            "/restaurants/",
            json={"name": "Edit Test Restaurant", "cuisine_type": "Mexican", "city": "Oakland"},
            headers=auth_headers(owner_token),
        ).json()
        r = review_client.post(
            "/reviews/",
            json={"restaurant_id": rest["id"], "rating": 3, "comment": "Okay"},
            headers=auth_headers(second_user_token),
        )
        assert r.status_code == 202
        # get the review ID from job
        job_id = r.json()["job_id"]
        status = review_client.get(f"/reviews/job/{job_id}").json()
        return {"review_id": status["review_id"], "restaurant_id": rest["id"]}

    def test_update_rating(self, review_client, second_user_token, review_to_edit):
        r = review_client.put(
            f"/reviews/{review_to_edit['review_id']}",
            json={"rating": 5, "comment": "Changed my mind, great!"},
            headers=auth_headers(second_user_token),
        )
        assert r.status_code == 202

    def test_other_user_cannot_update(self, review_client, user_token, review_to_edit):
        r = review_client.put(
            f"/reviews/{review_to_edit['review_id']}",
            json={"rating": 1},
            headers=auth_headers(user_token),
        )
        assert r.status_code == 403

    def test_update_nonexistent_review(self, review_client, second_user_token):
        r = review_client.put(
            "/reviews/999999",
            json={"rating": 4},
            headers=auth_headers(second_user_token),
        )
        assert r.status_code == 404


class TestDeleteReview:
    @pytest.fixture(scope="class")
    def review_to_delete(self, review_client, user_client, restaurant_client, owner_token):
        register_user(user_client, "deleter@yelp.com", "Del12345!", name="Deleter")
        token = login_user(user_client, "deleter@yelp.com", "Del12345!")

        rest = restaurant_client.post(
            "/restaurants/",
            json={"name": "Delete Test Resto", "cuisine_type": "Thai"},
            headers=auth_headers(owner_token),
        ).json()

        r = review_client.post(
            "/reviews/",
            json={"restaurant_id": rest["id"], "rating": 2},
            headers=auth_headers(token),
        )
        assert r.status_code == 202
        job_id = r.json()["job_id"]
        status = review_client.get(f"/reviews/job/{job_id}").json()
        return {"review_id": status["review_id"], "token": token}

    def test_other_user_cannot_delete(self, review_client, user_token, review_to_delete):
        r = review_client.delete(
            f"/reviews/{review_to_delete['review_id']}",
            headers=auth_headers(user_token),
        )
        assert r.status_code == 403

    def test_owner_can_delete(self, review_client, review_to_delete):
        r = review_client.delete(
            f"/reviews/{review_to_delete['review_id']}",
            headers=auth_headers(review_to_delete["token"]),
        )
        assert r.status_code == 202

    def test_delete_nonexistent(self, review_client, user_token):
        r = review_client.delete("/reviews/999999", headers=auth_headers(user_token))
        assert r.status_code == 404
