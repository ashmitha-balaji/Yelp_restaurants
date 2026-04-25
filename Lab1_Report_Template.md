# Lab 1: Yelp Prototype - Restaurant Discovery & Review Platform

**Course:** Distributed Systems  
**Due Date:** March 24, 2026  
**Submission:** YourName_Lab1_Report.doc  

---

## 1. Introduction

### Purpose and Goals

This project implements a Yelp-style restaurant discovery and review platform that supports two primary personas: **User (Reviewer)** and **Restaurant Owner**. The system enables users to search restaurants, write reviews, manage favorites, and interact with an AI assistant for personalized recommendations. Restaurant owners can post listings, claim restaurants, manage profiles, and view analytics.

**Key Goals:**
- Provide a modern, responsive web experience using React and TailwindCSS
- Offer RESTful APIs for all operations via FastAPI
- Integrate an AI chatbot that uses Langchain, Groq, and Tavily to deliver personalized restaurant recommendations
- Support Yelp API for enhanced restaurant discovery
- Ensure secure authentication with JWT and bcrypt

---mo,R

## 2. System Design

### Architecture Overview

The application follows a three-tier architecture:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React App     │────▶│   FastAPI       │────▶│   MySQL         │
│   (Frontend)    │     │   (Backend)     │     │   (Database)    │
│   Port 3000     │     │   Port 8000     │     │   Port 3306     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │
                                ├──▶ Groq API (LLM)
                                ├──▶ Tavily API (Web Search)
                                └──▶ Yelp API (Restaurant Data)
```

### Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, React Router, Axios, TailwindCSS |
| Backend | Python 3.10+, FastAPI, SQLAlchemy |
| Database | MySQL 8.0 |
| Authentication | JWT (JSON Web Tokens), bcrypt |
| AI Assistant | Langchain, Groq (Llama 3.3 70B), Tavily |

### Backend Structure (backend 2)

```
backend 2/
├── main.py              # FastAPI app, CORS, routes
├── config.py            # Environment config, .env loading
├── database.py          # SQLAlchemy engine, session
├── models/              # User, Restaurant, Review, Favorite, UserPreference
├── routers/
│   ├── auth.py          # Signup, login (JWT)
│   ├── users.py         # Profile, preferences
│   ├── restaurants.py   # CRUD, search
│   ├── reviews.py       # Create, update, delete reviews
│   ├── favorites.py     # Add/remove favorites
│   ├── history.py       # User history
│   ├── ai_assistant.py  # POST /ai-assistant/chat
│   ├── yelp.py          # Yelp API integration
│   └── owner_dashboard.py # Owner analytics
├── services/
│   └── ai_service.py   # Langchain, Groq, Tavily logic
└── utils/auth.py       # JWT verification
```

### Frontend Structure (frontend 2)

```
frontend 2/src/
├── App.js               # Routes, AuthProvider
├── context/AuthContext.js
├── services/api.js      # Axios, API calls
├── pages/
│   ├── Home.js          # Explore/search
│   ├── Login.js, Signup.js
│   ├── Profile.js       # Profile + photo upload
│   ├── Preferences.js   # AI preferences
│   ├── RestaurantDetails.js
│   ├── YelpRestaurantDetails.js  # Yelp businesses
│   ├── AddRestaurant.js
│   ├── WriteReview.js
│   ├── Favorites.js, MyReviews.js, History.js
│   └── OwnerDashboard.js
└── components/
    ├── ChatBot.js       # AI assistant UI
    ├── Navbar.js, Footer.js
    └── RestaurantCard.js, ReviewForm.js, etc.
```

---

## 3. AI Implementation

### How the Chatbot Works

1. **User Preferences Loading**  
   On each query, the backend fetches the user's saved preferences from the database: cuisine preferences, price range, preferred locations, dietary needs, ambiance preferences, and sort preference.

2. **Natural Language Understanding (Langchain + Groq)**  
   User messages are sent to Groq's Llama 3.3 70B model via Langchain. The system prompt instructs the model to:
   - Extract cuisine, price range, dietary restrictions, occasion, and ambiance from the query
   - Combine this with user preferences
   - Recommend restaurants from the database

3. **Restaurant Search**  
   The AI service queries the MySQL database with filters (cuisine, price, city, dietary, ambiance, keywords). Results are ranked by relevance and rating.

4. **Tavily Web Search**  
   Optional web context is fetched from Tavily for additional information (e.g., current hours, trending spots) to enrich recommendations.

5. **Structured Response**  
   The LLM returns a JSON object with:
   - `message`: Conversational response text
   - `recommendations`: List of restaurants with id, name, rating, price_range, cuisine_type, reason

### Endpoint

- **POST** `/ai-assistant/chat`  
  - Input: `{ "message": "user query", "conversation_history": [...] }`  
  - Output: `{ "message": "...", "recommendations": [...] }`

### Chatbot UI Features

- Floating chat button on all pages (when logged in)
- Conversation history
- Quick actions: "Find dinner tonight", "Best rated near me", "Vegan options", "Something romantic"
- Clickable restaurant cards linking to details
- Loading indicator while AI processes

---

## 4. Results (Screenshots)

### Screenshot Guide

Capture and paste the following screenshots into this section. Use clear, full-page or key-area captures.

---

#### 4.1 Home Page with AI Chatbot

**What to capture:** The main Explore/Search page with the AI chatbot button visible (red circle with chat icon). Show restaurant cards and search/filter UI.

**How:** Go to http://localhost:3000 (logged in). Capture the full page or the main content area including the floating AI button.

**Paste screenshot here:**
```
[INSERT SCREENSHOT: Home page with chatbot button]
```

---

#### 4.2 Restaurant Search Page

**What to capture:** Search results with filters (cuisine, city, price, keyword). Show at least a few restaurant cards.

**How:** Use the search bar and filters on the Home page. Capture the results.

**Paste screenshot here:**
```
[INSERT SCREENSHOT: Restaurant search with filters]
```

---

#### 4.3 Restaurant Details View

**What to capture:** A single restaurant's full details page — name, cuisine, address, hours, rating, reviews, photos.

**How:** Click any restaurant card. Capture the restaurant details page.

**Paste screenshot here:**
```
[INSERT SCREENSHOT: Restaurant details with reviews]
```

---

#### 4.4 Profile & Preferences Page

**What to capture:** User profile with photo and the Preferences section (cuisine, price range, dietary needs, ambiance, etc.).

**How:** Go to Profile (or Preferences). Capture the form with saved preferences.

**Paste screenshot here:**
```
[INSERT SCREENSHOT: Profile and Preferences]
```

---

#### 4.5 Reviews

**What to capture:** Either (a) a restaurant page showing reviews, or (b) the Write Review form, or (c) the My Reviews page.

**How:** Go to a restaurant and scroll to reviews, or go to Write Review / My Reviews.

**Paste screenshot here:**
```
[INSERT SCREENSHOT: Reviews]
```

---

#### 4.6 AI Chatbot Conversation Examples

**What to capture:** Chat window open with a conversation showing:
1. A user query (e.g., "Find dinner tonight" or "Vegan options")
2. The AI response with recommendations
3. Clickable restaurant cards in the response

**How:** Click the AI chat button. Send "Find dinner tonight" or "Best rated near me". Capture the conversation with recommendations.

**Paste screenshot here:**
```
[INSERT SCREENSHOT: AI chatbot conversation with recommendations]
```

**Optional second example:** Another query like "Something romantic" or "Vegan options".
```
[INSERT SCREENSHOT: Second chatbot example]
```

---

#### 4.7 Owner Dashboard (if implemented)

**What to capture:** Owner dashboard with restaurant analytics, recent reviews.

**How:** Sign in as owner. Go to Owner Dashboard.

**Paste screenshot here:**
```
[INSERT SCREENSHOT: Owner dashboard]
```

---

#### 4.8 API Test Results (Swagger)

**What to capture:** Swagger UI at http://localhost:8000/docs showing:
1. Expanded API endpoints
2. A successful API test (e.g., GET /restaurants/ or POST /ai-assistant/chat)

**How:** Open http://localhost:8000/docs. Expand an endpoint, click "Try it out", execute, and capture the response.

**Paste screenshot here:**
```
[INSERT SCREENSHOT: Swagger API documentation / test]
```

---

## 5. API Documentation

API documentation is available via **Swagger UI** at:

**http://localhost:8000/docs**

Key endpoints:
- `POST /auth/signup` — User/Owner registration
- `POST /auth/login` — Login (returns JWT)
- `GET /users/me` — Get profile
- `PUT /users/me/preferences` — Save AI preferences
- `GET /restaurants/` — Search restaurants
- `POST /restaurants/` — Create restaurant
- `GET /restaurants/yelp` — Yelp API search
- `POST /reviews/` — Create review
- `POST /ai-assistant/chat` — AI chatbot
- `GET /restaurants/owner/my-restaurants` — Owner's restaurants

---

## 6. Conclusion

This Lab 1 implementation delivers a full Yelp-style platform with user and owner personas, JWT authentication, restaurant search, reviews, favorites, history, and an AI assistant powered by Langchain, Groq, and Tavily. The application is responsive, uses Swagger for API documentation, and integrates the Yelp API for enhanced discovery.

---

## Appendix: How to Run

**Prerequisites:** Python 3.10+, Node.js 18+, MySQL 8.0

**Backend (backend 2):**
```bash
cd "backend 2"
python3 -m venv venvRR
source venv/bin/activate
pip install -r requirements.txt
# Create .env with DATABASE_URL, SECRET_KEY, GROQ_API_KEY, TAVILY_API_KEY, YELP_API_KEY
uvicorn main:app --reload --port 8000
```

**Frontend (frontend 2):**
```bash
cd "frontend 2"
npm install
npm start
```

**Database:**
```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS yelp_db_partner;"
```
