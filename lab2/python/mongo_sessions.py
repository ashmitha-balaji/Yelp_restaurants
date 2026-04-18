"""MongoDB session documents for Lab 2 (optional; enable with MONGODB_URL)."""
from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta, timezone
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


def record_login_session(user_id: int, access_token: str, expires_minutes: int = 60 * 24) -> Optional[str]:
    """Insert a server-side session row; returns session_id string or None if Mongo disabled."""
    db = _get_db()
    if db is None:
        return None
    fp = hashlib.sha256(access_token.encode()).hexdigest()[:32]
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes)
    doc: dict[str, Any] = {
        "user_id": user_id,
        "token_fingerprint": fp,
        "created_at": now,
        "expires_at": exp,
    }
    res = db.sessions.insert_one(doc)
    return str(res.inserted_id)


def revoke_session(session_oid: str) -> None:
    db = _get_db()
    if db is None:
        return
    from bson import ObjectId

    try:
        db.sessions.delete_one({"_id": ObjectId(session_oid)})
    except Exception:
        pass
