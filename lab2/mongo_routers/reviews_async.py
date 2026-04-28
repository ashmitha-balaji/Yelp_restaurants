"""
Lab 2: Review mutations go through Kafka; GET endpoints are synchronous MongoDB reads.
Replaces the root-level review_async_router.py for Lab 2 MongoDB-backed services.

New in v2.1:
  POST /reviews/{id}/photo      — attach a photo to a review
  POST /reviews/{id}/reply      — owner posts a public reply
  DELETE /reviews/{id}/reply    — owner removes their reply
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from mongo_auth import get_current_user
from mongo_client import get_db

router = APIRouter(prefix="/reviews", tags=["Reviews"])

try:
    from kafka_client import publish_review_event
    from mongo_jobs import create_job, get_job
except ImportError:
    publish_review_event = None  # type: ignore
    create_job = None  # type: ignore
    get_job = None  # type: ignore


class ReviewCreate(BaseModel):
    restaurant_id: int
    rating: int
    comment: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


class ReviewUpdate(BaseModel):
    rating: Optional[int] = None
    comment: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 5):
            raise ValueError("Rating must be between 1 and 5")
        return v


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    review_id: Optional[int] = None
    error: Optional[str] = None


def _review_resp(r: dict) -> dict:
    db = get_db()
    user = db.users.find_one({"_id": r["user_id"]}, {"name": 1}) or {}
    rest = db.restaurants.find_one({"_id": r["restaurant_id"]}, {"name": 1}) or {}
    created = r.get("created_at")
    updated = r.get("updated_at")
    owner_reply_at = r.get("owner_reply_at")
    return {
        "id": r["_id"],
        "user_id": r["user_id"],
        "restaurant_id": r["restaurant_id"],
        "rating": r["rating"],
        "comment": r.get("comment"),
        "photo_url": r.get("photo_url"),
        "created_at": created.isoformat() if created else None,
        "updated_at": updated.isoformat() if updated else None,
        "user_name": user.get("name"),
        "restaurant_name": rest.get("name"),
        # Owner reply fields
        "owner_reply": r.get("owner_reply"),
        "owner_reply_at": owner_reply_at.isoformat() if owner_reply_at else None,
    }


def _get_upload_dir() -> str:
    try:
        from config import UPLOAD_DIR
        return UPLOAD_DIR
    except ImportError:
        d = os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend", "uploads")
        os.makedirs(d, exist_ok=True)
        return d


@router.get("/recent")
def get_recent_reviews(limit: int = 6):
    docs = list(get_db().reviews.find({}).sort("created_at", -1).limit(limit))
    return [_review_resp(r) for r in docs]


@router.get("/restaurant/{restaurant_id}")
def get_restaurant_reviews(restaurant_id: int):
    docs = list(
        get_db().reviews.find({"restaurant_id": restaurant_id}).sort("created_at", -1)
    )
    return [_review_resp(r) for r in docs]


@router.get("/my-reviews")
def get_my_reviews(current_user: dict = Depends(get_current_user)):
    docs = list(
        get_db().reviews.find({"user_id": current_user["id"]}).sort("created_at", -1)
    )
    return [_review_resp(r) for r in docs]


@router.get("/job/{job_id}", response_model=JobStatusResponse)
def get_review_job_status(job_id: str):
    if get_job is None:
        raise HTTPException(503, "Job store not configured")
    doc = get_job(job_id)
    if not doc:
        raise HTTPException(404, "Job not found")
    return JobStatusResponse(
        job_id=doc["job_id"],
        status=doc.get("status", "unknown"),
        review_id=doc.get("review_id"),
        error=doc.get("error"),
    )


@router.post("/", status_code=202)
def create_review_async(data: ReviewCreate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    if not db.restaurants.find_one({"_id": data.restaurant_id}):
        raise HTTPException(404, "Restaurant not found")

    existing = db.reviews.find_one(
        {"user_id": current_user["id"], "restaurant_id": data.restaurant_id}
    )
    if existing:
        raise HTTPException(400, "You already reviewed this restaurant. Edit your existing review instead.")

    if publish_review_event is None:
        raise HTTPException(503, "Kafka not configured")

    job_id = str(uuid.uuid4())
    payload = {
        "job_id": job_id,
        "action": "create",
        "user_id": current_user["id"],
        "restaurant_id": data.restaurant_id,
        "rating": data.rating,
        "comment": data.comment,
    }
    try:
        publish_review_event("review.created", payload)
    except Exception as e:
        raise HTTPException(503, f"Kafka publish failed: {e}") from e

    if create_job:
        create_job(job_id, "review.created", payload)

    return JSONResponse(
        status_code=202,
        content={"status": "accepted", "job_id": job_id, "message": "Review queued for processing"},
    )


@router.put("/{review_id}", status_code=202)
def update_review_async(
    review_id: int,
    data: ReviewUpdate,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    review = db.reviews.find_one({"_id": review_id})
    if not review:
        raise HTTPException(404, "Review not found")
    if review["user_id"] != current_user["id"]:
        raise HTTPException(403, "Not authorized to edit this review")

    if publish_review_event is None:
        raise HTTPException(503, "Kafka not configured")

    job_id = str(uuid.uuid4())
    payload = {
        "job_id": job_id,
        "action": "update",
        "user_id": current_user["id"],
        "review_id": review_id,
        **data.model_dump(exclude_unset=True),
    }
    try:
        publish_review_event("review.updated", payload)
    except Exception as e:
        raise HTTPException(503, f"Kafka publish failed: {e}") from e

    if create_job:
        create_job(job_id, "review.updated", payload)

    return JSONResponse(
        status_code=202,
        content={"status": "accepted", "job_id": job_id, "message": "Review update queued"},
    )


@router.delete("/{review_id}", status_code=202)
def delete_review_async(review_id: int, current_user: dict = Depends(get_current_user)):
    db = get_db()
    review = db.reviews.find_one({"_id": review_id})
    if not review:
        raise HTTPException(404, "Review not found")
    if review["user_id"] != current_user["id"]:
        raise HTTPException(403, "Not authorized to delete this review")

    if publish_review_event is None:
        raise HTTPException(503, "Kafka not configured")

    job_id = str(uuid.uuid4())
    payload = {
        "job_id": job_id,
        "action": "delete",
        "user_id": current_user["id"],
        "review_id": review_id,
        "restaurant_id": review["restaurant_id"],
    }
    try:
        publish_review_event("review.deleted", payload)
    except Exception as e:
        raise HTTPException(503, f"Kafka publish failed: {e}") from e

    if create_job:
        create_job(job_id, "review.deleted", payload)

    return JSONResponse(
        status_code=202,
        content={"status": "accepted", "job_id": job_id, "message": "Review deletion queued"},
    )


# ── Review photo upload ────────────────────────────────────────────────────

@router.post("/{review_id}/photo")
async def upload_review_photo(
    review_id: int,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Attach a photo to an existing review (only the review author can do this)."""
    db = get_db()
    review = db.reviews.find_one({"_id": review_id})
    if not review:
        raise HTTPException(404, "Review not found")
    if review["user_id"] != current_user["id"]:
        raise HTTPException(403, "Only the review author can add a photo")

    upload_dir = _get_upload_dir()
    ext = os.path.splitext(file.filename or ".jpg")[1].lower()
    allowed_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    if ext not in allowed_exts:
        raise HTTPException(422, f"File type not allowed. Use: {', '.join(allowed_exts)}")

    filename = f"review_{review_id}_{uuid.uuid4().hex}{ext}"
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(413, "File too large. Maximum size is 10 MB")

    with open(os.path.join(upload_dir, filename), "wb") as f:
        f.write(contents)

    photo_url = f"/uploads/{filename}"
    db.reviews.update_one(
        {"_id": review_id},
        {"$set": {"photo_url": photo_url, "updated_at": datetime.now(timezone.utc)}},
    )
    return {"photo_url": photo_url, "review_id": review_id}


# ── Owner reply to reviews ─────────────────────────────────────────────────

class OwnerReplyRequest(BaseModel):
    reply: str

    @classmethod
    def validate_reply(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Reply cannot be empty")
        if len(v) > 2000:
            raise ValueError("Reply must be 2000 characters or fewer")
        return v.strip()


@router.post("/{review_id}/reply")
def post_owner_reply(
    review_id: int,
    data: OwnerReplyRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Restaurant owner publicly replies to a review.
    The owner must own the restaurant the review is about.
    """
    if current_user["role"] != "owner":
        raise HTTPException(403, "Only restaurant owners can reply to reviews")

    db = get_db()
    review = db.reviews.find_one({"_id": review_id})
    if not review:
        raise HTTPException(404, "Review not found")

    # Verify the owner owns this restaurant
    restaurant = db.restaurants.find_one({"_id": review["restaurant_id"]})
    if not restaurant or restaurant.get("owner_id") != current_user["id"]:
        raise HTTPException(403, "You can only reply to reviews of your own restaurants")

    reply_text = data.reply.strip()
    if not reply_text:
        raise HTTPException(422, "Reply text cannot be empty")

    now = datetime.now(timezone.utc)
    db.reviews.update_one(
        {"_id": review_id},
        {"$set": {"owner_reply": reply_text, "owner_reply_at": now, "updated_at": now}},
    )

    # Notify the reviewer
    try:
        from notification_client import notify_owner_reply_posted
        notify_owner_reply_posted(
            review_id=review_id,
            reviewer_user_id=review["user_id"],
            restaurant_name=restaurant.get("name", "the restaurant"),
            reply_text=reply_text,
        )
    except Exception:
        pass

    updated = db.reviews.find_one({"_id": review_id})
    return _review_resp(updated)


@router.delete("/{review_id}/reply", status_code=200)
def delete_owner_reply(
    review_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Owner removes their reply from a review."""
    if current_user["role"] != "owner":
        raise HTTPException(403, "Only restaurant owners can manage review replies")

    db = get_db()
    review = db.reviews.find_one({"_id": review_id})
    if not review:
        raise HTTPException(404, "Review not found")

    restaurant = db.restaurants.find_one({"_id": review["restaurant_id"]})
    if not restaurant or restaurant.get("owner_id") != current_user["id"]:
        raise HTTPException(403, "You can only manage replies on your own restaurants")

    if not review.get("owner_reply"):
        raise HTTPException(404, "No reply exists on this review")

    db.reviews.update_one(
        {"_id": review_id},
        {"$unset": {"owner_reply": "", "owner_reply_at": ""},
         "$set": {"updated_at": datetime.now(timezone.utc)}},
    )
    return {"message": "Reply removed"}
