"""
Waitlist / Reservation router (Lab 2).

Endpoints
---------
POST   /waitlist/{restaurant_id}        Join the waitlist
GET    /waitlist/{restaurant_id}/status My position + queue length
DELETE /waitlist/{restaurant_id}        Leave the waitlist
GET    /waitlist/{restaurant_id}        (owner only) Full queue
POST   /waitlist/{restaurant_id}/notify/{user_id}  Owner calls user's turn
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from mongo_auth import get_current_user
from mongo_client import get_db, get_next_id

router = APIRouter(prefix="/waitlist", tags=["Waitlist"])


class WaitlistJoinRequest(BaseModel):
    party_size: int = 1
    notes: Optional[str] = None


class WaitlistEntry(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str]
    restaurant_id: int
    party_size: int
    notes: Optional[str]
    position: int
    status: str          # pending | called | seated | cancelled
    joined_at: str


class WaitlistStatus(BaseModel):
    in_queue: bool
    position: Optional[int]
    total_ahead: Optional[int]
    queue_length: int
    entry: Optional[WaitlistEntry]


def _entry_resp(doc: dict, position: int) -> dict:
    db = get_db()
    user = db.users.find_one({"_id": doc["user_id"]}, {"name": 1}) or {}
    joined = doc.get("joined_at")
    return {
        "id": doc["_id"],
        "user_id": doc["user_id"],
        "user_name": user.get("name"),
        "restaurant_id": doc["restaurant_id"],
        "party_size": doc.get("party_size", 1),
        "notes": doc.get("notes"),
        "position": position,
        "status": doc.get("status", "pending"),
        "joined_at": joined.isoformat() if joined else None,
    }


def _get_active_queue(db, restaurant_id: int) -> list:
    """Return active (pending/called) queue sorted by joined_at."""
    return list(
        db.waitlist.find(
            {"restaurant_id": restaurant_id, "status": {"$in": ["pending", "called"]}}
        ).sort("joined_at", 1)
    )


@router.post("/{restaurant_id}", status_code=201)
def join_waitlist(
    restaurant_id: int,
    data: WaitlistJoinRequest,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    if not db.restaurants.find_one({"_id": restaurant_id}):
        raise HTTPException(404, "Restaurant not found")

    # Check if already in queue
    existing = db.waitlist.find_one({
        "restaurant_id": restaurant_id,
        "user_id": current_user["id"],
        "status": {"$in": ["pending", "called"]},
    })
    if existing:
        raise HTTPException(400, "You are already on the waitlist for this restaurant")

    entry_id = get_next_id("waitlist")
    now = datetime.now(timezone.utc)
    doc = {
        "_id": entry_id,
        "user_id": current_user["id"],
        "restaurant_id": restaurant_id,
        "party_size": max(1, data.party_size),
        "notes": data.notes,
        "status": "pending",
        "joined_at": now,
        "updated_at": now,
    }
    db.waitlist.insert_one(doc)

    queue = _get_active_queue(db, restaurant_id)
    position = next(
        (i + 1 for i, e in enumerate(queue) if e["_id"] == entry_id), len(queue)
    )

    # Fire Kafka event + notification (non-blocking)
    try:
        from kafka_client import publish_event
        publish_event("waitlist.joined", {
            "user_id": current_user["id"],
            "restaurant_id": restaurant_id,
            "entry_id": entry_id,
            "position": position,
            "party_size": data.party_size,
        })
    except Exception:
        pass

    try:
        from notification_client import notify_waitlist_position
        rest = db.restaurants.find_one({"_id": restaurant_id}, {"name": 1}) or {}
        notify_waitlist_position(
            current_user["id"],
            rest.get("name", "the restaurant"),
            position,
            restaurant_id,
        )
    except Exception:
        pass

    return {**_entry_resp(doc, position), "message": f"You are #{position} in the queue"}


@router.get("/{restaurant_id}/status", response_model=WaitlistStatus)
def get_my_waitlist_status(
    restaurant_id: int,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    if not db.restaurants.find_one({"_id": restaurant_id}):
        raise HTTPException(404, "Restaurant not found")

    queue = _get_active_queue(db, restaurant_id)
    queue_length = len(queue)

    entry = db.waitlist.find_one({
        "restaurant_id": restaurant_id,
        "user_id": current_user["id"],
        "status": {"$in": ["pending", "called"]},
    })

    if not entry:
        return WaitlistStatus(in_queue=False, position=None, total_ahead=None,
                               queue_length=queue_length, entry=None)

    position = next(
        (i + 1 for i, e in enumerate(queue) if e["_id"] == entry["_id"]), None
    )
    return WaitlistStatus(
        in_queue=True,
        position=position,
        total_ahead=(position - 1) if position else None,
        queue_length=queue_length,
        entry=_entry_resp(entry, position or 0),
    )


@router.delete("/{restaurant_id}", status_code=200)
def leave_waitlist(
    restaurant_id: int,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    entry = db.waitlist.find_one({
        "restaurant_id": restaurant_id,
        "user_id": current_user["id"],
        "status": {"$in": ["pending", "called"]},
    })
    if not entry:
        raise HTTPException(404, "You are not on the waitlist for this restaurant")

    db.waitlist.update_one(
        {"_id": entry["_id"]},
        {"$set": {"status": "cancelled", "updated_at": datetime.now(timezone.utc)}},
    )
    return {"message": "Removed from waitlist"}


@router.get("/{restaurant_id}")
def get_full_queue(
    restaurant_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Owner-only: see the full waitlist for their restaurant."""
    db = get_db()
    rest = db.restaurants.find_one({"_id": restaurant_id})
    if not rest:
        raise HTTPException(404, "Restaurant not found")
    if current_user["role"] != "owner" or rest.get("owner_id") != current_user["id"]:
        raise HTTPException(403, "Only the restaurant owner can view the full queue")

    queue = _get_active_queue(db, restaurant_id)
    return {
        "restaurant_id": restaurant_id,
        "queue_length": len(queue),
        "entries": [_entry_resp(e, i + 1) for i, e in enumerate(queue)],
    }


@router.post("/{restaurant_id}/notify/{user_id}", status_code=200)
def call_next(
    restaurant_id: int,
    user_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Owner marks a party as 'called' and notifies them."""
    db = get_db()
    rest = db.restaurants.find_one({"_id": restaurant_id})
    if not rest:
        raise HTTPException(404, "Restaurant not found")
    if current_user["role"] != "owner" or rest.get("owner_id") != current_user["id"]:
        raise HTTPException(403, "Only the restaurant owner can call guests")

    entry = db.waitlist.find_one({
        "restaurant_id": restaurant_id,
        "user_id": user_id,
        "status": "pending",
    })
    if not entry:
        raise HTTPException(404, "User not found in active waitlist")

    db.waitlist.update_one(
        {"_id": entry["_id"]},
        {"$set": {"status": "called", "updated_at": datetime.now(timezone.utc)}},
    )

    # Notify the guest
    try:
        from notification_client import send_notification
        user = db.users.find_one({"_id": user_id}, {"email": 1, "name": 1}) or {}
        send_notification(
            recipient_user_id=user_id,
            subject=f"It's your turn at {rest.get('name')}!",
            body=(
                f"Hi {user.get('name', 'there')},\n\n"
                f"Your table at {rest.get('name')} is ready! "
                f"Please proceed to the host stand.\n"
            ),
            notification_type="waitlist_called",
            metadata={"restaurant_id": restaurant_id},
            to_email=user.get("email"),
        )
    except Exception:
        pass

    return {"message": f"Guest notified", "entry_id": entry["_id"]}
