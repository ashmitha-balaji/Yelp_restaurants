"""User / Reviewer API: auth, users, favorites, history — MongoDB-backed (Lab 2)."""
import os
import sys

_ROOT = os.environ.get("APP_ROOT") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_LAB2 = os.path.join(_ROOT, "lab2")
_LAB2_PY = os.path.join(_LAB2, "python")
_BACKEND = os.path.join(_ROOT, "backend")
for p in (_LAB2, _LAB2_PY, _BACKEND):
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import UPLOAD_DIR
from db_init import init_mongo_db
from mongo_routers import auth, favorites, history, users

init_mongo_db()

app = FastAPI(title="User Service", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(favorites.router)
app.include_router(history.router)


@app.get("/health")
def health():
    return {"service": "user-service", "status": "ok", "db": "mongodb"}
