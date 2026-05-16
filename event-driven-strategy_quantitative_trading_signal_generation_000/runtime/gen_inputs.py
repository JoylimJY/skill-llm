import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "data/raw/events",
    "data/raw/analyst_reports",
    "data/processed",
    "data/archive/2025Q4",
    "configs",
    "scripts/utils",
    "scripts/loaders",
    "logs",
    "reports/drafts",
    "reports/final",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
(workspace / "configs" / "db_config.yaml").write_text(
    "host: localhost\nport: 5432\ndb: trading_db\nuser: analyst\n"
)
(workspace / "configs" / "logging.conf").write_text(
    "[loggers]\nkeys=root\n[handlers]\nkeys=consoleHandler\n"
)
(workspace / "scripts" / "utils" / "date_utils.py").write_text(
    "import datetime\ndef today(): return datetime.date.today()\n"
)
(workspace / "scripts" / "utils" / "ticker_map.py").write_text(
    "TICKER_MAP = {'002371': 'SZ', '000001': 'SZ', '600519': 'SH'}\n"
)
(workspace / "scripts" / "loaders" / "price_loader.py").write_text(
    "def load_prices(ticker, start, end): return []\n"
)
(workspace / "scripts" / "loaders" / "event_loader.py").write_text(
    "def load_events(path): import json; return json.load(open(path))\n"
)
(workspace / "logs" / "system.log").write_text(
    "2026-03-01 09:00:01 INFO system started\n2026-03-01 09:00:05 INFO data feed connected\n"
)
(workspace / "data" / "archive" / "2025Q4" / "summary.csv").write_text(
    "ticker,event,date,return\n002371.SZ,earnings,2025-10-28,0.043\n000001.SZ,policy,2025-11-15,0.021\n"
)
(workspace / "reports" / "drafts" / "template.md").write_text(
    "# Event Report Template\n## Summary\n## Signals\n## Risk\n"
)
(workspace / "data" / "processed" / ".gitkeep").write_text("")
(workspace / "reports" / "final" / ".gitkeep").write_text("")

# ── MAIN INPUT: raw events with messy/incomplete analyst data ────────────────
# This file deliberately has inconsistent fields, missing values, mixed types
# and messy naming to force the agent to clean and map data.

raw_events = [
    {
        "id": "EVT-001",
        "ticker": "002371.SZ",
        "event_category": "quarterly_earnings",   # agent must map → "earnings" (A class)
        "scheduled_date": "2026-04-18",
        "internal_eps_forecast": 1.52,
        "consensus_eps": 1.41,
        "historical_accuracy_weight": 0.88,       # for 调整因子
        "info_quality_score": 0.92,               # for 调整因子
        "base_importance": 3,                     # 基础重要性 (1-3)
        "market_attention": 1.8,                  # 市场关注度 (1-2)
        "historical_impact_coeff": 1.1,           # 历史影响系数 (0.8-1.2)
        "technical_alignment": 0.75,              # 技术面配合度 (0-1)
        "notes": "strong beat expected, insider confidence high"
    },
    {
        "id": "EVT-002",
        "ticker": "600519.SH",
        "event_category": "major_acquisition",    # agent must map → "merger_acquisition" (A class)
        "scheduled_date": "2026-04-22",
        "internal_eps_forecast": None,            # N/A for M&A events — use deal_premium instead
        "consensus_eps": None,
        "deal_premium_pct": 18.5,                 # percent above market price
        "market_implied_premium": 12.0,           # market's current expectation
        "historical_accuracy_weight": 0.80,
        "info_quality_score": 0.85,
        "base_importance": 3,
        "market_attention": 2.0,
        "historical_impact_coeff": 1.05,
        "technical_alignment": 0.60,
        "notes": "target company confirmed talks"
    },
    {
        "id": "EVT-003",
        "ticker": "000001.SZ",
        "event_category": "management_change",    # agent must map → "management_change" (B class)
        "scheduled_date": "2026-04-25",
        "internal_eps_forecast": 0.85,
        "consensus_eps": 0.87,
        "historical_accuracy_weight": 0.71,
        "info_quality_score": 0.78,
        "base_importance": 2,
        "market_attention": 1.5,
        "historical_impact_coeff": 0.95,
        "technical_alignment": 0.40,
        "notes": "new CEO from rival firm, uncertain market read"
    },
    {
        "id": "EVT-004",
        "ticker": "300760.SZ",
        "event_category": "nmpa_drug_approval",   # agent must map → "product_approval" (A class)
        "scheduled_date": "2026-04-30",
        "internal_eps_forecast": 2.10,
        "consensus_eps": 1.75,
        "historical_accuracy_weight": 0.93,
        "info_quality_score": 0.88,
        "base_importance": 3,
        "market_attention": 1.9,
        "historical_impact_coeff": 1.15,
        "technical_alignment": 0.85,
        "notes": "phase-3 data very strong, advisory committee positive"
    },
    {
        "id": "EVT-005",
        "ticker": "002594.SZ",
        "event_category": "analyst_conference",   # agent must map → (C class)
        "scheduled_date": "2026-05-03",
        "internal_eps_forecast": 3.20,
        "consensus_eps": 3.18,
        "historical_accuracy_weight": 0.65,
        "info_quality_score": 0.70,
        "base_importance": 1,
        "market_attention": 1.2,
        "historical_impact_coeff": 0.82,
        "technical_alignment": 0.30,
        "notes": "routine sell-side event, low conviction"
    }
]

(workspace / "data" / "raw" / "events" / "upcoming_events_raw.json").write_text(
    json.dumps(raw_events, indent=2, ensure_ascii=False)
)

# ── Analyst coverage context (distractor with some useful numbers) ───────────
analyst_context = {
    "generated": "2026-04-10",
    "source": "internal research team",
    "coverage": [
        {"ticker": "002371.SZ", "analyst": "Wang Lei", "rating": "BUY", "target_price": 45.0, "last_revision": "2026-03-28"},
        {"ticker": "600519.SH", "analyst": "Li Ming",  "rating": "HOLD", "target_price": 1800.0, "last_revision": "2026-04-01"},
        {"ticker": "000001.SZ", "analyst": "Zhang Fang","rating": "NEUTRAL","target_price": 12.5,  "last_revision": "2026-03-15"},
        {"ticker": "300760.SZ", "analyst": "Chen Yu",  "rating": "STRONG_BUY","target_price": 280.0,"last_revision": "2026-04-08"},
        {"ticker": "002594.SZ", "analyst": "Liu Hao",  "rating": "BUY",  "target_price": 210.0, "last_revision": "2026-03-20"},
    ]
}
(workspace / "data" / "raw" / "analyst_reports" / "coverage_summary.json").write_text(
    json.dumps(analyst_context, indent=2, ensure_ascii=False)
)

# ── Historical event reaction data (distractor) ──────────────────────────────
hist = [
    {"ticker":"002371.SZ","event":"earnings","date":"2025-10-28","pre_return":0.031,"post_return":0.043,"days_held":3},
    {"ticker":"002371.SZ","event":"earnings","date":"2025-07-22","pre_return":0.018,"post_return":-0.011,"days_held":2},
    {"ticker":"600519.SH","event":"acquisition","date":"2025-06-10","pre_return":0.055,"post_return":0.072,"days_held":5},
    {"ticker":"300760.SZ","event":"product_approval","date":"2025-11-30","pre_return":0.087,"post_return":0.121,"days_held":4},
]
(workspace / "data" / "archive" / "2025Q4" / "historical_event_reactions.json").write_text(
    json.dumps(hist, indent=2, ensure_ascii=False)
)

print("Workspace scaffold complete.")
print(f"Files created under {workspace}")