import os
import random

random.seed(42)

base = "/workspace"

# ─── Directory structure ────────────────────────────────────────────────────
dirs = [
    "db/migrations",
    "db/seeds",
    "db/drafts",
    "backend/api",
    "backend/models",
    "backend/services",
    "frontend/components",
    "frontend/pages",
    "infra/terraform",
    "infra/docker",
    "docs/architecture",
    "tests/integration",
    "tests/unit",
    "scripts/etl",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# ─── Distractor files ────────────────────────────────────────────────────────
distractors = {
    "backend/api/orders.py": """
from flask import Blueprint, jsonify, request
orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/orders', methods=['GET'])
def get_orders():
    # TODO: optimize this
    return jsonify([])
""",
    "backend/models/customer.py": """
class Customer:
    def __init__(self, id, email, name):
        self.id = id
        self.email = email
        self.name = name
""",
    "backend/services/analytics.py": """
# Analytics service — placeholder
def compute_revenue():
    pass
""",
    "frontend/components/OrderTable.jsx": """
export default function OrderTable({ orders }) {
  return <table>{orders.map(o => <tr key={o.id}><td>{o.id}</td></tr>)}</table>;
}
""",
    "frontend/pages/dashboard.jsx": "// Dashboard page\n",
    "infra/terraform/main.tf": """
provider "aws" {
  region = "ap-northeast-2"
}
resource "aws_db_instance" "ecommerce" {
  engine         = "postgres"
  instance_class = "db.t3.medium"
}
""",
    "infra/docker/docker-compose.yml": """
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: secret
""",
    "docs/architecture/overview.md": """
# Architecture Overview
Microservices-based e-commerce platform.
Uses PostgreSQL as primary data store.
""",
    "tests/integration/test_orders.py": """
def test_order_creation():
    assert True  # placeholder
""",
    "tests/unit/test_utils.py": """
def test_format_price():
    assert round(9.999, 2) == 10.0
""",
    "scripts/etl/load_products.py": """
# ETL script to load product catalog from CSV
import csv
def load(filepath):
    with open(filepath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            print(row)
""",
    "db/seeds/seed_customers.sql": """
INSERT INTO customers (id, email, name) VALUES
  ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'alice@example.com', 'Alice'),
  ('b2c3d4e5-f6a7-8901-bcde-f12345678901', 'bob@example.com', 'Bob');
""",
}

for path, content in distractors.items():
    full = os.path.join(base, path)
    with open(full, "w") as f:
        f.write(content.strip() + "\n")

# ─── THE PROBLEM: messy draft SQL files ─────────────────────────────────────

# Draft 1: initial schema — has SELECT *, missing indexes, bad JSONB use,
#           over-indexed composite, no partial index, no RLS
draft_schema = """\
-- Draft schema v0.3 (DO NOT USE AS-IS — needs perf review)
-- Author: departed engineer Kim

CREATE TABLE customers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE products (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    sku VARCHAR(100) NOT NULL,
    name VARCHAR(255),
    price NUMERIC(10,2),
    category VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- WARNING: metadata column used in WHERE and ORDER BY in analytics queries!
-- e.g.: WHERE metadata->>'region' = 'APAC' ORDER BY metadata->>'priority'
CREATE TABLE orders (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    customer_id UUID REFERENCES customers(id),
    status VARCHAR(50) DEFAULT 'pending',
    total_amount NUMERIC(12,2),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE order_items (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    order_id UUID REFERENCES orders(id),
    product_id UUID REFERENCES products(id),
    quantity INTEGER,
    unit_price NUMERIC(10,2)
);

-- Some indexes Kim added (might be wrong)
CREATE INDEX idx_everything_orders ON orders(customer_id, status, total_amount, created_at, metadata);
CREATE INDEX idx_sku ON products(sku);
"""

# Draft 2: query file — uses SELECT *, missing index hints
draft_queries = """\
-- Slow queries reported by analytics team (2024-Q1)

-- Query 1: Customer order lookup (VERY SLOW on large dataset)
SELECT * FROM orders WHERE customer_id = '{{customer_uuid}}';

-- Query 2: Active order dashboard — runs every 30 seconds
SELECT * FROM orders WHERE status = 'active' ORDER BY created_at DESC;

-- Query 3: Revenue report — product joins
SELECT * FROM order_items JOIN orders ON order_items.order_id = orders.id
WHERE orders.status = 'completed';

-- Query 4: Email-based customer lookup (used by support team ~500x/day)
SELECT * FROM customers WHERE email = '{{email}}';

-- Query 5: APAC region orders (analytics — metadata used in filter)
SELECT * FROM orders WHERE metadata->>'region' = 'APAC';
"""

# Draft 3: partial RLS attempt — incomplete and missing index pairing
draft_rls = """\
-- RLS attempt — INCOMPLETE, do not apply
-- We want to restrict order visibility so users only see their own orders.

ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Broken policy (auth.uid referenced but no index — will cause full scan)
CREATE POLICY order_visibility ON orders
  FOR SELECT USING (customer_id = auth.uid());

-- TODO: figure out if we need indexes here
"""

with open(os.path.join(base, "db/drafts/schema_draft.sql"), "w") as f:
    f.write(draft_schema)

with open(os.path.join(base, "db/drafts/slow_queries.sql"), "w") as f:
    f.write(draft_queries)

with open(os.path.join(base, "db/drafts/rls_draft.sql"), "w") as f:
    f.write(draft_rls)

# ─── Performance complaints notes ───────────────────────────────────────────
notes = """\
# Performance Issues — Reported by Analytics & Support Teams

## Symptoms
- Dashboard query (active orders) times out after 30s on prod
- Support team email lookups take 4-6 seconds each
- APAC region filter query causing full table scans (per ops team)
- Customer order lookup noted as "extremely slow" in last sprint retro

## Engineer Notes (Kim, departing)
- The orders table will grow to 50M+ rows
- status = 'active' only applies to ~2% of all orders at any time
- metadata->>'region' and metadata->>'priority' are queried heavily but I ran out of time
- The composite index I created might be doing more harm than good
- RLS for customer order isolation is required for compliance — needs to be perf-safe
- email column on customers is never indexed — oversight

## Reminder
- DO NOT use SELECT * in any production query
- Fix the schema before the next release (deadline: end of sprint)
"""

with open(os.path.join(base, "db/drafts/performance_notes.txt"), "w") as f:
    f.write(notes)

print("Workspace generated successfully.")