from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


class UserSignup(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "user"
    restaurant_location: Optional[str] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in ("user", "owner"):
            raise ValueError("role must be 'user' or 'owner'")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    about_me: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    languages: Optional[str] = None
    gender: Optional[str] = None


class UserPreferenceUpdate(BaseModel):
    cuisine_preferences: Optional[str] = None
    price_range: Optional[str] = None
    preferred_locations: Optional[str] = None
    search_radius: Optional[int] = None
    dietary_needs: Optional[str] = None
    ambiance_preferences: Optional[str] = None
    sort_preference: Optional[str] = None


class UserPreferenceResponse(BaseModel):
    id: int
    user_id: int
    cuisine_preferences: Optional[str] = None
    price_range: Optional[str] = None
    preferred_locations: Optional[str] = None
    search_radius: Optional[int] = None
    dietary_needs: Optional[str] = None
    ambiance_preferences: Optional[str] = None
    sort_preference: Optional[str] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    about_me: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    languages: Optional[str] = None
    gender: Optional[str] = None
    profile_picture: Optional[str] = None
    restaurant_location: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
