"""Auth router backed by MongoDB (Lab 2)."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from mongo_auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    hash_password,
    verify_password,
)
from mongo_client import get_db, get_next_id

router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserSignup(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "user"
    restaurant_location: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


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


def _record_session(user_id: int, token: str) -> None:
    if not os.getenv("MONGODB_URL"):
        return
    try:
        from mongo_sessions import record_login_session
        record_login_session(user_id, token, ACCESS_TOKEN_EXPIRE_MINUTES)
    except Exception:
        pass


@router.post("/token")
def token_for_swagger(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2-compatible token endpoint for Swagger Authorize. Use email as 'username'."""
    doc = get_db().users.find_one({"email": form_data.username})
    if not doc or not verify_password(form_data.password, doc["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    token = create_access_token({"sub": str(doc["_id"])})
    _record_session(doc["_id"], token)
    return {"access_token": token, "token_type": "bearer", "user": _user_resp(doc)}


@router.post("/signup", status_code=201)
def signup(data: UserSignup):
    if data.role not in ("user", "owner"):
        raise HTTPException(400, "role must be 'user' or 'owner'")
    db = get_db()
    if db.users.find_one({"email": data.email}):
        raise HTTPException(400, "Email already registered")
    user_id = get_next_id("users")
    doc = {
        "_id": user_id,
        "name": data.name,
        "email": data.email,
        "password_hash": hash_password(data.password),
        "role": data.role,
        "restaurant_location": data.restaurant_location,
        "created_at": datetime.now(timezone.utc),
    }
    db.users.insert_one(doc)
    token = create_access_token({"sub": str(user_id)})
    _record_session(user_id, token)
    return {"access_token": token, "token_type": "bearer", "user": _user_resp(doc)}


@router.post("/login")
def login(data: UserLogin):
    doc = get_db().users.find_one({"email": data.email})
    if not doc or not verify_password(data.password, doc["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    token = create_access_token({"sub": str(doc["_id"])})
    _record_session(doc["_id"], token)
    return {"access_token": token, "token_type": "bearer", "user": _user_resp(doc)}
