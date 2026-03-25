LAB - 1 

Yelp Prototype - Restaurants & Reviews Platform

Members:
* Ashmitha Paruchuri Balaji
* Naman Vipul Chheda

1. Introduction
   
Purpose:
This Project implements a Yelp-style restaurant discovery and review platform that supports two primary characters Users and Restaurant Owners. The system enables users to search restaurants, write reviews, manage favorites and interact with an AI assistant for personalized recommendations. Restaurant owners can post listings, claim restaurants, manage profiles and view analytics.

Key Goals:
Provide a modern, responsive web experience using React and TailwindCSS.
Offer RESTful APIs for all operations using FastAPI.
Integrate an AI chatbot that uses Langchain, Groq and Tavily to deliver personalized restaurant recommendations.
Support Yelp API for enhanced restaurant discovery.
Ensure secure authentication with JWT and bcrypt.

2. System Design
<img width="561" height="362" alt="Screenshot 2026-03-23 at 12 01 38 AM" src="https://github.com/user-attachments/assets/72b411b4-43a3-4cfc-8263-026531236bd5" />

Technology Stack:

Frontend - React 18, React Router, Axios, TailwindCSS

Backend - Python 3.10+, FastAPI, SQLAlchemy

Database - MySQL 8

Authentication - JWT(JSON Web token), bcrypt

AI Assistant - Langchain, Groq(Llama 3.3 70B), Tavily

Backend Structure:
<img width="529" height="900" alt="Screenshot 2026-03-23 at 8 13 49 AM" src="https://github.com/user-attachments/assets/a8362872-39f1-47b8-b867-a95e2520594e" />


Frontend Structure:
<img width="529" height="866" alt="Screenshot 2026-03-23 at 8 13 07 AM" src="https://github.com/user-attachments/assets/ee684ce4-cf11-462c-9438-b73fc77647cd" />


3. AI Implementation

How the Chatbot works:

User Preferences Loading: On each query, the backend fetches the users saved preferences from the database like Cuisine preferences, Preferred locations, Dietary needs, ambience preferences, prices and sort preferences.

Natural Language Understanding(Langchain + Groq) : User messages are sent to Groq’s Llama 3.3 70B model via Langchain. The system prompts instructs the model to
Extract cuisine, Price  Range, Dietary restrictions, occasion and ambiance from the query.

Combine this with user preferences.

Extract this from the database.

Restaurant Search: The AI service queries the MySQl database with filters(cuisine, price, city, dietary, ambience and key words). 

Tavily Web Search: Optional content is fetched from Tavily for additional information (e.g. Current hours, trending spots) to enrich recommendations.

Structure response: The LLM returns a JSON respons with

Message - Conversational response text

Recommendations - List of restaurants with ID, name, rating, price range, cuisine-type. 

Chatbot UI features:

Floating button on all pages when logged in

Conversation History 

Quick actions - “Find dinner tonight”, “Best rated near me”, “Vegan options”, “Something romantic”

Clickable restaurant cards linking to details

Loading indicator while AI processes.

4. Application Screenshots:
   

6. API Documentation:

7. Conclusion
The Lab1 implementation delivers a full Yelp-style platform for restaurants with users and owners personas, JWT authentication, restaurant search, reviews, favourites, history and AI assistant powered by Langchain, Groq and Tavily. The application is responsive, uses swagger for API documentation and integrates the Yelp API for enhanced discovery.

**How to Run**

**Prerequisites:** Python 3.10+, Node.js 18+, MySQL 8.0

**Backend (backend 2):**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Create .env with DATABASE_URL, SECRET_KEY, GROQ_API_KEY, TAVILY_API_KEY, YELP_API_KEY
uvicorn main:app --reload --port 8000
```

**Frontend (frontend 2):**
```bash
cd frontend
npm install
npm start
```

**Database:**
```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS yelp_db_partner;"
```
