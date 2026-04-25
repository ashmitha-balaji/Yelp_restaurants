# API Documentation — JSON to Paste for Screenshots

Use these exact JSON bodies when testing endpoints in Swagger (http://localhost:8000/docs).

---

## Report Endpoints — Request Bodies (Copy-Paste)

### POST /auth/signup
**User registration:**
```json
{
  "name": "Test User",
  "email": "test@example.com",
  "password": "password123",
  "role": "user"
}
```
**Owner registration:**
```json
{
  "name": "Restaurant Owner",
  "email": "owner@example.com",
  "password": "password123",
  "role": "owner",
  "restaurant_location": "San Jose, CA"
}
```

---

### POST /auth/login
```json
{
  "email": "test@example.com",
  "password": "password123"
}
```

---

### GET /users/me
**No request body.** Uses Bearer token. Query params: none.

---

### PUT /users/me/preferences
```json
{
  "cuisine_preferences": "Italian,Mexican,Japanese",
  "price_range": "$$",
  "preferred_locations": "San Jose,Livermore",
  "search_radius": 10,
  "dietary_needs": "Vegetarian",
  "ambiance_preferences": "Casual,Romantic",
  "sort_preference": "rating"
}
```
*(All fields optional — include only what you want to update.)*

---

### GET /restaurants/
**No request body.** Query params:
- `cuisine_type` — e.g. `Italian`
- `city` — e.g. `San Jose` or `San Jose, CA`
- `zip_code` — e.g. `95112`
- `price_range` — e.g. `$$`
- `page` — default `1`
- `limit` — default `20`, max `100`

---

### POST /restaurants/
```json
{
  "name": "My New Restaurant",
  "cuisine_type": "Italian",
  "description": "Cozy Italian eatery with homemade pasta",
  "address": "123 Main St",
  "city": "San Jose",
  "state": "CA",
  "zip_code": "95112",
  "country": "US",
  "phone": "408-555-1234",
  "email": "contact@restaurant.com",
  "website": "https://example.com",
  "price_range": "$$",
  "hours_of_operation": "Mon-Fri 11am-9pm",
  "amenities": "Takeout, Dine-in, WiFi",
  "ambiance": "Casual",
  "dietary_options": "Vegetarian"
}
```
*(Only `name` required; others optional.)*

---

### GET /restaurants/yelp
**No request body.** Query params:
- `term` — e.g. `restaurants` or `pizza`
- `city` — e.g. `San Jose, CA`
- `limit` — default `20`, max `50`

---

### POST /reviews/
```json
{
  "restaurant_id": 1,
  "rating": 5,
  "comment": "Amazing food and service! Will definitely come back."
}
```
*(`rating` 1–5 required; `comment` optional.)*

---

### POST /ai-assistant/chat
```json
{
  "message": "Find dinner tonight",
  "conversation_history": []
}
```
**Follow-up message:**
```json
{
  "message": "Something more casual under $20",
  "conversation_history": [
    {"role": "user", "content": "Find dinner tonight"},
    {"role": "assistant", "content": "Here are my recommendations..."}
  ]
}
```

---

### GET /restaurants/owner/my-restaurants
**No request body.** Uses Bearer token (owner role). Query params: none.

---

## Step 1: Authenticate First

Before testing protected endpoints, get a token:

### POST /auth/login

**Request body:**
```json
{
  "email": "your@email.com",
  "password": "yourpassword"
}
```

**Response (copy `access_token`):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "Your Name",
    "email": "your@email.com",
    "role": "user"
  }
}
```

**Then:** Click **Authorize** → In the modal:
- **username** = your **email** (e.g. `test@example.com`) — not your name
- **password** = your password  
- Click **Authorize**, then **Close**

*(Alternatively, after login, copy `access_token` and paste `Bearer <token>` if your Swagger supports it.)*

---

## Step 2: If You Need to Sign Up

### POST /auth/signup

**User:**
```json
{
  "name": "Test User",
  "email": "test@example.com",
  "password": "password123",
  "role": "user"
}
```

**Restaurant Owner:**
```json
{
  "name": "Restaurant Owner",
  "email": "owner@example.com",
  "password": "password123",
  "role": "owner",
  "restaurant_location": "San Jose, CA"
}
```

---

## Step 3: Endpoints to Screenshot

### GET /restaurants/ (No auth)

**Query params (optional):** `cuisine_type=Italian&city=San Jose&limit=10`

**Example response:**
```json
[
  {
    "id": 1,
    "name": "Pasta Paradise",
    "cuisine_type": "Italian",
    "city": "San Jose",
    "price_range": "$$",
    "average_rating": 4.5,
    "review_count": 12
  }
]
```

---

### GET /restaurants/yelp (No auth)

**Query params:** `term=restaurants&city=San Jose, CA&limit=20`

**Example response:**
```json
{
  "restaurants": [
    {
      "id": "abc123",
      "yelp_id": "abc123",
      "name": "Restaurant Name",
      "cuisine_type": "Italian",
      "city": "San Jose",
      "price_range": "$$",
      "average_rating": 4.5,
      "review_count": 100
    }
  ]
}
```

---

### POST /ai-assistant/chat (Auth required)

**Request body:**
```json
{
  "message": "Find dinner tonight",
  "conversation_history": []
}
```

**With follow-up:**
```json
{
  "message": "Something more casual",
  "conversation_history": [
    {"role": "user", "content": "Find dinner tonight"},
    {"role": "assistant", "content": "Here are my recommendations..."}
  ]
}
```

**Example response:**
```json
{
  "message": "Based on your preferences, here are my top picks for dinner tonight:\n\n1. Pasta Paradise (4.5★, $$) - Great Italian spot...",
  "recommendations": [
    {
      "id": 1,
      "name": "Pasta Paradise",
      "rating": 4.5,
      "price_range": "$$",
      "cuisine_type": "Italian",
      "reason": "Matches your Italian preference and budget"
    }
  ]
}
```

---

### POST /restaurants/ (Auth required)

**Request body:**
```json
{
  "name": "My New Restaurant",
  "cuisine_type": "Italian",
  "description": "Cozy Italian eatery with homemade pasta",
  "address": "123 Main St",
  "city": "San Jose",
  "state": "CA",
  "zip_code": "95112",
  "phone": "408-555-1234",
  "price_range": "$$",
  "hours_of_operation": "Mon-Fri 11am-9pm",
  "amenities": "Takeout, Dine-in, WiFi",
  "ambiance": "Casual",
  "dietary_options": "Vegetarian"
}
```

---

### POST /reviews/ (Auth required)

**Request body:**
```json
{
  "restaurant_id": 1,
  "rating": 5,
  "comment": "Amazing food and service! Will definitely come back."
}
```

---

### PUT /reviews/{id} (Auth required)

Replace `{id}` with actual review ID.

**Request body:**
```json
{
  "rating": 4,
  "comment": "Updated review - still great!"
}
```

---

### POST /favorites/ (Auth required)

**Request body:**
```json
{
  "restaurant_id": 1
}
```

---

### PUT /users/me (Auth required) — Profile update

**Request body:**
```json
{
  "name": "Updated Name",
  "email": "newemail@example.com",
  "phone": "408-555-9999",
  "city": "San Jose",
  "state": "CA",
  "country": "USA",
  "about_me": "Food enthusiast"
}
```

---

### PUT /users/me/preferences (Auth required)

**Request body:**
```json
{
  "cuisine_preferences": "Italian,Mexican,Japanese",
  "price_range": "$$",
  "preferred_locations": "San Jose,Livermore",
  "dietary_needs": "Vegetarian",
  "ambiance_preferences": "Casual,Romantic",
  "sort_preference": "rating"
}
```

---

### POST /restaurants/{id}/claim (Auth required — Owner only)

Replace `{id}` with restaurant ID. No body needed.

---

## Screenshot Order for Report

1. **POST /auth/login** — Request + Response (200)
2. **Authorize** — Token pasted, dialog closed
3. **GET /restaurants/** — Execute with params, show 200 + list
4. **POST /ai-assistant/chat** — Request body + Response (200)
5. **POST /reviews/** — Request body + Response (201)

---

## Quick Copy: AI Chat (Most Important)

**Paste this for AI endpoint screenshot:**

```json
{
  "message": "Find dinner tonight",
  "conversation_history": []
}
```

**Bearer token format for Authorize:**
```
Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.YOUR_TOKEN_HERE
```

(Get the full token from `POST /auth/login` response.)
