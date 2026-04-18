"""Favorites router backed by MongoDB (Lab 2)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from mongo_auth import get_current_user
from mongo_client import get_db, get_next_id

router = APIRouter(prefix="/favorites", tags=["Favorites"])


class FavoriteCreate(BaseModel):
    restaurant_id: int


def _fav_resp(doc: dict, restaurant: dict | None) -> dict:
    r = None
    if restaurant:
        from mongo_routers.restaurants import _rest_resp
        r = _rest_resp(restaurant)
    return {
        "id": doc.get("_id"),
        "user_id": doc["user_id"],
        "restaurant_id": doc["restaurant_id"],
        "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
        "restaurant": r,
    }


@router.get("/")
def list_favorites(current_user: dict = Depends(get_current_user)):
    db = get_db()
    favs = list(db.favorites.find({"user_id": current_user["id"]}))
    result = []
    for fav in favs:
        rest = db.restaurants.find_one({"_id": fav["restaurant_id"]})
        result.append(_fav_resp(fav, rest))
    return result


@router.post("/", status_code=201)
def add_favorite(data: FavoriteCreate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    rest = db.restaurants.find_one({"_id": data.restaurant_id})
    if not rest:
        raise HTTPException(404, "Restaurant not found")

    existing = db.favorites.find_one(
        {"user_id": current_user["id"], "restaurant_id": data.restaurant_id}
    )
    if existing:
        raise HTTPException(400, "Restaurant already in favorites")

    fav_id = get_next_id("favorites")
    doc = {
        "_id": fav_id,
        "user_id": current_user["id"],
        "restaurant_id": data.restaurant_id,
        "created_at": datetime.now(timezone.utc),
    }
    db.favorites.insert_one(doc)
    return _fav_resp(doc, rest)


@router.delete("/{restaurant_id}", status_code=204)
def remove_favorite(restaurant_id: int, current_user: dict = Depends(get_current_user)):
    db = get_db()
    result = db.favorites.delete_one(
        {"user_id": current_user["id"], "restaurant_id": restaurant_id}
    )
    if result.deleted_count == 0:
        raise HTTPException(404, "Favorite not found")
