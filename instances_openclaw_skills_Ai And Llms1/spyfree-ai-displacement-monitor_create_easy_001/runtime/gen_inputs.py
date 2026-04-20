from pathlib import Path
import json

base = Path('.')
base.mkdir(parents=True, exist_ok=True)

thresholds = {
    "A1": {"name": "Job posting decline", "threshold": -5, "tier": "A"},
    "A2": {"name": "AI hiring share", "threshold": 0.18, "tier": "A"},
    "A3": {"name": "Entry-level wage pressure", "threshold": -0.02, "tier": "A"},
    "A4": {"name": "Automation capex acceleration", "threshold": 0.12, "tier": "A"},
    "B1": {"name": "Layoff announcements", "threshold": 20, "tier": "B"},
    "B2": {"name": "Unemployment claims", "threshold": 240000, "tier": "B"},
    "B3": {"name": "Labor force reabsorption", "threshold": 0.03, "tier": "B"},
    "C1": {"name": "Retail sales growth", "threshold": 0.01, "tier": "C"},
    "C2": {"name": "Consumer delinquencies", "threshold": 0.045, "tier": "C"},
    "C3": {"name": "Credit spread widening", "threshold": 1.2, "tier": "C"}
}
(base / 'thresholds.example.json').write_text(json.dumps(thresholds, indent=2), encoding='utf-8')

rows = [
    'indicator_id,value,unit,timestamp,trend,threshold,status',
    'A1,-8.4,percent,2025-04-30,down,-5,triggered',
    'A2,0.24,share,2025-04-30,up,0.18,triggered',
    'A3,-0.03,percent,2025-03-31,down,-0.02,triggered',
    'A4,0.10,share,2025-03-31,up,0.12,not_triggered',
    'B1,14,count,2025-04-30,up,20,not_triggered',
    'B2,228000,count,2025-05-01,up,240000,not_triggered',
    'B3,0.025,share,2025-03-31,down,0.03,triggered',
    'C1,0.008,share,2025-04-30,down,0.01,triggered',
    'C2,0.052,share,2025-04-30,up,0.045,triggered',
    'C3,1.5,percentage_points,2025-05-01,up,1.2,triggered'
]
(base / 'signal_data.csv').write_text('\n'.join(rows) + '\n', encoding='utf-8')

(base / 'notes.txt').write_text(
    'MARKER: AI_DISPLACEMENT_MONITOR\nSubstitution is running ahead of re-absorption, while capex is only partially offsetting labor stress.\n',
    encoding='utf-8'
)
