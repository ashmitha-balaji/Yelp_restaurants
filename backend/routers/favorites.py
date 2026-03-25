from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from database import get_db
from models.user import User
from models.restaurant import Restaurant
from models.favorite import Favorite
from schemas.favorite import FavoriteCreate, FavoriteResponse
from utils.auth import get_current_user

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.post("/", response_model=FavoriteResponse, status_code=201)
def add_favorite(data: FavoriteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    restaurant = db.query(Restaurant).filter(Restaurant.id == data.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.restaurant_id == data.restaurant_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Restaurant is already in favorites")

    fav = Favorite(user_id=current_user.id, restaurant_id=data.restaurant_id)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return fav


@router.get("/", response_model=List[FavoriteResponse])
def get_favorites(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    favorites = (
        db.query(Favorite)
        .options(joinedload(Favorite.restaurant))
        .filter(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )
    return favorites


@router.delete("/{restaurant_id}", status_code=204)
def remove_favorite(restaurant_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    fav = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.restaurant_id == restaurant_id,
    ).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(fav)
    db.commit()


@router.get("/check/{restaurant_id}")
def check_favorite(restaurant_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    fav = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.restaurant_id == restaurant_id,
    ).first()
    return {"is_favorite": fav is not None}
