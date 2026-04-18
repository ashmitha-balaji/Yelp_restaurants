#!/usr/bin/env python3
"""
One-off migration: MySQL (SQLAlchemy) -> MongoDB.

Copies all Lab 1 tables into MongoDB collections for Lab 2.
Passwords remain bcrypt-hashed. Integer PKs become MongoDB _id values and
seed the counters collection so new documents get non-conflicting IDs.

Usage (from host machine, MySQL on localhost):
  export MYSQL_URL=mysql+pymysql://root:rootpass@localhost:3306/yelp_db
  export MONGODB_URL=mongodb://localhost:27017
  python lab2/migrations/mysql_to_mongo.py

From inside a Compose container (e.g. docker exec … user-service …):
  Use host name ``mysql``, not ``localhost`` — the defaults below match docker-compose.

Run this ONCE after ``docker compose up`` to backfill existing Lab 1 MySQL data into MongoDB.
"""
from __future__ import annotations

import os
import sys
from datetime import timezone

from pymongo import MongoClient


def _make_tz_aware(val):
    if val is None:
        return val
    if hasattr(val, "tzinfo") and val.tzinfo is None:
        return val.replace(tzinfo=timezone.utc)
    return val


def _upsert_counter(db, name: str, max_id: int) -> None:
    """Ensure the counter for 'name' is at least max_id."""
    existing = db.counters.find_one({"_id": name})
    if not existing or existing.get("seq", 0) < max_id:
        db.counters.update_one(
            {"_id": name}, {"$set": {"seq": max_id}}, upsert=True
        )


def migrate_table(conn, db, mysql_table: str, mongo_coll: str, pk: str = "id") -> int:
    from sqlalchemy import text
    try:
        rows = conn.execute(text(f"SELECT * FROM {mysql_table}")).mappings().all()
    except Exception as e:
        print(f"  skip {mysql_table}: {e}")
        return 0
    if not rows:
        print(f"  {mysql_table}: 0 rows")
        return 0

    docs = []
    max_id = 0
    for r in rows:
        doc = dict(r)
        pk_val = doc.pop(pk, None)
        if pk_val is not None:
            doc["_id"] = pk_val
            if isinstance(pk_val, int) and pk_val > max_id:
                max_id = pk_val

        # make all datetime fields timezone-aware
        for k, v in doc.items():
            doc[k] = _make_tz_aware(v) if hasattr(v, "year") else v
        docs.append(doc)

    coll = db[mongo_coll]
    coll.delete_many({})
    coll.insert_many(docs, ordered=False)
    print(f"  {mysql_table} → {mongo_coll}: {len(docs)} docs")
    return max_id


def _default_mysql_url() -> str:
    """Compose service name is ``mysql``; use MYSQL_HOST=localhost only when running on the host."""
    host = os.getenv("MYSQL_HOST", "mysql")
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "rootpass")
    database = os.getenv("MYSQL_DATABASE", "yelp_db")
    port = os.getenv("MYSQL_PORT", "3306")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"


def main() -> None:
    mysql_url = os.getenv("MYSQL_URL") or os.getenv("DATABASE_URL") or _default_mysql_url()
    # Inside docker-compose, MONGODB_URL is set (e.g. mongodb://mongo:27017). On the host, default local.
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB_NAME", "yelp_lab2")

    try:
        from sqlalchemy import create_engine
    except ImportError:
        print("pip install sqlalchemy pymysql", file=sys.stderr)
        sys.exit(1)

    engine = create_engine(mysql_url, connect_args={"connect_timeout": 10})
    mongo = MongoClient(mongo_url, serverSelectionTimeoutMS=8000)
    db = mongo[db_name]

    print(f"Migrating MySQL ({mysql_url}) → MongoDB ({db_name})")

    with engine.connect() as conn:
        # --- Core tables ---
        max_user = migrate_table(conn, db, "users", "users")
        max_rest = migrate_table(conn, db, "restaurants", "restaurants")
        max_rev = migrate_table(conn, db, "reviews", "reviews")
        max_fav = migrate_table(conn, db, "favorites", "favorites")
        migrate_table(conn, db, "user_preferences", "user_preferences", pk="id")
        migrate_table(conn, db, "restaurant_views", "restaurant_views")

        # Restaurant photos: embed into restaurant documents
        try:
            from sqlalchemy import text
            photos = conn.execute(text("SELECT * FROM restaurant_photos")).mappings().all()
            max_photo = 0
            if photos:
                for p in photos:
                    doc = dict(p)
                    pid = doc.pop("id", None)
                    rid = doc["restaurant_id"]
                    photo_obj = {
                        "id": pid,
                        "photo_url": doc.get("photo_url", ""),
                        "caption": doc.get("caption"),
                    }
                    db.restaurants.update_one(
                        {"_id": rid}, {"$push": {"photos": photo_obj}}
                    )
                    if pid and pid > max_photo:
                        max_photo = pid
                print(f"  restaurant_photos embedded: {len(photos)} photos")
                _upsert_counter(db, "restaurant_photos", max_photo)
        except Exception as e:
            print(f"  skip restaurant_photos: {e}")

    # Seed counters so new inserts don't collide with migrated IDs
    _upsert_counter(db, "users", max_user)
    _upsert_counter(db, "restaurants", max_rest)
    _upsert_counter(db, "reviews", max_rev)
    _upsert_counter(db, "favorites", max_fav)

    # Ensure indexes exist
    db.users.create_index("email", unique=True, background=True)
    db.reviews.create_index([("user_id", 1), ("restaurant_id", 1)], unique=True, background=True)
    db.favorites.create_index([("user_id", 1), ("restaurant_id", 1)], unique=True, background=True)

    print("Done. Verify with mongosh or MongoDB Compass.")


if __name__ == "__main__":
    main()
