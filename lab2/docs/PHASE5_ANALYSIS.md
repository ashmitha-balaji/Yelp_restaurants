# Phase 5 Performance Analysis

## Measured Results

| Concurrency | Total Samples | Avg Response Time (ms) | Throughput (req/s) | Error Rate (%) |
|---|---:|---:|---:|---:|
| 100 | 500 | 1741.98 | 4.26 | 0.00 |
| 300 | 1500 | 1141.16 | 6.92 | 0.00 |
| 500 | 2500 | 810.98 | 10.01 | 0.00 |

Source: `lab2/jmeter/results/phase5_summary.csv`

## Analysis Paragraph (report-ready)

Load testing at 100, 300, and 500 concurrent users completed with 0% error rate after fixing the `GET /restaurants/` serialization issue in the restaurant service. Throughput increased from 4.26 req/s at 100 users to 10.01 req/s at 500 users, indicating that the system scaled under higher concurrency during this test window. Average response time also trended down from 1741.98 ms to 810.98 ms, which suggests improved pipeline utilization at larger loads in this run profile. Overall, the Lab 2 stack remained stable across all tested levels, and asynchronous review processing continued to return accepted jobs without failures.
