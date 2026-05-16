import os
import sqlite3
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Directory structure with distractors ──────────────────────────────────────
dirs = [
    "data/raw",
    "data/processed",
    "data/archive",
    "configs",
    "logs",
    "scripts/etl",
    "scripts/reports",
    "docs/schema",
    "docs/business",
    "tmp",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────
distractors = {
    "configs/db_config.yaml": textwrap.dedent("""\
        host: localhost
        port: 5432
        database: ecommerce_prod
        pool_size: 10
        # NOTE: This config is for the legacy PostgreSQL instance.
        # The active SQLite DB is under data/ecommerce.db
    """),
    "configs/report_template_old.md": textwrap.dedent("""\
        # Report Template v1 (DEPRECATED)
        ## Summary
        ## Details
        ## Raw Data
    """),
    "docs/schema/erd_notes.txt": textwrap.dedent("""\
        Entity Relationship Notes (draft)
        - orders -> products via order_items.product_id
        - orders -> stores via orders.store_id
        - products has category_id FK to categories (not yet implemented)
        WARNING: province column was renamed from 'region' in migration 003.
    """),
    "docs/business/kpi_definitions.txt": textwrap.dedent("""\
        KPI Definitions:
        - GMV: Gross Merchandise Value = sum(order_amount)
        - AOV: Average Order Value = GMV / count(orders)
        - Active User: a user who placed at least one order in the period
        NOTE: 'active' in user_tags table means account_status='active', NOT the KPI definition above.
    """),
    "scripts/etl/migrate_001.sql": textwrap.dedent("""\
        -- Migration 001: initial schema
        CREATE TABLE IF NOT EXISTS legacy_orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            amount REAL,
            created_at TEXT
        );
    """),
    "scripts/etl/migrate_003.sql": textwrap.dedent("""\
        -- Migration 003: rename region to province
        ALTER TABLE stores RENAME COLUMN region TO province;
    """),
    "scripts/reports/weekly_sales.py": textwrap.dedent("""\
        # Stub: weekly sales report generator (uses legacy DB connection)
        # DO NOT USE - replaced by NL2SQL agent workflow
        import sqlite3
        def get_weekly_sales():
            pass
    """),
    "logs/etl_run_20240601.log": "\n".join([
        f"2024-06-0{i%9+1} 0{i%10}:00:00 INFO ETL job completed, rows={random.randint(100,9999)}"
        for i in range(20)
    ]),
    "data/archive/orders_backup_2023.csv": "order_id,user_id,amount,dt\n" + "\n".join([
        f"{i},{random.randint(1,500)},{random.uniform(10,500):.2f},2023-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        for i in range(1, 11)
    ]),
    "tmp/scratch_analysis.txt": textwrap.dedent("""\
        Scratch notes from last analysis session:
        - Top provinces by GMV in Q1: Guangdong, Zhejiang, Beijing
        - Need to check NULL handling in order_items.discount
        - Ask data team about stores without province set
    """),
    "docs/business/product_categories.json": json.dumps({
        "categories": [
            {"id": 1, "name": "Electronics"},
            {"id": 2, "name": "Clothing"},
            {"id": 3, "name": "Home & Kitchen"},
            {"id": 4, "name": "Sports"},
        ]
    }, indent=2, ensure_ascii=False),
}

for rel_path, content in distractors.items():
    p = workspace / rel_path
    p.write_text(content, encoding="utf-8")

# ── Main SQLite database ──────────────────────────────────────────────────────
db_path = workspace / "data" / "ecommerce.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# ── stores table ──────────────────────────────────────────────────────────────
cur.execute("DROP TABLE IF EXISTS stores")
cur.execute("""
CREATE TABLE stores (
    store_id   INTEGER PRIMARY KEY,
    store_name TEXT NOT NULL,
    province   TEXT,           -- can be NULL for online-only stores
    city       TEXT,
    store_type TEXT CHECK(store_type IN ('physical','online','franchise'))
)
""")

provinces = ["广东", "浙江", "北京", "上海", "四川", "湖北", "江苏", "福建", None]
store_types = ["physical", "online", "franchise"]
stores_data = []
random.seed(42)
for sid in range(1, 21):
    prov = random.choice(provinces)
    city = f"City_{sid}" if prov else None
    stype = random.choice(store_types)
    stores_data.append((sid, f"Store_{sid:03d}", prov, city, stype))
cur.executemany("INSERT INTO stores VALUES (?,?,?,?,?)", stores_data)

# ── products table ────────────────────────────────────────────────────────────
cur.execute("DROP TABLE IF EXISTS products")
cur.execute("""
CREATE TABLE products (
    product_id   INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category_id  INTEGER,
    unit_price   REAL NOT NULL,
    sku          TEXT UNIQUE
)
""")
products_data = []
for pid in range(1, 31):
    cat = random.randint(1, 4)
    price = round(random.uniform(9.9, 999.9), 2)
    products_data.append((pid, f"Product_{pid:03d}", cat, price, f"SKU-{pid:05d}"))
cur.executemany("INSERT INTO products VALUES (?,?,?,?,?)", products_data)

# ── orders table (date stored as YYYYMMDD integer — intentional format quirk) ─
cur.execute("DROP TABLE IF EXISTS orders")
cur.execute("""
CREATE TABLE orders (
    order_id     INTEGER PRIMARY KEY,
    user_id      INTEGER NOT NULL,
    store_id     INTEGER,
    order_date   INTEGER NOT NULL,   -- format: YYYYMMDD e.g. 20240515
    order_amount REAL NOT NULL,
    status       TEXT CHECK(status IN ('completed','cancelled','pending'))
)
""")

orders_data = []
# Recent 30 days: 20240601 - 20240630
base_dates = [20240601 + i for i in range(30)]
for oid in range(1, 301):
    uid = random.randint(1, 200)
    sid = random.randint(1, 20)
    odate = random.choice(base_dates)
    amount = round(random.uniform(15.0, 2000.0), 2)
    status = random.choices(["completed", "cancelled", "pending"], weights=[0.75, 0.15, 0.10])[0]
    orders_data.append((oid, uid, sid, odate, amount, status))
cur.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?)", orders_data)

# ── order_items table ─────────────────────────────────────────────────────────
cur.execute("DROP TABLE IF EXISTS order_items")
cur.execute("""
CREATE TABLE order_items (
    item_id    INTEGER PRIMARY KEY,
    order_id   INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity   INTEGER NOT NULL DEFAULT 1,
    unit_price REAL NOT NULL,
    discount   REAL             -- can be NULL (no discount applied)
)
""")
items_data = []
item_id = 1
for oid, uid, sid, odate, amount, status in orders_data:
    n_items = random.randint(1, 5)
    for _ in range(n_items):
        pid = random.randint(1, 30)
        qty = random.randint(1, 4)
        uprice = round(random.uniform(9.9, 499.9), 2)
        discount = round(random.uniform(0, 0.3), 2) if random.random() < 0.4 else None
        items_data.append((item_id, oid, pid, qty, uprice, discount))
        item_id += 1
cur.executemany("INSERT INTO order_items VALUES (?,?,?,?,?,?)", items_data)

# ── user_tags table (the 'active' trap from docs) ─────────────────────────────
cur.execute("DROP TABLE IF EXISTS user_tags")
cur.execute("""
CREATE TABLE user_tags (
    user_id        INTEGER PRIMARY KEY,
    account_status TEXT CHECK(account_status IN ('active','inactive','banned')),
    tier           TEXT CHECK(tier IN ('bronze','silver','gold','platinum')),
    signup_date    TEXT   -- format: YYYY-MM-DD (different from orders.order_date!)
)
""")
tiers = ["bronze", "silver", "gold", "platinum"]
statuses = ["active", "inactive", "banned"]
user_tags_data = []
for uid in range(1, 201):
    ast = random.choices(statuses, weights=[0.7, 0.2, 0.1])[0]
    tier = random.choice(tiers)
    y = random.randint(2020, 2023)
    m = random.randint(1, 12)
    d = random.randint(1, 28)
    user_tags_data.append((uid, ast, tier, f"{y}-{m:02d}-{d:02d}"))
cur.executemany("INSERT INTO user_tags VALUES (?,?,?,?)", user_tags_data)

conn.commit()
conn.close()

# ── Schema documentation file (intentionally incomplete / business-language) ──
schema_doc = textwrap.dedent("""\
    # E-Commerce Database Schema Reference

    Database file: data/ecommerce.db

    ## Tables

    ### stores
    Brick-and-mortar and online stores. Note: province may be NULL for online-only stores.
    Columns: store_id, store_name, province, city, store_type

    ### products
    Product catalog.
    Columns: product_id, product_name, category_id, unit_price, sku

    ### orders
    Customer orders. IMPORTANT: order_date is stored as an INTEGER in YYYYMMDD format (e.g., 20240615).
    Columns: order_id, user_id, store_id, order_date, order_amount, status

    ### order_items
    Line items per order. discount column is NULL when no discount was applied.
    Columns: item_id, order_id, product_id, quantity, unit_price, discount

    ### user_tags
    User account metadata. WARNING: account_status='active' means the account is enabled,
    NOT that the user made a purchase (see KPI definitions in docs/business/).
    signup_date is stored as TEXT 'YYYY-MM-DD'.
    Columns: user_id, account_status, tier, signup_date

    ## Database name (for schema linking): ecommerce
""")
(workspace / "docs" / "schema" / "schema_reference.md").write_text(schema_doc, encoding="utf-8")

# ── Task specification ─────────────────────────────────────────────────────────
task_spec = textwrap.dedent("""\
    # Analyst Task Brief

    **Business Question:**
    "Which provinces had the highest total sales (completed orders only) during June 2024,
     and what was the average order value per province? Show the top 5 provinces."

    **Context:**
    - Database: data/ecommerce.db
    - Schema reference: docs/schema/schema_reference.md
    - Relevant business KPI notes: docs/business/kpi_definitions.txt

    **Required Output:**
    Produce a file named `sales_report.md` containing the full analysis report.

    The intermediate schema linking result must also be saved as `schema_linking.json`
    (a JSON array of selected fields in "database.table.column" dotted notation).
""")
(workspace / "task_brief.md").write_text(task_spec, encoding="utf-8")

print("Workspace initialized successfully.")
print(f"Database: {db_path} ({db_path.stat().st_size} bytes)")
print(f"Tables created: stores, products, orders, order_items, user_tags")