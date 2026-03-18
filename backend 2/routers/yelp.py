# backend 2/routers/yelp.py
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
import httpx
from dotenv import load_dotenv

# Load .env from backend 2 folder
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

router = APIRouter(tags=["Yelp"])

YELP_API_KEY = os.getenv("YELP_API_KEY")
YELP_BASE = "https://api.yelp.com/v3"


def _transform_business(b: dict) -> dict:
    cats = b.get("categories") or []
    cuisine = cats[0].get("title", "Restaurant") if cats else "Restaurant"
    loc = b.get("location") or {}
    return {
        "id": b.get("id"),
        "yelp_id": b.get("id"),
        "name": b.get("name"),
        "cuisine_type": cuisine,
        "address": loc.get("address1"),
        "city": loc.get("city"),
        "state": loc.get("state"),
        "zip_code": loc.get("zip_code"),
        "country": loc.get("country"),
        "phone": b.get("phone"),
        "price_range": b.get("price") or "$$",
        "average_rating": b.get("rating"),
        "review_count": b.get("review_count", 0),
        "photos": [b.get("image_url")] if b.get("image_url") else [],
        "yelp_url": b.get("url"),
    }


@router.get("/restaurants/yelp")
async def search_yelp(
    term: str | None = Query(None, description="restaurants, pizza, sushi..."),
    city: str | None = Query(None, description="City or zip (e.g. San Jose, CA)"),
    limit: int = Query(20, ge=1, le=50),
):
    if not YELP_API_KEY:
        raise HTTPException(503, "YELP_API_KEY not configured in backend 2 .env")

    search_term = (term or "restaurants").strip()
    location = (city or "San Jose, CA").strip()

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{YELP_BASE}/businesses/search",
            params={"term": search_term, "location": location, "limit": limit},
            headers={"Authorization": f"Bearer {YELP_API_KEY}"},
        )

    if resp.status_code == 401:
        raise HTTPException(503, "Invalid Yelp API key")
    if resp.status_code != 200:
        raise HTTPException(502, f"Yelp API error: {resp.status_code}")

    data = resp.json()
    businesses = data.get("businesses") or []
    return {"restaurants": [_transform_business(b) for b in businesses]}