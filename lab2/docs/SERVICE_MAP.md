# Lab 2 — Service Map (Lab 1 → Microservices)

This document maps the monolithic [backend/main.py](../../backend/main.py) routers to the four backend services required by Lab 2, plus the fifth container (frontend).

## Fifth Dockerfile

| # | Image | Role |
|---|--------|------|
| 1 | `user-service` | Reviewer identity, auth, profile, favourites, history |
| 2 | `owner-service` | Restaurant owner dashboard & analytics |
| 3 | `restaurant-service` | Restaurants CRUD, Yelp proxy, AI assistant |
| 4 | `review-service` | Review API (Kafka producers for mutations) + read APIs |
| 5 | `frontend` | React SPA (nginx serving `build/`) |

**Separate worker process (not counted as “API service” in the table above):** `review-worker` — Kafka consumer that persists reviews and recalculates ratings.

## Router → Service

| Lab 1 router | Prefix / scope | Assigned service |
|--------------|----------------|-------------------|
| `auth` | `/auth` | **user-service** |
| `users` | `/users` | **user-service** |
| `favorites` | `/favorites` | **user-service** |
| `history` | `/history` | **user-service** |
| `owner_dashboard` | `/owner-dashboard` | **owner-service** |
| `restaurants` | `/restaurants` | **restaurant-service** |
| `yelp` | `/restaurants/yelp` (mounted at `/` in yelp router — see app) | **restaurant-service** |
| `ai_assistant` | `/ai-assistant` | **restaurant-service** |
| `reviews` | `/reviews` | **review-service** (mutations via Kafka in Lab 2) |

## Ports (docker-compose / local)

| Service | Port |
|---------|------|
| user-service | 8001 |
| owner-service | 8002 |
| restaurant-service | 8003 |
| review-service | 8004 |
| review-worker | (no HTTP) |
| nginx gateway | 8000 |
| MySQL | 3306 |
| MongoDB | 27017 |
| Kafka | 9092 |

## Frontend API base URL

Use the **gateway** single origin: `http://localhost:8000` with path-based routing (see [../docker/nginx.conf](../docker/nginx.conf)).

## JWT

All services share `SECRET_KEY` and validate the same JWT so a token from **user-service** `/auth/login` works on **review-service** protected routes.
