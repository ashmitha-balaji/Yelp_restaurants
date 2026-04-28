"""
Tests for POST /auth/signup, /auth/login, /auth/token
"""
import pytest
from conftest import auth_headers, register_user, login_user


class TestSignup:
    def test_signup_success(self, user_client):
        r = user_client.post("/auth/signup", json={
            "name": "Charlie",
            "email": "charlie@yelp.com",
            "password": "Charlie1!",
            "role": "user",
        })
        assert r.status_code == 201
        body = r.json()
        assert "access_token" in body
        assert body["user"]["email"] == "charlie@yelp.com"
        assert body["user"]["role"] == "user"
        assert "password" not in body["user"]
        assert "password_hash" not in body["user"]

    def test_signup_owner_role(self, user_client):
        r = user_client.post("/auth/signup", json={
            "name": "Dana Owner",
            "email": "dana@yelp.com",
            "password": "Dana1234!",
            "role": "owner",
        })
        assert r.status_code == 201
        assert r.json()["user"]["role"] == "owner"

    def test_signup_duplicate_email(self, user_client):
        payload = {"name": "Dup", "email": "dup@yelp.com", "password": "Dup12345!", "role": "user"}
        user_client.post("/auth/signup", json=payload)
        r = user_client.post("/auth/signup", json=payload)
        assert r.status_code == 400
        assert "already registered" in r.json()["detail"].lower()

    def test_signup_invalid_role(self, user_client):
        r = user_client.post("/auth/signup", json={
            "name": "Bad", "email": "bad@yelp.com", "password": "Bad1234!", "role": "admin"
        })
        assert r.status_code == 400

    def test_signup_invalid_email(self, user_client):
        r = user_client.post("/auth/signup", json={
            "name": "Bad", "email": "not-an-email", "password": "Bad1234!", "role": "user"
        })
        assert r.status_code == 422


class TestLogin:
    def test_login_success(self, user_client):
        user_client.post("/auth/signup", json={
            "name": "Eve", "email": "eve@yelp.com", "password": "Eve12345!", "role": "user"
        })
        r = user_client.post("/auth/login", json={"email": "eve@yelp.com", "password": "Eve12345!"})
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["user"]["email"] == "eve@yelp.com"

    def test_login_wrong_password(self, user_client):
        r = user_client.post("/auth/login", json={"email": "eve@yelp.com", "password": "WRONG"})
        assert r.status_code == 401

    def test_login_unknown_email(self, user_client):
        r = user_client.post("/auth/login", json={"email": "nobody@yelp.com", "password": "x"})
        assert r.status_code == 401

    def test_login_returns_jwt(self, user_client):
        """Token has 3 dot-separated base64 parts (header.payload.sig)."""
        r = user_client.post("/auth/login", json={"email": "eve@yelp.com", "password": "Eve12345!"})
        token = r.json()["access_token"]
        assert len(token.split(".")) == 3


class TestTokenEndpoint:
    def test_oauth2_token_endpoint(self, user_client):
        """Swagger /auth/token endpoint uses form data with username=email."""
        user_client.post("/auth/signup", json={
            "name": "Frank", "email": "frank@yelp.com", "password": "Frank123!", "role": "user"
        })
        r = user_client.post(
            "/auth/token",
            data={"username": "frank@yelp.com", "password": "Frank123!"},
        )
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_protected_endpoint_without_token(self, user_client):
        r = user_client.get("/users/me")
        assert r.status_code == 401

    def test_protected_endpoint_with_bad_token(self, user_client):
        r = user_client.get("/users/me", headers={"Authorization": "Bearer badtoken"})
        assert r.status_code == 401
