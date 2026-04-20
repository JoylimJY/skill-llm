import json
from pathlib import Path

root = Path('.')
root.mkdir(parents=True, exist_ok=True)

thresholds = {
    "indicators": [
        {"id": "A1", "threshold": 0.62, "tier": "A", "name": "AI hiring share"},
        {"id": "A2", "threshold": 0.58, "tier": "A", "name": "AI exposure layoffs"},
        {"id": "A3", "threshold": 0.55, "tier": "A", "name": "job-posting contraction"},
        {"id": "A4", "threshold": 0.50, "tier": "A", "name": "automation capex surge"},
        {"id": "B1", "threshold": 0.57, "tier": "B", "name": "unemployment uptick"},
        {"id": "B2", "threshold": 0.54, "tier": "B", "name": "wage growth slowdown"},
        {"id": "B3", "threshold": 0.56, "tier": "B", "name": "hours worked decline"},
        {"id": "C1", "threshold": 0.59, "tier": "C", "name": "consumption softness"},
        {"id": "C2", "threshold": 0.60, "tier": "C", "name": "consumer credit stress"},
        {"id": "C3", "threshold": 0.61, "tier": "C", "name": "delinquency increase"},
    ]
}

(root / 'references').mkdir(exist_ok=True)
(root / 'references' / 'thresholds.example.json').write_text(json.dumps(thresholds, indent=2), encoding='utf-8')

payload = {
    "asOf": "2025-05-15",
    "marker": "AI_DISPLACEMENT_BENCHMARK_MARKER_7F3C",
    "series": [
        {"id": "A1", "value": 0.64, "unit": "share", "trend": "up", "timestamp": "2025-05-10", "freq": "weekly"},
        {"id": "A2", "value": 0.61, "unit": "index", "trend": "up", "timestamp": "2025-05-01", "freq": "monthly"},
        {"id": "A3", "value": 0.47, "unit": "index", "trend": "down", "timestamp": "2025-05-09", "freq": "weekly"},
        {"id": "A4", "value": 0.53, "unit": "index", "trend": "up", "timestamp": "2025-04-30", "freq": "quarterly"},
        {"id": "B1", "value": 0.56, "unit": "index", "trend": "flat", "timestamp": "2025-05-01", "freq": "monthly"},
        {"id": "B2", "value": 0.51, "unit": "index", "trend": "down", "timestamp": "2025-04-28", "freq": "monthly"},
        {"id": "B3", "value": 0.58, "unit": "index", "trend": "down", "timestamp": "2025-05-08", "freq": "weekly"},
        {"id": "C1", "value": 0.57, "unit": "index", "trend": "down", "timestamp": "2025-05-03", "freq": "monthly"},
        {"id": "C2", "value": 0.62, "unit": "index", "trend": "up", "timestamp": "2025-05-01", "freq": "monthly"},
        {"id": "C3", "value": None, "unit": "index", "trend": "unknown", "timestamp": None, "freq": "monthly"},
    ],
    "notes": [
        "Benchmark note: substitution is accelerating, but capex reinvestment is mixed rather than collapsing.",
        "Benchmark note: consumer demand is soft, yet not all bottlenecks are easing.",
        "Benchmark note: include missingness explicitly and downgrade confidence if more than three inputs are absent or stale.",
        "Benchmark note: AI_DISPLACEMENT_BENCHMARK_MARKER_7F3C should appear in downstream output handling."
    ]
}
(root / 'input.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')

(root / 'README.txt').write_text(
    'Deterministic benchmark input generated.\nMarker: AI_DISPLACEMENT_BENCHMARK_MARKER_7F3C\n',
    encoding='utf-8'
)
