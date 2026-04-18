"""MongoDB connection singleton and auto-increment ID helper for Lab 2 services."""
from __future__ import annotations

import os
from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database

_client: Optional[MongoClient] = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        _client = MongoClient(url, serverSelectionTimeoutMS=5000)
    return _client


def get_db() -> Database:
    return get_client()[os.getenv("MONGODB_DB_NAME", "yelp_lab2")]


def get_next_id(collection_name: str) -> int:
    """Auto-increment integer ID via a counters collection."""
    result = get_db().counters.find_one_and_update(
        {"_id": collection_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    return result["seq"]
