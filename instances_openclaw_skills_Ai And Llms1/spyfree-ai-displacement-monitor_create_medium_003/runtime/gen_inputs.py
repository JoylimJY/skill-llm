from pathlib import Path
import json
import random

random.seed(42)

thresholds = {
    "A1": {"name": "Job postings for AI-exposed roles", "threshold": 0.85, "tier": "A"},
    "A2": {"name": "Resume response rate for displaced workers", "threshold": 0.70, "tier": "A"},
    "A3": {"name": "AI capex growth", "threshold": 0.20, "tier": "A"},
    "A4": {"name": "AI labor substitution speed", "threshold": 0.60, "tier": "A"},
    "B1": {"name": "Unemployment rate in affected occupations", "threshold": 0.06, "tier": "B"},
    "B2": {"name": "Median re-employment duration", "threshold": 90, "tier": "B"},
    "B3": {"name": "Layoff announcements in exposed sectors", "threshold": 15, "tier": "B"},
    "C1": {"name": "Consumer delinquency rate", "threshold": 0.03, "tier": "C"},
    "C2": {"name": "Retail spending growth", "threshold": -0.01, "tier": "C"},
    "C3": {"name": "Credit spread widening", "threshold": 0.015, "tier": "C"},
}
Path("references").mkdir(exist_ok=True)
Path("references/thresholds.example.json").write_text(json.dumps(thresholds, indent=2), encoding="utf-8")

signals = [
    {"id": "A1", "value": 0.81, "unit": "index", "trend": "down", "as_of": "2025-05-01", "frequency": "monthly"},
    {"id": "A2", "value": 0.72, "unit": "rate", "trend": "up", "as_of": "2025-04-28", "frequency": "weekly"},
    {"id": "A3", "value": 0.24, "unit": "yoy", "trend": "up", "as_of": "2025-03-31", "frequency": "quarterly"},
    {"id": "A4", "value": 0.63, "unit": "index", "trend": "up", "as_of": "2025-05-01", "frequency": "monthly"},
    {"id": "B1", "value": 0.058, "unit": "rate", "trend": "up", "as_of": "2025-04-30", "frequency": "monthly"},
    {"id": "B2", "value": 96, "unit": "days", "trend": "up", "as_of": "2025-04-30", "frequency": "monthly"},
    {"id": "B3", "value": 17, "unit": "count", "trend": "up", "as_of": "2025-04-30", "frequency": "weekly"},
    {"id": "C1", "value": 0.031, "unit": "rate", "trend": "up", "as_of": "2025-04-30", "frequency": "monthly"},
    {"id": "C2", "value": -0.008, "unit": "yoy", "trend": "down", "as_of": "2025-03-31", "frequency": "monthly"},
    {"id": "C3", "value": 0.017, "unit": "spread", "trend": "up", "as_of": "2025-04-30", "frequency": "daily"},
]
Path("inputs.json").write_text(json.dumps({"signals": signals}, indent=2), encoding="utf-8")
Path("marker.txt").write_text("AI_DISPLACEMENT_MONITOR_MARKER_7F3A\n", encoding="utf-8")
