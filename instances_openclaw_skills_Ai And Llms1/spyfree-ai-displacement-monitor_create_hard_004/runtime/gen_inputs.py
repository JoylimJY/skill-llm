from pathlib import Path
import json
import random

random.seed(17)

root = Path('.')
(root / 'references').mkdir(exist_ok=True)
(root / 'data').mkdir(exist_ok=True)

thresholds = {
    "A1": {"name": "Hiring momentum", "tier": "A", "threshold": 42, "direction": "lower_worse"},
    "A2": {"name": "Job posting breadth", "tier": "A", "threshold": 55, "direction": "lower_worse"},
    "A3": {"name": "AI task exposure", "tier": "A", "threshold": 68, "direction": "higher_worse"},
    "A4": {"name": "Employer AI adoption", "tier": "A", "threshold": 61, "direction": "higher_worse"},
    "B1": {"name": "Unemployment claims", "tier": "B", "threshold": 260000, "direction": "higher_worse"},
    "B2": {"name": "Layoff announcements", "tier": "B", "threshold": 52000, "direction": "higher_worse"},
    "B3": {"name": "Wage growth", "tier": "B", "threshold": 3.1, "direction": "lower_worse"},
    "C1": {"name": "Consumer delinquencies", "tier": "C", "threshold": 2.9, "direction": "higher_worse"},
    "C2": {"name": "SME credit spreads", "tier": "C", "threshold": 2.2, "direction": "higher_worse"},
    "C3": {"name": "Capex reinvestment", "tier": "C", "threshold": 4.6, "direction": "lower_worse"}
}
(root / 'references' / 'thresholds.example.json').write_text(json.dumps(thresholds, indent=2), encoding='utf-8')

report = """MARKER:AI_DISPLACEMENT_2025_Q2\nASOF:2025-05-14T09:30:00Z\nFREQ:A1 weekly; A2 monthly; A3 quarterly; A4 monthly; B1 weekly; B2 weekly; B3 monthly; C1 monthly; C2 monthly; C3 quarterly\n\nA1 Hiring momentum: 39.8 (below threshold 42, triggered)\nA2 Job posting breadth: 51.2 (below threshold 55, triggered)\nA3 AI task exposure: 71.4 (above threshold 68, triggered)\nA4 Employer AI adoption: 58.7 (below threshold 61, not triggered)\nB1 Unemployment claims: 268400 (above threshold 260000, triggered)\nB2 Layoff announcements: 49800 (below threshold 52000, not triggered)\nB3 Wage growth: 2.8 (below threshold 3.1, triggered)\nC1 Consumer delinquencies: 3.0 (above threshold 2.9, triggered)\nC2 SME credit spreads: 2.0 (below threshold 2.2, not triggered)\nC3 Capex reinvestment: 4.9 (above threshold 4.6, not triggered)\n\nNOTE: substitution speed is ahead of re-absorption speed, but reinvestment is not yet strong enough to offset bottlenecks.\nNOTE: purchasing power is softening while labor demand weakens.\n"""
(root / 'data' / 'source_report.txt').write_text(report, encoding='utf-8')

extra = {
    "meta": {
        "marker": "SUPPLEMENTAL_MARKER_77",
        "confidence_hint": "medium",
        "staleness": {"A3": "old", "C3": "old"}
    },
    "notes": [
        "Weekly claims are fresher than monthly wage data.",
        "The capex series is quarterly and should not be over-weighted."
    ]
}
(root / 'data' / 'supplemental.json').write_text(json.dumps(extra, indent=2), encoding='utf-8')
