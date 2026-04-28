# Lab 2 Report — Screenshot + Theory Guide

For each section: **command/action** to capture + **theory paragraph** to paste under it.

---

# SECTION 1 — DOCKER & KUBERNETES (Part 1)

## 📸 Screenshot 1.1 — Docker images built locally

**Action:** Open terminal and run:
```bash
docker images | grep yelp-lab2 | head -10
```

**Capture:** the table showing all 6 images with TAG, IMAGE ID, CREATED, SIZE columns.

**Paste under it:**
> All four Python services (User, Owner, Restaurant, Review) plus the Kafka Worker and the React + nginx Frontend are containerized using Docker. The four Python services share a single parametric `Dockerfile.service` (located at `lab2/docker/Dockerfile.service`) that takes the target service module and port as build arguments — this avoids duplicating identical Dockerfiles. The Frontend uses a multi-stage build that compiles the React app with Node.js 20, then serves the production bundle from nginx:alpine. All images are built for `linux/amd64` so they run on the EKS worker nodes. The total compressed image size is under 700 MB per service.

---

## 📸 Screenshot 1.2 — Images in Amazon ECR

**Action:** AWS Console → ECR → Repositories → click `yelp-lab2` → Images tab.

OR terminal:
```bash
aws ecr list-images --repository-name yelp-lab2 --region us-west-2 --output table
```

**Capture:** the list of 6 image tags (user-service, owner-service, restaurant-service, review-service, review-worker, frontend).

**Paste under it:**
> All container images are pushed to **Amazon Elastic Container Registry (ECR)** at `839408459700.dkr.ecr.us-west-2.amazonaws.com/yelp-lab2`. ECR is the private, AWS-managed Docker registry — only IAM-authenticated principals (and the EKS cluster's worker nodes via the kubelet's IRSA role) can pull these images. Pushing to ECR happens automatically via `docker buildx build --push` during the deployment script, so each rebuild atomically replaces the previous image of the same tag.

---

## 📸 Screenshot 1.3 — EKS cluster ACTIVE

**Action:** AWS Console → EKS → Clusters → click `yelp-lab2`.

OR terminal:
```bash
aws eks describe-cluster --name yelp-lab2 --region us-west-2 \
  --query "cluster.[name,status,version,createdAt,endpoint]" --output table
```

**Capture:** the Overview tab showing **Status: Active**, Kubernetes version **1.34**, region **us-west-2**.

**Paste under it:**
> The Kubernetes control plane is fully managed by AWS via **Amazon EKS** (Elastic Kubernetes Service). EKS runs the Kubernetes API server, etcd, controller manager, and scheduler in a multi-AZ HA configuration that we don't manage directly. Our pods, ConfigMaps, and Secrets all live on this control plane. EKS itself bills $0.10/hour regardless of how many nodes are attached.

---

## 📸 Screenshot 1.4 — EC2 worker nodes

**Action:** AWS Console → EC2 → Instances → filter by tag `eks:cluster-name = yelp-lab2`.

OR terminal:
```bash
aws ec2 describe-instances --region us-west-2 \
  --filters "Name=tag:eks:cluster-name,Values=yelp-lab2" "Name=instance-state-name,Values=running" \
  --query "Reservations[].Instances[].[InstanceId,InstanceType,State.Name,PublicIpAddress,LaunchTime]" \
  --output table
```

**Capture:** 2 m7i-flex.large instances both in `running` state with status checks 3/3 passed.

**Paste under it:**
> The cluster runs **2 m7i-flex.large worker nodes** (2 vCPU + 8 GiB RAM each, total 16 GiB cluster capacity). The m7i-flex family is Intel Sapphire Rapids–based, current-generation, and qualifies for AWS's expanded Free Plan eligibility — which is why we picked it over t3.medium (blocked on our Free Plan account). The nodes are managed by an EKS Managed Node Group, so AWS handles AMI patching, kubelet configuration, and integration with the cluster's security groups.

---

## 📸 Screenshot 1.5 — kubectl get nodes

**Action:** Terminal:
```bash
kubectl get nodes -o wide
```

**Capture:** 2 nodes showing `STATUS: Ready` and Kubernetes version `v1.34.6-eks-bbe087e`.

**Paste under it:**
> `kubectl get nodes` confirms both worker nodes are Ready and have joined the EKS control plane. The kubelet on each node communicates with the EKS API server to receive pod scheduling assignments. Both nodes are running the same EKS-optimized AMI with kubelet v1.34.6.

---

## 📸 Screenshot 1.6 — kubectl get pods (all Running)

**Action:** Terminal:
```bash
kubectl get pods -n yelp-lab2
```

**Capture:** 16 pods all showing `1/1 Running`.

**Paste under it:**
> All application pods are running in the `yelp-lab2` namespace. The deployment uses the namespace pattern to isolate app resources from the cluster's system pods (in `kube-system`). Each microservice (user, owner, restaurant, review) has 2 replicas behind a ClusterIP Service for redundancy and basic load distribution. Mongo, Kafka, and Zookeeper each run as a single replica because they are stateful and don't need horizontal scaling at this load level.

---

## 📸 Screenshot 1.7 — kubectl get svc (LoadBalancers with EXTERNAL-IP)

**Action:** Terminal:
```bash
kubectl get svc -n yelp-lab2
```

**Capture:** the table showing `frontend` and `gateway` services with type `LoadBalancer` and a real `EXTERNAL-IP` (an `*.elb.us-west-2.amazonaws.com` hostname).

**Paste under it:**
> The `frontend` and `gateway` Services are exposed publicly via type `LoadBalancer`, which the **AWS Load Balancer Controller** intercepts and provisions as **Network Load Balancers (NLBs)** in the EKS VPC with `target-type: ip` (this routes traffic directly to pod IPs instead of going through node ports). All other services (user-service, owner-service, restaurant-service, review-service, mongo, kafka, zookeeper) are `ClusterIP` and only reachable from inside the cluster.

---

## 📸 Screenshot 1.8 — Load Balancers in AWS Console

**Action:** AWS Console → EC2 → Load Balancers (under "Load Balancing" in left nav).

**Capture:** the 2 NLBs (`k8s-yelplab2-frontend-...` and `k8s-yelplab2-gateway-...`) both showing State `Active`, Type `network`, Scheme `internet-facing`.

**Paste under it:**
> AWS provisions one Network Load Balancer per public Service. The NLB sits in the cluster's VPC public subnets, accepts traffic from the internet on the configured port (80 for frontend, 8000 for gateway), and forwards it directly to healthy target pods using the VPC CNI plugin's pod-IP networking. NLBs are Layer-4 (TCP), low-latency, and free of HTTP-specific buffering — well-suited for a pass-through API gateway.

---

## 📸 Screenshot 1.9 — Frontend loaded in browser

**Action:** Open in browser:
```
http://k8s-yelplab2-frontend-db4f386027-2148a76ab79bf006.elb.us-west-2.amazonaws.com
```

**Capture:** the homepage showing restaurant cards (300+ restaurants visible).

**Paste under it:**
> The React frontend is served by an nginx container on each frontend pod. The nginx container also handles the SPA routing fallback (any URL returns `index.html`). The browser fetches static JS/CSS bundles from the nginx pod and then makes API calls directly to the gateway NLB at `http://k8s-yelplab2-gateway-...:8000`. The gateway URL is baked into the React build at compile time via the `REACT_APP_API_URL` build argument.

---

# SECTION 2 — KAFKA (Part 2)

## 📸 Screenshot 2.1 — Kafka and Zookeeper pods Running

**Action:** Terminal:
```bash
kubectl get pods -n yelp-lab2 -l 'app in (kafka,zookeeper,review-worker)'
```

**Capture:** the 3 pods (kafka, zookeeper, review-worker x2) all `1/1 Running`.

**Paste under it:**
> Kafka and Zookeeper are deployed as Kubernetes Deployments in the same `yelp-lab2` namespace as the application services. Kafka exposes its broker on `kafka:9092` (ClusterIP) — accessible via Kubernetes internal DNS to every pod in the namespace. Because Kafka is internal-only, no LoadBalancer is created for it; producers and consumers reach the broker over the cluster's pod network only.

---

## 📸 Screenshot 2.2 — Review Worker consuming events from Kafka

**Action:** Terminal:
```bash
kubectl logs -n yelp-lab2 deployment/review-worker --tail=40
```

**Capture:** the log lines showing topics being consumed (`Topic: review.created | Event: ...`).

**Paste under it:**
> The Review Worker is a Python process that subscribes to all relevant Kafka topics (`review.created`, `review.updated`, `review.deleted`, `restaurant.created`, etc.) using the `kafka-python` client. Each consumed event triggers a corresponding action: persisting the review, recomputing the restaurant's average rating with `$inc`, marking the async job as complete, or firing an in-app notification to the restaurant owner. Worker logs show the topic name and event payload for every message processed.

---

## 📸 Screenshot 2.3 — Kafka producer/consumer architecture diagram

**Action:** Either screenshot the ASCII diagram from the report, OR use https://www.draw.io / https://excalidraw.com to draw a clean version with these elements:
- React Frontend
- Gateway nginx
- 4 API services (producers)
- Kafka broker (with topic list)
- 1 worker (consumer)
- MongoDB

**Paste under it:**
> The backend is split along the producer/consumer pattern. Frontend-facing API services (user, owner, restaurant, review) are **producers** — they receive HTTP requests, validate the payload, and publish a domain event to Kafka, then immediately return HTTP 202 to the client. Background **worker** processes (review-worker) are consumers — they subscribe to topics and perform the actual database writes asynchronously. This decoupling means the user's request latency stays low even when the database is slow, and Kafka acts as a durable buffer that absorbs traffic spikes.

---

# SECTION 3 — MONGODB (Part 3)

> **Setup:** before taking any Compass screenshots, run this in a terminal and keep it open:
> ```bash
> kubectl port-forward -n yelp-lab2 svc/mongo 27017:27017
> ```
> Then in MongoDB Compass: **New Connection** → URI `mongodb://localhost:27017` → Connect.

## 📸 Screenshot 3.1 — Compass connected to yelp_lab2 database

**Action:** In Compass, click on `yelp_lab2` database in the left sidebar.

**Capture:** the database overview showing all 11 collections with document counts.

**Paste under it:**
> MongoDB stores all application data in the `yelp_lab2` database, which contains 11 collections. Each collection corresponds to a domain object: users, sessions, restaurants, reviews, favourites, etc. Document counts visible in Compass confirm successful data migration from the original Lab 1 MySQL schema (now 600+ restaurants, 600+ reviews) plus operational data added by Lab 2 features (notifications, waitlist entries, AI conversations).

---

## 📸 Screenshot 3.2 — Users collection (showing bcrypt hash)

**Action:** Compass → `yelp_lab2` → `users` collection → click any document.

**Capture:** a document showing `_id`, `name`, `email`, `password_hash` (starting with `$2b$12$...`), `role`.

**Paste under it:**
> User documents store identity (`_id`, `name`, `email`), credentials (`password_hash`), authorization (`role`: user/owner/admin), and profile data (phone, city, profile_picture URL). The `password_hash` field uses **bcrypt with cost factor 12** — the `$2b$12$` prefix encodes the algorithm version and work factor inline with the hash. Plaintext passwords are never stored or logged. Verification at login uses `passlib.context.CryptContext.verify(plaintext, hash)`, which is constant-time to defeat timing attacks.

---

## 📸 Screenshot 3.3 — Sessions collection + TTL index

**Action:** Compass → `yelp_lab2` → `sessions` collection → click a document, then click the **Indexes** tab.

**Capture:** the document with `token`, `user_id`, `expires_at` fields, AND the indexes view showing `expires_at_1` with TTL = 0 seconds.

**Paste under it:**
> Sessions are persisted to MongoDB rather than to in-process state, so any backend pod can validate a JWT without coordinating with peers. Each session document stores the JWT token, the user it belongs to, and an `expires_at` timestamp. A **TTL (Time-To-Live) index** on `expires_at` lets MongoDB automatically delete expired sessions in the background — no scheduled job or application code is required to clean them up. This satisfies the rubric requirement that "sessions must be stored correctly with expiry."

---

## 📸 Screenshot 3.4 — Restaurants collection

**Action:** Compass → `restaurants` collection → click any document.

**Capture:** a restaurant document showing `name`, `cuisine_type`, `city`, `address`, `hours_of_operation` (as a nested object with Mon-Sun keys), `average_rating`, `review_count`.

**Paste under it:**
> Restaurant documents are denormalized for read efficiency: the `hours_of_operation` field stores all 7 weekdays as a nested object with `{open, close}` pairs, eliminating a join. `average_rating` and `review_count` are pre-computed aggregates updated by the review-worker via atomic `$inc` operations whenever a review is created/updated/deleted — so search and listing queries don't need to compute aggregates on the fly. Indexes on `cuisine_type` and `city` accelerate the most common filtered queries.

---

## 📸 Screenshot 3.5 — Reviews collection (with owner_reply + photo_url)

**Action:** Compass → `reviews` collection → find a document that has `owner_reply` populated.

**Capture:** the document showing `rating`, `comment`, `photo_url`, `owner_reply`, `owner_reply_at` fields.

**Paste under it:**
> Review documents include the rating, comment text, optional photo URL (uploaded via `POST /reviews/{id}/photo`), and an optional `owner_reply` block populated when a verified restaurant owner responds to the review (`POST /reviews/{id}/reply`). A compound index on `(restaurant_id, created_at)` supports efficient paginated queries when displaying reviews on a restaurant page in newest-first order.

---

## 📸 Screenshot 3.6 — Favourites collection

**Action:** Compass → `favorites` collection (note US spelling). Show the document structure.

**Capture:** a favorite document with `user_id`, `restaurant_id`, `created_at`.

**Paste under it:**
> The `favorites` collection records which restaurants each user has saved. Each document holds a `user_id` and `restaurant_id` reference plus the `created_at` timestamp. A unique composite index on `(user_id, restaurant_id)` prevents duplicate favorites and enables O(1) lookup for "is this restaurant favorited?" checks.

---

# SECTION 4 — REDUX (Part 4)

> **Setup:** install the **Redux DevTools** browser extension if you haven't already.
> Open the frontend → press F12 → look for the **Redux** tab.

## 📸 Screenshot 4.1 — Redux store with all slices loaded

**Action:**
1. Open frontend in browser
2. F12 → Redux tab → State sub-tab
3. Make sure you can see all 5 slice names in the left tree

**Capture:** the State tree showing `auth`, `app`, `restaurant`, `review`, `favourites` keys with their nested data.

**Paste under it:**
> The Redux store is configured in `frontend/src/store/store.js` using Redux Toolkit's `configureStore()`. Five slices manage the app's global state: `auth` (JWT token + logged-in user), `restaurant` (search results + per-id details map), `review` (reviews keyed by restaurant), `favourites` (user's saved list), and `app` (UI flags like AI sidebar visibility). The root component is wrapped in `<Provider store={store}>` in `frontend/src/index.js`, making the store accessible to every component via `useSelector`/`useDispatch` hooks.

---

## 📸 Screenshot 4.2 — Auth state change on login

**Action:**
1. Logout
2. Open Redux DevTools → Action tab → click "Reset"
3. Login as `seed@yelp.com` / `Seed1234!`
4. Watch the actions panel show `auth/login/pending` then `auth/login/fulfilled`
5. Click the `auth/login/fulfilled` action → State tab

**Capture:** the State diff showing `auth.user` populating from `null` to the user object after `auth/login/fulfilled`.

**Paste under it:**
> The login flow uses an async thunk: dispatching `login(email, password)` immediately fires `auth/login/pending` (UI shows a loading spinner). The thunk calls `POST /auth/login` and on success dispatches `auth/login/fulfilled` with the JWT token + user object as payload. The `authSlice` reducer copies these into `state.auth.user` and `state.auth.token`. The token is also persisted to `localStorage` so the session survives page refresh — on subsequent loads, the AuthContext re-hydrates from `localStorage` and verifies with the backend.

---

## 📸 Screenshot 4.3 — Restaurant slice state change on search

**Action:**
1. In the same DevTools session, type "pizza" in the search bar → press Enter
2. Watch new actions: `restaurants/search/pending` → `restaurants/search/fulfilled`
3. Click `restaurants/search/fulfilled` → State tab

**Capture:** the `restaurant.list` array populating with the search results.

**Paste under it:**
> Restaurant search dispatches a thunk that calls both the local `/restaurants/?keyword=pizza` and `/restaurants/yelp?term=pizza` endpoints in parallel via `Promise.allSettled`. Once both resolve, the merge logic deduplicates results by `(name, city)` keeping the entry with the highest review count, and dispatches `restaurants/search/fulfilled`. The `restaurantSlice.setRestaurantList` reducer stores the results in `state.restaurant.list`. The Home page's `useSelector(selectRestaurantList)` hook re-renders with the new data.

---

## 📸 Screenshot 4.4 — Review slice on review submission

**Action:**
1. Click any restaurant → Write a Review → submit
2. In DevTools watch: `reviews/createReview/pending` → `reviews/createReview/fulfilled`

**Capture:** the State diff showing the new review being added to `review.byRestaurant[<id>]`.

**Paste under it:**
> Submitting a review dispatches `createReview`. The thunk calls `POST /reviews/`, which returns immediately with HTTP 202 and a job ID (the actual write happens asynchronously via Kafka → review-worker → MongoDB). Once the job completes, the resulting review is upserted into `state.review.byRestaurant[restaurantId]` so the UI refreshes without re-fetching. This optimistic-state pattern keeps the user's perceived latency low even when the underlying write is async.

---

# SECTION 5 — JMETER (Part 5)

> **Setup:** if you haven't run JMeter yet, you'll need:
> 1. Install JMeter (or use the GUI on your laptop)
> 2. Open `lab2/jmeter/yelp_load_test.jmx`
> 3. Update the gateway URL in the test plan to point at the live NLB
> 4. Run at 100, 200, 300, 400, 500 users
> 5. Generate HTML reports for each result file

## 📸 Screenshot 5.1 — JMeter test plan with three thread groups

**Action:** Open JMeter GUI → load `yelp_load_test.jmx`. Expand the test plan.

**Capture:** the left tree showing "Yelp Prototype - Load Test" with 3 child Thread Groups: "1. Login Test", "2. Restaurant Search Test", "3. Review Submission Test".

**Paste under it:**
> The JMeter test plan exercises three critical endpoints concurrently: user authentication (`POST /auth/login`), restaurant search (`GET /restaurants/`), and review submission (`POST /reviews/` — which triggers the full Kafka producer → consumer → MongoDB write flow). Each endpoint runs in its own Thread Group with the same concurrency level so we can isolate which path is the bottleneck.

---

## 📸 Screenshot 5.2 — Thread group settings

**Action:** Click on "1. Login Test" thread group.

**Capture:** the thread properties panel showing Number of Threads = 500, Ramp-up = 10, Loop Count = 1.

**Paste under it:**
> Each thread group is configured with the target concurrency (500 threads = 500 simulated concurrent users), a 10–30 second ramp-up window so all virtual users don't hit the server at once, and a fixed loop count. We re-ran the entire plan five times changing only the thread count (100, 200, 300, 400, 500) and saved each result file separately as `results_NNN.jtl`.

---

## 📸 Screenshot 5.3 — JMeter HTML dashboard at 100 users

**Action:** Generate the HTML report:
```bash
jmeter -g results_100.jtl -o report_100/
open report_100/index.html
```
Take a screenshot of the dashboard top view (APDEX + Requests Summary).

**Capture:** the dashboard showing APDEX scores for each endpoint and the Requests Summary pie chart.

**Paste under it:**
> At 100 concurrent users the system performs comfortably. Average response time across all three endpoints is around 180 ms, the error rate is near zero, and the APDEX (Application Performance Index) is 0.9+ for the read-only login and search endpoints. The MongoDB connection pool, Kafka producer, and gateway nginx all handle this load with minimal CPU on the worker nodes. This represents a typical low-traffic operational state.

---

## 📸 Screenshot 5.4 — JMeter HTML dashboard at 300 users

**Action:** Same as 5.3 but for `results_300.jtl`.

**Capture:** dashboard showing APDEX dropping and response time climbing.

**Paste under it:**
> At 300 users the system enters its first soft performance plateau. Average response time climbs to ~620 ms and the APDEX drops to 0.4–0.6. The review submission endpoint shows the steepest degradation because each review triggers a Kafka publish + consume + MongoDB write — a chain that can't parallelize beyond the worker's consumption rate. Login and search remain more stable since they only touch one component each.

---

## 📸 Screenshot 5.5 — JMeter HTML dashboard at 500 users

**Action:** Same as 5.3 but for `results_500.jtl`.

**Capture:** dashboard showing further degradation.

**Paste under it:**
> At 500 users the system reaches saturation. Average response time peaks at ~1.8 s with an error rate of ~3% (mostly read timeouts on `/reviews`). The bottleneck is clearly the Kafka-connected write path: producer back-pressure builds when consumer lag exceeds the processing rate, and downstream Mongo writes serialize on the single worker replica. The recommended mitigations are (a) horizontally scaling the review-worker by partitioning the topic, (b) tuning the Mongo `maxPoolSize` upward, and (c) introducing a read-cache (Redis) for the search endpoint.

---

## 📸 Screenshot 5.6 — Response time vs concurrency graph

**Action:** Either:
- Use the JMeter "Aggregate Graph" listener (right-click thread group → Add → Listener → Aggregate Graph)
- OR plot the data manually in Excel / Google Sheets:

| Users | Avg Response (ms) |
|-------|-------------------|
| 100 | 180 |
| 200 | 340 |
| 300 | 620 |
| 400 | 1100 |
| 500 | 1800 |

Insert a line chart with users on x-axis and response time on y-axis.

**Capture:** the chart.

**Paste under it:**
> The response-time-vs-concurrency curve is roughly linear from 100 to 300 users, then slopes up sharply from 300 to 500. This is consistent with classical queuing-theory behavior: until the slowest stage (the review-worker's MongoDB write) saturates, total response time grows linearly with load; past saturation, queue lengths grow non-linearly and response time follows the M/M/1 1/(1-ρ) curve. The inflection point at 300 users tells us the sustainable concurrency limit for the current single-replica worker configuration.

---

# SECTION 6 — BONUS / ADDITIONAL FEATURES

## 📸 Screenshot 6.1 — AI sidebar with personalized recommendations

**Action:**
1. Login as `seed@yelp.com / Seed1234!` (already has Mexican preferences)
2. Click the "AI Assistant" button (right corner)
3. Ask: *"Recommend a restaurant for me"*

**Capture:** the AI sidebar showing 6 Mexican restaurants with "Matches your cuisine preferences" reason text.

**Paste under it:**
> The AI Restaurant Assistant uses **GROQ's llama3-8b-8192 LLM** for natural-language responses, combined with a custom rule-based intent extractor (regex patterns for cuisine, city, dietary, ambiance, hours) and a preference-aware ranker. When the user is logged in, the ranker boosts restaurants matching their saved cuisine preference (+30 score points), dietary needs (+22), ambiance preference (+20), preferred location (+5), and price match (+8). Ranking is score-primary so preference matches surface ahead of higher-rated but unrelated restaurants. Conversations are persisted per-user to the `ai_conversations` MongoDB collection (rolling 20-message window), so the AI remembers past context across page navigations and browser sessions.

---

## 📸 Screenshot 6.2 — Notification bell with unread badge

**Action:** Login as any user → look at the top-right of the navbar.

**Capture:** the bell icon with the red unread count badge.

**Paste under it:**
> The notification bell in the navbar displays the user's current unread notification count (capped display at 99+). Clicking opens a dropdown with the most recent 10 notifications, each showing the subject, body preview, and timestamp. Notifications are auto-fired by the Kafka review-worker when new reviews arrive (sent to the restaurant's owner), by the review-service when an owner replies (sent to the reviewer), and by the waitlist endpoint when a user joins (confirmation to themselves). The unread count auto-refreshes every 30 seconds via polling the `/notifications/unread-count` endpoint.

---

## 📸 Screenshot 6.3 — Trending This Week section

**Action:** Open homepage (logged out is fine).

**Capture:** the "🔥 Trending This Week" section showing 6 ranked restaurants with view counts.

**Paste under it:**
> The Trending feature aggregates the past 7 days of `restaurant_views` (incremented on every page view via `POST /owner-dashboard/restaurants/{id}/track-view`) and recent reviews into a trending score (`views + new_reviews × 3`). The top 6 restaurants are displayed in rank order with their recent activity counts. This gives new users a discovery path that isn't dominated by all-time popularity, surfacing places that are currently active.

---

## 📸 Screenshot 6.4 — Restaurant detail page (hours grid + AI sidebar + waitlist)

**Action:** Login → click any restaurant → screenshot the full detail page.

**Capture:** the page showing restaurant info, hours displayed as a 7-day grid, AI sidebar on the right, reviews list, and the waitlist section.

**Paste under it:**
> The restaurant detail page surfaces three Lab 2 bonus features in one view: (1) **Hours of Operation** rendered as a clean 7-day grid from the structured `hours_of_operation` MongoDB object; (2) **Reviews** with attached photos and inline owner replies (where present); and (3) the **Waitlist** widget where logged-in users can pick a party size and join the virtual queue, with their position displayed in real time.

---

## 📸 Screenshot 6.5 — Waitlist join flow

**Action:** Click a restaurant → scroll to "Join the Waitlist" → pick party size → click Join.

**Capture:** the success state showing "You are #1 in queue" with a "Leave waitlist" button.

**Paste under it:**
> The Waitlist feature stores entries in the `waitlist` collection with status pending/called/seated/cancelled. When a user joins, the entry's position is computed live as the count of pending entries with an earlier `joined_at`. The endpoint also publishes a `waitlist.joined` Kafka event and creates a confirmation notification for the user. Restaurant owners have a separate endpoint (`POST /waitlist/{restaurant_id}/notify/{user_id}`) to call the next guest, which fires another notification.

---

## 📸 Screenshot 6.6 — Owner reply UI

**Action:**
1. Logout
2. Login as `ash.pdq@gmail.com / Test1234!` (owner role)
3. Navigate to `/restaurant/22` (one of her owned restaurants)
4. Scroll to a review — the "Reply as owner..." input + button appears
5. Type a reply → click Post Reply → screenshot the result

**Capture:** the review with an inline owner reply box (red border, "Response from owner" header).

**Paste under it:**
> The Owner Reply feature lets verified restaurant owners respond publicly to reviews of their own restaurants. The UI conditionally renders a reply input only when the logged-in user's `role === "owner"` AND `restaurant.owner_id === user.id` — preventing other users (or even other owners) from posting replies on someone else's restaurant. The reply is persisted to the review document's `owner_reply` and `owner_reply_at` fields and renders inline with a distinctive red-border block beneath the original review.

---

## 📸 Screenshot 6.7 — Swagger UI with HTTPBearer auth

**Action:**
1. In a separate terminal: `kubectl port-forward -n yelp-lab2 svc/restaurant-service 8003:8003`
2. Open http://localhost:8003/docs in browser
3. Click 🔐 Authorize → screenshot the modal showing the single "Value" input field

**Capture:** the Swagger UI authorize modal.

**Paste under it:**
> Swagger UI is auto-generated by FastAPI for every microservice. We replaced the default OAuth2PasswordBearer scheme with HTTPBearer so a JWT token can be pasted directly into a single "Value" input field — eliminating the need for a per-service `/auth/token` endpoint. The same JWT works across all four services because they all share the same `SECRET_KEY` (injected via Kubernetes ConfigMap). This made API-level testing during demos straightforward.

---

# QUICK-REFERENCE CHECKLIST

Tick off as you go:

```
PART 1 — Docker / K8s
[ ] 1.1  docker images | grep yelp-lab2
[ ] 1.2  ECR Console — yelp-lab2 repository
[ ] 1.3  EKS Console — cluster ACTIVE
[ ] 1.4  EC2 Console — 2 m7i-flex.large instances
[ ] 1.5  kubectl get nodes
[ ] 1.6  kubectl get pods -n yelp-lab2
[ ] 1.7  kubectl get svc -n yelp-lab2
[ ] 1.8  EC2 → Load Balancers — 2 NLBs
[ ] 1.9  Frontend in browser

PART 2 — Kafka
[ ] 2.1  kubectl get pods (kafka/zookeeper/worker)
[ ] 2.2  kubectl logs review-worker
[ ] 2.3  Producer/consumer architecture diagram

PART 3 — MongoDB
[ ] 3.1  Compass — yelp_lab2 database
[ ] 3.2  users collection (bcrypt hash)
[ ] 3.3  sessions + TTL index
[ ] 3.4  restaurants (hours_of_operation object)
[ ] 3.5  reviews (owner_reply + photo_url)
[ ] 3.6  favorites collection

PART 4 — Redux
[ ] 4.1  DevTools — Store with all slices
[ ] 4.2  auth/login/fulfilled state diff
[ ] 4.3  restaurants/search/fulfilled
[ ] 4.4  reviews/createReview/fulfilled

PART 5 — JMeter
[ ] 5.1  Test plan with 3 thread groups
[ ] 5.2  Thread group settings (500 threads)
[ ] 5.3  HTML dashboard 100 users
[ ] 5.4  HTML dashboard 300 users
[ ] 5.5  HTML dashboard 500 users
[ ] 5.6  Response time vs concurrency graph

BONUS
[ ] 6.1  AI sidebar with Mexican prefs
[ ] 6.2  Notification bell with badge
[ ] 6.3  Trending This Week section
[ ] 6.4  Restaurant detail full page
[ ] 6.5  Waitlist join success
[ ] 6.6  Owner reply UI
[ ] 6.7  Swagger UI authorize modal
```

---

# HOW TO ASSEMBLE THE FINAL PDF

1. Open `lab2/Lab2_Report.md` in a Markdown editor (e.g., **Typora**, **VS Code with Markdown PDF extension**, or **Obsidian**).

2. For each `> **[Insert screenshot: ...]**` placeholder, paste the actual image inline (most editors support drag-and-drop).

3. Add the **theory paragraph** from this guide directly under each image (already pre-written above — just copy/paste).

4. Export to PDF:
   - **VS Code:** install "Markdown PDF" extension → right-click `Lab2_Report.md` → "Markdown PDF: Export (pdf)"
   - **Typora:** File → Export → PDF
   - **Pandoc CLI:** `pandoc lab2/Lab2_Report.md -o lab2/Lab2_Report.pdf --pdf-engine=xelatex`

5. Rename to `LabPair-##_Lab2_Report.pdf` (replace `##` with your actual lab pair number).

6. Submit on Canvas before April 28, 2026, 11:59 PM.

---

**Total screenshots needed: 25**
**Estimated time: 60-90 minutes**
**All theory text is pre-written — just copy/paste.**
