import os
import random

random.seed(42)

base = "/workspace"

# --- Directory structure ---
dirs = [
    "src/inventory",
    "src/inventory/handlers",
    "src/inventory/models",
    "src/inventory/utils",
    "src/api",
    "src/api/routes",
    "tests/unit",
    "tests/integration",
    "docs",
    "config",
    "scripts",
    "migrations",
    ".github/workflows",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# --- Distractor files (not the main task but realistic project noise) ---
distractors = {
    "config/database.yml": """\
production:
  host: db.internal
  port: 5432
  name: inventory_prod
  pool_size: 20

development:
  host: localhost
  port: 5432
  name: inventory_dev
  pool_size: 5
""",
    "config/redis.yml": """\
cache:
  host: redis.internal
  port: 6379
  ttl: 3600
""",
    ".github/workflows/ci.yml": """\
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install -r requirements.txt
      - run: pytest tests/
""",
    "migrations/001_create_inventory.sql": """\
CREATE TABLE inventory_items (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(64) NOT NULL,
    quantity INTEGER DEFAULT 0,
    warehouse_id INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
""",
    "migrations/002_add_reserved.sql": """\
ALTER TABLE inventory_items ADD COLUMN reserved_qty INTEGER DEFAULT 0;
""",
    "scripts/seed_data.py": """\
import random
import psycopg2

conn = psycopg2.connect("dbname=inventory_dev")
cur = conn.cursor()
for i in range(100):
    cur.execute("INSERT INTO inventory_items (sku, quantity) VALUES (%s, %s)",
                (f"SKU-{i:04d}", random.randint(0, 500)))
conn.commit()
""",
    "src/inventory/utils/logger.py": """\
import logging

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger
""",
    "src/api/routes/__init__.py": "from .inventory import router\n",
    "tests/integration/test_api.py": """\
import pytest
# TODO: write integration tests
def test_placeholder():
    assert True
""",
    "docs/deployment.md": """\
# Deployment Guide

## Prerequisites
- Docker 20+
- Kubernetes 1.25+

## Steps
1. Build image: `docker build -t inventory-service .`
2. Push to registry
3. Apply k8s manifests
""",
}
for path, content in distractors.items():
    with open(os.path.join(base, path), "w") as f:
        f.write(content)

# --- MAIN TASK INPUT 1: Architecture notes (messy, for eng review) ---
arch_notes = """\
# Inventory Service — Architecture Notes (DRAFT)

## Overview
The inventory service handles stock tracking for our e-commerce platform.
It receives events from the orders service and updates item quantities.

## Components
- **InventoryHandler**: Receives order events (ORDER_PLACED, ORDER_CANCELLED, ORDER_SHIPPED)
- **StockRepository**: Reads/writes to PostgreSQL
- **CacheLayer**: Redis-backed, 60s TTL
- **EventPublisher**: Publishes stock_low events to Kafka

## Data Flow
1. Order event arrives via Kafka consumer
2. InventoryHandler validates and calls StockRepository.reserve()
3. StockRepository updates DB and invalidates cache
4. If quantity falls below threshold, EventPublisher emits stock_low

## Known Issues
- No retry logic on Kafka consumer failures
- CacheLayer and DB can get out of sync if a crash happens mid-transaction

## Testing
- Unit tests exist for StockRepository
- No integration tests for the full event flow
- No E2E tests
"""

with open(os.path.join(base, "docs/ARCHITECTURE_NOTES.md"), "w") as f:
    f.write(arch_notes)

# --- MAIN TASK INPUT 2: Code to review (has real bugs) ---
inventory_handler = """\
import logging
from .models.stock import StockItem
from .utils.logger import get_logger

logger = get_logger(__name__)

class InventoryHandler:
    def __init__(self, repo, cache, publisher):
        self.repo = repo
        self.cache = cache
        self.publisher = publisher

    def handle_order_placed(self, event):
        sku = event['sku']
        qty = event['quantity']
        # P0: No validation — qty could be negative or zero
        item = self.repo.get_by_sku(sku)
        if item is None:
            return False
        item.reserved += qty
        item.available -= qty
        self.repo.save(item)
        self.cache.delete(f"stock:{sku}")
        # P1: No check if available goes negative (overselling bug)
        if item.available < item.low_stock_threshold:
            self.publisher.emit('stock_low', {'sku': sku, 'available': item.available})
        return True

    def handle_order_cancelled(self, event):
        sku = event.get('sku')
        qty = event.get('qty')  # P2: inconsistent key name — should be 'quantity'
        item = self.repo.get_by_sku(sku)
        item.reserved -= qty
        item.available += qty
        self.repo.save(item)
        # P0: Cache never invalidated after cancellation — stale data served
        return True

    def handle_order_shipped(self, event):
        sku = event['sku']
        qty = event['quantity']
        item = self.repo.get_by_sku(sku)
        item.reserved -= qty  # decrement reserved
        self.repo.save(item)
        self.cache.delete(f"stock:{sku}")
        return True

    def bulk_adjust(self, adjustments):
        # P1: No transaction — partial failures leave DB in inconsistent state
        for adj in adjustments:
            item = self.repo.get_by_sku(adj['sku'])
            item.available += adj['delta']
            self.repo.save(item)
        return len(adjustments)
"""

with open(os.path.join(base, "src/inventory/handlers/inventory_handler.py"), "w") as f:
    f.write(inventory_handler)

stock_model = """\
class StockItem:
    def __init__(self, sku, available, reserved=0, low_stock_threshold=10):
        self.sku = sku
        self.available = available
        self.reserved = reserved
        self.low_stock_threshold = low_stock_threshold
"""
with open(os.path.join(base, "src/inventory/models/stock.py"), "w") as f:
    f.write(stock_model)

stock_repo = """\
class StockRepository:
    def __init__(self, db_conn):
        self.db = db_conn

    def get_by_sku(self, sku):
        row = self.db.execute("SELECT * FROM inventory_items WHERE sku = %s", (sku,)).fetchone()
        if row is None:
            return None
        from .models.stock import StockItem
        return StockItem(row['sku'], row['quantity'] - row['reserved_qty'], row['reserved_qty'])

    def save(self, item):
        self.db.execute(
            "UPDATE inventory_items SET quantity = %s, reserved_qty = %s WHERE sku = %s",
            (item.available + item.reserved, item.reserved, item.sku)
        )
        # P1: Missing db.commit() — changes never persisted
"""
with open(os.path.join(base, "src/inventory/models/stock_repository.py"), "w") as f:
    f.write(stock_repo)

# --- MAIN TASK INPUT 3: Sprint summary for retro ---
sprint_summary = """\
# Sprint 14 Summary — Inventory Service

## Completed Work
- Implemented InventoryHandler with ORDER_PLACED, ORDER_CANCELLED, ORDER_SHIPPED support
- Added StockRepository with PostgreSQL backend
- Added Redis caching layer (CacheLayer)
- Wrote 12 unit tests for StockRepository
- Fixed 3 bugs from previous sprint (race condition in reserve(), null-check in get_by_sku(), off-by-one in threshold check)

## Bugs Found During Sprint
- Cache invalidation missing after ORDER_CANCELLED (now fixed)
- Overselling could occur under concurrent load (P1, deferred)

## Test Coverage
- Unit test coverage: 61% (down from 68% last sprint due to new uncovered handlers)
- Integration tests: 0 (not yet built)
- E2E tests: 0

## Team Notes
- Kafka consumer retry logic still not implemented (carried over from Sprint 13)
- bulk_adjust() has no transaction wrapping — risky for production
- New engineer onboarded this sprint, velocity temporarily reduced
"""
with open(os.path.join(base, "docs/sprint14_summary.md"), "w") as f:
    f.write(sprint_summary)

# --- requirements.txt (distractor) ---
with open(os.path.join(base, "requirements.txt"), "w") as f:
    f.write("psycopg2-binary\nkafka-python\nredis\nfastapi\nuvicorn\npytest\n")

# --- Empty __init__ files ---
for init_path in [
    "src/__init__.py",
    "src/inventory/__init__.py",
    "src/inventory/handlers/__init__.py",
    "src/inventory/models/__init__.py",
    "tests/__init__.py",
    "tests/unit/__init__.py",
]:
    with open(os.path.join(base, init_path), "w") as f:
        f.write("")

print("Workspace initialized successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(base):
    for fname in files:
        print(f"  {os.path.join(root, fname)}")