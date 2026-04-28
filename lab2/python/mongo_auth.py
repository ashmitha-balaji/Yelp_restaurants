"""JWT authentication utilities backed by MongoDB for Lab 2 services."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from mongo_client import get_db

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# HTTPBearer makes Swagger UI show a single "Value" field where you can paste
# the JWT directly. The OAuth2 password flow form was removed because it
# required `/auth/token` to exist on every microservice (it only lives on
# user-service). With HTTPBearer, the same token works across all services.
_bearer_scheme = HTTPBearer(auto_error=False)


def _extract_token(creds: Optional[HTTPAuthorizationCredentials]) -> Optional[str]:
    if creds is None:
        return None
    return creds.credentials


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


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> dict:
    token = _extract_token(creds)
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


def get_optional_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> Optional[dict]:
    token = _extract_token(creds)
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
