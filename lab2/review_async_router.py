"""
Lab 2: Review mutations go through Kafka; GET endpoints remain synchronous MySQL reads.
Requires PYTHONPATH: backend root + lab2 + lab2/python (for kafka_client, mongo_jobs).
"""
from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.restaurant import Restaurant
from models.review import Review
from models.user import User
from schemas.review import ReviewCreate, ReviewResponse, ReviewUpdate
from utils.auth import get_current_user

router = APIRouter(prefix="/reviews", tags=["Reviews"])

try:
    from kafka_client import publish_review_event
    from mongo_jobs import create_job, get_job
except ImportError:
    publish_review_event = None  # type: ignore
    create_job = None  # type: ignore
    get_job = None  # type: ignore


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    review_id: int | None = None
    error: str | None = None


@router.get("/recent", response_model=List[ReviewResponse])
def get_recent_reviews(limit: int = 6, db: Session = Depends(get_db)):
    reviews = db.query(Review).order_by(Review.created_at.desc()).limit(limit).all()
    return [
        ReviewResponse(
            **{c.name: getattr(r, c.name) for c in r.__table__.columns},
            user_name=r.user.name if r.user else None,
            restaurant_name=r.restaurant.name if r.restaurant else None,
        )
        for r in reviews
    ]


@router.get("/restaurant/{restaurant_id}", response_model=List[ReviewResponse])
def get_restaurant_reviews(restaurant_id: int, db: Session = Depends(get_db)):
    reviews = (
        db.query(Review)
        .filter(Review.restaurant_id == restaurant_id)
        .order_by(Review.created_at.desc())
        .all()
    )
    out = []
    for r in reviews:
        out.append(
            ReviewResponse(
                **{c.name: getattr(r, c.name) for c in r.__table__.columns},
                user_name=r.user.name if r.user else None,
                restaurant_name=r.restaurant.name if r.restaurant else None,
            )
        )
    return out


@router.get("/my-reviews", response_model=List[ReviewResponse])
def get_my_reviews(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    reviews = (
        db.query(Review)
        .filter(Review.user_id == current_user.id)
        .order_by(Review.created_at.desc())
        .all()
    )
    return [
        ReviewResponse(
            **{c.name: getattr(r, c.name) for c in r.__table__.columns},
            user_name=current_user.name,
            restaurant_name=r.restaurant.name if r.restaurant else None,
        )
        for r in reviews
    ]


@router.get("/job/{job_id}", response_model=JobStatusResponse)
def get_review_job_status(job_id: str):
    if get_job is None:
        raise HTTPException(503, "Job store not configured")
    doc = get_job(job_id)
    if not doc:
        raise HTTPException(404, detail="Job not found")
    return JobStatusResponse(
        job_id=doc["job_id"],
        status=doc.get("status", "unknown"),
        review_id=doc.get("review_id"),
        error=doc.get("error"),
    )


@router.post("/", status_code=202)
def create_review_async(
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    restaurant = db.query(Restaurant).filter(Restaurant.id == data.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    existing = (
        db.query(Review)
        .filter(Review.user_id == current_user.id, Review.restaurant_id == data.restaurant_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="You already reviewed this restaurant. Edit your existing review instead.",
        )

    if publish_review_event is None:
        raise HTTPException(503, detail="Kafka not configured")

    job_id = str(uuid.uuid4())
    payload = {
        "job_id": job_id,
        "action": "create",
        "user_id": current_user.id,
        "restaurant_id": data.restaurant_id,
        "rating": data.rating,
        "comment": data.comment,
    }
    try:
        publish_review_event("review.created", payload)
    except Exception as e:
        raise HTTPException(503, detail=f"Kafka publish failed: {e}") from e

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this review")

    if publish_review_event is None:
        raise HTTPException(503, detail="Kafka not configured")

    job_id = str(uuid.uuid4())
    payload = {
        "job_id": job_id,
        "action": "update",
        "user_id": current_user.id,
        "review_id": review_id,
        **data.model_dump(exclude_unset=True),
    }
    try:
        publish_review_event("review.updated", payload)
    except Exception as e:
        raise HTTPException(503, detail=f"Kafka publish failed: {e}") from e

    if create_job:
        create_job(job_id, "review.updated", payload)

    return JSONResponse(
        status_code=202,
        content={"status": "accepted", "job_id": job_id, "message": "Review update queued"},
    )


@router.delete("/{review_id}", status_code=202)
def delete_review_async(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this review")

    if publish_review_event is None:
        raise HTTPException(503, detail="Kafka not configured")

    job_id = str(uuid.uuid4())
    payload = {
        "job_id": job_id,
        "action": "delete",
        "user_id": current_user.id,
        "review_id": review_id,
        "restaurant_id": review.restaurant_id,
    }
    try:
        publish_review_event("review.deleted", payload)
    except Exception as e:
        raise HTTPException(503, detail=f"Kafka publish failed: {e}") from e

    if create_job:
        create_job(job_id, "review.deleted", payload)

    return JSONResponse(
        status_code=202,
        content={"status": "accepted", "job_id": job_id, "message": "Review deletion queued"},
    )
