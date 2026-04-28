"""Lab 2 AI assistant router (Mongo-native, guest + logged-in).

AI pipeline
-----------
1. Rule-based intent extraction (cuisine, city, dietary, ambiance).
2. Parallel search: local MongoDB + Yelp Fusion API.
3. Preference-aware ranking using saved user preferences.
4. (Optional) Tavily web search for factual / non-restaurant questions.
5. GROQ LLM generates the final natural-language reply using the ranked
   results as context.  Falls back to a template message when GROQ is
   unavailable.
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from mongo_auth import get_optional_user
from mongo_client import get_db

try:
    from hours_utils import (
        is_open_at, is_open_for_meal, is_open_now,
        hours_display, current_day_and_minutes, _to_minutes,
        MEAL_WINDOWS,
    )
    _HOURS_AVAILABLE = True
except ImportError:
    _HOURS_AVAILABLE = False

router = APIRouter(prefix="/ai-assistant", tags=["AI Assistant"])

YELP_API_KEY  = (os.getenv("YELP_API_KEY")  or "").strip()
GROQ_API_KEY  = (os.getenv("GROQ_API_KEY")  or "").strip()
TAVILY_API_KEY = (os.getenv("TAVILY_API_KEY") or "").strip()
YELP_BASE = "https://api.yelp.com/v3/businesses/search"
GROQ_BASE = "https://api.groq.com/openai/v1/chat/completions"
TAVILY_BASE = "https://api.tavily.com/search"
GROQ_MODEL = "llama3-8b-8192"
AI_HISTORY_LIMIT = 20  # max turns to store per user


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []


class ChatResponse(BaseModel):
    message: str
    recommendations: List[Dict[str, Any]] = []


CUISINES = [
    "indian", "mexican", "italian", "chinese", "japanese", "thai",
    "american", "mediterranean", "vietnamese", "korean",
]


DIETARY_KEYWORDS = {
    "vegetarian": ["vegetarian", "veggie"],
    "vegan": ["vegan", "plant based", "plant-based"],
    "gluten_free": ["gluten free", "gluten-free"],
    "halal": ["halal"],
    "kosher": ["kosher"],
}

AMBIANCE_KEYWORDS = {
    "casual": ["casual", "laid back", "laid-back"],
    "fine_dining": ["fine dining", "upscale", "luxury", "elegant"],
    "romantic": ["romantic", "date night", "intimate"],
    "family_friendly": ["family", "kids", "family-friendly", "family friendly"],
}


def _extract_time_intent(lower: str) -> Dict[str, Optional[str]]:
    """
    Detect time/hours constraints from the message.

    Returns a dict with keys:
      open_now   : True if user wants currently open restaurants
      open_for   : meal name (breakfast/lunch/dinner/late/tonight/brunch)
      at_time    : explicit HH:MM string (e.g. "20:30")
      open_late  : True if user wants late-night places
    """
    result: Dict[str, Optional[str]] = {
        "open_now": None, "open_for": None, "at_time": None, "open_late": None,
    }

    # "open now" / "open right now" / "currently open"
    if re.search(r"\bopen\s+(right\s+)?now\b|\bcurrently\s+open\b|\bopen\s+today\b", lower):
        result["open_now"] = True

    # Explicit time: "open at 8pm", "open at 20:30", "open after 9"
    time_match = re.search(
        r"\b(?:open\s+)?(?:at|after|around|by)\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", lower
    )
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        meridiem = time_match.group(3)
        if meridiem == "pm" and hour != 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0
        result["at_time"] = f"{hour:02d}:{minute:02d}"
        result["open_now"] = True   # treat as open-filter

    # Meal window keywords
    for meal in ("breakfast", "brunch", "lunch", "dinner", "tonight", "late night", "late", "early"):
        if meal in lower:
            result["open_for"] = meal
            result["open_now"] = True
            break

    # "open late" / "late night" / "open past midnight"
    if re.search(r"\blate[\s-]night\b|\bopen\s+late\b|\bpast\s+midnight\b|\bafter\s+11\b|\bafter\s+midnight\b", lower):
        result["open_late"] = True
        result["open_for"] = result["open_for"] or "late"
        result["open_now"] = True

    return result


def _extract_intent(message: str) -> Dict[str, Optional[str]]:
    text = (message or "").strip()
    lower = text.lower()
    cuisine = next((c.title() for c in CUISINES if c in lower), None)

    city = None
    m = re.search(r"\bin\s+([A-Za-z][A-Za-z\s]+?)(?:\s*,|\s*$|\s+for|\s+with)", text)
    if m:
        city = m.group(1).strip()

    keyword = None
    words = re.findall(r"\b\w+\b", lower)
    stop = {
        "find", "best", "good", "great", "restaurant", "restaurants", "near",
        "me", "for", "in", "with", "and", "or", "the", "a", "an", "to",
        "something", "show", "options", "option", "food", "eat", "dinner",
        "lunch", "breakfast", "tonight", "please",
    }
    kept = [w for w in words if len(w) > 2 and w not in stop and w not in CUISINES]
    if kept:
        keyword = " ".join(kept[:3])

    time_intent = _extract_time_intent(lower)
    return {"cuisine": cuisine, "city": city, "keyword": keyword, **time_intent}


def _split_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def _normalize_pref_tokens(value: Optional[str]) -> List[str]:
    return [v.lower() for v in _split_csv(value)]


def _keywords_for(tokens: List[str], mapping: Dict[str, List[str]]) -> List[str]:
    keywords: List[str] = []
    for token in tokens:
        normalized = token.replace(" ", "_").replace("-", "_")
        if normalized in mapping:
            keywords.extend(mapping[normalized])
        else:
            keywords.append(token.replace("_", " "))
    # Keep stable order while deduplicating.
    return list(dict.fromkeys([k.strip().lower() for k in keywords if k.strip()]))


def _matches_any(text: str, keywords: List[str]) -> bool:
    t = (text or "").lower()
    return any(k in t for k in keywords if k)


def _get_user_preferences(user_id: Optional[int]) -> Dict[str, Optional[str]]:
    if not user_id:
        return {}
    doc = get_db().user_preferences.find_one({"user_id": user_id}) or {}
    return {
        "cuisine_preferences": doc.get("cuisine_preferences"),
        "price_range": doc.get("price_range"),
        "preferred_locations": doc.get("preferred_locations"),
        "dietary_needs": doc.get("dietary_needs"),
        "ambiance_preferences": doc.get("ambiance_preferences"),
        "sort_preference": doc.get("sort_preference"),
    }


def _search_local(
    intent: Dict[str, Optional[str]],
    sort_pref: str,
    dietary_keywords: List[str],
    ambiance_keywords: List[str],
    limit: int = 8,
) -> List[Dict[str, Any]]:
    db = get_db()
    filt: Dict[str, Any] = {}

    # Only hard-filter by cuisine when the user EXPLICITLY said it in their message.
    # When cuisine comes from saved preferences, ranking handles the boost instead —
    # this keeps dietary/ambiance-matched restaurants visible even if their
    # cuisine_type label doesn't exactly match the preferred cuisine.
    if intent.get("cuisine") and intent.get("cuisine_from_message"):
        filt["cuisine_type"] = {"$regex": re.escape(intent["cuisine"]), "$options": "i"}
    # Only hard-filter by city when it came from the user's message.
    # Saved-preference city is a soft boost (handled in _rank).
    if intent.get("city") and intent.get("city_from_message"):
        filt["city"] = {"$regex": re.escape(intent["city"]), "$options": "i"}

    sort_field = "average_rating"
    sort_dir = -1
    if sort_pref == "popularity":
        sort_field = "review_count"
    # Fetch extra docs when hours filtering is requested (filter in Python)
    fetch_limit = limit * 10 if (intent.get("open_now") or intent.get("open_for") or intent.get("at_time") or intent.get("open_late")) else limit * 3
    docs = list(db.restaurants.find(filt).sort(sort_field, sort_dir).limit(fetch_limit))

    # Fallback: if an explicit cuisine filter returned nothing, retry without it
    if not docs and intent.get("cuisine_from_message") and intent.get("cuisine"):
        fallback_filt = {k: v for k, v in filt.items() if k != "cuisine_type"}
        docs = list(db.restaurants.find(fallback_filt).sort(sort_field, sort_dir).limit(fetch_limit))

    # Preference-aware augmentation: pull in restaurants matching the user's
    # SAVED cuisine preference (cuisine_from_prefs) even if they didn't make
    # the top-N popularity sort. Ranking will surface them naturally.
    cuisine_pref = intent.get("cuisine_from_prefs")
    if cuisine_pref:
        existing_ids = {r.get("_id") for r in docs}
        pref_filt: Dict[str, Any] = {"cuisine_type": {"$regex": re.escape(cuisine_pref), "$options": "i"}}
        # Only constrain by city when the user EXPLICITLY mentioned one.
        # If city only came from saved prefs, fetch cuisine matches across
        # all cities — the ranker will boost the preferred city later.
        if intent.get("city") and intent.get("city_from_message"):
            pref_filt["city"] = {"$regex": re.escape(intent["city"]), "$options": "i"}
        pref_docs = list(db.restaurants.find(pref_filt).sort(sort_field, sort_dir).limit(limit * 2))
        # Last-resort fallback: if even an explicit city query returned nothing
        if not pref_docs and intent.get("city_from_message"):
            pref_filt.pop("city", None)
            pref_docs = list(db.restaurants.find(pref_filt).sort(sort_field, sort_dir).limit(limit * 2))
        for r in pref_docs:
            if r.get("_id") not in existing_ids:
                docs.append(r)

    # --- Hours filtering (Python-side) ---
    if _HOURS_AVAILABLE and (intent.get("open_now") or intent.get("open_for") or intent.get("at_time") or intent.get("open_late")):
        from hours_utils import is_open_late as _is_open_late
        filtered = []
        for r in docs:
            hours_raw = r.get("hours_of_operation")
            if not hours_raw:
                continue  # skip restaurants with no hours data

            # late-night filter
            if intent.get("open_late"):
                if not _is_open_late(hours_raw):
                    continue

            # specific time filter
            if intent.get("at_time"):
                day, _ = current_day_and_minutes()
                mins = _to_minutes(intent["at_time"])
                if is_open_at(hours_raw, day, mins) is False:
                    continue
            elif intent.get("open_for"):
                if is_open_for_meal(hours_raw, intent["open_for"]) is False:
                    continue
            elif intent.get("open_now"):
                if is_open_now(hours_raw) is False:
                    continue

            filtered.append(r)
            if len(filtered) >= limit:
                break
        # Graceful fallback: if no restaurants have hours data, use unfiltered set
        docs = filtered if filtered else docs[:limit]

    out: List[Dict[str, Any]] = []
    for r in docs:
        out.append(
            {
                "id": r.get("_id"),
                "name": r.get("name"),
                "rating": r.get("average_rating", 0),
                "price_range": r.get("price_range") or "",
                "cuisine_type": r.get("cuisine_type") or "",
                "city": r.get("city") or "",
                "tags_text": " ".join(
                    [
                        str(r.get("name") or ""),
                        str(r.get("cuisine_type") or ""),
                        str(r.get("description") or ""),
                    ]
                ).lower(),
                "hours_display": hours_display(r.get("hours_of_operation")) if _HOURS_AVAILABLE else "",
                "is_open_now": is_open_now(r.get("hours_of_operation")) if _HOURS_AVAILABLE else None,
                "reason": "From your app database",
                "source": "local",
                "yelp_id": "",
            }
        )
    cuisine_from_prefs = (intent.get("cuisine_from_prefs") or "").lower()
    for rec in out:
        matches = []
        text = rec.get("tags_text") or ""
        rc = (rec.get("cuisine_type") or "").lower()
        if cuisine_from_prefs and cuisine_from_prefs in rc:
            matches.append("cuisine")
        if dietary_keywords and _matches_any(text, dietary_keywords):
            matches.append("dietary")
        if ambiance_keywords and _matches_any(text, ambiance_keywords):
            matches.append("ambiance")
        if matches:
            rec["reason"] = f"Matches your {' and '.join(matches)} preferences"
        # Tag as "open now" if that filter was applied
        if intent.get("open_now") or intent.get("open_for") or intent.get("at_time"):
            rec["reason"] = (rec.get("reason") or "From your app database") + " · Open now"
    return out


def _search_yelp(
    intent: Dict[str, Optional[str]],
    sort_pref: str,
    dietary_keywords: List[str],
    ambiance_keywords: List[str],
    limit: int = 6,
) -> List[Dict[str, Any]]:
    if not YELP_API_KEY:
        return []
    term_parts = [p for p in [intent.get("cuisine"), intent.get("keyword")] if p]
    if dietary_keywords:
        term_parts.append(dietary_keywords[0])
    if ambiance_keywords:
        term_parts.append(ambiance_keywords[0])
    term = " ".join(term_parts).strip() or "restaurants"
    location = intent.get("city") or "San Jose, CA"
    yelp_sort = "best_match"
    if sort_pref == "rating":
        yelp_sort = "rating"
    elif sort_pref == "popularity":
        yelp_sort = "review_count"
    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.get(
                YELP_BASE,
                params={
                    "term": term,
                    "location": location,
                    "limit": min(limit, 20),
                    "sort_by": yelp_sort,
                },
                headers={"Authorization": f"Bearer {YELP_API_KEY}"},
            )
        if resp.status_code != 200:
            return []
        businesses = resp.json().get("businesses") or []
    except Exception:
        return []

    out: List[Dict[str, Any]] = []
    for b in businesses:
        cats = b.get("categories") or []
        loc = b.get("location") or {}
        cat_titles = [str(c.get("title") or "") for c in cats if c.get("title")]
        tags_text = " ".join(
            [
                str(b.get("name") or ""),
                str(b.get("categories") or ""),
                str(b.get("price") or ""),
            ]
        ).lower()
        out.append(
            {
                "id": b.get("id"),
                "name": b.get("name"),
                "rating": b.get("rating") or 0,
                "review_count": b.get("review_count") or 0,
                "price_range": b.get("price") or "",
                "cuisine_type": cats[0].get("title", "Restaurant") if cats else "Restaurant",
                "city": loc.get("city") or "",
                "tags_text": tags_text,
                "category_labels": cat_titles,
                "reason": "Live Yelp result",
                "source": "yelp",
                "yelp_id": b.get("id"),
            }
        )
    return out


def _normalize_sort_preference(sort_pref: Optional[str]) -> str:
    s = (sort_pref or "").strip().lower()
    if not s:
        return "rating"
    aliases = {
        "rating": "rating",
        "highest_rating": "rating",
        "top rated": "rating",
        "sort by rating": "rating",
        "price_low_to_high": "price_low_to_high",
        "low_to_high": "price_low_to_high",
        "price asc": "price_low_to_high",
        "price": "price_low_to_high",
        "sort by price": "price_low_to_high",
        "price_high_to_low": "price_high_to_low",
        "high_to_low": "price_high_to_low",
        "popularity": "popularity",
        "most_reviewed": "popularity",
        "review_count": "popularity",
    }
    return aliases.get(s, "rating")


def _price_rank(price_value: str) -> int:
    p = (price_value or "").strip()
    return len(p) if p else 99


def _apply_preferences_to_intent(
    intent: Dict[str, Optional[str]], prefs: Dict[str, Optional[str]]
) -> Dict[str, Optional[str]]:
    """
    Merge saved preferences into intent.

    Cuisine from preferences is stored under ``cuisine_from_prefs`` so that
    _search_local can use it for a SOFT (OR-based) boost rather than a hard
    filter — this ensures restaurants that match dietary/ambiance preferences
    (but not cuisine type) are still surfaced.

    City from preferences is applied the same way.
    """
    merged = dict(intent)
    # Track whether cuisine/city came from the user's message
    merged["cuisine_from_message"] = bool(merged.get("cuisine"))
    merged["city_from_message"] = bool(merged.get("city"))

    if not merged.get("cuisine"):
        pref_cuisines = _split_csv(prefs.get("cuisine_preferences"))
        if pref_cuisines:
            # Store separately — used for ranking/boosting, NOT hard filtering
            merged["cuisine_from_prefs"] = pref_cuisines[0]
    if not merged.get("city"):
        pref_locations = _split_csv(prefs.get("preferred_locations"))
        if pref_locations:
            # Store separately so _search_local doesn't hard-filter by saved
            # city — ranking gives a soft boost instead. Otherwise a single
            # preferred city would shrink the candidate pool too much when
            # there are few matches in that city.
            merged["city_from_prefs"] = pref_locations[0]
    return merged


def _rank(
    recommendations: List[Dict[str, Any]],
    intent: Dict[str, Optional[str]],
    prefs: Dict[str, Optional[str]],
) -> List[Dict[str, Any]]:
    pref_cuisines = [c.lower() for c in _split_csv(prefs.get("cuisine_preferences"))]
    pref_cities = [c.lower() for c in _split_csv(prefs.get("preferred_locations"))]
    pref_dietary = _normalize_pref_tokens(prefs.get("dietary_needs"))
    pref_ambiance = _normalize_pref_tokens(prefs.get("ambiance_preferences"))
    dietary_keywords = _keywords_for(pref_dietary, DIETARY_KEYWORDS)
    ambiance_keywords = _keywords_for(pref_ambiance, AMBIANCE_KEYWORDS)
    # Use explicit message cuisine for scoring; fall back to preference cuisine
    desired_cuisine = (intent.get("cuisine") or "").lower()
    cuisine_from_prefs = (intent.get("cuisine_from_prefs") or "").lower()
    desired_city = (intent.get("city") or "").lower()
    sort_pref = _normalize_sort_preference(prefs.get("sort_preference"))

    def score(rec: Dict[str, Any]) -> float:
        s = float(rec.get("rating") or 0) * 10
        rc = (rec.get("cuisine_type") or "").lower()
        rn = (rec.get("name") or "").lower()
        rcity = (rec.get("city") or "").lower()
        rt = (rec.get("tags_text") or "").lower()
        if desired_cuisine and desired_cuisine in rc:
            s += 35
        # Boost for preference cuisine (soft signal, not hard filter)
        if cuisine_from_prefs and cuisine_from_prefs in rc:
            s += 30
        if any(pc and pc in rc for pc in pref_cuisines):
            s += 15
        if desired_city and (desired_city in rn or desired_city in rcity):
            s += 8
        if any(pc and (pc in rn or pc in rcity) for pc in pref_cities):
            s += 5
        pref_price = (prefs.get("price_range") or "").strip()
        if pref_price and rec.get("price_range") == pref_price:
            s += 8
        if dietary_keywords:
            if _matches_any(rt, dietary_keywords):
                s += 22
            else:
                s -= 6
        if ambiance_keywords:
            if _matches_any(rt, ambiance_keywords):
                s += 20
            else:
                s -= 6
        if rec.get("source") == "local":
            s += 2
        return s

    primary_ranked = sorted(recommendations, key=score, reverse=True)

    def final_sort_key(rec: Dict[str, Any]):
        # Score (intent + preferences match) is PRIMARY. The user's
        # sort_preference acts as a tiebreaker only — it should not bury
        # preference-matched restaurants beneath unrelated popular ones.
        base = -score(rec)
        rating = float(rec.get("rating") or 0)
        price = _price_rank(rec.get("price_range") or "")
        popularity = int(rec.get("review_count") or 0)
        if sort_pref == "price_low_to_high":
            return (base, price, -rating, -popularity)
        if sort_pref == "price_high_to_low":
            return (base, -price, -rating, -popularity)
        if sort_pref == "popularity":
            return (base, -popularity, -rating, price)
        # default rating
        return (base, -rating, price, -popularity)

    return sorted(primary_ranked, key=final_sort_key)


# ── Conversation memory (MongoDB-backed) ──────────────────────────────────

def _load_conversation_history(user_id: int, limit: int = 10) -> List[Dict[str, str]]:
    """Load the last `limit` turns for a logged-in user from MongoDB."""
    db = get_db()
    doc = db.ai_conversations.find_one({"user_id": user_id})
    if not doc:
        return []
    messages = doc.get("messages", [])
    # Return last `limit` turns as plain {role, content} dicts
    return [{"role": m["role"], "content": m["content"]} for m in messages[-limit:]]


def _save_conversation_turn(user_id: int, user_message: str, assistant_reply: str) -> None:
    """Append a user+assistant turn to the user's conversation history in MongoDB."""
    db = get_db()
    now = datetime.now(timezone.utc)
    new_turns = [
        {"role": "user",      "content": user_message,    "timestamp": now},
        {"role": "assistant", "content": assistant_reply,  "timestamp": now},
    ]
    db.ai_conversations.update_one(
        {"user_id": user_id},
        {
            "$push": {
                "messages": {
                    "$each": new_turns,
                    "$slice": -AI_HISTORY_LIMIT * 2,  # keep last N turns (2 messages per turn)
                }
            },
            "$set": {"updated_at": now},
            "$setOnInsert": {"user_id": user_id, "created_at": now},
        },
        upsert=True,
    )


def _clear_conversation_history(user_id: int) -> None:
    """Erase a user's conversation history."""
    get_db().ai_conversations.delete_one({"user_id": user_id})


def _is_non_restaurant_question(message: str) -> bool:
    """Detect questions that are not about finding a restaurant."""
    lower = message.lower()
    factual_signals = [
        "what is", "how do", "when is", "why is", "tell me about",
        "history of", "festival", "weather", "hours of operation",
        "what time", "how far", "directions",
    ]
    return any(s in lower for s in factual_signals) and not any(
        w in lower for w in ["restaurant", "food", "eat", "dinner", "lunch", "breakfast", "cuisine"]
    )


def _tavily_search(query: str) -> Optional[str]:
    """Run a Tavily web search and return a brief context string."""
    if not TAVILY_API_KEY:
        return None
    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.post(
                TAVILY_BASE,
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": 3,
                    "include_answer": True,
                },
            )
        if resp.status_code != 200:
            return None
        data = resp.json()
        # Tavily can return a direct answer
        if data.get("answer"):
            return data["answer"]
        # Otherwise stitch together result snippets
        snippets = [r.get("content", "") for r in (data.get("results") or [])[:3]]
        return " ".join(snippets)[:800] if snippets else None
    except Exception:
        return None


def _groq_generate_response(
    user_message: str,
    recommendations: List[Dict[str, Any]],
    conversation_history: List[Dict[str, str]],
    is_logged_in: bool,
    tavily_context: Optional[str] = None,
) -> Optional[str]:
    """Call GROQ to generate a natural-language reply.  Returns None if GROQ is unavailable."""
    if not GROQ_API_KEY:
        return None

    # Build a compact context block from top recommendations
    rec_lines = []
    for i, r in enumerate(recommendations[:5], 1):
        line = (
            f"{i}. {r.get('name')} — {r.get('cuisine_type', 'Restaurant')}, "
            f"{r.get('city', '')}, rating {r.get('rating', 'N/A')}, "
            f"price {r.get('price_range', 'N/A')}. Reason: {r.get('reason', '')}"
        )
        rec_lines.append(line)

    rec_context = "\n".join(rec_lines) if rec_lines else "No specific restaurants found."

    web_block = f"\nRelevant web context:\n{tavily_context}" if tavily_context else ""

    system_prompt = (
        "You are a friendly and knowledgeable restaurant recommendation assistant for a Yelp-like app. "
        "Your job is to help users find great places to eat. "
        "Be warm, concise, and specific. Highlight 1-2 top picks from the list if available. "
        "Keep your response to 2-4 sentences maximum."
    )

    # Build messages: trim history to last 4 turns to stay within token budget
    messages = [{"role": "system", "content": system_prompt}]
    for turn in (conversation_history or [])[-4:]:
        role = turn.get("role", "user")
        if role in ("user", "assistant"):
            messages.append({"role": role, "content": turn.get("content", "")})

    user_context = (
        f"User message: {user_message}\n\n"
        f"Retrieved restaurant recommendations:\n{rec_context}"
        f"{web_block}\n\n"
        f"The user {'is logged in with saved preferences' if is_logged_in else 'is browsing as a guest'}. "
        "Generate a natural, helpful reply."
    )
    messages.append({"role": "user", "content": user_context})

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                GROQ_BASE,
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "max_tokens": 200,
                    "temperature": 0.7,
                },
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
        if resp.status_code != 200:
            return None
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def _fallback_message(recommendations: List[Dict[str, Any]], is_logged_in: bool) -> str:
    if not recommendations:
        return "I could not find matching restaurants right now. Try a different cuisine or city."
    if is_logged_in:
        return "Here are recommendations based on your request and saved preferences."
    return "Here are recommendations based on your request. Log in for personalized suggestions."


@router.post("/chat", response_model=ChatResponse)
def chat(data: ChatRequest, current_user: Optional[dict] = Depends(get_optional_user)):
    message = (data.message or "").strip()
    if not message:
        return ChatResponse(message="Please enter a question.", recommendations=[])

    is_logged_in = current_user is not None
    user_id = current_user["id"] if current_user else None

    # ── Load persistent conversation history (logged-in users only) ───────
    db_history: List[Dict[str, str]] = []
    if user_id:
        db_history = _load_conversation_history(user_id, limit=8)

    # Merge: DB history takes precedence; client-supplied history fills in for guests
    effective_history = db_history if db_history else (data.conversation_history or [])

    # ── Tavily web search for non-restaurant factual questions ────────────
    tavily_context: Optional[str] = None
    if _is_non_restaurant_question(message):
        tavily_context = _tavily_search(message)

    # ── Intent + preference extraction ────────────────────────────────────
    intent = _extract_intent(message)
    prefs = _get_user_preferences(user_id)
    intent = _apply_preferences_to_intent(intent, prefs)
    sort_pref = _normalize_sort_preference(prefs.get("sort_preference"))
    dietary_keywords = _keywords_for(
        _normalize_pref_tokens(prefs.get("dietary_needs")), DIETARY_KEYWORDS
    )
    ambiance_keywords = _keywords_for(
        _normalize_pref_tokens(prefs.get("ambiance_preferences")), AMBIANCE_KEYWORDS
    )

    # ── Search + rank ──────────────────────────────────────────────────────
    local_recs = _search_local(
        intent,
        sort_pref=sort_pref,
        dietary_keywords=dietary_keywords,
        ambiance_keywords=ambiance_keywords,
        limit=10,
    )
    yelp_recs = _search_yelp(
        intent,
        sort_pref=sort_pref,
        dietary_keywords=dietary_keywords,
        ambiance_keywords=ambiance_keywords,
        limit=10,
    )

    seen: set = set()
    merged: List[Dict[str, Any]] = []
    for rec in [*local_recs, *yelp_recs]:
        key = f"{(rec.get('name') or '').strip().lower()}|{rec.get('source')}|{rec.get('yelp_id') or rec.get('id')}"
        if key in seen:
            continue
        seen.add(key)
        merged.append(rec)

    ranked = _rank(merged, intent, prefs)[:6]

    # ── Generate natural-language response via GROQ ────────────────────────
    llm_message = _groq_generate_response(
        user_message=message,
        recommendations=ranked,
        conversation_history=effective_history,
        is_logged_in=is_logged_in,
        tavily_context=tavily_context,
    )
    final_message = llm_message or _fallback_message(ranked, is_logged_in)

    # ── Persist this turn for logged-in users ─────────────────────────────
    if user_id:
        try:
            _save_conversation_turn(user_id, message, final_message)
        except Exception:
            pass  # Never let persistence failure break the response

    return ChatResponse(message=final_message, recommendations=ranked)


@router.get("/history")
def get_conversation_history(current_user: dict = Depends(get_optional_user)):
    """Return the stored conversation history for the logged-in user."""
    from mongo_auth import get_current_user as _get_current_user
    if not current_user:
        from fastapi import HTTPException
        raise HTTPException(401, "Authentication required")
    history = _load_conversation_history(current_user["id"], limit=AI_HISTORY_LIMIT)
    return {"history": history, "count": len(history)}


@router.delete("/history", status_code=200)
def clear_conversation_history(current_user: dict = Depends(get_optional_user)):
    """Clear all stored conversation history for the logged-in user."""
    if not current_user:
        from fastapi import HTTPException
        raise HTTPException(401, "Authentication required")
    _clear_conversation_history(current_user["id"])
    return {"message": "Conversation history cleared"}

