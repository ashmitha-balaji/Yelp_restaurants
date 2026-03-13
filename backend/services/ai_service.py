import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from config import OPENAI_API_KEY, TAVILY_API_KEY
from models.restaurant import Restaurant
from models.user import UserPreference

try:
    from tavily import TavilyClient
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None
except Exception:
    tavily_client = None

llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7,
    openai_api_key=OPENAI_API_KEY,
) if OPENAI_API_KEY else None


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
                Restaurant.amenities.ilike(kw),
            )
        )

    restaurants = query.order_by(Restaurant.average_rating.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "cuisine_type": r.cuisine_type,
            "price_range": r.price_range,
            "average_rating": r.average_rating,
            "review_count": r.review_count,
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


def chat_with_assistant(
    db: Session,
    user_id: int,
    message: str,
    conversation_history: List[Dict[str, str]],
) -> Dict[str, Any]:
    preferences = get_user_preferences(db, user_id)
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

    all_restaurants = search_restaurants_for_ai(db, limit=50)
    restaurant_text = ""
    if all_restaurants:
        lines = []
        for r in all_restaurants:
            lines.append(
                f"- {r['name']} (ID:{r['id']}) | Cuisine: {r.get('cuisine_type','N/A')} | "
                f"Rating: {r.get('average_rating',0)}★ | Price: {r.get('price_range','N/A')} | "
                f"City: {r.get('city','N/A')} | Ambiance: {r.get('ambiance','N/A')} | "
                f"Dietary: {r.get('dietary_options','N/A')}"
            )
        restaurant_text = "\n".join(lines)

    web_context = ""
    if tavily_client:
        web_context = tavily_search(f"best restaurants {message}")

    system_prompt = f"""You are a helpful restaurant recommendation assistant for a Yelp-like platform.
You help users discover restaurants based on their preferences and queries.

USER PREFERENCES: {pref_text}

AVAILABLE RESTAURANTS IN DATABASE:
{restaurant_text if restaurant_text else "No restaurants in the database yet."}

{f"ADDITIONAL WEB CONTEXT: {web_context}" if web_context else ""}

INSTRUCTIONS:
- Recommend restaurants from the database that match the user's query and preferences
- For each recommendation, include: name, rating, price range, and a brief reason why it's a good match
- If no restaurants match, suggest the user broaden their search or add new restaurants
- Be conversational, friendly, and helpful
- If the user asks something unrelated to restaurants, politely redirect
- Format restaurant recommendations clearly with ratings and key details
- When recommending restaurants, include the restaurant ID so the frontend can link to details
- Respond in JSON format with keys: "message" (your response text), "recommendations" (list of restaurant objects with id, name, rating, price_range, cuisine_type, reason)
"""

    messages = [SystemMessage(content=system_prompt)]
    for entry in conversation_history:
        if entry.get("role") == "user":
            messages.append(HumanMessage(content=entry["content"]))
        elif entry.get("role") == "assistant":
            messages.append(AIMessage(content=entry["content"]))
    messages.append(HumanMessage(content=message))

    if not llm:
        filtered = search_restaurants_for_ai(db, keyword=message, limit=5)
        if not filtered:
            filtered = all_restaurants[:5]
        recs = [
            {
                "id": r["id"],
                "name": r["name"],
                "rating": r["average_rating"],
                "price_range": r["price_range"],
                "cuisine_type": r["cuisine_type"],
                "reason": f"Matches your search for '{message}'",
            }
            for r in filtered
        ]
        return {
            "message": f"Here are some restaurant suggestions based on your query '{message}':" if recs else "No restaurants found matching your query. Try a different search!",
            "recommendations": recs,
        }

    try:
        response = llm.invoke(messages)
        content = response.content

        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            parsed = json.loads(content)
            return parsed
        except (json.JSONDecodeError, IndexError):
            return {
                "message": content,
                "recommendations": [],
            }
    except Exception as e:
        return {
            "message": f"I'm having trouble processing your request right now. Please try again. Error: {str(e)}",
            "recommendations": [],
        }
