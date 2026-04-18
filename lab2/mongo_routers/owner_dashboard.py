"""Owner Dashboard router backed by MongoDB (Lab 2)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from mongo_auth import get_current_user, get_optional_user
from mongo_client import get_db

router = APIRouter(prefix="/owner-dashboard", tags=["Owner Dashboard"])


def _sentiment_bucket(comment: str) -> str:
    if not comment or not comment.strip():
        return "neutral"
    text = comment.lower()
    pos_words = ["great", "amazing", "excellent", "good", "love", "loved", "awesome",
                 "friendly", "fresh", "best", "delicious", "perfect", "nice"]
    neg_words = ["bad", "worst", "poor", "slow", "rude", "cold", "dirty",
                 "awful", "terrible", "disappoint", "expensive", "late", "bland"]
    pos = sum(1 for w in pos_words if w in text)
    neg = sum(1 for w in neg_words if w in text)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


@router.post("/restaurants/{restaurant_id}/track-view")
def track_restaurant_view(
    restaurant_id: int,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    db = get_db()
    if not db.restaurants.find_one({"_id": restaurant_id}):
        raise HTTPException(404, "Restaurant not found")
    db.restaurant_views.insert_one(
        {
            "restaurant_id": restaurant_id,
            "user_id": current_user["id"] if current_user else None,
            "viewed_at": datetime.now(timezone.utc),
        }
    )
    return {"ok": True}


@router.get("/reviews")
def get_owner_reviews(
    restaurant_id: Optional[int] = Query(None),
    rating: Optional[int] = Query(None, ge=1, le=5),
    search: Optional[str] = Query(None),
    sort_by: str = Query("newest"),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "owner":
        raise HTTPException(403, "Owner access required")
    db = get_db()
    owned_ids = [r["_id"] for r in db.restaurants.find({"owner_id": current_user["id"]}, {"_id": 1})]
    if not owned_ids:
        return {"reviews": []}

    filt: dict = {"restaurant_id": {"$in": owned_ids}}
    if restaurant_id:
        if restaurant_id not in owned_ids:
            raise HTTPException(403, "Not authorized for that restaurant")
        filt["restaurant_id"] = restaurant_id
    if rating:
        filt["rating"] = rating
    if search and search.strip():
        import re
        filt["comment"] = {"$regex": re.escape(search.strip()), "$options": "i"}

    sort_map = {
        "oldest": ("created_at", 1),
        "rating_high": ("rating", -1),
        "rating_low": ("rating", 1),
        "newest": ("created_at", -1),
    }
    sort_field, sort_dir = sort_map.get(sort_by, ("created_at", -1))
    reviews = list(db.reviews.find(filt).sort(sort_field, sort_dir).limit(300))

    response = []
    for r in reviews:
        user = db.users.find_one({"_id": r["user_id"]}, {"name": 1}) or {}
        rest = db.restaurants.find_one({"_id": r["restaurant_id"]}, {"name": 1}) or {}
        created = r.get("created_at")
        response.append({
            "id": r["_id"],
            "user_id": r["user_id"],
            "user_name": user.get("name"),
            "restaurant_id": r["restaurant_id"],
            "restaurant_name": rest.get("name"),
            "rating": r["rating"],
            "comment": r.get("comment"),
            "created_at": created.isoformat() if created else None,
        })
    return {"reviews": response}


@router.get("/analytics")
def get_owner_analytics(
    restaurant_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "owner":
        raise HTTPException(403, "Owner access required")
    db = get_db()
    owned_rests = list(db.restaurants.find({"owner_id": current_user["id"]}))
    owned_ids = [r["_id"] for r in owned_rests]

    empty = {
        "totals": {"restaurants": 0, "views": 0, "reviews": 0, "avg_rating": 0},
        "rating_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
        "sentiment": {"positive": 0, "neutral": 0, "negative": 0, "overall_score": 0},
        "recent_reviews": [],
        "restaurant_breakdown": [],
    }
    if not owned_ids:
        return empty

    target_ids = owned_ids
    if restaurant_id:
        if restaurant_id not in owned_ids:
            raise HTTPException(403, "Not authorized for that restaurant")
        target_ids = [restaurant_id]

    view_count = db.restaurant_views.count_documents({"restaurant_id": {"$in": target_ids}})
    review_rows = list(db.reviews.find({"restaurant_id": {"$in": target_ids}}))
    review_count = len(review_rows)
    avg_rating = round(sum(r["rating"] for r in review_rows) / review_count, 2) if review_count else 0

    dist = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    for r in review_rows:
        dist[str(r["rating"])] += 1

    sentiment = {"positive": 0, "neutral": 0, "negative": 0}
    for r in review_rows:
        sentiment[_sentiment_bucket(r.get("comment") or "")] += 1
    total_s = sum(sentiment.values()) or 1
    overall_score = round(((sentiment["positive"] - sentiment["negative"]) / total_s) * 100, 1)

    recent = (
        sorted(review_rows, key=lambda r: r.get("created_at") or datetime.min, reverse=True)[:10]
    )
    recent_payload = []
    for r in recent:
        user = db.users.find_one({"_id": r["user_id"]}, {"name": 1}) or {}
        rest = db.restaurants.find_one({"_id": r["restaurant_id"]}, {"name": 1}) or {}
        created = r.get("created_at")
        recent_payload.append({
            "id": r["_id"],
            "restaurant_id": r["restaurant_id"],
            "restaurant_name": rest.get("name"),
            "user_name": user.get("name"),
            "rating": r["rating"],
            "comment": r.get("comment"),
            "created_at": created.isoformat() if created else None,
        })

    breakdown = []
    for rest in owned_rests:
        if rest["_id"] not in target_ids:
            continue
        r_reviews = [rv for rv in review_rows if rv["restaurant_id"] == rest["_id"]]
        r_views = db.restaurant_views.count_documents({"restaurant_id": rest["_id"]})
        r_avg = round(sum(rv["rating"] for rv in r_reviews) / len(r_reviews), 2) if r_reviews else 0
        breakdown.append({
            "restaurant_id": rest["_id"],
            "restaurant_name": rest["name"],
            "views": r_views,
            "reviews": len(r_reviews),
            "avg_rating": r_avg,
        })

    return {
        "totals": {
            "restaurants": len(target_ids),
            "views": view_count,
            "reviews": review_count,
            "avg_rating": avg_rating,
        },
        "rating_distribution": dist,
        "sentiment": {**sentiment, "overall_score": overall_score},
        "recent_reviews": recent_payload,
        "restaurant_breakdown": breakdown,
    }
