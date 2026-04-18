# JMeter (Lab 2)

## Requirements

- Run tests against **login**, **GET /restaurants/** (or search), and **POST /reviews/** (Kafka flow) at **100, 200, 300, 400, 500** concurrent users.  
- Record **average response time**, **throughput (req/s)**, and **error rate** per level.  
- Plot **average response time (y)** vs **concurrency (x)** and write a short analysis.

## Using the starter plan

`Yelp-Lab2-LoadTest.jmx` is a minimal skeleton. **Open it in Apache JMeter** and:

1. Add **User Defined Variables**: `BASE_URL` = your gateway host, `BASE_PORT` = `8000`.  
2. Complete **HTTP Request** bodies: e.g. `POST /auth/login` with JSON `{"email":"...","password":"..."}`.  
3. Add **Authorization** header from login response (extract `access_token` with JSON Extractor) for protected routes.  
4. **POST /reviews/** — include a valid `restaurant_id` and JWT.  
5. Set **Thread Group** thread count to 100, 200, … 500 for separate runs (or use a stepping thread group plugin).  
6. Add **Summary Report** / **Aggregate Report** listeners; export results CSV for the graph.

## Submit

- `.jmx` file  
- Results summary CSV or screenshots  
- Graph + analysis paragraph (in report PDF)
