from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(200), nullable=False, index=True)
    cuisine_type = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True, index=True)
    state = Column(String(10), nullable=True)
    zip_code = Column(String(20), nullable=True)
    country = Column(String(100), default="US")
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)
    price_range = Column(String(10), nullable=True)     # "$", "$$", "$$$", "$$$$"
    hours_of_operation = Column(Text, nullable=True)     # JSON string
    amenities = Column(Text, nullable=True)              # comma-separated
    ambiance = Column(String(100), nullable=True)
    dietary_options = Column(Text, nullable=True)        # comma-separated: "vegetarian,vegan,gluten-free"
    average_rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    is_claimed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="restaurants")
    photos = relationship("RestaurantPhoto", back_populates="restaurant", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="restaurant", cascade="all, delete-orphan")
    favorited_by = relationship("Favorite", back_populates="restaurant", cascade="all, delete-orphan")


class RestaurantPhoto(Base):
    __tablename__ = "restaurant_photos"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    photo_url = Column(String(500), nullable=False)
    caption = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    restaurant = relationship("Restaurant", back_populates="photos")
