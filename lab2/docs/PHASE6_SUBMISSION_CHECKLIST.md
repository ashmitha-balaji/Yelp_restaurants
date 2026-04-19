# Phase 6 Submission Checklist

Use this checklist to finalize and submit Lab 2.

## A) Final Smoke Validation (completed baseline)

- [x] `GET /restaurants/` via gateway returns 200.
- [x] Auth flow works (`/auth/signup`, `/auth/login`).
- [x] Async review flow works (`POST /reviews/` returns 202 + job completes).
- [x] Kubernetes deployments in `yelp-lab2` namespace are all `READY`.

## B) Evidence to Include in Final PDF

- [ ] Phase 1: Kafka producer-consumer evidence
  - [ ] `restaurant.created` event in `restaurant_events`
  - [ ] review async job accepted + completed
- [ ] Phase 2: Security evidence
  - [ ] bcrypt hash in `users.password_hash`
  - [ ] `sessions` TTL index (`expireAfterSeconds: 0`)
  - [ ] expired session auto-delete proof
- [ ] Phase 3: Infrastructure evidence
  - [ ] `kubectl get nodes`
  - [ ] `kubectl get deployments -n yelp-lab2`
  - [ ] `kubectl get pods -n yelp-lab2`
  - [ ] `kubectl get svc -n yelp-lab2`
- [ ] Phase 4: Redux evidence
  - [ ] DevTools screenshot of `auth` slice transitions
  - [ ] DevTools screenshot of `app` slice route events
- [ ] Phase 5: JMeter evidence
  - [ ] `phase5_summary.csv` table (100/300/500)
  - [ ] response-time graph
  - [ ] one analysis paragraph

## C) Files Ready for Report

- `lab2/docs/ARCHITECTURE_KAFKA.md`
- `lab2/docs/PHASE5_ANALYSIS.md`
- `lab2/jmeter/results/phase5_summary.csv`
- `lab2/jmeter/results/html_100/index.html`
- `lab2/jmeter/results/html_300/index.html`
- `lab2/jmeter/results/html_500/index.html`

## D) Final Packaging Steps

- [ ] Create final report file: `LabPair-##_Lab2_Report.pdf`
- [ ] Ensure no secrets are committed (`.env` files excluded).
- [ ] Final quick run:
  - [ ] `docker compose --env-file lab2/.env -f lab2/docker-compose.yml up -d`
  - [ ] Validate frontend at `http://localhost:3000`
  - [ ] Validate gateway at `http://localhost:8000`
- [ ] Submit repo + PDF per course instructions.
