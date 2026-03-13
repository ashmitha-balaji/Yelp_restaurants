from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from schemas.restaurant import RestaurantResponse


class FavoriteCreate(BaseModel):
    restaurant_id: int


class FavoriteResponse(BaseModel):
    id: int
    user_id: int
    restaurant_id: int
    created_at: Optional[datetime] = None
    restaurant: Optional[RestaurantResponse] = None

    class Config:
        from_attributes = True
