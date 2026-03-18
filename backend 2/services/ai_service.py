import json
import os
import re
from pathlib import Path
from typing import List, Optional, Dict, Any

_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=_env_path, override=True)
GROQ_API_KEY = (os.getenv("GROQ_API_KEY") or "").strip()
TAVILY_API_KEY = (os.getenv("TAVILY_API_KEY") or "").strip()

from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from models.restaurant import Restaurant
from models.user import UserPreference


llm = None
tavily_client = None

if GROQ_API_KEY:
    try:
        from langchain_groq import ChatGroq
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7, api_key=GROQ_API_KEY)
    except Exception:
        llm = None

if TAVILY_API_KEY:
    try:
        from tavily import TavilyClient
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    except Exception:
        tavily_client = None



def get_user_preferences(db: Session, user_id: int) -> Optional[Dict[str, Any]]:
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if not pref:
        return None
    return {
        "cuisine_preferences": pref.cuisine_preferences,
        "price_range": pref.price_range,
        "preferred_locations": pref.preferred_locations,
        "dietary_needs": pref.dietary_needs,
        "ambiance_preferences": pref.ambiance_preferences,
        "sort_preference": pref.sort_preference,
    }


def search_restaurants_for_ai(
    db: Session,
    cuisine: Optional[str] = None,
    price_range: Optional[str] = None,
    city: Optional[str] = None,
    dietary: Optional[str] = None,
    ambiance: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 10,
) -> List[Dict]:
    query = db.query(Restaurant)

    if cuisine:
        query = query.filter(Restaurant.cuisine_type.ilike(f"%{cuisine}%"))
    if price_range:
        query = query.filter(Restaurant.price_range == price_range)
    if city:
        query = query.filter(Restaurant.city.ilike(f"%{city}%"))
    if dietary:
        query = query.filter(Restaurant.dietary_options.ilike(f"%{dietary}%"))
    if ambiance:
        query = query.filter(Restaurant.ambiance.ilike(f"%{ambiance}%"))
    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(
            or_(
                Restaurant.name.ilike(kw),
                Restaurant.description.ilike(kw),
                Restaurant.cuisine_type.ilike(kw),
                Restaurant.amenities.ilike(kw),
                Restaurant.ambiance.ilike(kw),
                Restaurant.dietary_options.ilike(kw),
            )
        )

    restaurants = query.order_by(Restaurant.average_rating.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "cuisine_type": r.cuisine_type,
            "price_range": r.price_range,
            "average_rating": r.average_rating or 0,
            "review_count": r.review_count or 0,
            "city": r.city,
            "address": r.address,
            "ambiance": r.ambiance,
            "dietary_options": r.dietary_options,
            "description": r.description,
        }
        for r in restaurants
    ]


def tavily_search(query: str) -> str:
    if not tavily_client:
        return ""
    try:
        result = tavily_client.search(query=query, max_results=3)
        snippets = [r.get("content", "") for r in result.get("results", [])]
        return "\n".join(snippets[:3])
    except Exception:
        return ""


# ---------- NLU: extract intent from user message ----------

CUISINE_KEYWORDS = {
    "italian": "Italian", "chinese": "Chinese", "mexican": "Mexican",
    "indian": "Indian", "japanese": "Japanese", "american": "American",
    "thai": "Thai", "french": "French", "korean": "Korean",
    "mediterranean": "Mediterranean", "vietnamese": "Vietnamese",
    "greek": "Greek", "spanish": "Spanish", "sushi": "Japanese",
    "pizza": "Italian", "pasta": "Italian", "tacos": "Mexican",
    "curry": "Indian", "ramen": "Japanese", "pho": "Vietnamese",
    "burger": "American", "bbq": "American", "seafood": "Seafood",
    "steak": "American", "biryani": "Indian", "dim sum": "Chinese",
    "noodle": "Chinese",
}

AMBIANCE_KEYWORDS = {
    "romantic": "romantic", "casual": "casual", "family": "family-friendly",
    "fine dining": "fine dining", "outdoor": "outdoor", "cozy": "cozy",
    "quiet": "quiet", "lively": "lively", "upscale": "fine dining",
    "anniversary": "romantic", "date": "romantic", "kids": "family-friendly",
    "special occasion": "romantic", "business": "fine dining",
}

DIETARY_KEYWORDS = {
    "vegan": "vegan", "vegetarian": "vegetarian", "gluten-free": "gluten-free",
    "halal": "halal", "kosher": "kosher", "dairy-free": "dairy-free",
    "keto": "keto", "organic": "organic", "healthy": "vegetarian",
    "plant-based": "vegan", "meat-free": "vegetarian",
}

PRICE_KEYWORDS = {
    "cheap": "$", "budget": "$", "affordable": "$",
    "moderate": "$$", "mid-range": "$$", "mid range": "$$",
    "expensive": "$$$", "upscale": "$$$", "fancy": "$$$",
    "fine dining": "$$$$", "luxury": "$$$$", "splurge": "$$$$",
}


def extract_intent(message: str) -> Dict[str, Optional[str]]:
    """Parse the user's message to extract cuisine, ambiance, dietary, price, and city."""
    msg = message.lower().strip()
    result: Dict[str, Optional[str]] = {
        "cuisine": None, "ambiance": None, "dietary": None,
        "price_range": None, "city": None, "keyword": None,
    }

    for kw, val in CUISINE_KEYWORDS.items():
        if kw in msg:
            result["cuisine"] = val
            break

    for kw, val in AMBIANCE_KEYWORDS.items():
        if kw in msg:
            result["ambiance"] = val
            break

    for kw, val in DIETARY_KEYWORDS.items():
        if kw in msg:
            result["dietary"] = val
            break

    for kw, val in PRICE_KEYWORDS.items():
        if kw in msg:
            result["price_range"] = val
            break

    city_match = re.search(r'\bin\s+([A-Z][a-zA-Z\s]+?)(?:\s*,|\s*$|\s+area|\s+near)', message)
    if city_match:
        result["city"] = city_match.group(1).strip()

    words = re.findall(r'\b\w+\b', msg)
    skip = {"i", "me", "my", "a", "an", "the", "for", "in", "at", "to", "of",
            "find", "get", "want", "need", "looking", "something", "some",
            "good", "best", "great", "nice", "recommend", "show", "tonight",
            "dinner", "lunch", "breakfast", "meal", "place", "restaurant",
            "restaurants", "food", "eat", "eating", "near", "around", "please",
            "can", "you", "me", "with", "and", "or", "like", "am", "is", "are",
            "that", "this", "have", "do", "what", "where", "how", "any"}
    remaining = [w for w in words if w not in skip and len(w) > 2
                 and w not in CUISINE_KEYWORDS and w not in AMBIANCE_KEYWORDS
                 and w not in DIETARY_KEYWORDS and w not in PRICE_KEYWORDS]
    if remaining:
        result["keyword"] = " ".join(remaining[:3])

    return result


def score_restaurant(r: Dict, intent: Dict, prefs: Optional[Dict]) -> float:
    """Score a restaurant based on match with user intent and saved preferences."""
    score = (r.get("average_rating") or 0) * 10

    if intent.get("cuisine") and r.get("cuisine_type"):
        if intent["cuisine"].lower() in r["cuisine_type"].lower():
            score += 30
    if intent.get("ambiance") and r.get("ambiance"):
        if intent["ambiance"].lower() in r["ambiance"].lower():
            score += 20
    if intent.get("dietary") and r.get("dietary_options"):
        if intent["dietary"].lower() in r["dietary_options"].lower():
            score += 25
    if intent.get("price_range") and r.get("price_range"):
        if intent["price_range"] == r["price_range"]:
            score += 15

    if prefs:
        if prefs.get("cuisine_preferences") and r.get("cuisine_type"):
            for c in prefs["cuisine_preferences"].split(","):
                if c.strip().lower() in r["cuisine_type"].lower():
                    score += 15
                    break
        if prefs.get("price_range") and r.get("price_range"):
            if prefs["price_range"] == r["price_range"]:
                score += 10
        if prefs.get("dietary_needs") and r.get("dietary_options"):
            for d in prefs["dietary_needs"].split(","):
                if d.strip().lower() in r["dietary_options"].lower():
                    score += 10
                    break
        if prefs.get("ambiance_preferences") and r.get("ambiance"):
            for a in prefs["ambiance_preferences"].split(","):
                if a.strip().lower() in r["ambiance"].lower():
                    score += 10
                    break

    score += min((r.get("review_count") or 0), 20)
    return score


def build_reason(r: Dict, intent: Dict, prefs: Optional[Dict]) -> str:
    """Build a human-readable reason why this restaurant was recommended."""
    parts = []
    rating = r.get("average_rating", 0)
    if rating >= 4.0:
        parts.append(f"Highly rated ({rating}\u2605)")

    if intent.get("cuisine") and r.get("cuisine_type") and intent["cuisine"].lower() in r["cuisine_type"].lower():
        parts.append(f"Matches your {intent['cuisine']} cuisine preference")
    elif prefs and prefs.get("cuisine_preferences") and r.get("cuisine_type"):
        for c in prefs["cuisine_preferences"].split(","):
            if c.strip().lower() in r["cuisine_type"].lower():
                parts.append(f"Matches your saved {c.strip()} preference")
                break

    if intent.get("ambiance") and r.get("ambiance") and intent["ambiance"].lower() in r["ambiance"].lower():
        parts.append(f"{r['ambiance'].title()} ambiance")
    if intent.get("dietary") and r.get("dietary_options") and intent["dietary"].lower() in r["dietary_options"].lower():
        parts.append(f"Offers {intent['dietary']} options")
    if intent.get("price_range") and r.get("price_range") and intent["price_range"] == r["price_range"]:
        parts.append(f"Within your {r['price_range']} budget")

    if not parts:
        if r.get("cuisine_type"):
            parts.append(f"{r['cuisine_type']} cuisine")
        if r.get("price_range"):
            parts.append(f"{r['price_range']} price range")

    return ", ".join(parts) if parts else "Top-rated restaurant in your area"


def build_conversational_message(intent: Dict, recommendations: List[Dict], prefs: Optional[Dict], user_msg: str) -> str:
    """Build a conversational response message."""
    if not recommendations:
        parts = ["I couldn't find restaurants matching your specific criteria."]
        suggestions = []
        if intent.get("cuisine"):
            suggestions.append(f"try a different cuisine type")
        if intent.get("city"):
            suggestions.append("search in a different location")
        if not suggestions:
            suggestions.append("try broader search terms like 'Italian', 'casual dinner', or 'vegan options'")
        parts.append(f"You could {' or '.join(suggestions)}.")
        return " ".join(parts)

    intro_phrases = {
        "romantic": "For a romantic evening, here are my top picks:",
        "casual": "For a casual dining experience, check these out:",
        "family": "Great family-friendly options for you:",
        "vegan": "Here are some excellent vegan-friendly restaurants:",
        "vegetarian": "These restaurants have great vegetarian options:",
    }

    intro = None
    for kw, phrase in intro_phrases.items():
        if kw in user_msg.lower():
            intro = phrase
            break

    if not intro:
        if prefs and prefs.get("cuisine_preferences"):
            cuisines = prefs["cuisine_preferences"].split(",")[0].strip()
            intro = f"Based on your preferences for {cuisines} cuisine, here are my recommendations:"
        elif intent.get("cuisine"):
            intro = f"Here are some great {intent['cuisine']} restaurants I found:"
        else:
            intro = "Here are my top restaurant recommendations for you:"

    return intro



def chat_with_llm(
    db: Session, user_id: int, message: str,
    conversation_history: List[Dict[str, str]],
    preferences: Optional[Dict], all_restaurants: List[Dict],
) -> Dict[str, Any]:
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

    pref_text = "No preferences saved."
    if preferences:
        pref_parts = []
        if preferences["cuisine_preferences"]:
            pref_parts.append(f"Cuisine: {preferences['cuisine_preferences']}")
        if preferences["price_range"]:
            pref_parts.append(f"Price range: {preferences['price_range']}")
        if preferences["preferred_locations"]:
            pref_parts.append(f"Preferred locations: {preferences['preferred_locations']}")
        if preferences["dietary_needs"]:
            pref_parts.append(f"Dietary needs: {preferences['dietary_needs']}")
        if preferences["ambiance_preferences"]:
            pref_parts.append(f"Ambiance: {preferences['ambiance_preferences']}")
        if pref_parts:
            pref_text = ", ".join(pref_parts)

    restaurant_lines = []
    for r in all_restaurants:
        restaurant_lines.append(
            f"- {r['name']} (ID:{r['id']}) | Cuisine: {r.get('cuisine_type','N/A')} | "
            f"Rating: {r.get('average_rating',0)}\u2605 | Price: {r.get('price_range','N/A')} | "
            f"City: {r.get('city','N/A')} | Ambiance: {r.get('ambiance','N/A')} | "
            f"Dietary: {r.get('dietary_options','N/A')}"
        )
    restaurant_text = "\n".join(restaurant_lines) if restaurant_lines else "No restaurants in the database yet."

    web_context = tavily_search(f"best restaurants {message}") if tavily_client else ""

    system_prompt = f"""You are a helpful restaurant recommendation assistant for a Yelp-like platform.

USER PREFERENCES: {pref_text}

AVAILABLE RESTAURANTS IN DATABASE:
{restaurant_text}

{f"ADDITIONAL WEB CONTEXT: {web_context}" if web_context else ""}

INSTRUCTIONS:
- Recommend restaurants from the database that match the user's query and preferences
- For each recommendation, include: name, rating, price range, and a brief reason why it matches
- Be conversational, friendly, and helpful
- Format response as JSON with keys: "message" (your response text), "recommendations" (list with id, name, rating, price_range, cuisine_type, reason)
"""

    messages = [SystemMessage(content=system_prompt)]
    for entry in conversation_history:
        if entry.get("role") == "user":
            messages.append(HumanMessage(content=entry["content"]))
        elif entry.get("role") == "assistant":
            messages.append(AIMessage(content=entry["content"]))
    messages.append(HumanMessage(content=message))

    try:
        response = llm.invoke(messages)
        content = response.content
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except (json.JSONDecodeError, IndexError):
            return {"message": content, "recommendations": []}
    except Exception as e:
        err_str = str(e).lower()
        if "quota" in err_str or "rate" in err_str or "429" in err_str:
            return {"message": "API quota exceeded. Check your Groq account at console.groq.com.", "recommendations": []}
        return {"message": "I'm having trouble right now. Please try again in a moment.", "recommendations": []}


def chat_with_assistant(
    db: Session,
    user_id: int,
    message: str,
    conversation_history: List[Dict[str, str]],
) -> Dict[str, Any]:
    if not llm:
        return {
            "message": "AI Assistant requires configuration. Add GROQ_API_KEY (free at console.groq.com) to .env and restart the backend.",
            "recommendations": [],
        }

    preferences = get_user_preferences(db, user_id)
    all_restaurants = search_restaurants_for_ai(db, limit=50)

    result = chat_with_llm(db, user_id, message, conversation_history, preferences, all_restaurants)

    if result is not None:
        return result

    return {
        "message": "I'm having trouble processing your request. Please try again.",
        "recommendations": [],
    }
