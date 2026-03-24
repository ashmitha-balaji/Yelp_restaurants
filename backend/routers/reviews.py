from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from database import get_db
from models.user import User
from models.restaurant import Restaurant
from models.review import Review
from schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse
from utils.auth import get_current_user

router = APIRouter(prefix="/reviews", tags=["Reviews"])


def _recalculate_rating(db: Session, restaurant_id: int):
    result = db.query(
        func.avg(Review.rating).label("avg"),
        func.count(Review.id).label("cnt"),
    ).filter(Review.restaurant_id == restaurant_id).first()

    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if restaurant:
        restaurant.average_rating = round(float(result.avg or 0), 2)
        restaurant.review_count = int(result.cnt or 0)
        db.commit()


@router.post("/", response_model=ReviewResponse, status_code=201)
def create_review(data: ReviewCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    restaurant = db.query(Restaurant).filter(Restaurant.id == data.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    existing = db.query(Review).filter(
        Review.user_id == current_user.id,
        Review.restaurant_id == data.restaurant_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already reviewed this restaurant. Edit your existing review instead.")

    review = Review(user_id=current_user.id, **data.model_dump())
    db.add(review)
    db.commit()
    db.refresh(review)

    _recalculate_rating(db, data.restaurant_id)

    return ReviewResponse(
        **{c.name: getattr(review, c.name) for c in review.__table__.columns},
        user_name=current_user.name,
        restaurant_name=restaurant.name,
    )


@router.get("/recent", response_model=List[ReviewResponse])
def get_recent_reviews(limit: int = 6, db: Session = Depends(get_db)):
    """Get most recent reviews across all restaurants (for Recent Activity feed)."""
    reviews = (
        db.query(Review)
        .order_by(Review.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        ReviewResponse(
            **{c.name: getattr(r, c.name) for c in r.__table__.columns},
            user_name=r.user.name if r.user else None,
            restaurant_name=r.restaurant.name if r.restaurant else None,
        )
        for r in reviews
    ]


@router.get("/restaurant/{restaurant_id}", response_model=List[ReviewResponse])
def get_restaurant_reviews(restaurant_id: int, db: Session = Depends(get_db)):
    reviews = (
        db.query(Review)
        .filter(Review.restaurant_id == restaurant_id)
        .order_by(Review.created_at.desc())
        .all()
    )
    result = []
    for r in reviews:
        result.append(ReviewResponse(
            **{c.name: getattr(r, c.name) for c in r.__table__.columns},
            user_name=r.user.name if r.user else None,
            restaurant_name=r.restaurant.name if r.restaurant else None,
        ))
    return result


@router.get("/my-reviews", response_model=List[ReviewResponse])
def get_my_reviews(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    reviews = (
        db.query(Review)
        .filter(Review.user_id == current_user.id)
        .order_by(Review.created_at.desc())
        .all()
    )
    result = []
    for r in reviews:
        result.append(ReviewResponse(
            **{c.name: getattr(r, c.name) for c in r.__table__.columns},
            user_name=current_user.name,
            restaurant_name=r.restaurant.name if r.restaurant else None,
        ))
    return result


@router.put("/{review_id}", response_model=ReviewResponse)
def update_review(review_id: int, data: ReviewUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this review")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(review, key, value)
    db.commit()
    db.refresh(review)

    _recalculate_rating(db, review.restaurant_id)

    return ReviewResponse(
        **{c.name: getattr(review, c.name) for c in review.__table__.columns},
        user_name=current_user.name,
        restaurant_name=review.restaurant.name if review.restaurant else None,
    )


@router.delete("/{review_id}", status_code=204)
def delete_review(review_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this review")

    restaurant_id = review.restaurant_id
    db.delete(review)
    db.commit()
    _recalculate_rating(db, restaurant_id)
