"""
Shared pytest fixtures for Lab 2 microservice tests.

How it works
------------
Each test module gets a FastAPI TestClient wired to an in-process app
instance backed by a real (local) MongoDB test database that is wiped
before every test session.  Kafka calls are monkey-patched so reviews
are written directly to MongoDB and job status is immediately set to
"done" — no real Kafka broker required.

Prerequisites
-------------
    pip install pytest pytest-httpx httpx mongomock pymongo pydantic[email] passlib[bcrypt] python-jose

Run from the repo root:
    cd assignment_solutions/lab-1
    MONGODB_URL=mongodb://localhost:27017 \
    MONGODB_DB_NAME=yelp_test \
    SECRET_KEY=testsecret \
    pytest lab2/tests/ -v
"""

from __future__ import annotations

import os
import sys
import types
from datetime import datetime, timezone
from typing import Generator

import pytest
from fastapi.testclient import TestClient

# ── path setup ─────────────────────────────────────────────────────────────
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_LAB2 = os.path.join(_ROOT, "lab2")
_LAB2_PY = os.path.join(_LAB2, "python")
_BACKEND = os.path.join(_ROOT, "backend")
for p in (_LAB2, _LAB2_PY, _BACKEND, _ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

# ── force test env vars BEFORE any app import ──────────────────────────────
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB_NAME", "yelp_test")
os.environ.setdefault("SECRET_KEY", "testsecret1234567890")
os.environ.setdefault("APP_ROOT", _ROOT)

# ── stub out Kafka so tests run without a broker ───────────────────────────
def _make_kafka_stub():
    """Return a module stub that synchronously writes to MongoDB instead of Kafka."""
    stub = types.ModuleType("kafka_client")

    def publish_review_event(topic: str, payload: dict):
        from mongo_client import get_db
        db = get_db()
        action = payload.get("action")
        job_id = payload.get("job_id")

        if action == "create":
            from mongo_client import get_next_id
            review_id = get_next_id("reviews")
            doc = {
                "_id": review_id,
                "user_id": payload["user_id"],
                "restaurant_id": payload["restaurant_id"],
                "rating": payload["rating"],
                "comment": payload.get("comment"),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            db.reviews.insert_one(doc)
            # update restaurant averages
            reviews = list(db.reviews.find({"restaurant_id": payload["restaurant_id"]}))
            avg = sum(r["rating"] for r in reviews) / len(reviews)
            db.restaurants.update_one(
                {"_id": payload["restaurant_id"]},
                {"$set": {"average_rating": round(avg, 2), "review_count": len(reviews)}},
            )
            if job_id:
                db.review_jobs.update_one(
                    {"job_id": job_id},
                    {"$set": {"status": "done", "review_id": review_id}},
                    upsert=True,
                )

        elif action == "update":
            updates = {}
            if "rating" in payload:
                updates["rating"] = payload["rating"]
            if "comment" in payload:
                updates["comment"] = payload["comment"]
            updates["updated_at"] = datetime.now(timezone.utc)
            db.reviews.update_one({"_id": payload["review_id"]}, {"$set": updates})
            if job_id:
                db.review_jobs.update_one(
                    {"job_id": job_id},
                    {"$set": {"status": "done", "review_id": payload["review_id"]}},
                    upsert=True,
                )

        elif action == "delete":
            db.reviews.delete_one({"_id": payload["review_id"]})
            if job_id:
                db.review_jobs.update_one(
                    {"job_id": job_id},
                    {"$set": {"status": "done"}},
                    upsert=True,
                )

    def publish_restaurant_event(topic: str, payload: dict):
        pass  # no-op for tests

    stub.publish_review_event = publish_review_event
    stub.publish_restaurant_event = publish_restaurant_event
    return stub


sys.modules.setdefault("kafka_client", _make_kafka_stub())

# stub mongo_jobs so job status queries work
def _make_jobs_stub():
    stub = types.ModuleType("mongo_jobs")

    def create_job(job_id: str, topic: str, payload: dict):
        from mongo_client import get_db
        get_db().review_jobs.update_one(
            {"job_id": job_id},
            {"$setOnInsert": {"job_id": job_id, "status": "pending", "topic": topic}},
            upsert=True,
        )

    def get_job(job_id: str):
        from mongo_client import get_db
        return get_db().review_jobs.find_one({"job_id": job_id})

    stub.create_job = create_job
    stub.get_job = get_job
    return stub


sys.modules.setdefault("mongo_jobs", _make_jobs_stub())


# ── DB helpers ─────────────────────────────────────────────────────────────
def _wipe_db():
    from mongo_client import get_db
    db = get_db()
    for coll in db.list_collection_names():
        db.drop_collection(coll)


# ── App factories ───────────────────────────────────────────────────────────
def _make_user_app():
    import importlib, sys
    # reload to pick up fresh DB connection
    for mod in list(sys.modules.keys()):
        if mod.startswith("mongo_routers") or mod in ("mongo_client", "mongo_auth"):
            pass  # keep imported — they read env vars at import time
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from mongo_routers import auth, users, favorites, history

    app = FastAPI()
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(favorites.router)
    app.include_router(history.router)
    return app


def _make_restaurant_app():
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from mongo_routers import restaurants, ai_assistant

    app = FastAPI()
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    app.include_router(restaurants.router)
    app.include_router(ai_assistant.router)
    return app


def _make_review_app():
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from mongo_routers import reviews_async

    app = FastAPI()
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    app.include_router(reviews_async.router)
    return app


def _make_owner_app():
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from mongo_routers import owner_dashboard

    app = FastAPI()
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    app.include_router(owner_dashboard.router)
    return app


# ── Session-scoped clients ──────────────────────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
def clean_db():
    _wipe_db()
    yield
    _wipe_db()


@pytest.fixture(scope="session")
def user_client() -> TestClient:
    return TestClient(_make_user_app())


@pytest.fixture(scope="session")
def restaurant_client() -> TestClient:
    return TestClient(_make_restaurant_app())


@pytest.fixture(scope="session")
def review_client() -> TestClient:
    return TestClient(_make_review_app())


@pytest.fixture(scope="session")
def owner_client() -> TestClient:
    return TestClient(_make_owner_app())


# ── Convenience: register + login helpers ──────────────────────────────────
def register_user(client: TestClient, email: str, password: str,
                  name: str = "Test User", role: str = "user") -> dict:
    r = client.post("/auth/signup", json={
        "name": name, "email": email, "password": password, "role": role
    })
    assert r.status_code == 201, r.text
    return r.json()


def login_user(client: TestClient, email: str, password: str) -> str:
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Session-wide fixtures: one user, one owner, one restaurant ──────────────
@pytest.fixture(scope="session")
def user_token(user_client) -> str:
    register_user(user_client, "testuser@yelp.com", "Test1234!", name="Alice")
    return login_user(user_client, "testuser@yelp.com", "Test1234!")


@pytest.fixture(scope="session")
def owner_token(user_client) -> str:
    register_user(user_client, "owner@yelp.com", "Owner1234!", name="Bob", role="owner")
    return login_user(user_client, "owner@yelp.com", "Owner1234!")


@pytest.fixture(scope="session")
def seeded_restaurant(restaurant_client, owner_token) -> dict:
    r = restaurant_client.post(
        "/restaurants/",
        json={
            "name": "Test Bistro",
            "cuisine_type": "Italian",
            "city": "San Jose",
            "state": "CA",
            "zip_code": "95101",
            "price_range": "$$",
            "description": "A cozy italian bistro with vegetarian options and romantic ambiance",
        },
        headers=auth_headers(owner_token),
    )
    assert r.status_code == 201, r.text
    return r.json()
