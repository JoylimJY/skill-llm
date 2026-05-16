import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Deep directory structure with distractor files ──────────────────────────

dirs = [
    "workspace/research/hk_equities/internet_sector",
    "workspace/research/hk_equities/financials",
    "workspace/research/macro",
    "workspace/research/archived/2025Q4",
    "workspace/tools/hk-stock-predictor",
    "workspace/tools/gougoubi-create-prediction",
    "workspace/tools/utils",
    "workspace/config",
    "workspace/outputs/drafts",
    "workspace/outputs/submitted",
    "workspace/logs",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files
distractors = {
    "workspace/research/hk_equities/internet_sector/sector_overview.txt": (
        "Internet sector overview: Tencent, Meituan, Kuaishou, NetEase\n"
        "Southbound flow trend: generally positive in Q1 2026.\n"
        "Note: This is NOT the final prediction input.\n"
    ),
    "workspace/research/hk_equities/financials/banking_notes.txt": (
        "HSBC, BOC HK, Hang Seng Bank Q1 preview.\n"
        "Net interest margin compression expected.\n"
    ),
    "workspace/research/macro/southbound_flow_march2026.csv": (
        "date,net_flow_HKD_bn\n"
        "2026-03-10,+3.2\n"
        "2026-03-11,-1.1\n"
        "2026-03-12,+2.8\n"
        "2026-03-13,+0.5\n"
        "2026-03-14,-0.3\n"
    ),
    "workspace/research/archived/2025Q4/old_predictions.json": json.dumps({
        "archived": True,
        "note": "These are expired drafts from 2025 Q4. Do not use.",
        "candidates": [
            {"title": "Will 00700 close above HK$400 on 2025-12-31?", "status": "expired"}
        ]
    }, indent=2, ensure_ascii=False),
    "workspace/tools/utils/timezone_helper.py": (
        "# Utility: Convert HKT to UTC\n"
        "# HKT = UTC+8\n"
        "# Example: 16:00 HKT on 2026-04-22 = 08:00 UTC\n"
        "import pytz\n"
        "from datetime import datetime\n"
        "def hkt_close_to_utc(date_str):\n"
        "    hkt = pytz.timezone('Asia/Hong_Kong')\n"
        "    dt = datetime.strptime(date_str + ' 16:00:00', '%Y-%m-%d %H:%M:%S')\n"
        "    return hkt.localize(dt).astimezone(pytz.utc).isoformat()\n"
    ),
    "workspace/config/market_defaults.json": json.dumps({
        "default_timezone": "Asia/Hong_Kong",
        "default_safety_buffer_hours": 17,
        "fallback_source": "HKEX official quote data"
    }, indent=2),
    "workspace/logs/predictor_run_20260315.log": (
        "[INFO] hk-stock-predictor started for 09988\n"
        "[INFO] Fetched price data\n"
        "[WARN] Low confidence on macro thesis candidate\n"
        "[INFO] Recommended: close-price binary on earnings day\n"
    ),
    "workspace/outputs/submitted/example_submitted.json": json.dumps({
        "marketName": "Will 09988 close above HK$110 on 2026-03-25?",
        "deadlineIsoUtc": "2026-03-25T08:00:00Z",
        "status": "submitted",
        "txHash": "0xabc123"
    }, indent=2),
    "workspace/outputs/drafts/.gitkeep": "",
    "workspace/tools/hk-stock-predictor/README_INTERNAL.txt": (
        "Internal tool. Do not call directly from outside the workflow.\n"
        "Output schema: predictionCandidates[], recommendedPrediction\n"
    ),
    "workspace/tools/gougoubi-create-prediction/README_INTERNAL.txt": (
        "Accepts: marketName, deadlineIsoUtc (required).\n"
        "Optional: rules, tags.\n"
        "Returns: txHash, proposalAddress.\n"
    ),
}

for path, content in distractors.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# ── THE CORE PROBLEM FILE ────────────────────────────────────────────────────
# Raw analyst notes for 02318 (Ping An Insurance) with multiple prediction
# candidates. Some are invalid per Market Filters. The agent must pick the
# valid one, then produce the full Gougoubi proposal.

analyst_notes = {
    "symbol": "02318",
    "companyName": "Ping An Insurance (Group) Company of China",
    "analysisDate": "2026-04-14",
    "referenceClose": "HK$49.20",
    "catalystNote": (
        "Ping An is expected to release its Q1 2026 interim results on 2026-04-28. "
        "Southbound inflows have been steady. "
        "The stock has recovered from a Jan trough and consensus expects YoY net profit growth of 8-12%."
    ),
    "horizon": "14d",
    "predictionCandidates": [
        {
            "id": "C1",
            "title": "Will Ping An Insurance become the dominant force in Chinese fintech over the next decade?",
            "type": "open_narrative",
            "deadlineIsoUtc": None,
            "resolutionSource": None,
            "confidence": 0.55,
            "note": "Broad macro thesis, no measurable threshold, no deadline."
        },
        {
            "id": "C2",
            "title": "Will 02318 close above HK$52 on 2026-04-28?",
            "type": "direction",
            "deadlineIsoUtc": "2026-04-28T08:00:00Z",
            "resolutionSource": "Yahoo Finance 2318.HK historical data, fallback HKEX official quote data",
            "confidence": 0.61,
            "note": "High-liquidity underlying. Near-dated catalyst (Q1 results day). Simple binary. Externally resolvable."
        },
        {
            "id": "C3",
            "title": "Is Ping An's management sentiment positive this quarter?",
            "type": "sentiment",
            "deadlineIsoUtc": "2026-04-30T00:00:00Z",
            "resolutionSource": "Analyst sentiment aggregators",
            "confidence": 0.50,
            "note": "Sentiment-based, subjective judgment required."
        },
        {
            "id": "C4",
            "title": "Will 02318 report YoY net profit growth above 10% in Q1 2026 results?",
            "type": "earnings",
            "deadlineIsoUtc": "2026-04-30T16:00:00Z",
            "resolutionSource": "Ping An official earnings release, fallback HKEX regulatory filing",
            "confidence": 0.57,
            "note": "Earnings metric. Resolvable from official report. But deadline UTC needs careful check — report date is 2026-04-28, safety buffer should put deadline at 2026-04-30."
        }
    ],
    "recommendedPrediction": "C2"
}

with open("workspace/research/hk_equities/financials/02318_analysis_notes.json", "w", encoding="utf-8") as f:
    json.dump(analyst_notes, f, indent=2, ensure_ascii=False)

print("Workspace generated successfully.")
print("Key file: workspace/research/hk_equities/financials/02318_analysis_notes.json")