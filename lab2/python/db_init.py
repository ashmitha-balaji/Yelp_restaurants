"""
Lab 2 database initialisation.

init_mongo_db()     — creates MongoDB indexes for all Lab 2 collections.
safe_create_all()   — kept for Lab 1 monolith backward-compatibility;
                      creates MySQL tables via SQLAlchemy, ignoring 1050 races.
"""
from __future__ import annotations


def init_mongo_db() -> None:
    """Create MongoDB indexes.  Safe to call multiple times (idempotent)."""
    from mongo_client import get_db
    db = get_db()

    db.users.create_index("email", unique=True, background=True)

    db.restaurants.create_index("name", background=True)
    db.restaurants.create_index("city", background=True)
    db.restaurants.create_index("cuisine_type", background=True)
    db.restaurants.create_index([("average_rating", -1)], background=True)

    db.reviews.create_index("user_id", background=True)
    db.reviews.create_index("restaurant_id", background=True)
    db.reviews.create_index(
        [("user_id", 1), ("restaurant_id", 1)], unique=True, background=True
    )

    db.favorites.create_index(
        [("user_id", 1), ("restaurant_id", 1)], unique=True, background=True
    )

    db.sessions.create_index("expires_at", expireAfterSeconds=0, background=True)

    db.review_jobs.create_index("job_id", unique=True, background=True)

    db.restaurant_views.create_index("restaurant_id", background=True)
    db.restaurant_views.create_index("viewed_at", background=True)

    db.user_preferences.create_index("user_id", unique=True, background=True)


def safe_create_all() -> None:
    """Lab 1 backward-compat: create MySQL tables, silently skip if tables already exist."""
    import models  # noqa: F401 — register all ORM models on Base.metadata
    from sqlalchemy.exc import OperationalError
    from database import Base, engine
    try:
        Base.metadata.create_all(bind=engine)
    except OperationalError as e:
        msg = str(e.orig) if getattr(e, "orig", None) is not None else str(e)
        if "1050" in msg or "already exists" in msg.lower():
            return
        raise
