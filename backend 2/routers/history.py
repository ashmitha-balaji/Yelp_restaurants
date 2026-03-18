"""User history: reviews and restaurants owned/added."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.restaurant import Restaurant
from models.review import Review
from utils.auth import get_current_user

router = APIRouter(prefix="/history", tags=["History"])


@router.get("")
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Combined view of user's reviews and restaurants they've added/own."""
    reviews = (
        db.query(Review)
        .filter(Review.user_id == current_user.id)
        .order_by(Review.created_at.desc())
        .all()
    )
    restaurants = (
        db.query(Restaurant)
        .filter(Restaurant.owner_id == current_user.id)
        .order_by(Restaurant.created_at.desc())
        .all()
    )

    def _review_item(r):
        rest = db.query(Restaurant).filter(Restaurant.id == r.restaurant_id).first()
        return {
            "id": r.id,
            "restaurant_id": r.restaurant_id,
            "restaurant_name": rest.name if rest else f"Restaurant #{r.restaurant_id}",
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }

    return {
        "reviews": [_review_item(r) for r in reviews],
        "restaurants": [
            {
                "id": r.id,
                "name": r.name,
                "cuisine_type": r.cuisine_type,
                "city": r.city,
                "average_rating": r.average_rating,
            }
            for r in restaurants
        ],
    }
