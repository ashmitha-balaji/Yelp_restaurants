# JMeter (Lab 2)

## Requirements

- Run tests against **login**, **GET /restaurants/** (or search), and **POST /reviews/** (Kafka flow) at **100, 200, 300, 400, 500** concurrent users.  
- Record **average response time**, **throughput (req/s)**, and **error rate** per level.  
- Plot **average response time (y)** vs **concurrency (x)** and write a short analysis.

## Using the starter plan

`Yelp-Lab2-LoadTest.jmx` now includes:

- `POST /auth/signup` (unique user per thread)
- `POST /auth/login` (captures JWT)
- `GET /restaurants/`
- `POST /reviews/` (Kafka async create)

### Pre-run checklist

1. Ensure gateway is reachable on your host (`http://localhost:8000` for Docker compose).
2. Ensure a valid restaurant exists; note its numeric id (default in plan is `2`).
3. Keep backend stack running during all concurrency levels.

### Option A: GUI run

Open the plan in Apache JMeter and run with thread counts 100, 200, 300, 400, 500.

### Option B: Headless Docker run (recommended)

From `lab2/jmeter`:

```bash
./run_phase5.sh
```

Useful overrides:

```bash
BASE_URL=host.docker.internal BASE_PORT=8000 RESTAURANT_ID=2 ./run_phase5.sh
LEVELS="100 300 500" ./run_phase5.sh
```

Outputs are written to:

- `results/raw_<users>.jtl` (raw samples)
- `results/html_<users>/index.html` (JMeter HTML report)
- `results/phase5_summary.csv` (report-ready metrics)

## Submit

- `.jmx` file  
- Results summary CSV or screenshots from JMeter aggregate/summary report
- Graph + analysis paragraph (in report PDF)
