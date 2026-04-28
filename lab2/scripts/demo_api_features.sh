#!/bin/bash
# =============================================================
#   Lab2 Demo — API Showcase for the 7 New Features
#   Copy each block during demo to show the feature working.
# =============================================================

GATEWAY="http://k8s-yelplab2-gateway-de60c872aa-808511d286c06347.elb.us-west-2.amazonaws.com:8000"

# ── Auth: get a token (run once at start of demo) ────────────
echo "=== Login as seed admin ==="
TOKEN=$(curl -s -X POST "$GATEWAY/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"seed@yelp.com","password":"Seed1234!"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
echo "Token acquired: ${TOKEN:0:40}..."
echo ""

# ── Feature 1: Search Autocomplete ────────────────────────────
echo "=== 1. Search Autocomplete (type 'fla' → live suggestions) ==="
curl -s "$GATEWAY/restaurants/autocomplete?q=fla" | python3 -m json.tool
echo ""

# ── Feature 2: Trending Restaurants ───────────────────────────
echo "=== 2. Trending Restaurants (top 5 by views + new reviews) ==="
curl -s "$GATEWAY/restaurants/trending?limit=5" \
  | python3 -c "import sys,json;[print(f\"  #{r['trending_rank']} {r['name']} | views={r['recent_views']} | reviews={r['recent_reviews']} | score={r['trending_score']}\") for r in json.load(sys.stdin)]"
echo ""

# ── Feature 3: Open-Now Filter ────────────────────────────────
echo "=== 3. Open-Now Restaurants (currently open) ==="
curl -s "$GATEWAY/restaurants/open-now?limit=3" \
  | python3 -c "import sys,json;[print(f\"  - {r['name']} ({r['cuisine_type']}) | {r.get('hours_today','')}\") for r in json.load(sys.stdin)]"
echo ""

echo "=== 3b. Restaurants Open at 8pm Tonight ==="
curl -s "$GATEWAY/restaurants/?at_time=20:00&limit=3" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);items=d if isinstance(d,list) else d.get('restaurants',[]);[print(f\"  - {r['name']} ({r['cuisine_type']})\") for r in items[:3]]"
echo ""

echo "=== 3c. Open for Dinner ==="
curl -s "$GATEWAY/restaurants/?open_for=dinner&limit=3" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);items=d if isinstance(d,list) else d.get('restaurants',[]);[print(f\"  - {r['name']} ({r['cuisine_type']})\") for r in items[:3]]"
echo ""

# ── Feature 4: Waitlist / Reservation ─────────────────────────
echo "=== 4. Waitlist — Join queue at restaurant 16 ==="
curl -s -X POST "$GATEWAY/waitlist/16" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"party_size":4,"notes":"birthday dinner"}' \
  | python3 -m json.tool
echo ""

echo "=== 4b. Check my waitlist position ==="
curl -s -H "Authorization: Bearer $TOKEN" \
  "$GATEWAY/waitlist/16/status" | python3 -m json.tool
echo ""

# ── Feature 5: AI Memory Across Sessions ──────────────────────
echo "=== 5. AI Memory — Read past conversation history ==="
curl -s -H "Authorization: Bearer $TOKEN" \
  "$GATEWAY/ai-assistant/history" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);[print(f\"  [{m['role']}] {m['content'][:80]}\") for m in d.get('history',[])[:6]]"
echo ""

echo "=== 5b. New chat — AI remembers and uses preferences ==="
curl -s -X POST "$GATEWAY/ai-assistant/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"What should I eat tonight?"}' \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print('AI:', d['message'][:120]);[print(f\"  - {r['name']} ({r['cuisine_type']}, {r['price_range']}) — {r.get('reason','')}\") for r in d.get('recommendations',[])[:5]]"
echo ""

# ── Feature 6: Owner Reply to Reviews ─────────────────────────
echo "=== 6. Owner Reply — Get a review with owner_reply field ==="
curl -s "$GATEWAY/reviews/restaurant/16" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);[print(f\"  Review #{r['id']}: rating={r['rating']} | reply={r.get('owner_reply') or '(no reply yet)'}\") for r in d[:3]]"
echo ""

# ── Feature 7: Notifications ──────────────────────────────────
echo "=== 7. Notifications — Unread count ==="
curl -s -H "Authorization: Bearer $TOKEN" \
  "$GATEWAY/notifications/unread-count" | python3 -m json.tool
echo ""

echo "=== 7b. List recent notifications ==="
curl -s -H "Authorization: Bearer $TOKEN" \
  "$GATEWAY/notifications/?limit=5" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);items=d if isinstance(d,list) else d.get('notifications',[]);[print(f\"  - [{n.get('type','?')}] {n.get('title','')} | read={n.get('is_read',False)}\") for n in items[:5]]"
echo ""

# ── Bonus: AI with Hours Filter (combines features 3 + 5) ────
echo "=== BONUS: AI 'Italian restaurants open right now' ==="
curl -s -X POST "$GATEWAY/ai-assistant/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Find Italian restaurants open right now"}' \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print('AI:', d['message'][:120]);[print(f\"  - {r['name']} ({r['cuisine_type']}) — {r.get('reason','')}\") for r in d.get('recommendations',[])[:4]]"
echo ""

echo "=========================================="
echo "  All 7 features demoed successfully ✅"
echo "=========================================="
