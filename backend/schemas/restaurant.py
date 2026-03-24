from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RestaurantCreate(BaseModel):
    name: str
    cuisine_type: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = "US"
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    price_range: Optional[str] = None
    hours_of_operation: Optional[str] = None
    amenities: Optional[str] = None
    ambiance: Optional[str] = None
    dietary_options: Optional[str] = None


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    cuisine_type: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    price_range: Optional[str] = None
    hours_of_operation: Optional[str] = None
    amenities: Optional[str] = None
    ambiance: Optional[str] = None
    dietary_options: Optional[str] = None


class PhotoResponse(BaseModel):
    id: int
    photo_url: str
    caption: Optional[str] = None

    class Config:
        from_attributes = True


class RestaurantResponse(BaseModel):
    id: int
    owner_id: Optional[int] = None
    name: str
    cuisine_type: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    price_range: Optional[str] = None
    hours_of_operation: Optional[str] = None
    amenities: Optional[str] = None
    ambiance: Optional[str] = None
    dietary_options: Optional[str] = None
    average_rating: Optional[float] = 0.0
    review_count: Optional[int] = 0
    is_claimed: Optional[bool] = False
    photos: List[PhotoResponse] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RestaurantSearchQuery(BaseModel):
    name: Optional[str] = None
    cuisine_type: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    keyword: Optional[str] = None
    price_range: Optional[str] = None
    page: int = 1
    limit: int = 20
