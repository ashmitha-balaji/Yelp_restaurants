"""Restaurants router backed by MongoDB (Lab 2)."""
from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

try:
    from hours_utils import (
        is_open_now, is_open_at, is_open_for_meal,
        is_open_late, hours_display, _to_minutes, current_day_and_minutes,
    )
    _HOURS_UTILS_AVAILABLE = True
except ImportError:
    _HOURS_UTILS_AVAILABLE = False

from mongo_auth import get_current_user, get_optional_user
from mongo_client import get_db, get_next_id

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])
try:
    from kafka_client import publish_restaurant_event
except ImportError:
    publish_restaurant_event = None  # type: ignore


def _photo_resp(p: dict) -> dict:
    return {"id": p["id"], "photo_url": p["photo_url"], "caption": p.get("caption")}


def _to_iso(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        # Kafka projections may already store ISO strings.
        return value
    return str(value)


def _rest_resp(doc: dict) -> dict:
    created = _to_iso(doc.get("created_at"))
    return {
        "id": doc["_id"],
        "owner_id": doc.get("owner_id"),
        "name": doc["name"],
        "cuisine_type": doc.get("cuisine_type"),
        "description": doc.get("description"),
        "address": doc.get("address"),
        "city": doc.get("city"),
        "state": doc.get("state"),
        "zip_code": doc.get("zip_code"),
        "country": doc.get("country", "US"),
        "phone": doc.get("phone"),
        "email": doc.get("email"),
        "website": doc.get("website"),
        "price_range": doc.get("price_range"),
        "hours_of_operation": doc.get("hours_of_operation"),
        "amenities": doc.get("amenities"),
        "ambiance": doc.get("ambiance"),
        "dietary_options": doc.get("dietary_options"),
        "average_rating": doc.get("average_rating", 0.0),
        "review_count": doc.get("review_count", 0),
        "is_claimed": doc.get("is_claimed", False),
        "photos": [_photo_resp(p) for p in doc.get("photos", [])],
        "created_at": created,
    }


def _parse_city(location: str) -> str:
    if not location or not location.strip():
        return location or ""
    return location.split(",")[0].strip()


def _json_safe(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    return value


def _emit_restaurant_event(topic: str, payload: dict) -> None:
    if publish_restaurant_event is None:
        return
    try:
        publish_restaurant_event(topic, _json_safe(payload))
    except Exception:
        # Do not break main API flow if Kafka is temporarily unavailable.
        pass


def _get_upload_dir() -> str:
    try:
        from config import UPLOAD_DIR
        return UPLOAD_DIR
    except ImportError:
        d = os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend", "uploads")
        os.makedirs(d, exist_ok=True)
        return d


# ── Autocomplete ──────────────────────────────────────────────────────────

@router.get("/autocomplete")
def autocomplete_restaurants(q: str = Query("", min_length=1)):
    """
    Returns up to 8 name/cuisine suggestions as the user types.
    Matches against restaurant name, cuisine_type, and city.
    """
    if not q or len(q.strip()) < 1:
        return []

    db = get_db()
    pattern = re.escape(q.strip())
    docs = list(
        db.restaurants.find(
            {
                "$or": [
                    {"name": {"$regex": pattern, "$options": "i"}},
                    {"cuisine_type": {"$regex": pattern, "$options": "i"}},
                    {"city": {"$regex": pattern, "$options": "i"}},
                ]
            },
            {"name": 1, "cuisine_type": 1, "city": 1, "average_rating": 1},
        )
        .sort("average_rating", -1)
        .limit(8)
    )
    return [
        {
            "id": d["_id"],
            "name": d.get("name"),
            "cuisine_type": d.get("cuisine_type"),
            "city": d.get("city"),
        }
        for d in docs
    ]


# ── Trending ───────────────────────────────────────────────────────────────

@router.get("/trending")
def get_trending_restaurants(days: int = Query(7, ge=1, le=30), limit: int = Query(10, ge=1, le=50)):
    """
    Weekly trending leaderboard: restaurants ranked by combined view + review
    activity in the past `days` days.
    """
    db = get_db()
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Count views per restaurant in window
    view_pipeline = [
        {"$match": {"viewed_at": {"$gte": since}}},
        {"$group": {"_id": "$restaurant_id", "views": {"$sum": 1}}},
    ]
    view_counts = {r["_id"]: r["views"] for r in db.restaurant_views.aggregate(view_pipeline)}

    # Count reviews per restaurant in window
    review_pipeline = [
        {"$match": {"created_at": {"$gte": since}}},
        {"$group": {"_id": "$restaurant_id", "new_reviews": {"$sum": 1},
                    "avg_recent_rating": {"$avg": "$rating"}}},
    ]
    review_counts = {
        r["_id"]: {"new_reviews": r["new_reviews"], "avg_recent_rating": round(r["avg_recent_rating"], 2)}
        for r in db.reviews.aggregate(review_pipeline)
    }

    # Merge: trending_score = views + new_reviews * 3 (reviews weighted more)
    all_ids = set(view_counts) | set(review_counts)
    scored = []
    for rid in all_ids:
        v = view_counts.get(rid, 0)
        rc = review_counts.get(rid, {})
        score = v + rc.get("new_reviews", 0) * 3
        scored.append((rid, score, v, rc))

    scored.sort(key=lambda x: -x[1])
    top_ids = [s[0] for s in scored[:limit]]

    if not top_ids:
        return []

    docs = {d["_id"]: d for d in db.restaurants.find({"_id": {"$in": top_ids}})}
    result = []
    for i, (rid, score, views, rc) in enumerate(scored[:limit]):
        doc = docs.get(rid)
        if not doc:
            continue
        result.append({
            **_rest_resp(doc),
            "trending_rank": i + 1,
            "trending_score": score,
            "recent_views": views,
            "recent_reviews": rc.get("new_reviews", 0),
            "recent_avg_rating": rc.get("avg_recent_rating"),
        })
    return result


# ── Open-now shortcut ─────────────────────────────────────────────────────

@router.get("/open-now")
def get_open_now_restaurants(
    city: Optional[str] = Query(None),
    cuisine_type: Optional[str] = Query(None),
    at_time: Optional[str] = Query(None, description="Override time as HH:MM (24h), e.g. 20:30"),
    for_meal: Optional[str] = Query(None, description="e.g. breakfast, lunch, dinner, late"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Return restaurants that are currently open (or open at a specific time/meal).

    Query params:
      - at_time   : check a specific time today, e.g. '20:30'
      - for_meal  : breakfast | brunch | lunch | dinner | late | tonight
      - city      : filter by city
      - cuisine_type : filter by cuisine
    """
    if not _HOURS_UTILS_AVAILABLE:
        raise HTTPException(503, "Hours utility not available")

    db = get_db()
    filt: dict = {}
    if city:
        filt["city"] = {"$regex": re.escape(_parse_city(city)), "$options": "i"}
    if cuisine_type:
        filt["cuisine_type"] = {"$regex": re.escape(cuisine_type), "$options": "i"}

    # Fetch a broad set; we'll filter by hours in Python
    docs = list(db.restaurants.find(filt).sort("average_rating", -1).limit(limit * 5))

    now = datetime.now()
    day, cur_minutes = current_day_and_minutes(now)

    if at_time:
        check_minutes = _to_minutes(at_time)
        if check_minutes < 0:
            raise HTTPException(422, "at_time must be HH:MM format, e.g. 20:30")
    else:
        check_minutes = cur_minutes

    open_docs = []
    for doc in docs:
        hours_raw = doc.get("hours_of_operation")
        if hours_raw is None:
            continue  # skip restaurants without hours data

        if for_meal:
            result = is_open_for_meal(hours_raw, for_meal, now)
        else:
            result = is_open_at(hours_raw, day, check_minutes)

        if result is True:
            resp = _rest_resp(doc)
            resp["hours_today"] = hours_display(hours_raw)
            resp["is_open_now"] = True
            open_docs.append(resp)

        if len(open_docs) >= limit:
            break

    return open_docs


# Must be registered before /{restaurant_id} so the path doesn't swallow it
@router.get("/owner/my-restaurants")
def get_owner_restaurants(current_user: dict = Depends(get_current_user)):
    docs = list(get_db().restaurants.find({"owner_id": current_user["id"]}).sort("created_at", -1))
    return [_rest_resp(d) for d in docs]


@router.get("/")
def search_restaurants(
    name: Optional[str] = Query(None),
    cuisine_type: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    zip_code: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    price_range: Optional[str] = Query(None),
    open_now: bool = Query(False, description="Only return currently open restaurants"),
    open_for: Optional[str] = Query(None, description="breakfast | lunch | dinner | late | tonight"),
    at_time: Optional[str] = Query(None, description="Check open status at HH:MM today"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    db = get_db()
    filt: dict = {}

    if name:
        filt["name"] = {"$regex": re.escape(name), "$options": "i"}
    if cuisine_type:
        filt["cuisine_type"] = {"$regex": re.escape(cuisine_type), "$options": "i"}
    if city:
        city_q = _parse_city(city)
        filt["city"] = {"$regex": re.escape(city_q), "$options": "i"}
    if zip_code:
        filt["zip_code"] = zip_code
    if price_range:
        filt["price_range"] = price_range
    if keyword and keyword.strip().lower() not in ("restaurants", "restaurant"):
        kw = re.escape(keyword.strip())
        filt["$or"] = [
            {"name": {"$regex": kw, "$options": "i"}},
            {"cuisine_type": {"$regex": kw, "$options": "i"}},
            {"description": {"$regex": kw, "$options": "i"}},
            {"amenities": {"$regex": kw, "$options": "i"}},
            {"ambiance": {"$regex": kw, "$options": "i"}},
        ]

    needs_hours_filter = (open_now or open_for or at_time) and _HOURS_UTILS_AVAILABLE

    if needs_hours_filter:
        # Fetch more docs so we have enough after hours filtering
        docs = list(db.restaurants.find(filt).sort("average_rating", -1).limit(limit * 10))
        now_dt = datetime.now()
        day, cur_minutes = current_day_and_minutes(now_dt)
        check_minutes = _to_minutes(at_time) if at_time else cur_minutes

        filtered = []
        for doc in docs:
            hours_raw = doc.get("hours_of_operation")
            if hours_raw is None:
                continue
            if open_for:
                result = is_open_for_meal(hours_raw, open_for, now_dt)
            else:
                result = is_open_at(hours_raw, day, check_minutes)
            if result is True:
                r = _rest_resp(doc)
                r["hours_today"] = hours_display(hours_raw)
                r["is_open_now"] = True
                filtered.append(r)
            if len(filtered) >= limit * 3:
                break

        skip = (page - 1) * limit
        return filtered[skip: skip + limit]

    skip = (page - 1) * limit
    docs = list(
        db.restaurants.find(filt).sort("average_rating", -1).skip(skip).limit(limit)
    )
    return [_rest_resp(d) for d in docs]


@router.get("/{restaurant_id}")
def get_restaurant(restaurant_id: int):
    doc = get_db().restaurants.find_one({"_id": restaurant_id})
    if not doc:
        raise HTTPException(404, "Restaurant not found")
    return _rest_resp(doc)


@router.post("/", status_code=201)
def create_restaurant(data: dict, current_user: dict = Depends(get_current_user)):
    from pydantic import BaseModel

    db = get_db()
    rest_id = get_next_id("restaurants")
    allowed = {
        "name", "cuisine_type", "description", "address", "city", "state",
        "zip_code", "country", "phone", "email", "website", "price_range",
        "hours_of_operation", "amenities", "ambiance", "dietary_options",
    }
    doc = {k: v for k, v in data.items() if k in allowed}
    if "name" not in doc:
        raise HTTPException(422, "name is required")
    doc.update(
        {
            "_id": rest_id,
            "owner_id": current_user["id"],
            "average_rating": 0.0,
            "review_count": 0,
            "is_claimed": False,
            "photos": [],
            "created_at": datetime.now(timezone.utc),
        }
    )
    db.restaurants.insert_one(doc)
    _emit_restaurant_event(
        "restaurant.created",
        {
            "action": "create",
            "restaurant_id": rest_id,
            "owner_id": current_user["id"],
            "restaurant": doc,
        },
    )
    return _rest_resp(doc)


@router.put("/{restaurant_id}")
def update_restaurant(
    restaurant_id: int,
    data: dict,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    doc = db.restaurants.find_one({"_id": restaurant_id})
    if not doc:
        raise HTTPException(404, "Restaurant not found")
    if doc.get("owner_id") and doc["owner_id"] != current_user["id"]:
        raise HTTPException(403, "Not authorized to update this restaurant")

    allowed = {
        "name", "cuisine_type", "description", "address", "city", "state",
        "zip_code", "country", "phone", "email", "website", "price_range",
        "hours_of_operation", "amenities", "ambiance", "dietary_options",
    }
    updates = {k: v for k, v in data.items() if k in allowed}
    if updates:
        updates["updated_at"] = datetime.now(timezone.utc)
        db.restaurants.update_one({"_id": restaurant_id}, {"$set": updates})
    updated_doc = db.restaurants.find_one({"_id": restaurant_id})
    _emit_restaurant_event(
        "restaurant.updated",
        {
            "action": "update",
            "restaurant_id": restaurant_id,
            "owner_id": current_user["id"],
            "updates": updates,
            "restaurant": updated_doc,
        },
    )
    return _rest_resp(updated_doc)


@router.post("/{restaurant_id}/claim")
def claim_restaurant(restaurant_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "owner":
        raise HTTPException(403, "Only owners can claim restaurants")
    db = get_db()
    doc = db.restaurants.find_one({"_id": restaurant_id})
    if not doc:
        raise HTTPException(404, "Restaurant not found")
    if doc.get("is_claimed"):
        raise HTTPException(400, "Restaurant is already claimed")
    db.restaurants.update_one(
        {"_id": restaurant_id},
        {"$set": {"owner_id": current_user["id"], "is_claimed": True}},
    )
    claimed_doc = db.restaurants.find_one({"_id": restaurant_id})
    _emit_restaurant_event(
        "restaurant.claimed",
        {
            "action": "claim",
            "restaurant_id": restaurant_id,
            "owner_id": current_user["id"],
            "restaurant": claimed_doc,
        },
    )
    return _rest_resp(claimed_doc)


@router.post("/{restaurant_id}/photos")
async def upload_restaurant_photo(
    restaurant_id: int,
    file: UploadFile = File(...),
    caption: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    doc = db.restaurants.find_one({"_id": restaurant_id})
    if not doc:
        raise HTTPException(404, "Restaurant not found")

    upload_dir = _get_upload_dir()
    ext = os.path.splitext(file.filename or ".jpg")[1]
    filename = f"restaurant_{restaurant_id}_{uuid.uuid4().hex}{ext}"
    contents = await file.read()
    with open(os.path.join(upload_dir, filename), "wb") as f:
        f.write(contents)

    photo_id = get_next_id("restaurant_photos")
    photo = {"id": photo_id, "photo_url": f"/uploads/{filename}", "caption": caption}
    db.restaurants.update_one({"_id": restaurant_id}, {"$push": {"photos": photo}})
    return photo
