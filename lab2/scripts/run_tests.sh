#!/bin/bash
# =============================================================
#   Yelp Lab2 — Local Test Runner
#   Runs all unit/integration tests WITHOUT needing AWS, K8s,
#   or Kafka. Requires a local MongoDB on port 27017.
#
#   Usage:
#     bash lab2/scripts/run_tests.sh            # all tests
#     bash lab2/scripts/run_tests.sh auth       # just auth tests
#     bash lab2/scripts/run_tests.sh ai         # just AI tests
# =============================================================

set -e

ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
LAB2="$ROOT/lab2"
TESTS="$LAB2/tests"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Yelp Lab2 — Test Suite                         ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# ── Pre-flight ─────────────────────────────────────────────────
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}❌ python3 not found${NC}"; exit 1; }
command -v mongod  >/dev/null 2>&1 || echo -e "${YELLOW}⚠️  mongod not in PATH — assuming MongoDB is running externally${NC}"

# Check MongoDB is reachable
python3 -c "
import sys
try:
    from pymongo import MongoClient
    MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=2000).server_info()
    print('MongoDB OK')
except Exception as e:
    print(f'MongoDB not reachable: {e}')
    sys.exit(1)
" || { echo -e "${RED}❌ MongoDB not running. Start it with: brew services start mongodb-community${NC}"; exit 1; }

echo -e "${GREEN}✅ MongoDB reachable${NC}"

# ── Install test deps if needed ─────────────────────────────────
echo -e "${BLUE}ℹ️  Checking test dependencies...${NC}"
python3 -m pip install -q \
    pytest pytest-httpx httpx "pymongo>=4" "pydantic[email]" \
    "passlib[bcrypt]" "python-jose[cryptography]" \
    fastapi starlette python-multipart 2>/dev/null || true

# ── Set environment ──────────────────────────────────────────────
export MONGODB_URL="mongodb://localhost:27017"
export MONGODB_DB_NAME="yelp_test"
export SECRET_KEY="testsecret1234567890abcdef"
export APP_ROOT="$ROOT"

# Forward real API keys if available (enables live GROQ/Tavily tests)
[ -n "$GROQ_API_KEY" ]   && echo -e "${GREEN}✅ GROQ_API_KEY set — live LLM tests enabled${NC}"
[ -n "$TAVILY_API_KEY" ] && echo -e "${GREEN}✅ TAVILY_API_KEY set — Tavily tests enabled${NC}"
[ -z "$GROQ_API_KEY" ]   && echo -e "${YELLOW}⚠️  GROQ_API_KEY not set — LLM tests will be skipped${NC}"

# ── Run tests ────────────────────────────────────────────────────
FILTER="${1:-}"

if [ -n "$FILTER" ]; then
    echo -e "${BLUE}ℹ️  Running tests matching: $FILTER${NC}"
    PYTEST_ARGS="-k $FILTER"
else
    echo -e "${BLUE}ℹ️  Running all tests${NC}"
    PYTEST_ARGS=""
fi

cd "$ROOT"
python3 -m pytest "$TESTS" \
    --tb=short \
    -v \
    --import-mode=importlib \
    $PYTEST_ARGS

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  All tests complete!                             ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
