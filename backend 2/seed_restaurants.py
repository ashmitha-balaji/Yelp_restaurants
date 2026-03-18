#!/usr/bin/env python3
"""
Seed the database with sample restaurants and locations.
Run from the backend directory: python seed_restaurants.py
"""
import os
import sys

# Ensure we can import from the project
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models.restaurant import Restaurant

SAMPLE_RESTAURANTS = [
    {
        "name": "Mountain Mike's Pizza",
        "cuisine_type": "Pizza",
        "description": "Family-friendly pizza restaurant with all-you-can-eat options. Great for groups and casual dining.",
        "address": "2500 Las Positas Rd",
        "city": "Livermore",
        "state": "CA",
        "zip_code": "94551",
        "country": "US",
        "phone": "(925) 447-6000",
        "price_range": "$$",
        "hours_of_operation": "Mon-Thu: 11am-10pm, Fri-Sat: 11am-11pm, Sun: 11am-9pm",
        "amenities": "Takeout, Delivery, Dine-in, Kid-friendly",
        "ambiance": "Casual, Family-friendly",
        "dietary_options": "Vegetarian",
    },
    {
        "name": "Taqueria San Juditas",
        "cuisine_type": "Mexican",
        "description": "Authentic Mexican food truck and restaurant. Famous for tacos and burritos.",
        "address": "1800 Railroad Ave",
        "city": "Livermore",
        "state": "CA",
        "zip_code": "94550",
        "country": "US",
        "phone": "(925) 555-0101",
        "price_range": "$",
        "hours_of_operation": "Mon-Sun: 10am-9pm",
        "amenities": "Takeout, Outdoor seating",
        "ambiance": "Casual",
        "dietary_options": "Vegetarian",
    },
    {
        "name": "Sakura Japanese Restaurant",
        "cuisine_type": "Japanese",
        "description": "Traditional Japanese cuisine including sushi, ramen, and teriyaki. Fresh fish daily.",
        "address": "1500 First St",
        "city": "Livermore",
        "state": "CA",
        "zip_code": "94550",
        "country": "US",
        "phone": "(925) 555-0202",
        "price_range": "$$",
        "hours_of_operation": "Tue-Sun: 11:30am-2:30pm, 5pm-9:30pm",
        "amenities": "Dine-in, Takeout, Sushi bar",
        "ambiance": "Casual, Romantic",
        "dietary_options": "Vegetarian, Gluten-free options",
    },
    {
        "name": "The Livermore Bistro",
        "cuisine_type": "American",
        "description": "Upscale American bistro with seasonal menu. Perfect for date night or special occasions.",
        "address": "2100 First St",
        "city": "Livermore",
        "state": "CA",
        "zip_code": "94550",
        "country": "US",
        "phone": "(925) 555-0303",
        "price_range": "$$$",
        "hours_of_operation": "Tue-Sat: 5pm-10pm",
        "amenities": "Reservations, Full bar, Outdoor seating",
        "ambiance": "Romantic, Upscale",
        "dietary_options": "Vegetarian, Vegan, Gluten-free",
    },
    {
        "name": "Spice of India",
        "cuisine_type": "Indian",
        "description": "Authentic North Indian cuisine. Tandoori, curries, and vegetarian options.",
        "address": "1000 East Stanley Blvd",
        "city": "Livermore",
        "state": "CA",
        "zip_code": "94550",
        "country": "US",
        "phone": "(925) 555-0404",
        "price_range": "$$",
        "hours_of_operation": "Mon-Sun: 11am-2:30pm, 5pm-9:30pm",
        "amenities": "Buffet, Takeout, Dine-in",
        "ambiance": "Casual",
        "dietary_options": "Vegetarian, Vegan",
    },
    {
        "name": "Pho Saigon",
        "cuisine_type": "Vietnamese",
        "description": "Traditional Vietnamese pho and banh mi. Comfort food at its best.",
        "address": "800 Portola Ave",
        "city": "San Jose",
        "state": "CA",
        "zip_code": "95129",
        "country": "US",
        "phone": "(408) 555-0505",
        "price_range": "$",
        "hours_of_operation": "Mon-Sun: 10am-9pm",
        "amenities": "Takeout, Dine-in",
        "ambiance": "Casual",
        "dietary_options": "Vegetarian",
    },
    {
        "name": "Koreana BBQ",
        "cuisine_type": "Korean",
        "description": "All-you-can-eat Korean BBQ. Grill your own meat at the table.",
        "address": "2500 El Camino Real",
        "city": "Santa Clara",
        "state": "CA",
        "zip_code": "95051",
        "country": "US",
        "phone": "(408) 555-0606",
        "price_range": "$$",
        "hours_of_operation": "Mon-Sun: 11am-10pm",
        "amenities": "Dine-in, All-you-can-eat",
        "ambiance": "Casual, Group-friendly",
        "dietary_options": "",
    },
    {
        "name": "Ramen House",
        "cuisine_type": "Japanese",
        "description": "Authentic ramen with rich broths. Tonkotsu, miso, and shoyu options.",
        "address": "500 Castro St",
        "city": "Mountain View",
        "state": "CA",
        "zip_code": "94041",
        "country": "US",
        "phone": "(650) 555-0707",
        "price_range": "$$",
        "hours_of_operation": "Mon-Sun: 11am-10pm",
        "amenities": "Dine-in, Takeout",
        "ambiance": "Casual",
        "dietary_options": "Vegetarian",
    },
    {
        "name": "Bella Italia",
        "cuisine_type": "Italian",
        "description": "Classic Italian pasta, pizza, and wine. Family-owned since 1995.",
        "address": "1200 Main St",
        "city": "Pleasanton",
        "state": "CA",
        "zip_code": "94566",
        "country": "US",
        "phone": "(925) 555-0808",
        "price_range": "$$",
        "hours_of_operation": "Tue-Sun: 11am-10pm",
        "amenities": "Dine-in, Takeout, Wine bar",
        "ambiance": "Romantic, Family-friendly",
        "dietary_options": "Vegetarian, Gluten-free pasta",
    },
    {
        "name": "Thai Orchid",
        "cuisine_type": "Thai",
        "description": "Traditional Thai cuisine with bold flavors. Pad thai, curries, and stir-fries.",
        "address": "600 W Calaveras Blvd",
        "city": "Milpitas",
        "state": "CA",
        "zip_code": "95035",
        "country": "US",
        "phone": "(408) 555-0909",
        "price_range": "$$",
        "hours_of_operation": "Mon-Sun: 11am-9:30pm",
        "amenities": "Dine-in, Takeout, Delivery",
        "ambiance": "Casual",
        "dietary_options": "Vegetarian, Vegan",
    },
]


def seed(force=False):
    db = SessionLocal()
    try:
        existing = db.query(Restaurant).count()
        if existing > 0 and not force:
            print(f"Database already has {existing} restaurants. Skipping seed.")
            print("Run with --force to add sample data anyway.")
            return

        for data in SAMPLE_RESTAURANTS:
            r = Restaurant(**data)
            db.add(r)

        db.commit()
        print(f"✓ Added {len(SAMPLE_RESTAURANTS)} sample restaurants.")
        print("\nCities included: Livermore, San Jose, Santa Clara, Mountain View, Pleasanton, Milpitas")
        print("\nYou can now search for restaurants by name, cuisine, or city!")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    force = "--force" in sys.argv
    seed(force=force)
