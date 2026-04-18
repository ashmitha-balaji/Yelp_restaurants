"""Kafka consumer: persist review.created / review.updated / review.deleted to MongoDB (Lab 2)."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

_ROOT = os.environ.get("APP_ROOT") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_LAB2 = os.path.join(_ROOT, "lab2")
_LAB2_PY = os.path.join(_LAB2, "python")
_BACKEND = os.path.join(_ROOT, "backend")
for p in (_LAB2, _LAB2_PY, _BACKEND):
    if p not in sys.path:
        sys.path.insert(0, p)

from kafka import KafkaConsumer

from mongo_client import get_db, get_next_id

try:
    from mongo_jobs import mark_done, mark_error
except ImportError:
    def mark_done(jid, rid):
        pass
    def mark_error(jid, msg):
        pass


def _recalculate_rating(db, restaurant_id: int) -> None:
    pipeline = [
        {"$match": {"restaurant_id": restaurant_id}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}},
    ]
    result = list(db.reviews.aggregate(pipeline))
    avg = round(result[0]["avg"], 2) if result else 0.0
    count = result[0]["count"] if result else 0
    db.restaurants.update_one(
        {"_id": restaurant_id},
        {"$set": {"average_rating": avg, "review_count": count}},
    )


def handle_create(db, payload: dict) -> None:
    user_id = payload["user_id"]
    restaurant_id = payload["restaurant_id"]
    job_id = payload["job_id"]

    if not db.users.find_one({"_id": user_id}):
        mark_error(job_id, "user not found")
        return
    if not db.restaurants.find_one({"_id": restaurant_id}):
        mark_error(job_id, "restaurant not found")
        return

    existing = db.reviews.find_one({"user_id": user_id, "restaurant_id": restaurant_id})
    if existing:
        mark_done(job_id, existing["_id"])
        return

    now = datetime.now(timezone.utc)
    review_id = get_next_id("reviews")
    db.reviews.insert_one(
        {
            "_id": review_id,
            "user_id": user_id,
            "restaurant_id": restaurant_id,
            "rating": payload["rating"],
            "comment": payload.get("comment"),
            "created_at": now,
            "updated_at": now,
        }
    )
    _recalculate_rating(db, restaurant_id)
    mark_done(job_id, review_id)


def handle_update(db, payload: dict) -> None:
    review_id = payload["review_id"]
    job_id = payload["job_id"]

    review = db.reviews.find_one({"_id": review_id})
    if not review or review["user_id"] != payload["user_id"]:
        mark_error(job_id, "review not found or forbidden")
        return

    updates: dict = {"updated_at": datetime.now(timezone.utc)}
    if payload.get("rating") is not None:
        updates["rating"] = payload["rating"]
    if "comment" in payload:
        updates["comment"] = payload["comment"]
    db.reviews.update_one({"_id": review_id}, {"$set": updates})
    _recalculate_rating(db, review["restaurant_id"])
    mark_done(job_id, review_id)


def handle_delete(db, payload: dict) -> None:
    review_id = payload["review_id"]
    job_id = payload["job_id"]

    review = db.reviews.find_one({"_id": review_id})
    if not review or review["user_id"] != payload["user_id"]:
        mark_error(job_id, "review not found or forbidden")
        return

    restaurant_id = review["restaurant_id"]
    db.reviews.delete_one({"_id": review_id})
    _recalculate_rating(db, restaurant_id)
    mark_done(job_id, review_id)


def run() -> None:
    servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(",")
    topics = ["review.created", "review.updated", "review.deleted"]
    consumer = KafkaConsumer(
        *topics,
        bootstrap_servers=servers,
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
        group_id=os.getenv("KAFKA_GROUP_ID", "review-worker"),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )
    print("Review worker (MongoDB) listening on", topics, servers, flush=True)
    for msg in consumer:
        payload = msg.value
        if not payload:
            continue
        db = get_db()
        try:
            action = payload.get("action") or msg.topic.split(".")[-1]
            if action == "create":
                handle_create(db, payload)
            elif action == "update":
                handle_update(db, payload)
            elif action == "delete":
                handle_delete(db, payload)
        except Exception as e:
            jid = payload.get("job_id", "")
            mark_error(jid, str(e))


if __name__ == "__main__":
    run()
