from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models.restaurant import Restaurant
from models.restaurant_view import RestaurantView
from models.review import Review
from models.user import User
from utils.auth import get_current_user, get_optional_user

router = APIRouter(prefix="/owner-dashboard", tags=["Owner Dashboard"])


def _owner_restaurant_ids(db: Session, owner_id: int):
    return [r.id for r in db.query(Restaurant.id).filter(Restaurant.owner_id == owner_id).all()]


def _sentiment_bucket(comment: str) -> str:
    if not comment or not comment.strip():
        return "neutral"
    text = comment.lower()
    positive_words = [
        "great", "amazing", "excellent", "good", "love", "loved", "awesome",
        "friendly", "fresh", "best", "delicious", "perfect", "nice",
    ]
    negative_words = [
        "bad", "worst", "poor", "slow", "rude", "cold", "dirty",
        "awful", "terrible", "disappoint", "expensive", "late", "bland",
    ]
    pos = sum(1 for w in positive_words if w in text)
    neg = sum(1 for w in negative_words if w in text)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


@router.post("/restaurants/{restaurant_id}/track-view")
def track_restaurant_view(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    view = RestaurantView(
        restaurant_id=restaurant_id,
        user_id=current_user.id if current_user else None,
    )
    db.add(view)
    db.commit()
    return {"ok": True}


@router.get("/reviews")
def get_owner_reviews(
    restaurant_id: Optional[int] = Query(None),
    rating: Optional[int] = Query(None, ge=1, le=5),
    search: Optional[str] = Query(None),
    sort_by: str = Query("newest"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Owner access required")

    owned_ids = _owner_restaurant_ids(db, current_user.id)
    if not owned_ids:
        return {"reviews": []}

    query = db.query(Review).filter(Review.restaurant_id.in_(owned_ids))
    if restaurant_id:
        if restaurant_id not in owned_ids:
            raise HTTPException(status_code=403, detail="Not authorized for that restaurant")
        query = query.filter(Review.restaurant_id == restaurant_id)
    if rating:
        query = query.filter(Review.rating == rating)
    if search and search.strip():
        s = f"%{search.strip()}%"
        query = query.filter(Review.comment.ilike(s))

    if sort_by == "oldest":
        query = query.order_by(Review.created_at.asc())
    elif sort_by == "rating_high":
        query = query.order_by(Review.rating.desc(), Review.created_at.desc())
    elif sort_by == "rating_low":
        query = query.order_by(Review.rating.asc(), Review.created_at.desc())
    else:
        query = query.order_by(Review.created_at.desc())

    reviews = query.limit(300).all()

    response = []
    for r in reviews:
        response.append({
            "id": r.id,
            "user_id": r.user_id,
            "user_name": r.user.name if r.user else None,
            "restaurant_id": r.restaurant_id,
            "restaurant_name": r.restaurant.name if r.restaurant else None,
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return {"reviews": response}


@router.get("/analytics")
def get_owner_analytics(
    restaurant_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Owner access required")

    owned_restaurants = db.query(Restaurant).filter(Restaurant.owner_id == current_user.id).all()
    owned_ids = [r.id for r in owned_restaurants]

    if not owned_ids:
        return {
            "totals": {"restaurants": 0, "views": 0, "reviews": 0, "avg_rating": 0},
            "rating_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
            "sentiment": {"positive": 0, "neutral": 0, "negative": 0, "overall_score": 0},
            "recent_reviews": [],
            "restaurant_breakdown": [],
        }

    target_ids = owned_ids
    if restaurant_id:
        if restaurant_id not in owned_ids:
            raise HTTPException(status_code=403, detail="Not authorized for that restaurant")
        target_ids = [restaurant_id]

    view_count = (
        db.query(func.count(RestaurantView.id))
        .filter(RestaurantView.restaurant_id.in_(target_ids))
        .scalar()
        or 0
    )
    review_rows = db.query(Review).filter(Review.restaurant_id.in_(target_ids)).all()
    review_count = len(review_rows)
    avg_rating = round(sum(r.rating for r in review_rows) / review_count, 2) if review_count else 0

    dist = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    for r in review_rows:
        dist[str(r.rating)] += 1

    sentiment = {"positive": 0, "neutral": 0, "negative": 0}
    for r in review_rows:
        sentiment[_sentiment_bucket(r.comment or "")] += 1
    total_sentiment = sum(sentiment.values()) or 1
    overall_score = round(((sentiment["positive"] - sentiment["negative"]) / total_sentiment) * 100, 1)

    recent_reviews = (
        db.query(Review)
        .filter(Review.restaurant_id.in_(target_ids))
        .order_by(Review.created_at.desc())
        .limit(10)
        .all()
    )
    recent_payload = [{
        "id": r.id,
        "restaurant_id": r.restaurant_id,
        "restaurant_name": r.restaurant.name if r.restaurant else None,
        "user_name": r.user.name if r.user else None,
        "rating": r.rating,
        "comment": r.comment,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in recent_reviews]

    breakdown = []
    for rest in owned_restaurants:
        if rest.id not in target_ids:
            continue
        r_reviews = [rv for rv in review_rows if rv.restaurant_id == rest.id]
        r_views = (
            db.query(func.count(RestaurantView.id))
            .filter(RestaurantView.restaurant_id == rest.id)
            .scalar()
            or 0
        )
        r_avg = round(sum(rv.rating for rv in r_reviews) / len(r_reviews), 2) if r_reviews else 0
        breakdown.append({
            "restaurant_id": rest.id,
            "restaurant_name": rest.name,
            "views": r_views,
            "reviews": len(r_reviews),
            "avg_rating": r_avg,
        })

    return {
        "totals": {
            "restaurants": len(target_ids),
            "views": view_count,
            "reviews": review_count,
            "avg_rating": avg_rating,
        },
        "rating_distribution": dist,
        "sentiment": {
            **sentiment,
            "overall_score": overall_score,
        },
        "recent_reviews": recent_payload,
        "restaurant_breakdown": breakdown,
    }
