"""Users router backed by MongoDB (Lab 2)."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, EmailStr

from mongo_auth import get_current_user
from mongo_client import get_db

router = APIRouter(prefix="/users", tags=["Users"])


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    about_me: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    languages: Optional[str] = None
    gender: Optional[str] = None


class UserPreferenceUpdate(BaseModel):
    cuisine_preferences: Optional[str] = None
    price_range: Optional[str] = None
    preferred_locations: Optional[str] = None
    search_radius: Optional[int] = None
    dietary_needs: Optional[str] = None
    ambiance_preferences: Optional[str] = None
    sort_preference: Optional[str] = None


def _user_resp(doc: dict) -> dict:
    created = doc.get("created_at")
    return {
        "id": doc["_id"],
        "name": doc["name"],
        "email": doc["email"],
        "role": doc["role"],
        "phone": doc.get("phone"),
        "about_me": doc.get("about_me"),
        "city": doc.get("city"),
        "state": doc.get("state"),
        "country": doc.get("country"),
        "languages": doc.get("languages"),
        "gender": doc.get("gender"),
        "profile_picture": doc.get("profile_picture"),
        "restaurant_location": doc.get("restaurant_location"),
        "created_at": created.isoformat() if created else None,
    }


def _get_upload_dir() -> str:
    try:
        from config import UPLOAD_DIR
        return UPLOAD_DIR
    except ImportError:
        d = os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend", "uploads")
        os.makedirs(d, exist_ok=True)
        return d


@router.get("/me")
def get_profile(current_user: dict = Depends(get_current_user)):
    return _user_resp(current_user)


@router.put("/me")
def update_profile(data: UserProfileUpdate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    updates = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if updates:
        updates["updated_at"] = datetime.now(timezone.utc)
        db.users.update_one({"_id": current_user["id"]}, {"$set": updates})
    return _user_resp(db.users.find_one({"_id": current_user["id"]}))


@router.post("/me/photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    upload_dir = _get_upload_dir()
    ext = os.path.splitext(file.filename or ".jpg")[1]
    filename = f"profile_{current_user['id']}_{uuid.uuid4().hex}{ext}"
    contents = await file.read()
    with open(os.path.join(upload_dir, filename), "wb") as f:
        f.write(contents)
    db = get_db()
    pic = f"/uploads/{filename}"
    db.users.update_one({"_id": current_user["id"]}, {"$set": {"profile_picture": pic}})
    return _user_resp(db.users.find_one({"_id": current_user["id"]}))


@router.get("/me/preferences")
def get_preferences(current_user: dict = Depends(get_current_user)):
    db = get_db()
    pref = db.user_preferences.find_one({"user_id": current_user["id"]})
    if not pref:
        pref = {
            "user_id": current_user["id"],
            "cuisine_preferences": None,
            "price_range": None,
            "preferred_locations": None,
            "search_radius": None,
            "dietary_needs": None,
            "ambiance_preferences": None,
            "sort_preference": None,
        }
        db.user_preferences.insert_one(pref)
    pref.pop("_id", None)
    pref["id"] = current_user["id"]
    return pref


@router.put("/me/preferences")
def update_preferences(data: UserPreferenceUpdate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    updates = data.model_dump(exclude_unset=True)
    if updates:
        db.user_preferences.update_one(
            {"user_id": current_user["id"]}, {"$set": updates}, upsert=True
        )
    pref = db.user_preferences.find_one({"user_id": current_user["id"]}) or {}
    pref.pop("_id", None)
    pref["id"] = current_user["id"]
    pref.setdefault("user_id", current_user["id"])
    return pref


@router.get("/{user_id}")
def get_user(user_id: int):
    doc = get_db().users.find_one({"_id": user_id})
    if not doc:
        raise HTTPException(404, "User not found")
    return _user_resp(doc)
