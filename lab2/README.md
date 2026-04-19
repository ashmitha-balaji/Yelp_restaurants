# Lab 2 — Docker, Kubernetes, Kafka, MongoDB, Redux, JMeter

This folder contains **Lab 2–specific** artifacts: microservice entrypoints, Docker/Kubernetes files, Kafka review pipeline, Mongo helpers, JMeter assets, and documentation. Lab 1 application code remains under `backend/` and `frontend/`.

## Quick start (full stack with Docker)

From the repo root (parent of `lab2/`), use an explicit env file:

```bash
docker compose --env-file lab2/.env -f lab2/docker-compose.yml up --build -d
```

- **API gateway:** http://localhost:8000  
- **Frontend:** http://localhost:3000  
- **MySQL:** localhost:3306 (user `root`, password `rootpass`, database `yelp_db`)  
- **MongoDB:** localhost:27017 (`MONGODB_DB_NAME=yelp_lab2`)  
- **Kafka:** localhost:9092  

Set `GROQ_API_KEY`, `TAVILY_API_KEY`, `YELP_API_KEY` in `lab2/.env` (recommended for this project).

## Kubernetes quick start (Docker Desktop)

1. Enable Kubernetes in Docker Desktop and confirm:

   ```bash
   kubectl config use-context docker-desktop
   kubectl get nodes
   ```

2. Apply manifests:

   ```bash
   kubectl apply -f lab2/k8s/namespace.yaml
   kubectl apply -f lab2/k8s/configmap-env.yaml
   kubectl apply -f lab2/k8s/deployment-mongo.yaml
   kubectl apply -f lab2/k8s/deployment-zookeeper.yaml
   kubectl apply -f lab2/k8s/deployment-kafka.yaml
   kubectl apply -f lab2/k8s/deployment-user-service.yaml
   kubectl apply -f lab2/k8s/deployment-owner-service.yaml
   kubectl apply -f lab2/k8s/deployment-restaurant-service.yaml
   kubectl apply -f lab2/k8s/deployment-review-service.yaml
   kubectl apply -f lab2/k8s/deployment-review-worker.yaml
   kubectl apply -f lab2/k8s/deployment-restaurant-worker.yaml
   kubectl apply -f lab2/k8s/deployment-gateway.yaml
   kubectl apply -f lab2/k8s/deployment-frontend.yaml
   ```

3. If app pods show `ErrImagePull` locally, tag compose-built images to manifest image names:

   ```bash
   docker tag yelp-lab2-user-service:latest yelp-user-service:latest
   docker tag yelp-lab2-owner-service:latest yelp-owner-service:latest
   docker tag yelp-lab2-restaurant-service:latest yelp-restaurant-service:latest
   docker tag yelp-lab2-review-service:latest yelp-review-service:latest
   docker tag yelp-lab2-review-worker:latest yelp-review-worker:latest
   docker tag yelp-lab2-restaurant-worker:latest yelp-restaurant-worker:latest
   docker tag yelp-lab2-frontend:latest yelp-frontend:latest
   kubectl rollout restart deployment user-service owner-service restaurant-service review-service review-worker restaurant-worker frontend -n yelp-lab2
   ```

4. Verify:

   ```bash
   kubectl get deployments -n yelp-lab2
   kubectl get pods -n yelp-lab2
   kubectl get svc -n yelp-lab2
   ```

### First-time DB

Lab 2 **runtime** uses **MongoDB**. If you need to **copy existing Lab 1 data from MySQL** into MongoDB, MySQL must contain the Lab 1 tables first.

1. Start MySQL (and Mongo) so the migration can connect:

   ```bash
   docker compose -f lab2/docker-compose.yml up -d mysql mongo user-service
   ```

2. **Create MySQL tables** (only if migration reports `1146 Table … doesn't exist`):

   ```bash
   docker exec yelp-lab2-user-service-1 python /app/lab2/migrations/init_mysql_schema.py
   ```

3. **Optional:** seed MySQL (`docker exec … python /app/backend/seed_restaurants.py` with `DATABASE_URL` pointing at MySQL), or load data however you did in Lab 1.

4. **Migrate** MySQL → MongoDB:

   ```bash
   docker exec yelp-lab2-user-service-1 python /app/lab2/migrations/mysql_to_mongo.py
   ```

### Review flow (Kafka)

- **POST/PUT/DELETE** `/reviews/*` returns **202** with `job_id` when Kafka is configured.  
- **review-worker** consumes `review.created`, `review.updated`, `review.deleted` and writes to **MongoDB**.  
- Job status: **GET** `/reviews/job/{job_id}` (MongoDB).  
- **Sessions:** login/signup record a document in MongoDB `sessions` when `MONGODB_URL` is set (see `lab2/python/mongo_sessions.py`).

### Restaurant event flow (Kafka)

- **POST** `/restaurants/` still returns **201** for frontend compatibility.
- Restaurant API also publishes Kafka events: `restaurant.created`, `restaurant.updated`, `restaurant.claimed`.
- **restaurant-worker** consumes these topics and stores processed event records in MongoDB `restaurant_events`.

### Monolith (Lab 1) without Docker

Continue using `uvicorn main:app` on port 8000 and `npm start` on port 3000 — review endpoints remain **synchronous 201/204** on the monolith.

## Layout

| Path | Description |
|------|-------------|
| `docker-compose.yml` | MySQL, Mongo, Zookeeper, Kafka, 4 APIs, worker, nginx gateway, frontend |
| `docker/` | Dockerfiles, nginx configs |
| `services/` | Per-service FastAPI `app.py` entrypoints |
| `python/` | `mongo_sessions`, `mongo_jobs`, `kafka_client` |
| `review_async_router.py` | Kafka-backed review routes |
| `k8s/` | Sample Kubernetes manifests (replace image URIs for AWS) |
| `jmeter/` | Load-test plan and notes |
| `migrations/init_mysql_schema.py` | Create Lab 1 tables in Compose MySQL before migration |
| `migrations/mysql_to_mongo.py` | Copy MySQL rows → MongoDB collections |
| `docs/` | Service map, Kafka diagram, MongoDB schema notes |

## Redux (frontend)

The React app uses **Redux Toolkit** (`frontend/src/store/`) with at least these slices:

- `auth` — mirrors login/logout/session user state
- `app` — tracks current route, query string, and visit counter

### Redux evidence capture (Phase 4)

1. Open app and browser **Redux DevTools**.
2. Sign in/out once to capture `auth` slice state transitions.
3. Navigate across pages (`/`, `/favorites`, `/my-reviews`) to capture `app.routeVisited` updates.
4. Take at least 2 screenshots showing distinct slices in state + action timeline.

## AWS

Build images, push to **ECR**, deploy to **EKS** (or EC2 + `kubectl`), update secrets and `ConfigMap` values. Capture screenshots of pods/services for the report — placeholders are not included in-repo.

## Pair number

Replace `##` in the report filename `LabPair-##_Lab2_Report.pdf` per course instructions.
