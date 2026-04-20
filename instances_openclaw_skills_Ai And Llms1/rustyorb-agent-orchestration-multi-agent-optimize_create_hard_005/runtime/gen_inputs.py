import json
from pathlib import Path

root = Path('.')
root.mkdir(parents=True, exist_ok=True)

inputs = {
    'profile_db.json': {
        'marker': 'DB-PROFILE-MARKER-7Q2',
        'service': 'checkout-api',
        'p95_query_ms': 184,
        'slow_queries': ['SELECT order_id FROM orders WHERE user_id = ?', 'UPDATE inventory SET reserved = reserved + 1 WHERE sku = ?'],
        'index_utilization': 0.41,
        'note': 'Connection pool saturation observed during peak traffic.'
    },
    'profile_app.json': {
        'marker': 'APP-PROFILE-MARKER-4K9',
        'service': 'checkout-api',
        'cpu_percent': 86,
        'memory_mb': 1730,
        'hot_path': 'checkout validation and pricing rules',
        'concurrency_issue': 'Lock contention in coupon validation cache.'
    },
    'profile_frontend.json': {
        'marker': 'FE-PROFILE-MARKER-1X8',
        'service': 'checkout-ui',
        'lcp_ms': 2900,
        'network_requests': 43,
        'render_blocking': ['bundle-main.js', 'checkout.css'],
        'note': 'Client-side hydration is acceptable but not primary bottleneck.'
    },
    'targets.yaml': """marker: TARGETS-MARKER-9Z1
service: checkout-api
performance_goals:
  p95_latency_ms: 120
  cpu_percent: 70
  cost_reduction_percent: 15
  error_rate_percent: 1.0
optimization_scope: comprehensive
budget_constraints:
  max_additional_monthly_usd: 250
quality_metrics:
  rollback_safe: true
  no_user_facing_regression: true
"""
}

for name, data in inputs.items():
    p = root / name
    if name.endswith('.json'):
        p.write_text(json.dumps(data, indent=2), encoding='utf-8')
    else:
        p.write_text(data, encoding='utf-8')

(root / 'README_INPUTS.txt').write_text(
    'Deterministic benchmark inputs generated with fixed marker strings.\n'
    'Markers: DB-PROFILE-MARKER-7Q2, APP-PROFILE-MARKER-4K9, FE-PROFILE-MARKER-1X8, TARGETS-MARKER-9Z1\n',
    encoding='utf-8'
)
