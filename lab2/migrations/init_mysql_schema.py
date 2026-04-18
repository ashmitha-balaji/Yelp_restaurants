#!/usr/bin/env python3
"""
Create Lab 1 MySQL tables inside the Compose MySQL service (SQLAlchemy ``create_all``).

Run this **once** if ``mysql_to_mongo.py`` reports missing tables (1146). The Lab 2
services use MongoDB; this script only prepares MySQL so the migration can read rows.

Usage (same container/image as user-service, MySQL hostname ``mysql``):

  docker compose -f lab2/docker-compose.yml up -d mysql mongo
  docker compose -f lab2/docker-compose.yml up -d user-service
  docker exec yelp-lab2-user-service-1 python /app/lab2/migrations/init_mysql_schema.py
"""
from __future__ import annotations

import os
import sys

# DATABASE_URL must be set before any backend import (config reads it at import time).
def _mysql_url() -> str:
    return (
        os.getenv("MYSQL_URL")
        or os.getenv("DATABASE_URL")
        or f"mysql+pymysql://{os.getenv('MYSQL_USER', 'root')}:{os.getenv('MYSQL_PASSWORD', 'rootpass')}"
        f"@{os.getenv('MYSQL_HOST', 'mysql')}:{os.getenv('MYSQL_PORT', '3306')}/{os.getenv('MYSQL_DATABASE', 'yelp_db')}"
    )


def main() -> None:
    url = _mysql_url()
    os.environ["DATABASE_URL"] = url

    root = os.environ.get("APP_ROOT") or os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
    backend = os.path.join(root, "backend")
    lab2 = os.path.join(root, "lab2")
    lab2_py = os.path.join(lab2, "python")
    for p in (backend, lab2, lab2_py):
        if p not in sys.path:
            sys.path.insert(0, p)

    from db_init import safe_create_all

    safe_create_all()
    print("MySQL schema is ready (tables created or already present).")
    print(f"  {url.split('@')[-1]}")


if __name__ == "__main__":
    main()
