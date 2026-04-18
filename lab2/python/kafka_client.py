"""Kafka producer helpers for review events."""
from __future__ import annotations

import json
import os
import uuid
from typing import Any, Optional

_producer = None


def _get_producer():
    global _producer
    if _producer is not None:
        return _producer
    servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    try:
        from kafka import KafkaProducer
    except ImportError:
        return None
    _producer = KafkaProducer(
        bootstrap_servers=servers.split(","),
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        linger_ms=5,
    )
    return _producer


def publish_review_event(topic: str, payload: dict[str, Any]) -> str:
    """Publish JSON event; returns job_id (generated if missing)."""
    job_id = payload.get("job_id") or str(uuid.uuid4())
    payload = {**payload, "job_id": job_id}
    p = _get_producer()
    if p is None:
        raise RuntimeError("KafkaProducer unavailable (install kafka-python or set KAFKA_BOOTSTRAP_SERVERS)")
    p.send(topic, payload)
    p.flush(timeout=10)
    return job_id
