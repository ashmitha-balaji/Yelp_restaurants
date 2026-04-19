"""Lab 2 AI assistant router (Mongo-native, guest + logged-in)."""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from mongo_auth import get_optional_user
from mongo_client import get_db

router = APIRouter(prefix="/ai-assistant", tags=["AI Assistant"])

YELP_API_KEY = (os.getenv("YELP_API_KEY") or "").strip()
YELP_BASE = "https://api.yelp.com/v3/businesses/search"


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

    return {"cuisine": cuisine, "city": city, "keyword": keyword}


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
    if intent.get("cuisine"):
        filt["cuisine_type"] = {"$regex": re.escape(intent["cuisine"]), "$options": "i"}
    if intent.get("city"):
        filt["city"] = {"$regex": re.escape(intent["city"]), "$options": "i"}

    sort_field = "average_rating"
    sort_dir = -1
    if sort_pref == "popularity":
        sort_field = "review_count"
    docs = list(db.restaurants.find(filt).sort(sort_field, sort_dir).limit(limit))
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
                "reason": "From your app database",
                "source": "local",
                "yelp_id": "",
            }
        )
    if dietary_keywords or ambiance_keywords:
        # Local docs might not have rich metadata; still boost likely textual matches.
        for rec in out:
            matches = []
            text = rec.get("tags_text") or ""
            if _matches_any(text, dietary_keywords):
                matches.append("dietary")
            if _matches_any(text, ambiance_keywords):
                matches.append("ambiance")
            if matches:
                rec["reason"] = f"Matches your {' and '.join(matches)} preferences"
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
    merged = dict(intent)
    if not merged.get("cuisine"):
        pref_cuisines = _split_csv(prefs.get("cuisine_preferences"))
        if pref_cuisines:
            merged["cuisine"] = pref_cuisines[0]
    if not merged.get("city"):
        pref_locations = _split_csv(prefs.get("preferred_locations"))
        if pref_locations:
            merged["city"] = pref_locations[0]
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
    desired_cuisine = (intent.get("cuisine") or "").lower()
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
        # Preserve intent/preferences match first, then apply preferred sort.
        base = -score(rec)
        rating = float(rec.get("rating") or 0)
        price = _price_rank(rec.get("price_range") or "")
        popularity = int(rec.get("review_count") or 0)
        if sort_pref == "price_low_to_high":
            return (price, base, -rating, -popularity)
        if sort_pref == "price_high_to_low":
            return (-price, base, -rating, -popularity)
        if sort_pref == "popularity":
            return (-popularity, base, -rating, price)
        # default rating
        return (-rating, base, price, -popularity)

    return sorted(primary_ranked, key=final_sort_key)


@router.post("/chat", response_model=ChatResponse)
def chat(data: ChatRequest, current_user: Optional[dict] = Depends(get_optional_user)):
    message = (data.message or "").strip()
    if not message:
        return ChatResponse(message="Please enter a question.", recommendations=[])

    intent = _extract_intent(message)
    prefs = _get_user_preferences(current_user["id"] if current_user else None)
    intent = _apply_preferences_to_intent(intent, prefs)
    sort_pref = _normalize_sort_preference(prefs.get("sort_preference"))
    dietary_keywords = _keywords_for(
        _normalize_pref_tokens(prefs.get("dietary_needs")), DIETARY_KEYWORDS
    )
    ambiance_keywords = _keywords_for(
        _normalize_pref_tokens(prefs.get("ambiance_preferences")), AMBIANCE_KEYWORDS
    )

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

    # Deduplicate by normalized name + source id.
    seen = set()
    merged: List[Dict[str, Any]] = []
    for rec in [*local_recs, *yelp_recs]:
        key = f"{(rec.get('name') or '').strip().lower()}|{rec.get('source')}|{rec.get('yelp_id') or rec.get('id')}"
        if key in seen:
            continue
        seen.add(key)
        merged.append(rec)

    ranked = _rank(merged, intent, prefs)[:6]
    if not ranked:
        return ChatResponse(
            message="I could not find matching restaurants right now. Try a different cuisine or city.",
            recommendations=[],
        )

    if current_user:
        msg = "Here are recommendations based on your request and saved preferences."
    else:
        msg = "Here are recommendations based on your request. Log in for personalized suggestions."
    return ChatResponse(message=msg, recommendations=ranked)

