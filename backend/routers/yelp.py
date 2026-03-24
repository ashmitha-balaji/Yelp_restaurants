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
    raw = (city or "San Jose, CA").strip()
    # Yelp needs valid location: min 3 chars for city names, 5 for zip codes
    if len(raw) < 3 or (raw.isdigit() and len(raw) < 5):
        location = "San Jose, CA"
    else:
        location = raw

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{YELP_BASE}/businesses/search",
            params={"term": search_term, "location": location, "limit": limit},
            headers={"Authorization": f"Bearer {YELP_API_KEY}"},
        )

    if resp.status_code == 401:
        raise HTTPException(503, "Invalid Yelp API key")
    if resp.status_code != 200:
        detail = str(resp.status_code)
        try:
            err_body = resp.json()
            if isinstance(err_body.get("error"), dict):
                detail = err_body["error"].get("description", detail)
        except Exception:
            pass
        raise HTTPException(502, f"Yelp API error: {detail}")

    data = resp.json()
    businesses = data.get("businesses") or []
    return {"restaurants": [_transform_business(b) for b in businesses]}


@router.get("/restaurants/yelp/{yelp_id}")
async def get_yelp_business(yelp_id: str):
    """Fetch Yelp business details by Yelp business id."""
    if not YELP_API_KEY:
        raise HTTPException(503, "YELP_API_KEY not configured in backend 2 .env")

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{YELP_BASE}/businesses/{yelp_id}",
            headers={"Authorization": f"Bearer {YELP_API_KEY}"},
        )

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Yelp business not found")
    if resp.status_code == 401:
        raise HTTPException(status_code=503, detail="Invalid Yelp API key")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Yelp API error: {resp.status_code}")

    b = resp.json()
    cats = b.get("categories") or []
    cuisine = cats[0].get("title", "Restaurant") if cats else "Restaurant"
    loc = b.get("location") or {}
    photos = b.get("photos") or []
    # Some businesses only include image_url
    if not photos and b.get("image_url"):
        photos = [b.get("image_url")]

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
        "phone": b.get("display_phone") or b.get("phone"),
        "price_range": b.get("price") or "$$",
        "average_rating": b.get("rating"),
        "review_count": b.get("review_count", 0),
        "photos": photos,
        "yelp_url": b.get("url"),
        "is_closed": b.get("is_closed"),
        "transactions": b.get("transactions") or [],
        "location_display": loc.get("display_address") or [],
    }