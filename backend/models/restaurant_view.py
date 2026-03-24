from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class RestaurantView(Base):
    __tablename__ = "restaurant_views"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    viewed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    restaurant = relationship("Restaurant")
    user = relationship("User")
