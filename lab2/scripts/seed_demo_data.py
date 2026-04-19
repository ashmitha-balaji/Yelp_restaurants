"""Seed Lab 2 MongoDB with demo users, owners, and restaurants.

Usage:
  python lab2/scripts/seed_demo_data.py

This script is idempotent for seeded accounts:
- Creates/updates 3 regular users and their preferences.
- Creates/updates 3 owner users.
- Recreates owner restaurants with distribution 5 / 3 / 4 in San Jose.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import bcrypt
import re

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from mongo_client import get_db, get_next_id  # type: ignore


SEED_TAG = "lab2_demo_seed_v1"
DEFAULT_PASSWORD = "Demo@12345"


USERS: List[Dict[str, str]] = [
    {
        "name": "Alice Nguyen",
        "email": "namanvipul.chheda@sjsu.edu",
        "password": "naman123",
        "role": "user",
        "city": "San Jose",
        "state": "CA",
        "country": "USA",
        "phone": "+1-408-555-1001",
    },
    {
        "name": "Brian Patel",
        "email": "ashmitha@gmail.com",
        "password": "ashmitha123",
        "role": "user",
        "city": "San Jose",
        "state": "CA",
        "country": "USA",
        "phone": "+1-408-555-1002",
    },
    {
        "name": "Carla Martinez",
        "email": "carla.user.demo@example.com",
        "password": DEFAULT_PASSWORD,
        "role": "user",
        "city": "San Jose",
        "state": "CA",
        "country": "USA",
        "phone": "+1-408-555-1003",
    },
]


USER_PREFERENCES: Dict[str, Dict[str, object]] = {
    "namanvipul.chheda@sjsu.edu": {
        "cuisine_preferences": "Japanese,Thai",
        "price_range": "$$",
        "preferred_locations": "San Jose",
        "search_radius": 8,
        "dietary_needs": "vegetarian",
        "ambiance_preferences": "casual",
        "sort_preference": "rating",
    },
    "ashmitha@gmail.com": {
        "cuisine_preferences": "Mexican,American",
        "price_range": "$",
        "preferred_locations": "San Jose",
        "search_radius": 10,
        "dietary_needs": "halal",
        "ambiance_preferences": "family_friendly",
        "sort_preference": "price_low_to_high",
    },
    "carla.user.demo@example.com": {
        "cuisine_preferences": "Italian,Mediterranean",
        "price_range": "$$$",
        "preferred_locations": "San Jose",
        "search_radius": 12,
        "dietary_needs": "gluten_free",
        "ambiance_preferences": "fine_dining",
        "sort_preference": "popularity",
    },
}


OWNERS: List[Dict[str, str]] = [
    {
        "name": "David Kim",
        "email": "lewishamilton@gmail.com",
        "password": "lewis123",
        "role": "owner",
        "restaurant_location": "San Jose, CA",
        "phone": "+1-408-555-2001",
    },
    {
        "name": "Elena Garcia",
        "email": "maxv@gmail.com",
        "password": "max1234",
        "role": "owner",
        "restaurant_location": "San Jose, CA",
        "phone": "+1-408-555-2002",
    },
    {
        "name": "Farhan Ali",
        "email": "owner.three.demo@example.com",
        "password": DEFAULT_PASSWORD,
        "role": "owner",
        "restaurant_location": "San Jose, CA",
        "phone": "+1-408-555-2003",
    },
]


OWNER_RESTAURANTS: Dict[str, List[Dict[str, str]]] = {
    "lewishamilton@gmail.com": [
        {
            "name": "Willow Street Thai Kitchen",
            "cuisine_type": "Thai",
            "description": "Neighborhood Thai spot with vegetarian options and lunch specials.",
            "address": "1250 Willow St",
            "zip_code": "95125",
            "phone": "+1-408-555-3101",
            "email": "contact@willowthai.example.com",
            "website": "https://willowthai.example.com",
            "price_range": "$$",
            "hours_of_operation": "Mon-Sun 11:00-22:00",
            "amenities": "WiFi,Outdoor Seating",
            "ambiance": "casual",
            "dietary_options": "vegetarian,vegan",
        },
        {
            "name": "Japantown Ramen House",
            "cuisine_type": "Japanese",
            "description": "Handcrafted ramen and small plates in a lively setting.",
            "address": "624 N 6th St",
            "zip_code": "95112",
            "phone": "+1-408-555-3102",
            "email": "hello@ramenhouse.example.com",
            "website": "https://ramenhouse.example.com",
            "price_range": "$$",
            "hours_of_operation": "Mon-Sun 12:00-22:30",
            "amenities": "Takeout,Delivery",
            "ambiance": "casual",
            "dietary_options": "vegetarian",
        },
        {
            "name": "Downtown Fusion Grill",
            "cuisine_type": "American",
            "description": "Modern grill menu with seasonal cocktails and late hours.",
            "address": "88 S 4th St",
            "zip_code": "95112",
            "phone": "+1-408-555-3103",
            "email": "team@fusiongrill.example.com",
            "website": "https://fusiongrill.example.com",
            "price_range": "$$$",
            "hours_of_operation": "Tue-Sun 16:00-23:00",
            "amenities": "Bar,Reservation",
            "ambiance": "upscale",
            "dietary_options": "gluten_free",
        },
        {
            "name": "Rose Garden Mediterranean",
            "cuisine_type": "Mediterranean",
            "description": "Fresh kebabs, mezze platters, and family-style dining.",
            "address": "1234 Naglee Ave",
            "zip_code": "95126",
            "phone": "+1-408-555-3104",
            "email": "hi@rosegardenmed.example.com",
            "website": "https://rosegardenmed.example.com",
            "price_range": "$$",
            "hours_of_operation": "Mon-Sun 11:30-21:30",
            "amenities": "Family Seating,Parking",
            "ambiance": "family_friendly",
            "dietary_options": "halal,vegetarian",
        },
        {
            "name": "Santana Row Fine Table",
            "cuisine_type": "Italian",
            "description": "Chef-driven Italian tasting menu in an elegant dining room.",
            "address": "377 Santana Row",
            "zip_code": "95128",
            "phone": "+1-408-555-3105",
            "email": "reserve@fintable.example.com",
            "website": "https://fintable.example.com",
            "price_range": "$$$$",
            "hours_of_operation": "Wed-Sun 17:00-23:00",
            "amenities": "Reservation,Valet",
            "ambiance": "fine_dining",
            "dietary_options": "gluten_free",
        },
    ],
    "maxv@gmail.com": [
        {
            "name": "Alum Rock Tacos",
            "cuisine_type": "Mexican",
            "description": "Street-style tacos and burritos with fast service.",
            "address": "2121 Alum Rock Ave",
            "zip_code": "95116",
            "phone": "+1-408-555-3201",
            "email": "orders@alumrocktacos.example.com",
            "website": "https://alumrocktacos.example.com",
            "price_range": "$",
            "hours_of_operation": "Mon-Sun 10:00-22:00",
            "amenities": "Takeout,Delivery",
            "ambiance": "casual",
            "dietary_options": "halal",
        },
        {
            "name": "Little Saigon Pho Corner",
            "cuisine_type": "Vietnamese",
            "description": "Traditional pho and banh mi in East San Jose.",
            "address": "1688 Tully Rd",
            "zip_code": "95122",
            "phone": "+1-408-555-3202",
            "email": "contact@phocorner.example.com",
            "website": "https://phocorner.example.com",
            "price_range": "$$",
            "hours_of_operation": "Mon-Sun 09:00-21:00",
            "amenities": "Parking,Takeout",
            "ambiance": "casual",
            "dietary_options": "gluten_free",
        },
        {
            "name": "Evergreen Family Diner",
            "cuisine_type": "American",
            "description": "Comfort food and all-day breakfast for families.",
            "address": "2975 Aborn Rd",
            "zip_code": "95135",
            "phone": "+1-408-555-3203",
            "email": "hello@evergreendiner.example.com",
            "website": "https://evergreendiner.example.com",
            "price_range": "$$",
            "hours_of_operation": "Mon-Sun 07:00-21:00",
            "amenities": "Kids Menu,Parking",
            "ambiance": "family_friendly",
            "dietary_options": "vegetarian",
        },
    ],
    "owner.three.demo@example.com": [
        {
            "name": "Campbell Avenue Bistro",
            "cuisine_type": "French",
            "description": "Classic bistro plates with rotating wine selection.",
            "address": "72 N First St",
            "zip_code": "95113",
            "phone": "+1-408-555-3301",
            "email": "info@campbellbistro.example.com",
            "website": "https://campbellbistro.example.com",
            "price_range": "$$$",
            "hours_of_operation": "Tue-Sun 17:00-22:00",
            "amenities": "Wine Bar,Reservation",
            "ambiance": "romantic",
            "dietary_options": "vegetarian",
        },
        {
            "name": "San Pedro Seafood House",
            "cuisine_type": "Seafood",
            "description": "Fresh oysters, grilled fish, and weekend brunch.",
            "address": "95 N San Pedro St",
            "zip_code": "95110",
            "phone": "+1-408-555-3302",
            "email": "bookings@sanpedroseafood.example.com",
            "website": "https://sanpedroseafood.example.com",
            "price_range": "$$$",
            "hours_of_operation": "Wed-Mon 11:00-22:00",
            "amenities": "Outdoor Seating,Reservation",
            "ambiance": "upscale",
            "dietary_options": "gluten_free",
        },
        {
            "name": "Bascom Vegan Cafe",
            "cuisine_type": "Cafe",
            "description": "Plant-based cafe with smoothies, bowls, and salads.",
            "address": "1510 Bascom Ave",
            "zip_code": "95128",
            "phone": "+1-408-555-3303",
            "email": "hi@bascomvegan.example.com",
            "website": "https://bascomvegan.example.com",
            "price_range": "$$",
            "hours_of_operation": "Mon-Sun 08:00-20:00",
            "amenities": "WiFi,Takeout",
            "ambiance": "casual",
            "dietary_options": "vegan,gluten_free",
        },
        {
            "name": "Berryessa Kebab House",
            "cuisine_type": "Middle Eastern",
            "description": "Charcoal kebabs, rice plates, and fresh wraps.",
            "address": "1790 Berryessa Rd",
            "zip_code": "95133",
            "phone": "+1-408-555-3304",
            "email": "orders@berryessakebab.example.com",
            "website": "https://berryessakebab.example.com",
            "price_range": "$$",
            "hours_of_operation": "Mon-Sun 11:00-22:00",
            "amenities": "Halal,Takeout,Delivery",
            "ambiance": "family_friendly",
            "dietary_options": "halal",
        },
    ],
}


def hash_password_for_seed(raw_password: str) -> str:
    """Create bcrypt hash without passlib dependency quirks in local env."""
    return bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")


def upsert_user(account: Dict[str, str]) -> int:
    db = get_db()
    now = datetime.now(timezone.utc)
    existing = db.users.find_one({"email": account["email"]})
    base = {
        "name": account["name"],
        "email": account["email"],
        "password_hash": hash_password_for_seed(account.get("password", DEFAULT_PASSWORD)),
        "role": account["role"],
        "phone": account.get("phone"),
        "city": account.get("city", "San Jose"),
        "state": account.get("state", "CA"),
        "country": account.get("country", "USA"),
        "restaurant_location": account.get("restaurant_location"),
        "updated_at": now,
        "seed_source": SEED_TAG,
    }
    if existing:
        db.users.update_one({"_id": existing["_id"]}, {"$set": base})
        return int(existing["_id"])

    user_id = get_next_id("users")
    doc = {
        "_id": user_id,
        **base,
        "created_at": now,
    }
    db.users.insert_one(doc)
    return user_id


def upsert_preferences(user_id: int, email: str) -> None:
    db = get_db()
    prefs = USER_PREFERENCES[email]
    db.user_preferences.update_one(
        {"user_id": user_id},
        {
            "$set": {
                **prefs,
                "user_id": user_id,
                "seed_source": SEED_TAG,
                "updated_at": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )


def recreate_owner_restaurants(owner_id: int, owner_email: str) -> int:
    db = get_db()
    now = datetime.now(timezone.utc)
    created = 0
    active_seed_keys: List[str] = []
    for idx, r in enumerate(OWNER_RESTAURANTS[owner_email], start=1):
        seed_key = f"{owner_email}:{_slugify(r['name'])}"
        active_seed_keys.append(seed_key)
        rating = round(3.8 + (idx * 0.2), 1)
        review_count = 20 + idx * 7
        existing = db.restaurants.find_one({"seed_key": seed_key})
        if existing:
            rest_id = int(existing["_id"])
        else:
            rest_id = get_next_id("restaurants")
        doc = {
            "owner_id": owner_id,
            "name": r["name"],
            "cuisine_type": r["cuisine_type"],
            "description": r["description"],
            "address": r["address"],
            "city": "San Jose",
            "state": "CA",
            "zip_code": r["zip_code"],
            "country": "US",
            "phone": r["phone"],
            "email": r["email"],
            "website": r["website"],
            "price_range": r["price_range"],
            "hours_of_operation": r["hours_of_operation"],
            "amenities": r["amenities"],
            "ambiance": r["ambiance"],
            "dietary_options": r["dietary_options"],
            "average_rating": min(rating, 5.0),
            "review_count": review_count,
            "is_claimed": True,
            "photos": [],
            "seed_source": SEED_TAG,
            "seed_key": seed_key,
            "updated_at": now,
        }
        if existing:
            db.restaurants.update_one({"_id": rest_id}, {"$set": doc, "$setOnInsert": {"created_at": now}})
        else:
            db.restaurants.insert_one({"_id": rest_id, **doc, "created_at": now})
        created += 1
    # Remove outdated restaurants from this seed for this owner only.
    db.restaurants.delete_many(
        {
            "owner_id": owner_id,
            "seed_source": SEED_TAG,
            "seed_key": {"$nin": active_seed_keys},
        }
    )
    return created


def main() -> None:
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB_NAME", "yelp_lab2")
    print(f"Seeding MongoDB at {mongo_url} (db={db_name})")

    regular_user_ids: Dict[str, int] = {}
    for account in USERS:
        uid = upsert_user(account)
        regular_user_ids[account["email"]] = uid
        upsert_preferences(uid, account["email"])

    owner_ids: Dict[str, int] = {}
    for owner in OWNERS:
        oid = upsert_user(owner)
        owner_ids[owner["email"]] = oid

    total_restaurants = 0
    for owner_email, owner_id in owner_ids.items():
        total_restaurants += recreate_owner_restaurants(owner_id, owner_email)

    print("\nSeed complete.")
    print(f"- Users (role=user): {len(regular_user_ids)}")
    print(f"- Owners (role=owner): {len(owner_ids)}")
    print(f"- Restaurants created: {total_restaurants} (expected 12)")
    print("- Seeded account credentials:")
    for account in [*USERS, *OWNERS]:
        print(f"  - {account['role']}: {account['email']} / {account.get('password', DEFAULT_PASSWORD)}")
    print("- All seeded restaurants are in San Jose, CA.")


if __name__ == "__main__":
    main()
