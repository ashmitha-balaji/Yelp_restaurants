#!/usr/bin/env bash
set -euo pipefail

# Phase 5 load-test runner (Dockerized JMeter)
# Usage:
#   ./run_phase5.sh
#   BASE_URL=host.docker.internal BASE_PORT=8000 RESTAURANT_ID=2 ./run_phase5.sh
#   LEVELS="100 300 500" ./run_phase5.sh

JMETER_IMAGE="${JMETER_IMAGE:-justb4/jmeter:5.5}"
BASE_URL="${BASE_URL:-host.docker.internal}"
BASE_PORT="${BASE_PORT:-8000}"
RESTAURANT_ID="${RESTAURANT_ID:-2}"
LEVELS="${LEVELS:-100 200 300 400 500}"
RAMP_DIVISOR="${RAMP_DIVISOR:-2}"
LOOPS="${LOOPS:-1}"
PLAN_FILE="${PLAN_FILE:-Yelp-Lab2-LoadTest.jmx}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/results"
mkdir -p "${RESULTS_DIR}"

SUMMARY_CSV="${RESULTS_DIR}/phase5_summary.csv"
echo "concurrency,total_samples,avg_response_ms,throughput_req_per_sec,error_rate_percent" > "${SUMMARY_CSV}"

run_level() {
  local users="$1"
  local ramp_up=$(( users / RAMP_DIVISOR ))
  if [[ "${ramp_up}" -lt 1 ]]; then
    ramp_up=1
  fi

  local jtl_file="${RESULTS_DIR}/raw_${users}.jtl"
  local html_dir="${RESULTS_DIR}/html_${users}"
  rm -f "${jtl_file}"
  rm -rf "${html_dir}"

  echo "=== Running load level: ${users} users (ramp=${ramp_up}s) ==="
  docker run --rm \
    -v "${SCRIPT_DIR}:/tests" \
    -w /tests \
    "${JMETER_IMAGE}" \
    -n \
    -t "${PLAN_FILE}" \
    -l "results/raw_${users}.jtl" \
    -e \
    -o "results/html_${users}" \
    -JTHREADS="${users}" \
    -JRAMP_UP="${ramp_up}" \
    -JLOOPS="${LOOPS}" \
    -JBASE_URL="${BASE_URL}" \
    -JBASE_PORT="${BASE_PORT}" \
    -JRESTAURANT_ID="${RESTAURANT_ID}" \
    -Jjmeter.save.saveservice.output_format=csv \
    -Jjmeter.save.saveservice.assertion_results=none \
    -Jjmeter.save.saveservice.response_data=false \
    -Jjmeter.save.saveservice.samplerData=false

  python3 - "${jtl_file}" "${users}" <<'PY' >> "${SUMMARY_CSV}"
import csv
import math
import sys

jtl_path = sys.argv[1]
users = int(sys.argv[2])

rows = []
with open(jtl_path, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

if not rows:
    print(f"{users},0,0,0,100")
    raise SystemExit(0)

def to_int(v, default=0):
    try:
        return int(float(v))
    except Exception:
        return default

elapsed_values = [to_int(r.get("elapsed", 0)) for r in rows]
success_values = [1 if str(r.get("success", "")).lower() == "true" else 0 for r in rows]
timestamps = [to_int(r.get("timeStamp", 0)) for r in rows]

total = len(rows)
avg_ms = sum(elapsed_values) / total if total else 0
errors = total - sum(success_values)
error_rate = (errors * 100.0 / total) if total else 0.0

start_ts = min(timestamps) if timestamps else 0
end_ts = max(timestamps) if timestamps else 0
duration_s = max((end_ts - start_ts) / 1000.0, 1e-6)
throughput = total / duration_s

print(f"{users},{total},{avg_ms:.2f},{throughput:.2f},{error_rate:.2f}")
PY
}

for level in ${LEVELS}; do
  run_level "${level}"
done

echo
echo "Done. Summary: ${SUMMARY_CSV}"
echo "HTML reports: ${RESULTS_DIR}/html_<concurrency>/index.html"
