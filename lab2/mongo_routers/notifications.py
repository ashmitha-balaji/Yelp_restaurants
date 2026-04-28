"""
Notifications router — lets users view and mark notifications as read.

Endpoints
---------
GET    /notifications/          List my notifications (newest first)
PUT    /notifications/{id}/read Mark a notification as read
DELETE /notifications/{id}      Delete a notification
GET    /notifications/unread-count  Fast badge count
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from mongo_auth import get_current_user
from mongo_client import get_db

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _notif_resp(doc: dict) -> dict:
    created = doc.get("created_at")
    return {
        "id": doc["_id"],
        "type": doc.get("type", "general"),
        "subject": doc.get("subject", ""),
        "body": doc.get("body", ""),
        "metadata": doc.get("metadata", {}),
        "read": doc.get("read", False),
        "created_at": created.isoformat() if created else None,
    }


@router.get("/unread-count")
def unread_count(current_user: dict = Depends(get_current_user)):
    db = get_db()
    count = db.notifications.count_documents({"user_id": current_user["id"], "read": False})
    return {"unread_count": count}


@router.get("/")
def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    filt: dict = {"user_id": current_user["id"]}
    if unread_only:
        filt["read"] = False
    docs = list(
        db.notifications.find(filt)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    total = db.notifications.count_documents(filt)
    return {
        "notifications": [_notif_resp(d) for d in docs],
        "total": total,
        "unread_count": db.notifications.count_documents(
            {"user_id": current_user["id"], "read": False}
        ),
    }


@router.put("/{notification_id}/read")
def mark_as_read(
    notification_id: int,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    doc = db.notifications.find_one({"_id": notification_id})
    if not doc:
        raise HTTPException(404, "Notification not found")
    if doc["user_id"] != current_user["id"]:
        raise HTTPException(403, "Not your notification")
    db.notifications.update_one(
        {"_id": notification_id},
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc)}},
    )
    return {"message": "Marked as read"}


@router.put("/read-all")
def mark_all_read(current_user: dict = Depends(get_current_user)):
    db = get_db()
    db.notifications.update_many(
        {"user_id": current_user["id"], "read": False},
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc)}},
    )
    return {"message": "All notifications marked as read"}


@router.delete("/{notification_id}", status_code=200)
def delete_notification(
    notification_id: int,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    doc = db.notifications.find_one({"_id": notification_id})
    if not doc:
        raise HTTPException(404, "Notification not found")
    if doc["user_id"] != current_user["id"]:
        raise HTTPException(403, "Not your notification")
    db.notifications.delete_one({"_id": notification_id})
    return {"message": "Notification deleted"}
