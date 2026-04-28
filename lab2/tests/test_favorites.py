"""
Tests for /favorites/ — add, list, remove.
"""
from conftest import auth_headers


class TestFavorites:
    def test_add_favorite(self, user_client, user_token, seeded_restaurant):
        r = user_client.post(
            "/favorites/",
            json={"restaurant_id": seeded_restaurant["id"]},
            headers=auth_headers(user_token),
        )
        assert r.status_code in (200, 201)

    def test_list_favorites(self, user_client, user_token, seeded_restaurant):
        r = user_client.get("/favorites/", headers=auth_headers(user_token))
        assert r.status_code == 200
        ids = [f["restaurant_id"] for f in r.json()]
        assert seeded_restaurant["id"] in ids

    def test_add_duplicate_favorite(self, user_client, user_token, seeded_restaurant):
        # Adding same restaurant twice should not crash
        r = user_client.post(
            "/favorites/",
            json={"restaurant_id": seeded_restaurant["id"]},
            headers=auth_headers(user_token),
        )
        assert r.status_code in (200, 201, 400)

    def test_remove_favorite(self, user_client, user_token, seeded_restaurant):
        r = user_client.delete(
            f"/favorites/{seeded_restaurant['id']}",
            headers=auth_headers(user_token),
        )
        assert r.status_code in (200, 204)
        # Verify removed
        r2 = user_client.get("/favorites/", headers=auth_headers(user_token))
        ids = [f["restaurant_id"] for f in r2.json()]
        assert seeded_restaurant["id"] not in ids

    def test_requires_auth(self, user_client):
        r = user_client.get("/favorites/")
        assert r.status_code == 401
