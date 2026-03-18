from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("user", "owner", name="user_role"), default="user", nullable=False)
    phone = Column(String(20), nullable=True)
    about_me = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(10), nullable=True)
    country = Column(String(100), nullable=True)
    languages = Column(String(255), nullable=True)
    gender = Column(Enum("male", "female", "other", "prefer_not_to_say", name="gender_type"), nullable=True)
    profile_picture = Column(String(500), nullable=True)
    restaurant_location = Column(String(255), nullable=True)  # for owners
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    restaurants = relationship("Restaurant", back_populates="owner", cascade="all, delete-orphan")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    cuisine_preferences = Column(Text, nullable=True)       # comma-separated: "Italian,Chinese,Mexican"
    price_range = Column(String(20), nullable=True)          # "$", "$$", "$$$", "$$$$"
    preferred_locations = Column(Text, nullable=True)        # comma-separated locations
    search_radius = Column(Integer, nullable=True)           # in miles
    dietary_needs = Column(Text, nullable=True)              # comma-separated: "vegetarian,vegan"
    ambiance_preferences = Column(Text, nullable=True)       # comma-separated: "casual,romantic"
    sort_preference = Column(String(50), nullable=True)      # "rating", "distance", "popularity", "price"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="preferences")
