# Lab 2 — Demo Day Playbook

Everything you need on demo day, in one document.

---

# Part A — Tonight: shut down your current cluster

```bash
cd /Users/ashmitharoopkumar/Desktop/236-distributed/assignment_solutions/lab-1
bash lab2/scripts/delete_all.sh
# When asked "Delete ECR repository?" → answer 'n'
# (keeps images, saves ~10 min on tomorrow's build)
```

Wait ~10-15 min for full teardown. After it finishes, AWS billing stops. You can close the laptop.

---

# Part B — Demo day morning: rebuild everything

## B1. Pre-flight

Make sure these are running on your Mac:

```bash
# Docker Desktop must be running (open it from Applications)
docker ps                        # should not error

# AWS credentials still valid?
aws sts get-caller-identity      # should print your account 839408459700

# Kubernetes tools installed?
kubectl version --client
helm version
eksctl version
```

## B2. One-command full deploy

```bash
cd /Users/ashmitharoopkumar/Desktop/236-distributed/assignment_solutions/lab-1

export YELP_API_KEY='Ls3QXX7jN0X6RlR8fV2Mwh7ZJACHxEc3YLIgW8RcQtSYXyeT4bvHlV5FCkFjt1pETfTg3IAMHQOku1LspKQwgYWmHUjzcuWpFlS65eck347EBrOGFaW7afb6R0HkaXYx'

bash lab2/scripts/full_setup.sh
```

**Time: ~30-40 min** (or ~15 min if you kept ECR images last night).

At the end the script prints:
```
Frontend:  http://k8s-yelplab2-frontend-XXXXXXXXXX.elb.us-west-2.amazonaws.com
API:       http://k8s-yelplab2-gateway-XXXXXXXXXX.elb.us-west-2.amazonaws.com:8000
Login:     seed@yelp.com / Seed1234!
```

**Save those URLs.** Every URL changes on each redeploy.

## B3. Capture the URLs into env vars (paste these in your demo terminal)

```bash
export FE_URL=$(kubectl get svc frontend -n yelp-lab2 -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
export GW_URL=$(kubectl get svc gateway -n yelp-lab2 -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "Frontend: http://$FE_URL"
echo "Gateway:  http://$GW_URL:8000"
```

## B4. Reset known passwords (so you can log in as different roles)

```bash
HASH=$(kubectl exec -n yelp-lab2 deployment/user-service -- python3 -c "
from passlib.context import CryptContext
print(CryptContext(schemes=['bcrypt']).hash('Test1234!'))
" | tail -1)

kubectl exec -n yelp-lab2 deployment/mongo -- mongosh yelp_lab2 --quiet --eval "
db.users.updateMany({email: {\$ne: 'seed@yelp.com'}}, {\$set: {password_hash: '$HASH'}});
print('All non-seed user passwords reset to Test1234!');
"
```

## B5. Set Mexican preferences for the seed user (so AI demo works cleanly)

```bash
kubectl exec -n yelp-lab2 deployment/mongo -- mongosh yelp_lab2 --quiet --eval '
db.user_preferences.updateOne(
  {user_id: 1},
  {$set: {
    cuisine_preferences: "Mexican",
    price_range: "$$",
    dietary_needs: "Vegan",
    ambiance_preferences: "Casual",
    preferred_locations: null,
    sort_preference: null
  }},
  {upsert: true}
);
print("done");
'
```

---

# Part C — Login credentials

| Email | Password | Role | Use for demo |
|-------|----------|------|--------------|
| `seed@yelp.com` | `Seed1234!` | user | AI prefs, write reviews, search |
| `ash.pdq@gmail.com` | `Test1234!` | **owner** | Owner dashboard, reply to reviews |
| `davidray@gmail.com` | `Test1234!` | user | Second user demo |
| `naman.chheda@sjsu.edu` | `Test1234!` | user | Partner login |
| `testowner@yelp.com` | `Test1234!` | **owner** | Spare owner account |

---

# Part D — Verify everything is healthy (before demo)

```bash
# 1. Worker nodes
kubectl get nodes

# 2. All app pods Running (should show 15 pods all 1/1)
kubectl get pods -n yelp-lab2

# 3. NLBs have public DNS
kubectl get svc -n yelp-lab2

# 4. PVC bound to real EBS volume
kubectl get pvc -n yelp-lab2

# 5. EBS CSI driver pods running
kubectl get pods -n kube-system | grep ebs

# 6. AWS LB Controller running
kubectl get pods -n kube-system | grep aws-load-balancer

# 7. Test frontend responds
curl -sf -o /dev/null -w "Frontend HTTP %{http_code}\n" http://$FE_URL

# 8. Test API responds
curl -sf -o /dev/null -w "Gateway HTTP %{http_code}\n" http://$GW_URL:8000/restaurants/
```

---

# Part E — Show Docker images (during demo)

## E1. List images locally on your laptop
```bash
docker images | grep yelp-lab2
```

## E2. List images in your ECR registry
```bash
aws ecr list-images --repository-name yelp-lab2 --region us-west-2 --output table
```

## E3. Show what image each pod is running
```bash
kubectl get pods -n yelp-lab2 -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].image}{"\n"}{end}'
```

---

# Part F — Show MongoDB data (during demo)

## F1. Quick CLI query (fastest)

```bash
# All users
kubectl exec -n yelp-lab2 deployment/mongo -- mongosh yelp_lab2 --quiet --eval '
db.users.find({}, {_id:1, name:1, email:1, role:1}).toArray()
'

# Collections + counts
kubectl exec -n yelp-lab2 deployment/mongo -- mongosh yelp_lab2 --quiet --eval '
print("=== Counts ===");
["users","restaurants","reviews","sessions","favorites","notifications","waitlist","ai_conversations","user_preferences"].forEach(c => 
  print(`  ${c.padEnd(20)}: ${db[c].countDocuments()}`)
);
'

# Sample documents
kubectl exec -n yelp-lab2 deployment/mongo -- mongosh yelp_lab2 --quiet --eval '
print("=== Sample user ===");
print(JSON.stringify(db.users.findOne({email: "seed@yelp.com"}), null, 2));
print("");
print("=== Sample restaurant ===");
print(JSON.stringify(db.restaurants.findOne(), null, 2));
print("");
print("=== Sample session (TTL on expires_at) ===");
print(JSON.stringify(db.sessions.findOne(), null, 2));
'
```

## F2. MongoDB Compass (visual, recommended for demo)

In a **separate terminal** (keep open during demo):
```bash
kubectl port-forward -n yelp-lab2 svc/mongo 27017:27017
```

Then open MongoDB Compass → connect to:
```
mongodb://localhost:27017
```

Browse `yelp_lab2` database → click any collection.

---

# Part G — Swagger UI (during demo)

## G1. Start port-forwards in background

In a **dedicated terminal** (don't close it):
```bash
kubectl port-forward -n yelp-lab2 svc/user-service 8001:8001 >/dev/null 2>&1 &
kubectl port-forward -n yelp-lab2 svc/owner-service 8002:8002 >/dev/null 2>&1 &
kubectl port-forward -n yelp-lab2 svc/restaurant-service 8003:8003 >/dev/null 2>&1 &
kubectl port-forward -n yelp-lab2 svc/review-service 8004:8004 >/dev/null 2>&1 &
echo "All 4 port-forwards started"
sleep 5
for p in 8001 8002 8003 8004; do
  echo "  http://localhost:$p/docs → HTTP $(curl -s -o /dev/null -w '%{http_code}' http://localhost:$p/docs)"
done
```

## G2. Open these URLs in browser tabs

| Service | URL | Features |
|---------|-----|----------|
| User + Auth | http://localhost:8001/docs | login, signup, profile, favorites, **notifications** |
| Owner | http://localhost:8002/docs | owner analytics, reviews moderation |
| Restaurant + AI | http://localhost:8003/docs | restaurants, **autocomplete, trending, open-now**, AI chat |
| Reviews + Waitlist | http://localhost:8004/docs | reviews, **owner reply, photo upload, waitlist** |

## G3. Authorize each Swagger tab

Get a token first:
```bash
TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"seed@yelp.com","password":"Seed1234!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Paste this in Swagger 🔐 Authorize:"
echo "$TOKEN"
```

In each `/docs` tab:
1. Click 🔐 **Authorize** (top right)
2. Paste the token in the **Value** field (no "Bearer " prefix)
3. Click **Authorize** → **Close**

All locked endpoints in that tab now work.

---

# Part H — Demo flow (40 minutes)

## H1. Architecture intro (5 min, terminal)

```bash
# Show the cluster overview
kubectl get nodes
kubectl get pods -n yelp-lab2
kubectl get svc -n yelp-lab2
kubectl get pvc -n yelp-lab2
```

Talk through:
- "2 m7i-flex.large EC2 worker nodes managed by EKS"
- "All pods Running — 5 microservices + Mongo + Kafka + Zookeeper + 2 nginx (gateway, frontend)"
- "MongoDB has a 2 GB EBS volume bound — survives pod restarts"
- "Two NLBs route public traffic into the cluster"

## H2. Frontend walkthrough (15 min, browser)

Open: `http://$FE_URL`

1. **Homepage**
   - "🔥 Trending This Week" section
   - 300 seeded restaurants + real Yelp data (Bibo's NY Pizza, etc.) mixed in

2. **Search** for "pizza" → shows deduped results (no triple-Bibo)

3. **Login** as `seed@yelp.com / Seed1234!`
   - Notification bell appears in navbar with unread count

4. **Restaurant detail page** (click any card)
   - Hours displayed as 7-day grid
   - Reviews with photos
   - Waitlist section: pick party size → Join → see queue position

5. **AI Sidebar** (right corner)
   - Ask: *"Recommend a restaurant for me"* → all Mexican (uses prefs)
   - Ask: *"Italian restaurants open right now"* → Italian + open-now filter
   - Show conversation history persists across page navigation

6. **Write a Review**
   - Star + comment + 📷 attach photo + submit
   - Refresh → see review with photo on restaurant page

7. **Owner login** (logout, login as `ash.pdq@gmail.com / Test1234!`)
   - Open Owner Dashboard from menu
   - Click into one of her 3 restaurants (id 22, 302, or 303)
   - On a review → see "Reply as owner..." input → post a reply
   - Reply renders with red border + "Response from owner" label

## H3. API/Swagger demo (10 min)

Open the 4 Swagger tabs (already authorized). Click "Try it out" → "Execute" on:

- `GET /restaurants/autocomplete?q=fla` (port 8003)
- `GET /restaurants/trending` (port 8003)
- `GET /restaurants/open-now` (port 8003)
- `POST /waitlist/{restaurant_id}` with `{"party_size": 4}` (port 8004)
- `GET /notifications/` (port 8001)
- `GET /ai-assistant/history` (port 8003)

Or run the all-in-one demo script:
```bash
bash lab2/scripts/demo_api_features.sh
```

## H4. MongoDB walkthrough (5 min)

In Compass (already connected):
- Show **users** collection — bcrypt password hashes, role field
- Show **sessions** — TTL index on expires_at
- Show **restaurants** — hours_of_operation as object, indexes on cuisine_type
- Show **reviews** — owner_reply, photo_url fields
- Show **notifications** — auto-fired by Kafka worker

## H5. JMeter results (5 min)

Show the JMeter dashboard HTML reports for 100, 300, 500 concurrent users.
Walk through the response time vs concurrency graph.

---

# Part I — Test features quickly via curl (during demo if needed)

```bash
# Get fresh token
GATEWAY="http://$GW_URL:8000"
TOKEN=$(curl -s -X POST "$GATEWAY/auth/login" -H "Content-Type: application/json" \
  -d '{"email":"seed@yelp.com","password":"Seed1234!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 1. Search autocomplete
curl -s "$GATEWAY/restaurants/autocomplete?q=fla" | python3 -m json.tool

# 2. Trending
curl -s "$GATEWAY/restaurants/trending?limit=5" | python3 -m json.tool

# 3. Open-now
curl -s "$GATEWAY/restaurants/open-now?limit=3" | python3 -m json.tool

# 4. Hours filter
curl -s "$GATEWAY/restaurants/?at_time=20:00&limit=3" | python3 -m json.tool

# 5. AI history (logged-in)
curl -s -H "Authorization: Bearer $TOKEN" "$GATEWAY/ai-assistant/history" | python3 -m json.tool

# 6. Notifications
curl -s -H "Authorization: Bearer $TOKEN" "$GATEWAY/notifications/unread-count"

# 7. AI chat with prefs
curl -s -X POST "$GATEWAY/ai-assistant/chat" -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Recommend a restaurant"}' | python3 -m json.tool

# 8. Run all 7 features in one command
bash lab2/scripts/demo_api_features.sh
```

---

# Part J — Troubleshooting (if anything breaks during demo)

## J1. Pod showing CrashLoopBackOff
```bash
kubectl get pods -n yelp-lab2
kubectl describe pod <pod-name> -n yelp-lab2 | tail -20
kubectl logs <pod-name> -n yelp-lab2 --tail=50
```

## J2. NLB not getting public DNS
```bash
kubectl logs -n kube-system deployment/aws-load-balancer-controller --tail=30
```

## J3. Restart a service (if hung)
```bash
kubectl rollout restart deployment/<service-name> -n yelp-lab2
kubectl rollout status deployment/<service-name> -n yelp-lab2 --timeout=120s
```

## J4. Mongo PVC stuck in Pending
```bash
kubectl describe pvc mongo-pvc -n yelp-lab2 | tail -10
# If "no provisioner", EBS CSI driver isn't installed — re-run install step
```

## J5. Port-forward died (Swagger tab broke)
```bash
pkill -f "kubectl port-forward"
sleep 2
# Restart from Part G1
```

## J6. Frontend shows old "localhost:8000" error
```bash
# JS bundle is cached or build didn't pick up real URL
# Rebuild with --no-cache
docker buildx build --no-cache --platform linux/amd64 \
  -t 839408459700.dkr.ecr.us-west-2.amazonaws.com/yelp-lab2:frontend \
  --build-arg REACT_APP_API_URL=http://$GW_URL:8000 \
  -f lab2/docker/Dockerfile.frontend --push .
kubectl rollout restart deployment/frontend -n yelp-lab2
```

## J7. AI returning unrelated cuisine
```bash
# Make sure user prefs are set
kubectl exec -n yelp-lab2 deployment/mongo -- mongosh yelp_lab2 --quiet --eval '
db.user_preferences.findOne({user_id: 1})
'
# If wrong, re-run Part B5
```

---

# Part K — Right after demo: stop the bill

```bash
cd /Users/ashmitharoopkumar/Desktop/236-distributed/assignment_solutions/lab-1
bash lab2/scripts/delete_all.sh
# When asked "Delete ECR repository?" → 'y' (no future demo, free up ~$0.18/mo)
```

Wait ~10-15 min. Verify nothing remains:
```bash
aws eks list-clusters --region us-west-2
aws ec2 describe-instances --region us-west-2 \
  --filters "Name=instance-state-name,Values=running,pending" \
  --query "Reservations[].Instances[].[InstanceId,State.Name,InstanceType]" --output table
aws elbv2 describe-load-balancers --region us-west-2 \
  --query "LoadBalancers[].LoadBalancerName" --output table
```

All three should be empty.

---

# Part L — Cost summary

| Phase | Duration | Cost |
|-------|----------|------|
| Tonight (existing cluster runs overnight) | 12 hrs | ~$3.60 |
| Tomorrow morning rebuild | 30 min | ~$0.15 |
| Demo session | 1 hr | ~$0.30 |
| Cleanup | — | $0 |
| **Total** | | **~$4** |

Well within your $100 credits.

---

# Part M — All public URLs (fill in after deploy)

| Resource | URL |
|----------|-----|
| Frontend | `http://__________________________________` |
| Gateway API | `http://__________________________________:8000` |
| GitHub repo | https://github.com/ashmitha-balaji/Yelp_restaurants |

---

# Quick reference card (print this!)

```
=== DEPLOY ===
bash lab2/scripts/full_setup.sh

=== MONGO ===
kubectl port-forward -n yelp-lab2 svc/mongo 27017:27017
# then connect Compass to mongodb://localhost:27017

=== SWAGGER (4 ports) ===
kubectl port-forward -n yelp-lab2 svc/user-service 8001:8001 &
kubectl port-forward -n yelp-lab2 svc/owner-service 8002:8002 &
kubectl port-forward -n yelp-lab2 svc/restaurant-service 8003:8003 &
kubectl port-forward -n yelp-lab2 svc/review-service 8004:8004 &

=== HEALTH ===
kubectl get nodes
kubectl get pods -n yelp-lab2
kubectl get svc -n yelp-lab2

=== DOCKER IMAGES ===
docker images | grep yelp-lab2
aws ecr list-images --repository-name yelp-lab2 --region us-west-2

=== CLEANUP ===
bash lab2/scripts/delete_all.sh

=== LOGINS ===
seed@yelp.com / Seed1234!           (user)
ash.pdq@gmail.com / Test1234!       (owner — owns 3 restaurants)
testowner@yelp.com / Test1234!      (owner)
davidray@gmail.com / Test1234!      (user)
```
