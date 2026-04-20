import json
from pathlib import Path

base = Path('.')
(base / 'references').mkdir(exist_ok=True)

thresholds = {
    "indicators": [
        {"id": "A1", "name": "AI hiring displacement mentions", "threshold": 12, "tier": "A"},
        {"id": "A2", "name": "Professional services job ads", "threshold": -8, "tier": "A"},
        {"id": "A3", "name": "Entry-level white-collar openings", "threshold": -10, "tier": "A"},
        {"id": "A4", "name": "GenAI adoption in workflow", "threshold": 35, "tier": "A"},
        {"id": "B1", "name": "Unemployment claims in affected sectors", "threshold": 9, "tier": "B"},
        {"id": "B2", "name": "Average weeks unemployed", "threshold": 18, "tier": "B"},
        {"id": "B3", "name": "Wage growth for clerical/analyst roles", "threshold": -1.0, "tier": "B"},
        {"id": "C1", "name": "Retail sales growth", "threshold": -0.5, "tier": "C"},
        {"id": "C2", "name": "Consumer delinquency rate", "threshold": 3.5, "tier": "C"},
        {"id": "C3", "name": "SME credit spreads", "threshold": 180, "tier": "C"},
    ]
}
(base / 'references' / 'thresholds.example.json').write_text(json.dumps(thresholds, indent=2), encoding='utf-8')

inputs = {
    "as_of": "2025-04-30",
    "marker": "AI_DISPLACEMENT_MONITOR_MARKER_7F3A",
    "series": [
        {"id": "A1", "value": 14.2, "unit": "index", "timestamp": "2025-04-30", "trend": "up", "frequency": "weekly"},
        {"id": "A2", "value": -9.1, "unit": "pct yoy", "timestamp": "2025-03-31", "trend": "down", "frequency": "monthly"},
        {"id": "A3", "value": -12.4, "unit": "pct yoy", "timestamp": "2025-03-31", "trend": "down", "frequency": "monthly"},
        {"id": "A4", "value": 41.0, "unit": "pct", "timestamp": "2025-04-15", "trend": "up", "frequency": "monthly"},
        {"id": "B1", "value": 8.4, "unit": "pct", "timestamp": "2025-04-26", "trend": "up", "frequency": "weekly"},
        {"id": "B2", "value": 17.3, "unit": "weeks", "timestamp": "2025-03-31", "trend": "flat", "frequency": "monthly"},
        {"id": "B3", "value": -0.6, "unit": "pct yoy", "timestamp": "2025-03-31", "trend": "down", "frequency": "monthly"},
        {"id": "C1", "value": 0.2, "unit": "pct mom", "timestamp": "2025-03-31", "trend": "up", "frequency": "monthly"},
        {"id": "C2", "value": 3.1, "unit": "pct", "timestamp": "2025-03-31", "trend": "up", "frequency": "quarterly"},
        {"id": "C3", "value": 172, "unit": "bps", "timestamp": "2025-04-30", "trend": "down", "frequency": "weekly"}
    ],
    "notes": [
        "Capex announcements in automation and model deployment are accelerating.",
        "Bottleneck tasks in compliance, client-facing judgment, and systems integration remain scarce.",
        "Consumer demand is mixed, with no broad collapse in purchasing power yet."
    ]
}
(base / 'input.json').write_text(json.dumps(inputs, indent=2), encoding='utf-8')
