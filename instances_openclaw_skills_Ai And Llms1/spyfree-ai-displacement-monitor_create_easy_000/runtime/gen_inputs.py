from pathlib import Path
import json

base = Path('.')
refs = base / 'references'
refs.mkdir(exist_ok=True)

thresholds = {
    "A1": {"name": "job_posting_change", "threshold": -10, "tier": "A"},
    "A2": {"name": "ai_capex_growth", "threshold": 15, "tier": "A"},
    "A3": {"name": "white_collar_layoff_rate", "threshold": 5, "tier": "A"},
    "A4": {"name": "automation_mentions", "threshold": 20, "tier": "A"},
    "B1": {"name": "unemployment_rate", "threshold": 4.5, "tier": "B"},
    "B2": {"name": "reemployment_speed", "threshold": -15, "tier": "B"},
    "B3": {"name": "wage_growth", "threshold": -2, "tier": "B"},
    "C1": {"name": "consumer_spending", "threshold": -3, "tier": "C"},
    "C2": {"name": "credit_delinquency", "threshold": 1.5, "tier": "C"},
    "C3": {"name": "business_bankruptcies", "threshold": 8, "tier": "C"}
}

(refs / 'thresholds.example.json').write_text(json.dumps(thresholds, indent=2), encoding='utf-8')

sample = {
    "as_of": "2025-05-01",
    "markers": ["MARKER_ALPHA", "MARKER_BETA", "MARKER_GAMMA"],
    "note": "Deterministic input seed 42"
}
(base / 'input_data.json').write_text(json.dumps(sample, indent=2), encoding='utf-8')
