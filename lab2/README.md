# Lab 2 — Docker, Kubernetes, Kafka, MongoDB, Redux, JMeter

This folder contains **Lab 2–specific** artifacts: microservice entrypoints, Docker/Kubernetes files, Kafka review pipeline, Mongo helpers, JMeter assets, and documentation. Lab 1 application code remains under `backend/` and `frontend/`.

## Quick start (full stack with Docker)

From the **`lab-1`** directory (parent of `lab2/`):

```bash
docker compose -f lab2/docker-compose.yml up --build
```

- **API gateway:** http://localhost:8000  
- **Frontend:** http://localhost:3000  
- **MySQL:** localhost:3306 (user `root`, password `rootpass`, database `yelp_db`)  
- **MongoDB:** localhost:27017 (`MONGODB_DB_NAME=yelp_lab2`)  
- **Kafka:** localhost:9092  

Set `GROQ_API_KEY`, `TAVILY_API_KEY`, `YELP_API_KEY` in the environment or a `.env` file in the project root if your compose setup loads it.

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

The React app uses **Redux Toolkit** (`frontend/src/store/`) for auth, restaurants, reviews, and favourites. Use **Redux DevTools** in the browser for screenshots required by the report.

## AWS

Build images, push to **ECR**, deploy to **EKS** (or EC2 + `kubectl`), update secrets and `ConfigMap` values. Capture screenshots of pods/services for the report — placeholders are not included in-repo.

## Pair number

Replace `##` in the report filename `LabPair-##_Lab2_Report.pdf` per course instructions.
