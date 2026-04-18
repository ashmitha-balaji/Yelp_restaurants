"""User history router backed by MongoDB (Lab 2)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from mongo_auth import get_current_user
from mongo_client import get_db

router = APIRouter(prefix="/history", tags=["History"])


@router.get("")
def get_history(current_user: dict = Depends(get_current_user)):
    db = get_db()

    reviews = list(
        db.reviews.find({"user_id": current_user["id"]}).sort("created_at", -1)
    )
    restaurants = list(
        db.restaurants.find({"owner_id": current_user["id"]}).sort("created_at", -1)
    )

    def _review_item(r: dict) -> dict:
        rest = db.restaurants.find_one({"_id": r["restaurant_id"]}, {"name": 1})
        name = rest["name"] if rest else f"Restaurant #{r['restaurant_id']}"
        created = r.get("created_at")
        return {
            "id": r["_id"],
            "restaurant_id": r["restaurant_id"],
            "restaurant_name": name,
            "rating": r["rating"],
            "comment": r.get("comment"),
            "created_at": created.isoformat() if created else None,
        }

    return {
        "reviews": [_review_item(r) for r in reviews],
        "restaurants": [
            {
                "id": r["_id"],
                "name": r["name"],
                "cuisine_type": r.get("cuisine_type"),
                "city": r.get("city"),
                "average_rating": r.get("average_rating", 0.0),
            }
            for r in restaurants
        ],
    }
