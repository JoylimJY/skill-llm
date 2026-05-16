import os
import random
import textwrap

random.seed(42)

workspace = "/workspace"

# ── distractor directory structure ──────────────────────────────────────────
dirs = [
    "logistics/src/utils",
    "logistics/src/models",
    "logistics/src/api",
    "logistics/tests/unit",
    "logistics/tests/integration",
    "logistics/config",
    "logistics/docs/internal",
    "logistics/docs/external",
    "logistics/scripts",
    "logistics/data/fixtures",
    "logistics/.github/workflows",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "logistics/src/models/order.py": textwrap.dedent("""\
        class Order:
            def __init__(self, order_id, items, destination):
                self.order_id = order_id
                self.items = items
                self.destination = destination
    """),
    "logistics/src/models/carrier.py": textwrap.dedent("""\
        CARRIERS = ['FedEx', 'UPS', 'DHL', 'USPS']
    """),
    "logistics/src/api/routes.py": textwrap.dedent("""\
        # Placeholder API routes for shipping service
        def get_shipping_quote(order_id):
            pass
    """),
    "logistics/src/utils/validators.py": textwrap.dedent("""\
        def validate_zipcode(zc):
            return len(str(zc)) == 5
    """),
    "logistics/config/settings.py": textwrap.dedent("""\
        DEBUG = False
        DATABASE_URL = 'sqlite:///logistics.db'
        BASE_RATE = 5.99
    """),
    "logistics/docs/internal/architecture.md": textwrap.dedent("""\
        # Architecture Notes
        Service handles shipping cost calculation for B2B clients.
        Legacy module: src/utils/shipping.py
    """),
    "logistics/docs/external/api_guide.md": textwrap.dedent("""\
        # Shipping API Guide
        POST /api/v1/quote  { order_id, weight_kg, zone }
        Returns: { cost_usd }
    """),
    "logistics/scripts/migrate_db.py": textwrap.dedent("""\
        # DB migration script - do not modify
        print('migrating...')
    """),
    "logistics/data/fixtures/sample_orders.json": textwrap.dedent("""\
        [
          {"order_id": "ORD001", "weight_kg": 2.5, "zone": "domestic"},
          {"order_id": "ORD002", "weight_kg": 10.0, "zone": "international"}
        ]
    """),
    "logistics/.github/workflows/ci.yml": textwrap.dedent("""\
        name: CI
        on: [push]
        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v3
              - run: pytest logistics/tests/
    """),
    "logistics/src/utils/__init__.py": "",
    "logistics/src/models/__init__.py": "",
    "logistics/src/api/__init__.py": "",
    "logistics/tests/__init__.py": "",
    "logistics/tests/unit/__init__.py": "",
    "logistics/tests/integration/__init__.py": "",
}

for path, content in distractors.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# ── THE BUGGY MODULE (core target) ───────────────────────────────────────────
# Bug: the weight multiplier uses integer division (//) instead of float division
# causing undercharging on fractional weights, and the zone surcharge lookup
# uses the wrong key ('intl' instead of 'international').
buggy_shipping = textwrap.dedent("""\
    \"\"\"
    shipping.py — core cost calculation for the logistics platform.
    
    Rate table:
      base_rate   = 5.99  USD flat fee
      weight_rate = 1.25  USD per kg
      zone surcharges:
        domestic      = 0.00
        regional      = 2.50
        international = 15.00
    \"\"\"

    ZONE_SURCHARGES = {
        'domestic': 0.00,
        'regional': 2.50,
        'intl': 15.00,          # BUG: key should be 'international'
    }

    BASE_RATE = 5.99
    WEIGHT_RATE = 1.25


    def calculate_shipping_cost(weight_kg: float, zone: str) -> float:
        \"\"\"Return total shipping cost in USD.\"\"\"
        weight_cost = weight_kg // WEIGHT_RATE   # BUG: // should be /  (integer division)
        surcharge = ZONE_SURCHARGES.get(zone, 0.00)
        return round(BASE_RATE + weight_cost + surcharge, 2)
""")

with open(os.path.join(workspace, "logistics/src/utils/shipping.py"), "w") as f:
    f.write(buggy_shipping)

# ── EXISTING FAILING TESTS (used to demonstrate "prove failure first") ────────
failing_tests = textwrap.dedent("""\
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
    from logistics.src.utils.shipping import calculate_shipping_cost


    def test_domestic_fractional_weight():
        # 2.5 kg domestic: expected = 5.99 + (2.5/1.25) + 0.00 = 5.99 + 2.0 = 7.99
        result = calculate_shipping_cost(2.5, 'domestic')
        assert result == 7.99, f\"Expected 7.99, got {result}\"


    def test_international_standard():
        # 10.0 kg international: expected = 5.99 + (10.0/1.25) + 15.00 = 5.99 + 8.0 + 15.00 = 28.99
        result = calculate_shipping_cost(10.0, 'international')
        assert result == 28.99, f\"Expected 28.99, got {result}\"


    def test_regional_heavy():
        # 7.5 kg regional: expected = 5.99 + (7.5/1.25) + 2.50 = 5.99 + 6.0 + 2.50 = 14.49
        result = calculate_shipping_cost(7.5, 'regional')
        assert result == 14.49, f\"Expected 14.49, got {result}\"


    def test_domestic_whole_weight():
        # 5.0 kg domestic: expected = 5.99 + (5.0/1.25) + 0.00 = 5.99 + 4.0 = 9.99
        result = calculate_shipping_cost(5.0, 'domestic')
        assert result == 9.99, f\"Expected 9.99, got {result}\"
""")

with open(os.path.join(workspace, "logistics/tests/unit/test_shipping.py"), "w") as f:
    f.write(failing_tests)

# ── Create the agentic-coding memory dir skeleton (empty — agent must populate)
agentic_dir = os.path.expanduser("~/agentic-coding")
os.makedirs(agentic_dir, exist_ok=True)
# Leave all files absent — agent must create them per the SKILL.md spec

print("Workspace generated successfully.")
print(f"Bug planted in: {workspace}/logistics/src/utils/shipping.py")
print(f"Failing tests at: {workspace}/logistics/tests/unit/test_shipping.py")
print(f"Agentic-coding dir (empty): {agentic_dir}")