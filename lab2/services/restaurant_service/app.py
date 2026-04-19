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

from mongo_routers import ai_assistant as mongo_ai_assistant
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
# IMPORTANT: register Yelp routes before /restaurants/{restaurant_id}
# so /restaurants/yelp does not get parsed as {restaurant_id}="yelp".
app.include_router(yelp.router)
app.include_router(restaurants.router)
app.include_router(mongo_ai_assistant.router)


@app.get("/health")
def health():
    return {"service": "restaurant-service", "status": "ok", "db": "mongodb"}
