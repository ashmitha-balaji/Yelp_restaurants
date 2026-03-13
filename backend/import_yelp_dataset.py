#!/usr/bin/env python3
"""
Import restaurants from Yelp Open Dataset (yelp_dataset.tar) into the database.
Reads directly from the tar file - no need to extract first.

Usage:
  cd backend
  python import_yelp_dataset.py [--limit N] [--state CA]

Options:
  --limit N    Import at most N restaurants (default: 5000)
  --state XX   Only import businesses in this state (e.g. CA, NY)
"""
import argparse
import json
import os
import sys
import tarfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models.restaurant import Restaurant

# Path to the Yelp dataset tar (in lab-1/datasets/Yelp JSON/)
YELP_TAR_PATH = os.path.join(os.path.dirname(__file__), "..", "datasets", "Yelp JSON", "yelp_dataset.tar")
BUSINESS_JSON = "yelp_academic_dataset_business.json"


def parse_price_range(attrs):
    """Map Yelp RestaurantsPriceRange2 (1-4) to $, $$, $$$, $$$$"""
    if not attrs or not isinstance(attrs, dict):
        return None
    val = attrs.get("RestaurantsPriceRange2")
    if val is None:
        return None
    try:
        n = int(val)
        return "$" * min(max(n, 1), 4)
    except (ValueError, TypeError):
        return None


def format_hours(hours):
    """Convert Yelp hours dict to readable string"""
    if not hours or not isinstance(hours, dict):
        return None
    parts = []
    for day, time_range in hours.items():
        if time_range:
            parts.append(f"{day}: {time_range}")
    return ", ".join(parts) if parts else None


def get_cuisine_type(categories):
    """Extract cuisine type from Yelp categories. Skip generic ones like Restaurants, Food."""
    if not categories:
        return None
    skip = {"Restaurants", "Food", "Restaurant", "Food and Drink"}
    for cat in categories.split(","):
        cat = cat.strip()
        if cat and cat not in skip:
            return cat[:100]  # Limit length
    return "Restaurant"


def yelp_to_restaurant(row):
    """Convert a Yelp business JSON row to our Restaurant model fields."""
    attrs = row.get("attributes") or {}
    categories = row.get("categories") or ""

    # Only import if "Restaurants" is in categories
    if "Restaurants" not in categories:
        return None

    price = parse_price_range(attrs)
    hours_str = format_hours(row.get("hours"))

    return {
        "name": (row.get("name") or "Unknown")[:200],
        "address": (row.get("address") or "")[:500],
        "city": (row.get("city") or "")[:100],
        "state": (row.get("state") or "")[:10],
        "zip_code": (row.get("postal_code") or "")[:20],
        "country": "US",
        "cuisine_type": get_cuisine_type(categories),
        "price_range": price,
        "hours_of_operation": hours_str,
        "average_rating": float(row.get("stars", 0) or 0),
        "review_count": int(row.get("review_count", 0) or 0),
        "description": None,  # Yelp business JSON doesn't have description
    }


def run_import(limit=5000, state_filter=None):
    if not os.path.exists(YELP_TAR_PATH):
        print(f"Error: {YELP_TAR_PATH} not found.")
        print("Make sure 'datasets/Yelp JSON/yelp_dataset.tar' exists in the lab-1 folder.")
        return

    db = SessionLocal()
    imported = 0
    skipped = 0

    try:
        with tarfile.open(YELP_TAR_PATH, "r") as tar:
            member = tar.getmember(BUSINESS_JSON)
            f = tar.extractfile(member)
            if not f:
                print("Could not read business.json from tar")
                return

            for line in f:
                if imported >= limit:
                    break

                line = line.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    skipped += 1
                    continue

                if state_filter and row.get("state") != state_filter:
                    continue

                data = yelp_to_restaurant(row)
                if not data:
                    continue

                try:
                    r = Restaurant(**data)
                    db.add(r)
                    imported += 1
                    if imported % 500 == 0:
                        print(f"  Imported {imported}...")
                        db.commit()
                except Exception as e:
                    skipped += 1
                    if skipped <= 3:
                        print(f"  Skip: {data.get('name', '?')} - {e}")

        db.commit()
        print(f"\n✓ Imported {imported} restaurants into the database.")
        if skipped:
            print(f"  (Skipped {skipped} rows)")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import Yelp dataset restaurants")
    parser.add_argument("--limit", type=int, default=5000, help="Max restaurants to import")
    parser.add_argument("--state", type=str, default=None, help="Filter by state (e.g. CA)")
    args = parser.parse_args()

    print(f"Reading from {YELP_TAR_PATH}")
    print(f"Importing up to {args.limit} restaurants" + (f" in state {args.state}" if args.state else ""))
    run_import(limit=args.limit, state_filter=args.state)
