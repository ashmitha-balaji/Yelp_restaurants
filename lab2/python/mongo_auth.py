"""JWT authentication utilities backed by MongoDB for Lab 2 services."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from mongo_client import get_db

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    if len(pwd_bytes) > 72:
        password = pwd_bytes[:72].decode("utf-8", errors="replace")
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _doc_to_user(doc: dict) -> dict:
    """Normalise a raw MongoDB user document: expose integer id."""
    d = dict(doc)
    d["id"] = d["_id"]
    return d


def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> dict:
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
        user_id = int(sub)
    except (JWTError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    doc = get_db().users.find_one({"_id": user_id})
    if doc is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return _doc_to_user(doc)


def get_optional_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[dict]:
    if token is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            return None
        doc = get_db().users.find_one({"_id": int(sub)})
        return _doc_to_user(doc) if doc else None
    except (JWTError, ValueError):
        return None
