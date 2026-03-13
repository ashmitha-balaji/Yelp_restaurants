import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List, Optional
from database import get_db
from models.user import User
from models.restaurant import Restaurant, RestaurantPhoto
from schemas.restaurant import RestaurantCreate, RestaurantUpdate, RestaurantResponse
from utils.auth import get_current_user, get_optional_user
from config import UPLOAD_DIR

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


@router.post("/", response_model=RestaurantResponse, status_code=201)
def create_restaurant(data: RestaurantCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    restaurant = Restaurant(
        owner_id=current_user.id if current_user.role == "owner" else None,
        **data.model_dump(),
    )
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant


def _parse_city_from_location(location: str) -> str:
    """Extract city name from 'San Jose, CA' or 'Livermore, CA' -> 'San Jose' / 'Livermore'"""
    if not location or not location.strip():
        return location or ""
    return location.split(",")[0].strip()


@router.get("/", response_model=List[RestaurantResponse])
def search_restaurants(
    name: Optional[str] = Query(None),
    cuisine_type: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    zip_code: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    price_range: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Restaurant).options(joinedload(Restaurant.photos))

    # Parse "San Jose, CA" -> "San Jose" so it matches DB city field
    city_filter = _parse_city_from_location(city) if city else None

    if name:
        query = query.filter(Restaurant.name.ilike(f"%{name}%"))
    if cuisine_type:
        query = query.filter(Restaurant.cuisine_type.ilike(f"%{cuisine_type}%"))
    if city_filter:
        query = query.filter(Restaurant.city.ilike(f"%{city_filter}%"))
    if zip_code:
        query = query.filter(Restaurant.zip_code == zip_code)
    if price_range:
        query = query.filter(Restaurant.price_range == price_range)
    # Skip keyword filter for generic "Restaurants" - DB only has restaurants
    if keyword and keyword.strip().lower() not in ("restaurants", "restaurant"):
        keyword_filter = f"%{keyword}%"
        query = query.filter(
            or_(
                Restaurant.name.ilike(keyword_filter),
                Restaurant.cuisine_type.ilike(keyword_filter),
                Restaurant.description.ilike(keyword_filter),
                Restaurant.amenities.ilike(keyword_filter),
                Restaurant.ambiance.ilike(keyword_filter),
            )
        )

    offset = (page - 1) * limit
    restaurants = query.order_by(Restaurant.average_rating.desc()).offset(offset).limit(limit).all()
    return restaurants


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    restaurant = (
        db.query(Restaurant)
        .options(joinedload(Restaurant.photos))
        .filter(Restaurant.id == restaurant_id)
        .first()
    )
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant


@router.put("/{restaurant_id}", response_model=RestaurantResponse)
def update_restaurant(
    restaurant_id: int,
    data: RestaurantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if restaurant.owner_id and restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this restaurant")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(restaurant, key, value)
    db.commit()
    db.refresh(restaurant)
    return restaurant


@router.post("/{restaurant_id}/claim", response_model=RestaurantResponse)
def claim_restaurant(restaurant_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can claim restaurants")

    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if restaurant.is_claimed:
        raise HTTPException(status_code=400, detail="Restaurant is already claimed")

    restaurant.owner_id = current_user.id
    restaurant.is_claimed = True
    db.commit()
    db.refresh(restaurant)
    return restaurant


@router.post("/{restaurant_id}/photos")
async def upload_restaurant_photo(
    restaurant_id: int,
    file: UploadFile = File(...),
    caption: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    ext = os.path.splitext(file.filename)[1]
    filename = f"restaurant_{restaurant_id}_{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)

    photo = RestaurantPhoto(
        restaurant_id=restaurant_id,
        photo_url=f"/uploads/{filename}",
        caption=caption,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return {"id": photo.id, "photo_url": photo.photo_url, "caption": photo.caption}


@router.get("/owner/my-restaurants", response_model=List[RestaurantResponse])
def get_owner_restaurants(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    restaurants = (
        db.query(Restaurant)
        .options(joinedload(Restaurant.photos))
        .filter(Restaurant.owner_id == current_user.id)
        .all()
    )
    return restaurants
