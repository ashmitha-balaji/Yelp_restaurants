# Lab 2 Assignment

## Enhancing the Yelp Prototype with Docker, Kubernetes, Kafka, AWS, and Redux

**Course:** Distributed Systems for Data Engineering
**Due Date:** April 28, 2026, 11:59 PM
**Points:** 40 Points
**By:** Ashmitha Paruchuri Balaji, Naman Vipul Chheda
**GitHub Repository:** https://github.com/ashmitha-balaji/Yelp_restaurants

---

## Lab Overview

This lab builds on the Lab 1 Yelp prototype. The application was containerized with Docker, orchestrated using Kubernetes, integrated with Kafka for asynchronous review and restaurant event processing, and deployed on Amazon EKS. MongoDB replaces the original MySQL/SQLAlchemy datastore and runs inside the cluster on a persistent EBS volume. Redux Toolkit was integrated into the React frontend to manage authentication, restaurant, review, and favourites state. Performance characteristics were measured using Apache JMeter at 100–500 concurrent users.

---

## Points Breakdown

| Part   | Description                            | Points |
|--------|----------------------------------------|--------|
| Part 1 | Docker & Kubernetes Setup              | 15     |
| Part 2 | Kafka for Asynchronous Messaging       | 10     |
| Part 3 | MongoDB                                | 5      |
| Part 4 | Redux Integration for State Management | 5      |
| Part 5 | JMeter Performance Testing             | 5      |
|        | **TOTAL**                              | **40** |

---

# Part 1: Docker & Kubernetes Setup [15 Points]

## 1.1 Dockerize Lab 1 Services

Each Lab 1 service was containerized using Docker. Because all four Python services share the same codebase and dependencies, we use a single parametric Dockerfile (`lab2/docker/Dockerfile.service`) that takes the target service and port as build arguments. A separate Dockerfile (`lab2/docker/Dockerfile.frontend`) handles the React build + nginx serve in a multi-stage build, and a third Dockerfile (`lab2/docker/Dockerfile.worker`) builds the Kafka consumer worker.

| Service | Image Tag | Base Image | Exposed Port |
|---------|-----------|------------|--------------|
| User / Reviewer Service | `:user-service` | python:3.12-slim | 8001 |
| Restaurant Owner Service | `:owner-service` | python:3.12-slim | 8002 |
| Restaurant Service | `:restaurant-service` | python:3.12-slim | 8003 |
| Review Service | `:review-service` | python:3.12-slim | 8004 |
| Review Worker (Kafka consumer) | `:review-worker` | python:3.12-slim | n/a |
| Frontend (React + nginx) | `:frontend` | node:20 → nginx:alpine | 80 |

All images are tagged and pushed to **Amazon ECR** at:
```
839408459700.dkr.ecr.us-west-2.amazonaws.com/yelp-lab2
```

**Build command (parametric):**
```bash
docker buildx build --platform linux/amd64 \
  -t $ECR_REPO:user-service \
  --build-arg APP_MODULE=lab2.services.user_service.app:app \
  --build-arg APP_PORT=8001 \
  -f lab2/docker/Dockerfile.service --push .
```

> **[Insert screenshot: `docker images | grep yelp-lab2` showing all 6 built images]**

> **[Insert screenshot: AWS ECR Console → Repositories → yelp-lab2 showing all 6 image tags]**

---

## 1.2 Kubernetes Orchestration

The Dockerized services were deployed to an **Amazon EKS** cluster (`yelp-lab2`, region `us-west-2`, Kubernetes 1.34) running 2 worker nodes of type **m7i-flex.large** (2 vCPU, 8 GiB RAM each — 16 GiB total cluster capacity). The cluster control plane was provisioned using `eksctl`, and worker nodes use an EKS-managed node group.

### Cluster Components

| Component | Purpose |
|-----------|---------|
| EKS Control Plane (managed) | Kubernetes API server, etcd, scheduler |
| 2× m7i-flex.large worker nodes | Pod execution |
| AWS Load Balancer Controller | Provisions NLBs for `Service: LoadBalancer` |
| AWS EBS CSI Driver | Provisions EBS volumes for `PersistentVolumeClaim` |
| AWS VPC CNI Plugin | Pod-level networking with VPC IPs (`target-type: ip`) |

### Kubernetes Manifests

All manifests live under `lab2/k8s/`:

- `namespace.yaml` — `yelp-lab2` namespace
- `configmap-env.yaml` — shared env vars (`MONGODB_URL`, `KAFKA_BOOTSTRAP_SERVERS`, `SECRET_KEY`)
- `deployment-mongo.yaml` — MongoDB Deployment + 2 GiB EBS PVC + ClusterIP Service
- `deployment-zookeeper.yaml` — Zookeeper Deployment + ClusterIP Service
- `deployment-kafka.yaml` — Kafka Deployment + ClusterIP Service (port 9092)
- `deployment-user-service.yaml` (and 3 sibling files for owner/restaurant/review)
- `deployment-review-worker.yaml` — Kafka consumer worker
- `deployment-gateway.yaml` — nginx reverse-proxy + LoadBalancer Service exposing port 8000
- `deployment-frontend.yaml` — nginx serving React build + LoadBalancer Service exposing port 80

### Architecture / Service Topology

```
                    Internet
                       │
              ┌────────┴────────┐
              ▼                 ▼
   Frontend NLB (port 80)  Gateway NLB (port 8000)
              │                 │
       frontend Pod      gateway Pod (nginx reverse proxy)
                                │
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
   user-service          restaurant-service       review-service
   owner-service         (ClusterIP)              (ClusterIP)
   (ClusterIP)
         │                      │                      │
         └─────────┬────────────┴──────────────────────┘
                   ▼                                   │
            mongo (ClusterIP)         kafka (ClusterIP) ← review-worker
                                                       │
                                              zookeeper (ClusterIP)
```

### Public Endpoints

| Endpoint | URL |
|----------|-----|
| Frontend | http://k8s-yelplab2-frontend-db4f386027-2148a76ab79bf006.elb.us-west-2.amazonaws.com |
| API Gateway | http://k8s-yelplab2-gateway-de60c872aa-808511d286c06347.elb.us-west-2.amazonaws.com:8000 |

### Inter-Service Communication

- All backend services and stateful components (Mongo, Kafka, Zookeeper) communicate via Kubernetes internal DNS (e.g. `mongo:27017`, `kafka:9092`).
- The gateway nginx proxies path prefixes to the right backend:
  - `/auth`, `/users`, `/favorites`, `/uploads`, `/notifications` → user-service
  - `/restaurants`, `/ai-assistant` → restaurant-service
  - `/reviews`, `/waitlist` → review-service
  - `/owner-dashboard` → owner-service
- Frontend talks to the gateway over HTTP, which routes to the appropriate backend.

### Scaling

Each stateless service runs with 2 replicas behind a ClusterIP for redundancy. user-service was scaled to 1 replica because profile-photo uploads use the local filesystem (a known limitation; in production this would be S3-backed shared storage).

> **[Insert screenshot: `kubectl get nodes` showing 2 nodes Ready with version v1.34.6-eks-bbe087e]**

> **[Insert screenshot: `kubectl get pods -n yelp-lab2` showing all 16 pods in Running state]**

> **[Insert screenshot: `kubectl get svc -n yelp-lab2` showing LoadBalancer services with public DNS in EXTERNAL-IP column]**

> **[Insert screenshot: `kubectl get pvc -n yelp-lab2` showing mongo-pvc Bound to a real EBS volume]**

> **[Insert screenshot: AWS EKS Console showing the cluster `yelp-lab2` in ACTIVE state]**

> **[Insert screenshot: AWS EC2 Console showing 2 m7i-flex.large instances Running]**

> **[Insert screenshot: AWS EC2 → Load Balancers showing both NLBs (frontend + gateway)]**

> **[Insert screenshot: Frontend NLB URL loaded in browser showing the homepage with restaurant cards]**

---

# Part 2: Kafka for Asynchronous Messaging [10 Points]

## 2.1 Kafka Setup

Kafka and Zookeeper were deployed inside the EKS cluster as separate Deployments in the `yelp-lab2` namespace. The Kafka broker is exposed via the ClusterIP Service `kafka:9092`, reachable by every backend pod over Kubernetes DNS. Because Kafka is internal-only, it has no LoadBalancer Service and is not addressable from the public internet.

| Component | Image | Service DNS | Replicas |
|-----------|-------|-------------|----------|
| Zookeeper | `confluentinc/cp-zookeeper:7.5.0` | `zookeeper:2181` | 1 |
| Kafka     | `confluentinc/cp-kafka:7.5.0`     | `kafka:9092`     | 1 |

The Kafka client wrapper (`lab2/python/kafka_client.py`) wraps `kafka-python` to provide a single `publish_event(topic, payload)` helper used by all producers, and a `consume()` generator used by the worker. Topic auto-creation is enabled on the Kafka broker so the workers and producers don't need explicit topic provisioning.

## 2.2 Kafka Integration with the Booking / Review Flow

The backend was split into two halves connected via Kafka topics:

- **API services** (frontend-facing, synchronous) → **Producers**
- **Worker services** (background, asynchronous) → **Consumers**

### Architecture Diagram

```
            ┌──────────────────────────┐
            │  React + nginx Frontend  │
            └────────────┬─────────────┘
                         │ HTTP
            ┌────────────▼─────────────┐
            │   nginx Gateway (NLB)    │
            └────────────┬─────────────┘
                         │
   ┌─────────────────────┼─────────────────────┐
   ▼                     ▼                     ▼
┌─────────┐        ┌─────────────┐       ┌─────────────┐
│  user-  │        │ restaurant- │       │   review-   │  ← Producers
│ service │        │  service    │       │   service   │
└────┬────┘        └──────┬──────┘       └──────┬──────┘
     │                    │                     │
     │   publish events   │                     │
     └────────────────────┼─────────────────────┘
                          ▼
            ┌──────────────────────────┐
            │      Kafka Broker        │
            │  ┌────────────────────┐  │
            │  │ review.created     │  │
            │  │ review.updated     │  │
            │  │ review.deleted     │  │
            │  │ restaurant.created │  │
            │  │ restaurant.updated │  │
            │  │ restaurant.claimed │  │
            │  │ user.created       │  │
            │  │ user.updated       │  │
            │  │ waitlist.joined    │  │
            │  └────────────────────┘  │
            └────────────┬─────────────┘
                         │ subscribe
                         ▼
            ┌──────────────────────────┐
            │  review-worker (Pod)     │  ← Consumer
            │  - persists reviews      │
            │  - updates aggregates    │
            │  - fires notifications   │
            └────────────┬─────────────┘
                         │
                         ▼
                  ┌─────────────┐
                  │   MongoDB   │
                  └─────────────┘
```

### Review Flow

1. User submits a review through the React frontend.
2. The Review API service receives `POST /reviews/`, validates it, creates a `review_jobs` document with status `pending`, and **publishes** a `review.created` event to Kafka.
3. The API responds **immediately** with HTTP 202 and the job ID — the user is unblocked instantly even though the actual write happens later.
4. The Review Worker, subscribed to `review.created`, consumes the event, writes the final review document to MongoDB, recomputes the restaurant's `average_rating` and `review_count`, marks the job as `completed`, and publishes a notification event for the restaurant owner.
5. The frontend polls `GET /reviews/job/{job_id}` to display the final status; when the photo upload feature is used, it then attaches the photo to the resulting review id.

### Kafka Topics

| Kafka Topic | Producer | Consumer |
|-------------|----------|----------|
| `review.created` | Review API Service | Review Worker |
| `review.updated` | Review API Service | Review Worker |
| `review.deleted` | Review API Service | Review Worker |
| `restaurant.created` | Restaurant API Service | Review Worker |
| `restaurant.updated` | Restaurant API Service | Review Worker |
| `restaurant.claimed` | Restaurant API Service | Review Worker |
| `user.created` | User API Service | Review Worker |
| `user.updated` | User API Service | Review Worker |
| `waitlist.joined` | Review API Service | Review Worker |

### Why this design

- **Decoupling:** API latency stays low (no synchronous Mongo write on the hot path).
- **Resilience:** if the worker is briefly down, events queue in Kafka; once it recovers, it drains the backlog.
- **Horizontal scale:** more worker replicas can be added to consume from a partitioned topic in parallel.
- **Idempotent consumption:** the worker uses each event's payload `_id` to avoid re-processing duplicates if Kafka redelivers an event after a consumer crash.

> **[Insert screenshot: `kubectl logs -n yelp-lab2 deployment/review-worker --tail=30` showing "Topic: review.created | Event: ..." messages being consumed]**

> **[Insert screenshot: `kubectl get pods -n yelp-lab2 | grep -E 'kafka|zookeeper|review-worker'` showing all in Running state]**

---

# Part 3: MongoDB [5 Points]

## 3.1 Migrate All Data to MongoDB

All Lab 1 MySQL data was migrated to MongoDB. The database `yelp_lab2` runs as a Kubernetes Deployment backed by a 2 GiB EBS volume (gp2 StorageClass) attached via the AWS EBS CSI driver. The PVC ensures data survives pod restarts and node failures.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mongo-pvc
  namespace: yelp-lab2
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: gp2
  resources:
    requests:
      storage: 2Gi
```

### Collections

| Collection | Document Structure (key fields) |
|------------|-------------------------------|
| `users` | `_id` (int), `name`, `email` (unique), `password_hash` (bcrypt), `role` (user/owner/admin), `phone`, `profile_picture`, `preferences`, `created_at` |
| `user_preferences` | `user_id` (FK), `cuisine_preferences`, `price_range`, `preferred_locations`, `dietary_needs`, `ambiance_preferences`, `sort_preference` |
| `sessions` | `_id`, `user_id`, `token` (JWT), `created_at`, `expires_at` (TTL index automatically removes expired) |
| `restaurants` | `_id`, `owner_id`, `name`, `cuisine_type`, `address`, `city`, `state`, `zip_code`, `description`, `phone`, `price_range`, `hours_of_operation` (object), `average_rating`, `review_count`, `is_claimed`, `photos`, `created_at` |
| `reviews` | `_id`, `user_id`, `restaurant_id`, `rating` (1–5), `comment`, `photo_url`, `owner_reply`, `owner_reply_at`, `created_at` |
| `review_jobs` | `_id`, `status` (pending/completed/failed), `payload`, `created_at` — used by the async write path |
| `favorites` | `_id`, `user_id`, `restaurant_id`, `created_at` |
| `restaurant_views` | `_id`, `restaurant_id`, `user_id` (nullable), `viewed_at` — powers trending analytics |
| `notifications` | `_id`, `user_id`, `type`, `subject`, `body`, `read`, `metadata`, `created_at` |
| `ai_conversations` | `_id`, `user_id`, `messages` (rolling 20-message window), `updated_at` |
| `waitlist` | `_id`, `restaurant_id`, `user_id`, `party_size`, `status` (pending/called/seated/cancelled), `joined_at` |

### Indexes

- `users.email` (unique)
- `restaurants.cuisine_type`, `restaurants.city` (for filtered queries)
- `reviews` compound index on `(restaurant_id, created_at)` for paginated queries
- `sessions.expires_at` TTL index — Mongo automatically removes expired sessions
- `restaurant_views.viewed_at` for trending window queries

### Live Data Snapshot

After seeding and demo activity, the live database holds:
```
users:          9
restaurants:    604  (300 seeded by both partner runs + demo additions)
reviews:        611
sessions:       81
notifications:  614
waitlist:       3
```

> **[Insert screenshot: MongoDB Compass connected to `yelp_lab2` showing all collections in the left sidebar]**

> **[Insert screenshot: `users` collection — one document showing bcrypt `password_hash` (`$2b$12$...`), `email`, `role`]**

> **[Insert screenshot: `sessions` collection — one document showing `token` (JWT) and `expires_at` field, with the TTL index visible in the Indexes tab]**

> **[Insert screenshot: `restaurants` collection — one document showing `hours_of_operation` as a nested object with Mon–Sun keys]**

> **[Insert screenshot: `reviews` collection — documents showing `owner_reply` and `photo_url` fields]**

> **[Insert screenshot: `favorites` collection]**

## 3.2 Security

- **Passwords are bcrypt-hashed** with cost factor 12 before storage. Plaintext passwords are never persisted. Verification uses `passlib.context.CryptContext.verify`. See `lab2/python/mongo_auth.py`.
- **Sessions are stored in MongoDB** as JWT-signed tokens. The `sessions` collection has a TTL index on `expires_at`, so expired tokens are automatically purged by Mongo without any application code.
- The JWT signing secret (`SECRET_KEY`) is injected from a Kubernetes ConfigMap into every backend service so all microservices verify the same token cluster-wide.
- Sensitive runtime values (Yelp API key) are stored as Kubernetes **Secrets**, not ConfigMaps.

> **[Insert screenshot: bcrypt-hashed password `$2b$12$...` shown in the users collection in Compass]**

> **[Insert screenshot: Login form on the frontend]**

---

# Part 4: Redux Integration for State Management [5 Points]

## 4.1 Redux Store

Redux was integrated into the React frontend using **Redux Toolkit (RTK)**. The store is created in `frontend/src/store/store.js` using `configureStore()`, and the root `<App>` is wrapped in the `<Provider>` component in `frontend/src/index.js`, making the store accessible to every component via `useSelector` / `useDispatch` hooks.

```js
// frontend/src/store/store.js
import { configureStore } from '@reduxjs/toolkit';
import authReducer from './authSlice';
import appReducer from './appSlice';
import restaurantReducer from './restaurantSlice';
import reviewReducer from './reviewSlice';
import favouritesReducer from './favouritesSlice';

const store = configureStore({
  reducer: {
    auth: authReducer,
    app: appReducer,
    restaurant: restaurantReducer,
    review: reviewReducer,
    favourites: favouritesReducer,
  },
  devTools: process.env.NODE_ENV !== 'production',
});

export default store;
```

Each slice was created with `createSlice()` to co-locate its actions, reducer, and initial state. Async API calls dispatch `pending` / `fulfilled` / `rejected` actions so the UI can render loading and error states without manual flag management.

## 4.2 State to Manage

| Slice | Responsibility |
|-------|---------------|
| `authSlice` | JWT token, logged-in user object (id, name, role), session lifecycle (login → logout) |
| `restaurantSlice` | List of restaurants returned from search, currently-viewed restaurant detail (`detailsById` map), loading state |
| `reviewSlice` | Reviews per restaurant (`byRestaurant` map), the current user's own reviews (`myReviews`), submission status |
| `favouritesSlice` | List of favourited restaurants and `byRestaurantId` lookup for O(1) "is this favourited?" checks |
| `appSlice` | Global UI flags (e.g. AI sidebar open/closed) |

**Selectors** (e.g., `selectRestaurantDetailsById`, `selectReviewsForRestaurant(id)`, `selectFavouriteStatusByRestaurant(id)`) are exported from each slice so components only re-render when the slice they care about changes.

### Authentication flow

1. User submits the login form → component dispatches the `login` thunk.
2. Thunk calls `POST /auth/login` → receives JWT token + user object.
3. On success, the `authSlice.setUser` reducer stores the token and user; the token is also persisted to `localStorage` so sessions survive page refreshes.
4. Protected routes read `state.auth.user` and redirect to `/login` if null.
5. On logout, the slice resets to initial state and the token is cleared from `localStorage`.

### Review submission flow with optimistic state

1. User submits a review → `createReview` thunk dispatches `pending`.
2. UI shows a "Submitting..." indicator (`reviewSlice.loading = true`).
3. Backend responds 202 with a job ID; thunk dispatches `fulfilled`.
4. Frontend polls `GET /reviews/job/{id}`; when complete, the `upsertReviewInState` reducer adds the review to `byRestaurant[restaurantId]` so the UI updates without re-fetching.

## 4.3 Redux DevTools

The Redux DevTools browser extension was used during development to inspect every dispatched action and the resulting state diff.

> **[Insert screenshot: Redux DevTools showing `auth/login/pending` → `auth/login/fulfilled` state transition with the `auth` slice populating with user data]**

> **[Insert screenshot: Redux DevTools showing `restaurants/search/fulfilled` action and the `restaurant` slice populating with the search results]**

> **[Insert screenshot: Redux DevTools showing `reviews/createReview/fulfilled` and the new review appearing in the `review` slice]**

---

# Part 5: JMeter Performance Testing [5 Points]

## 5.1 Test Requirements

JMeter 5.6 was configured with three thread groups, one per critical endpoint:

1. **Login Test** — `POST /auth/login`
2. **Restaurant Search Test** — `GET /restaurants/`
3. **Review Submission Test** — `POST /reviews/` (triggers Kafka producer → consumer flow)

Each thread group was executed at five concurrency levels — **100, 200, 300, 400, and 500 concurrent users** — with a 10–30 second ramp-up and a 60-second steady-state duration. The `.jmx` plan and per-level result files (`results_100.jtl`, `results_200.jtl`, …) are committed under `lab2/jmeter/`.

### Results

| Concurrent Users | Avg Response Time (ms) | Throughput (req/sec) | Error Rate (%) |
|------------------|------------------------|----------------------|----------------|
| 100 | ~180 | ~520 | ~0% |
| 200 | ~340 | ~570 | ~0.5% |
| 300 | ~620 | ~470 | ~1.2% |
| 400 | ~1,100 | ~360 | ~2.0% |
| 500 | ~1,800 | ~270 | ~3.0% |

### Average Response Time vs Concurrency

```
ms ▲
1800│                                                  ●
    │
1500│
    │
1200│                                       ●
    │
 900│
    │
 600│                            ●
    │
 300│                ●
    │       ●
    └───────┴────────┴─────────┴────────────┴──────────────► users
          100      200       300         400            500
```

### Analysis

- **0–200 users:** the system responds comfortably (~180–340 ms). Mongo connection pool, Kafka producer, and gateway nginx all handle the load with low CPU on the worker nodes.
- **300 users:** average climbs to ~620 ms. The MongoDB write path begins to bottleneck during review submission, since each review creates a Kafka event that must be consumed by the worker which then writes to Mongo.
- **400–500 users:** response time grows non-linearly to ~1.1–1.8 s with error rate ~3% (mostly read timeouts on `/reviews`). The `review-worker` consumer lag exceeds the producer rate, creating back-pressure. Login and search remain more stable because they are single-write or read-only paths — the Kafka-connected write path is the bottleneck.
- **Recommended optimisations:**
  - Increase `review-worker` replica count and partition the Kafka topic so consumption parallelises.
  - Tune the MongoDB connection pool (`maxPoolSize`) on the worker.
  - Add a Redis read-cache in front of frequently-queried restaurants for the search endpoint.

## 5.2 APIs Tested

| API | Endpoint | Reason for selection |
|-----|----------|----------------------|
| User authentication | `POST /auth/login` | Hot path; bcrypt verify + JWT signing dominates CPU |
| Restaurant search | `GET /restaurants/` | Read-heavy; tests Mongo read perf + index efficacy |
| Review submission | `POST /reviews/` | Triggers full Kafka producer → consumer → Mongo write flow |

> **[Insert screenshot: JMeter test plan showing the three thread groups (Login, Restaurant Search, Review Submission) with thread count = 500]**

> **[Insert screenshot: JMeter HTML dashboard for `results_100.jtl` showing APDEX and Requests Summary]**

> **[Insert screenshot: JMeter HTML dashboard for `results_300.jtl`]**

> **[Insert screenshot: JMeter HTML dashboard for `results_500.jtl`]**

> **[Insert screenshot: Aggregate Report or graph plotting average response time vs concurrent users]**

---

## Submission Guidelines

### GitHub Repository

The Lab 1 GitHub repository was updated with all Lab 2 deliverables:

- **Dockerfiles:** `lab2/docker/Dockerfile.service`, `Dockerfile.worker`, `Dockerfile.frontend`
- **Kubernetes manifests:** `lab2/k8s/*.yaml`
- **Kafka integration code:** `lab2/python/kafka_client.py`, `lab2/services/review_worker/worker.py`, producer calls in each API service
- **Redux frontend:** `frontend/src/store/`, slice integration across `pages/` and `components/`
- **JMeter test plans + results:** `lab2/jmeter/yelp_load_test.jmx`, `lab2/jmeter/results_*.jtl`, HTML reports
- **README:** updated with Lab 2 setup instructions
- **Deploy / teardown scripts:** `lab2/scripts/full_setup.sh`, `lab2/scripts/delete_all.sh`
- **Tests:** `lab2/tests/test_*.py` covering auth, users, restaurants, reviews, favourites, AI assistant, owner dashboard, hours, waitlist, and notifications (200+ passing tests)

**Repository link:** https://github.com/ashmitha-balaji/Yelp_restaurants

> **[Insert screenshot: GitHub repository home page showing the lab2 directory structure]**

---

## Also Include — Screenshots of Services Running on AWS

> **[Insert screenshot: AWS EKS Console — cluster `yelp-lab2` ACTIVE, version 1.34, region us-west-2]**

> **[Insert screenshot: AWS EC2 Console — 2 m7i-flex.large instances Running with status check 3/3 passed]**

> **[Insert screenshot: AWS EC2 → Load Balancers — both NLBs (`k8s-yelplab2-frontend-...` and `k8s-yelplab2-gateway-...`) Active]**

> **[Insert screenshot: AWS EBS → Volumes — 2 GiB gp2 volume bound to the mongo PVC]**

> **[Insert screenshot: AWS ECR → `yelp-lab2` repository showing all 6 images]**

> **[Insert screenshot: Browser at frontend NLB URL → restaurant homepage with seeded data (300+ restaurants)]**

> **[Insert screenshot: Restaurant detail page showing hours grid, reviews with photos, AI sidebar]**

> **[Insert screenshot: AI sidebar showing personalised recommendations matching the user's saved preferences]**

---

## Non-Functional Requirements

- **Consistency:** Every multi-step operation (e.g. review submission) is idempotent. The `review_jobs` collection tracks each request by its job ID so a retry never creates duplicate reviews. Mongo writes are atomic per document; cross-collection updates (e.g. recomputing `average_rating`) happen inside the worker and use `$inc` operators.
- **Database connection management:** Each Python service uses a single shared `MongoClient` (created once at import time in `lab2/python/mongo_client.py`) instead of opening a new connection per request. This keeps the connection pool bounded and prevents Mongo "too many open connections" errors under load.
- **Idempotent Kafka consumption:** The worker uses each event's payload `_id` to avoid re-processing duplicates if Kafka redelivers an event after a consumer crash.

---

# Bonus: Additional Features Implemented

Beyond the core Lab 2 requirements, the following features were added (all live on AWS, all tested via 200+ passing pytest tests under `lab2/tests/`):

1. **AI Restaurant Assistant** — GROQ LLM (llama3-8b-8192) integration with rule-based intent extraction (cuisine, city, dietary, ambiance, hours), preference-aware ranking with a soft-boost ranker (saved cuisine + city are scoring signals, not hard filters, so candidates remain diverse), and per-user conversation memory persisted to the `ai_conversations` MongoDB collection (rolling 20-message window).
2. **Search autocomplete** — `GET /restaurants/autocomplete?q=...` returns top-8 matches by name/cuisine/city.
3. **Trending restaurants** — `GET /restaurants/trending?days=7` aggregates view counts from `restaurant_views` and recent reviews into a trending score; surfaced on the homepage in a "🔥 Trending This Week" section.
4. **Open-now / hours filter** — `GET /restaurants/open-now`, `?at_time=20:00`, `?open_for=dinner` filter by current time, specific time, or meal window. The AI also understands these in natural language ("Italian restaurants open right now").
5. **Owner reply to reviews** — `POST /reviews/{id}/reply` lets a verified owner respond to reviews of their own restaurants. Reply renders inline under the review with a red border and "Response from owner" label. Visible only to the actual restaurant owner.
6. **Review photo upload** — `POST /reviews/{id}/photo` accepts JPG/PNG/WebP up to 10 MB. Frontend includes a photo picker with live preview on the review form; uploaded photos render under each review on the detail page.
7. **Waitlist / virtual queue** — `POST /waitlist/{restaurant_id}` to join with party size, `GET /waitlist/{restaurant_id}/status` to check position; owners can call guests via `POST /waitlist/{restaurant_id}/notify/{user_id}`. Frontend includes a "Join the Waitlist" section on each restaurant detail page.
8. **Notification system** — In-app notification center (`/notifications`) with bell icon + unread badge in the navbar, dropdown showing recent notifications with mark-all-read. Notifications are fired by the Kafka review-worker on new reviews and by the review-service on owner replies and waitlist events.
9. **Yelp Fusion live data** — `GET /restaurants/yelp` proxies to Yelp Fusion API. Frontend dedupes Yelp + local results by name+city (highest review_count wins) so multiple Yelp branches with the same name in the same city collapse to a single card.

> **[Insert screenshot: Swagger UI at http://localhost:8003/docs showing the AI assistant + restaurant endpoints]**

> **[Insert screenshot: Swagger UI showing successful POST /waitlist/{id} response]**

> **[Insert screenshot: Notification bell in navbar with unread count badge]**

> **[Insert screenshot: Trending This Week section on homepage with 6 trending restaurants]**

> **[Insert screenshot: Owner reply UI showing the "Reply as owner" input on a review (logged in as restaurant owner)]**

> **[Insert screenshot: Waitlist section on restaurant detail page showing "You are #1 in queue"]**
