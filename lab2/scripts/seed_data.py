#!/usr/bin/env python3
"""
Seed script to populate the Yelp Lab2 app with 300 sample restaurants and reviews.
Usage: python3 lab2/scripts/seed_data.py
Requires: requests library (pip install requests)
"""

import requests
import random
import sys

BASE_URL = "http://localhost:8000"

SEED_USER = {
    "name": "Seed Admin",
    "email": "seed@yelp.com",
    "password": "Seed1234!",
    "role": "user"
}

CUISINES = [
    "Italian", "Japanese", "Mexican", "Chinese", "Indian",
    "American", "French", "Korean", "Thai", "Vietnamese",
    "Mediterranean", "Greek", "Spanish", "Lebanese", "Turkish",
    "Ethiopian", "Peruvian", "Brazilian", "Caribbean", "Filipino",
]

PRICE_RANGES = ["$", "$$", "$$$", "$$$$"]

ADJECTIVES = [
    "Golden", "Silver", "Royal", "Grand", "Little", "Big", "Happy",
    "Lucky", "Famous", "Original", "Classic", "Modern", "Ancient",
    "Secret", "Hidden", "Local", "Urban", "Rustic", "Cozy", "Lively",
    "Spicy", "Sweet", "Fresh", "Authentic", "Traditional", "New",
    "Old", "Blue", "Red", "Green", "Pearl", "Jade", "Crystal",
]

NOUNS = [
    "Kitchen", "Bistro", "Grill", "Garden", "Palace", "House",
    "Table", "Fork", "Spoon", "Bowl", "Plate", "Pot", "Flame",
    "Fire", "Ember", "Leaf", "Root", "Vine", "Bloom", "Stone",
    "Harbor", "Pier", "Market", "Corner", "Place", "Spot", "Den",
    "Lounge", "Terrace", "Courtyard", "Hall", "Room", "Bar",
]

STREETS = [
    "Main St", "Oak Ave", "Elm St", "Maple Rd", "Cedar Blvd",
    "Pine Way", "Sunset Dr", "Broadway", "Park Ave", "Lake Rd",
    "River Ln", "Hill St", "Valley Rd", "Forest Ave", "Garden Way",
    "Willow St", "Cherry Ln", "Peach St", "Rose Ave", "Lily Rd",
    "Curry Lane", "Noodle Way", "Spice Blvd", "Olive St", "Bamboo Rd",
    "Lotus Blvd", "Fiesta Ave", "Kimchi Ave", "Sushi Rd", "Taco St",
]

CITIES = [
    ("San Jose", "CA", "951"),
    ("San Francisco", "CA", "941"),
    ("Oakland", "CA", "946"),
    ("Berkeley", "CA", "947"),
    ("Palo Alto", "CA", "943"),
    ("Mountain View", "CA", "940"),
    ("Sunnyvale", "CA", "940"),
    ("Santa Clara", "CA", "950"),
    ("Fremont", "CA", "945"),
    ("Milpitas", "CA", "950"),
]

DESCRIPTIONS = {
    "Italian": [
        "Handmade pasta, wood-fired pizzas, and classic Italian dishes in a warm, family-friendly atmosphere.",
        "Authentic Roman-style trattoria serving traditional recipes passed down through generations.",
        "Northern Italian cuisine featuring risottos, osso buco, and an extensive wine list.",
        "Neapolitan pizza masters using imported Italian flour and San Marzano tomatoes.",
    ],
    "Japanese": [
        "Fresh sushi and sashimi crafted by master chefs with over 20 years of experience.",
        "Traditional ramen shop with broths simmered for 18 hours, topped with premium ingredients.",
        "Omakase dining experience featuring seasonal ingredients flown in directly from Japan.",
        "Casual izakaya with yakitori, takoyaki, and a wide selection of sake and Japanese whisky.",
    ],
    "Mexican": [
        "Street-style tacos and burritos made fresh daily with locally sourced ingredients.",
        "Traditional mole sauces, slow-cooked carnitas, and handmade tortillas from heirloom corn.",
        "Modern Mexican cuisine with creative cocktails and a lively rooftop atmosphere.",
        "Family-owned taqueria serving authentic recipes from Oaxaca, Mexico.",
    ],
    "Chinese": [
        "Dim sum paradise with over 60 varieties of dumplings, bao, and small plates.",
        "Szechuan cuisine featuring bold, spicy flavors and signature mapo tofu.",
        "Cantonese seafood restaurant with live tanks and daily fresh catches.",
        "Northern Chinese specialties including Peking duck carved tableside.",
    ],
    "Indian": [
        "Tandoor-fired breads, aromatic curries, and regional specialties from across India.",
        "South Indian dosa and idli masters serving crispy crepes and fluffy rice cakes.",
        "Modern Indian fine dining with a contemporary twist on classic Mughal recipes.",
        "Vegetarian and vegan Indian cuisine with over 100 plant-based dishes.",
    ],
    "American": [
        "Farm-to-table comfort food using locally sourced ingredients from regional farms.",
        "Classic American diner serving all-day breakfast, burgers, and milkshakes since 1985.",
        "Craft burger joint with 20 signature creations and hand-cut seasoned fries.",
        "BBQ smokehouse with 12-hour slow-smoked brisket, ribs, and pulled pork.",
    ],
    "French": [
        "Classic French bistro with steak frites, croque monsieur, and crème brûlée.",
        "Fine dining Parisian experience with seasonal tasting menus and rare wine pairings.",
        "Casual boulangerie-café serving freshly baked croissants, quiches, and galettes.",
        "Modern French cuisine incorporating local California produce with French techniques.",
    ],
    "Korean": [
        "Tabletop Korean BBQ with premium meats, unlimited banchan, and soju cocktails.",
        "Traditional Korean home cooking featuring kimchi jjigae, bibimbap, and japchae.",
        "Modern Seoul-style cafe and restaurant with Korean fried chicken and tteokbokki.",
        "Authentic Jeju Island seafood and haemul pajeon (seafood pancakes).",
    ],
    "Thai": [
        "Authentic Thai street food including pad thai, green curry, and mango sticky rice.",
        "Royal Thai cuisine with elaborate presentations and complex spice-layered dishes.",
        "Northern Thai specialties like khao soi and larb not found in most Thai restaurants.",
        "Fresh Thai ingredients imported weekly, traditional wok cooking over high heat.",
    ],
    "Vietnamese": [
        "Rich pho broth simmered for 24 hours with aromatic spices and fresh herbs.",
        "Banh mi sandwiches with house-baked baguettes and premium fillings.",
        "Modern Vietnamese fusion with traditional flavors in a contemporary setting.",
        "Fresh spring rolls, vermicelli bowls, and Vietnamese coffee specialties.",
    ],
    "Mediterranean": [
        "Fresh mezze platters, wood-fired pita, and slow-roasted lamb dishes.",
        "Coastal Mediterranean seafood and vegetable dishes with olive oil and herbs.",
        "Mezze bar with 40+ shared plates, hummus variations, and regional specialties.",
        "Farm-fresh Mediterranean cuisine with organic produce and artisanal cheeses.",
    ],
    "Greek": [
        "Authentic Greek taverna with moussaka, spanakopita, and grilled octopus.",
        "Family recipes from Santorini featuring fresh seafood and local cheeses.",
        "Modern Greek cuisine with traditional flavors and contemporary presentations.",
        "Classic gyros, souvlaki, and baklava made fresh daily.",
    ],
    "Spanish": [
        "Tapas bar with over 50 small plates, sangria, and live flamenco on weekends.",
        "Authentic paella cooked in traditional pans over open flame.",
        "Modern Spanish pintxos and a curated selection of Rioja wines.",
        "Basque-inspired cuisine with txakoli wine and pintxos bar.",
    ],
    "Lebanese": [
        "Mezze platters, shawarma, and freshly baked manaeesh with za'atar.",
        "Traditional Lebanese home cooking with kibbeh, fattoush, and kafta.",
        "Charcoal-grilled meats and vegetarian Lebanese dishes with fresh herbs.",
        "Authentic Beirut-style cuisine with house-made hummus and falafel.",
    ],
    "Turkish": [
        "Ottoman-inspired cuisine with kebabs, börek, and Turkish delight desserts.",
        "Authentic Istanbul street food including simit, balık ekmek, and lahmacun.",
        "Traditional Turkish breakfast spread with cheeses, olives, and fresh bread.",
        "Charcoal-grilled adana and urfa kebabs with pomegranate molasses.",
    ],
    "Ethiopian": [
        "Injera-based communal dining with rich stews and vegetarian platters.",
        "Authentic Addis Ababa recipes with berbere-spiced dishes and tej honey wine.",
        "Family-style Ethiopian feasts with doro wat, tibs, and fresh injera.",
        "Vegetarian-friendly Ethiopian cuisine with lentil and vegetable wots.",
    ],
    "Peruvian": [
        "Ceviche bar with fresh seafood, leche de tigre, and Amazonian ingredients.",
        "Nikkei fusion blending Japanese and Peruvian culinary traditions.",
        "Traditional Peruvian rotisserie chicken and causa potato dishes.",
        "Modern Peruvian fine dining inspired by Lima's gastronomic revolution.",
    ],
    "Brazilian": [
        "Churrascaria with 15 cuts of flame-grilled meats served tableside.",
        "Authentic feijoada, pão de queijo, and tropical caipirinhas.",
        "Brazilian street food with coxinha, pastel, and acaí bowls.",
        "Amazonian ingredients in modern Brazilian cuisine with indigenous flavors.",
    ],
    "Caribbean": [
        "Jerk chicken and grilled fish with coconut rice and plantains.",
        "Island-inspired cuisine from Jamaica, Trinidad, and Barbados.",
        "Rum cocktails and seafood dishes with Caribbean spice blends.",
        "Tropical flavors with fresh mango, papaya, and scotch bonnet chilies.",
    ],
    "Filipino": [
        "Authentic adobo, sinigang, and lechon from regional Philippine provinces.",
        "Kamayan feast-style dining with banana leaf-lined tables.",
        "Modern Filipino cuisine celebrating indigenous ingredients and techniques.",
        "Filipino BBQ and streetfood including isaw, balut, and halo-halo dessert.",
    ],
}

REVIEW_TEMPLATES = [
    "Absolutely loved this place! The food was incredible and the service was top-notch.",
    "Great food, perfect atmosphere. Will definitely come back with friends!",
    "One of the best restaurants I've been to in the Bay Area. Highly recommend!",
    "Amazing flavors and generous portions. The staff was very friendly.",
    "Decent food but a bit overpriced. The ambiance makes up for it though.",
    "Really enjoyed the meal. Fresh ingredients and authentic preparation.",
    "Hidden gem! The food is outstanding and the prices are very reasonable.",
    "Excellent dining experience. The chef clearly knows what they're doing.",
    "Good food, nothing extraordinary but a solid choice for the neighborhood.",
    "Fantastic place! Came here for a date night and it was perfect.",
    "The portions are huge and the taste is amazing. Great value for money.",
    "Authentic flavors that remind me of home. So happy I found this place!",
    "Very consistent quality. I've been coming here for years and it never disappoints.",
    "Tried it for the first time today and was blown away by the quality.",
    "Service could be better but the food more than makes up for it.",
]


def signup_or_login():
    print(f"Attempting signup for {SEED_USER['email']}...")
    resp = requests.post(f"{BASE_URL}/auth/signup", json=SEED_USER)
    if resp.status_code in (200, 201):
        print("✅ Signup successful!")
        return resp.json()["access_token"]
    print("User already exists, logging in...")
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": SEED_USER["email"],
        "password": SEED_USER["password"]
    })
    if resp.status_code == 200:
        print("✅ Login successful!")
        return resp.json()["access_token"]
    print(f"❌ Auth failed: {resp.text}")
    sys.exit(1)


def generate_restaurants(count=300):
    restaurants = []
    used_names = set()
    attempts = 0
    while len(restaurants) < count and attempts < count * 3:
        attempts += 1
        cuisine = random.choice(CUISINES)
        adj = random.choice(ADJECTIVES)
        noun = random.choice(NOUNS)
        name = f"The {adj} {noun}"
        if name in used_names:
            name = f"{adj} {noun} {random.randint(1, 99)}"
        used_names.add(name)
        street_num = random.randint(100, 9999)
        street = random.choice(STREETS)
        city, state, zip_prefix = random.choice(CITIES)
        zip_code = f"{zip_prefix}{random.randint(10, 99)}"
        address = f"{street_num} {street}, {city}, {state} {zip_code}"
        descriptions = DESCRIPTIONS.get(cuisine, ["Great food in a wonderful atmosphere."])
        description = random.choice(descriptions)
        price_range = random.choice(PRICE_RANGES)
        phone = f"408-{random.randint(200,999)}-{random.randint(1000,9999)}"
        restaurants.append({
            "name": name,
            "address": address,
            "cuisine_type": cuisine,
            "description": description,
            "phone": phone,
            "price_range": price_range,
            "city": city,
            "state": state,
            "country": "US",
            "zip_code": zip_code,
        })
    return restaurants


def add_restaurant(token, restaurant):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    resp = requests.post(f"{BASE_URL}/restaurants/", json=restaurant, headers=headers)
    if resp.status_code in (200, 201):
        return resp.json()["id"]
    return None


def add_review(token, restaurant_id):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "restaurant_id": restaurant_id,
        "rating": random.randint(3, 5),
        "comment": random.choice(REVIEW_TEMPLATES)
    }
    requests.post(f"{BASE_URL}/reviews/", json=payload, headers=headers)


def refresh_token():
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": SEED_USER["email"],
        "password": SEED_USER["password"]
    })
    if resp.status_code == 200:
        return resp.json()["access_token"]
    return None


def main():
    print("=" * 55)
    print("   Yelp Lab2 - Database Seed Script (300 Restaurants)")
    print("=" * 55)
    print(f"Target API: {BASE_URL}\n")

    token = signup_or_login()

    restaurants = generate_restaurants(300)
    print(f"\nAdding {len(restaurants)} restaurants...\n")

    added = 0
    failed = 0
    restaurant_ids = []

    for i, restaurant in enumerate(restaurants):
        # Refresh token every 50 restaurants to avoid expiry
        if i > 0 and i % 50 == 0:
            token = refresh_token() or token
            print(f"  🔄 Token refreshed at restaurant {i}")

        rid = add_restaurant(token, restaurant)
        if rid:
            restaurant_ids.append(rid)
            added += 1
            if added % 25 == 0:
                print(f"  ✅ {added} restaurants added so far...")
        else:
            failed += 1

    print(f"\nAdding reviews for {len(restaurant_ids)} restaurants...")
    review_count = 0
    for i, rid in enumerate(restaurant_ids):
        if i % 50 == 0:
            token = refresh_token() or token
        num_reviews = random.randint(1, 3)
        for _ in range(num_reviews):
            add_review(token, rid)
            review_count += 1

    print("\n" + "=" * 55)
    print(f"✅ Seeding complete!")
    print(f"   {added} restaurants added")
    print(f"   {failed} failed")
    print(f"   {review_count} reviews added")
    print(f"\n🌐 Open http://localhost:8080 to see the data!")
    print("=" * 55)


if __name__ == "__main__":
    main()
