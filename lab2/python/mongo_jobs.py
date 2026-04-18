"""MongoDB job status for async review processing (Kafka worker)."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Optional

from pymongo import MongoClient

_client: Optional[MongoClient] = None


def _get_db():
    url = os.getenv("MONGODB_URL", "").strip()
    if not url:
        return None
    global _client
    if _client is None:
        _client = MongoClient(url, serverSelectionTimeoutMS=5000)
    return _client.get_database(os.getenv("MONGODB_DB_NAME", "yelp_lab2"))


def create_job(job_id: str, topic: str, payload: dict[str, Any]) -> None:
    db = _get_db()
    if db is None:
        return
    db.review_jobs.insert_one(
        {
            "job_id": job_id,
            "topic": topic,
            "status": "queued",
            "payload": payload,
            "review_id": None,
            "error": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
    )


def mark_done(job_id: str, review_id: int) -> None:
    db = _get_db()
    if db is None:
        return
    db.review_jobs.update_one(
        {"job_id": job_id},
        {
            "$set": {
                "status": "completed",
                "review_id": review_id,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )


def mark_error(job_id: str, message: str) -> None:
    db = _get_db()
    if db is None:
        return
    db.review_jobs.update_one(
        {"job_id": job_id},
        {
            "$set": {
                "status": "error",
                "error": message[:2000],
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )


def get_job(job_id: str) -> Optional[dict[str, Any]]:
    db = _get_db()
    if db is None:
        return None
    doc = db.review_jobs.find_one({"job_id": job_id})
    if not doc:
        return None
    doc.pop("_id", None)
    return doc
