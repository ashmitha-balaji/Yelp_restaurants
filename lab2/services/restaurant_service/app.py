"""Restaurants, Yelp proxy — MongoDB-backed (Lab 2)."""
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

from mongo_routers import restaurants
from routers import yelp

app = FastAPI(title="Restaurant Service", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(restaurants.router)
app.include_router(yelp.router)

# AI assistant — optional; requires GROQ_API_KEY and MySQL (Lab 1 feature)
try:
    from routers import ai_assistant
    app.include_router(ai_assistant.router)
except Exception:
    pass


@app.get("/health")
def health():
    return {"service": "restaurant-service", "status": "ok", "db": "mongodb"}
