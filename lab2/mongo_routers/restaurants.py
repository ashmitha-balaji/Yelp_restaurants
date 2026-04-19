"""Restaurants router backed by MongoDB (Lab 2)."""
from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

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
