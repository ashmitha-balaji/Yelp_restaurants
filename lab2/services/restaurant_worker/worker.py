"""Kafka consumer: process restaurant.created/updated/claimed events (Lab 2)."""
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

from mongo_client import get_db


def _upsert_restaurant_projection(db, payload: dict) -> None:
    rest = payload.get("restaurant") or {}
    rest_id = payload.get("restaurant_id") or rest.get("_id")
    if rest_id is None:
        return
    if isinstance(rest, dict):
        doc = dict(rest)
    else:
        doc = {}
    doc["_id"] = rest_id
    doc["event_synced_at"] = datetime.now(timezone.utc)
    db.restaurants.update_one({"_id": rest_id}, {"$set": doc}, upsert=True)


def _record_event(db, topic: str, payload: dict) -> None:
    db.restaurant_events.insert_one(
        {
            "topic": topic,
            "event_id": payload.get("event_id") or payload.get("job_id"),
            "restaurant_id": payload.get("restaurant_id"),
            "owner_id": payload.get("owner_id"),
            "action": payload.get("action"),
            "payload": payload,
            "processed_at": datetime.now(timezone.utc),
        }
    )


def run() -> None:
    servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(",")
    topics = ["restaurant.created", "restaurant.updated", "restaurant.claimed"]
    consumer = KafkaConsumer(
        *topics,
        bootstrap_servers=servers,
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
        group_id=os.getenv("KAFKA_RESTAURANT_GROUP_ID", "restaurant-worker"),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )
    print("Restaurant worker listening on", topics, servers, flush=True)
    for msg in consumer:
        payload = msg.value or {}
        db = get_db()
        try:
            _upsert_restaurant_projection(db, payload)
            _record_event(db, msg.topic, payload)
        except Exception as e:
            print(f"restaurant-worker failed for topic={msg.topic}: {e}", flush=True)


if __name__ == "__main__":
    run()
