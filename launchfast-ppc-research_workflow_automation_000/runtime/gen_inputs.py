import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── distractor files ──────────────────────────────────────────────────────────

(workspace / "notes" / "meeting_notes_2024_03.txt").write_text(
    "Meeting with PPC agency:\n- Discussed raising bids on exact match\n- Need to audit negative keywords\n- Budget review next quarter\n"
)

(workspace / "notes" / "competitor_asins.txt").write_text(
    "# Competitor ASINs identified by VA\nB09RESISTANCE1\nB08FITNESSBAND\nB07RUBBERBAND1\nB09GYMBAND001\nB08WORKOUTSET1\n\nOwn ASIN: B0MYOWNBAND1\nCampaign name: ResistanceBands-Q3\nDefault bid: $0.85\nDaily budget: $40\n"
)

(workspace / "competitor_research" / "market_notes.txt").write_text(
    "Top sellers in resistance bands:\n1. FitLoop Pro - B09RESISTANCE1\n2. PowerStretch Elite - B08FITNESSBAND\n3. FlexBand 5-Pack - B07RUBBERBAND1\n4. GymCore Set - B09GYMBAND001\n5. WorkoutPro Kit - B08WORKOUTSET1\n\nOur product: B0MYOWNBAND1\n"
)

(workspace / "old_exports" / "old_bulk_upload_2023.csv").write_text(
    "Product,Entity,Operation,Campaign Name,State,Bid\n"
    "Sponsored Products,Campaign,Create,OldCampaign2023,enabled,0.75\n"
    "Sponsored Products,Ad Group,Create,OldCampaign2023,enabled,0.75\n"
)

(workspace / "old_exports" / "README_old.txt").write_text(
    "Old CSV exports from 2023 — DO NOT USE\nFormat changed, re-run research tool\n"
)

(workspace / "templates" / "generic_ppc_template.txt").write_text(
    "Generic PPC template (not Amazon-specific)\nCampaign,AdGroup,Keyword,MatchType,Bid\n"
)

(workspace / "archive" / "ppc_results_jan.json").write_text(json.dumps({
    "date": "2024-01-15",
    "keywords": ["resistance band", "workout bands", "exercise bands"],
    "note": "outdated data - re-run tool"
}, indent=2))

(workspace / "raw_data" / "asin_list_draft.txt").write_text(
    "Draft ASIN list (not finalized):\nB09RESISTANCE1\nB08FITNESSBAND\n??? need to verify last 3\n"
)

(workspace / "campaign_data" / "budget_planning.txt").write_text(
    "Q3 Budget Plan:\n- Resistance Bands: $40/day\n- Default bid: $0.85\n- Aggressive on Tier 1\n"
)

(workspace / "tools" / "tool_usage_notes.txt").write_text(
    "LaunchFast keyword research tool notes:\n- Run with ASIN list\n- Check output JSON for keywords\n- Process into bulk upload format\n"
)

# ── mock MCP server script ────────────────────────────────────────────────────
# This is the mock mcp__launchfast__amazon_keyword_research endpoint
# Agent must discover and call this service

mock_server = '''#!/usr/bin/env python3
"""Mock LaunchFast MCP Server — simulates mcp__launchfast__amazon_keyword_research"""
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

KEYWORD_DATA = {
    "B09RESISTANCE1": [
        {"keyword": "resistance bands", "search_volume": 45000, "competition": "high", "rank": 1},
        {"keyword": "exercise bands for working out", "search_volume": 12000, "competition": "medium", "rank": 3},
        {"keyword": "resistance band set", "search_volume": 38000, "competition": "high", "rank": 2},
        {"keyword": "loop resistance bands", "search_volume": 8500, "competition": "medium", "rank": 5},
        {"keyword": "physical therapy bands", "search_volume": 4200, "competition": "low", "rank": 8},
        {"keyword": "crossfit resistance bands", "search_volume": 3100, "competition": "low", "rank": 12},
        {"keyword": "nike shoes", "search_volume": 120000, "competition": "high", "rank": 15},
    ],
    "B08FITNESSBAND": [
        {"keyword": "resistance bands", "search_volume": 45000, "competition": "high", "rank": 2},
        {"keyword": "fitness resistance bands", "search_volume": 22000, "competition": "high", "rank": 1},
        {"keyword": "resistance band set", "search_volume": 38000, "competition": "high", "rank": 4},
        {"keyword": "workout bands for legs", "search_volume": 6700, "competition": "medium", "rank": 6},
        {"keyword": "pull up assist bands", "search_volume": 9100, "competition": "medium", "rank": 3},
        {"keyword": "stretching bands", "search_volume": 2800, "competition": "low", "rank": 11},
        {"keyword": "adidas running shoes", "search_volume": 95000, "competition": "high", "rank": 20},
    ],
    "B07RUBBERBAND1": [
        {"keyword": "resistance bands", "search_volume": 45000, "competition": "high", "rank": 4},
        {"keyword": "resistance band set", "search_volume": 38000, "competition": "high", "rank": 6},
        {"keyword": "rubber resistance bands", "search_volume": 5500, "competition": "low", "rank": 2},
        {"keyword": "exercise resistance bands", "search_volume": 18000, "competition": "medium", "rank": 3},
        {"keyword": "loop resistance bands", "search_volume": 8500, "competition": "medium", "rank": 7},
        {"keyword": "physical therapy bands", "search_volume": 4200, "competition": "low", "rank": 5},
        {"keyword": "mini resistance bands", "search_volume": 3400, "competition": "low", "rank": 9},
    ],
    "B09GYMBAND001": [
        {"keyword": "resistance band set", "search_volume": 38000, "competition": "high", "rank": 3},
        {"keyword": "gym resistance bands", "search_volume": 15000, "competition": "medium", "rank": 1},
        {"keyword": "resistance bands for men", "search_volume": 11000, "competition": "medium", "rank": 2},
        {"keyword": "loop resistance bands", "search_volume": 8500, "competition": "medium", "rank": 4},
        {"keyword": "pull up assist bands", "search_volume": 9100, "competition": "medium", "rank": 5},
        {"keyword": "physical therapy bands", "search_volume": 4200, "competition": "low", "rank": 6},
        {"keyword": "booty bands", "search_volume": 7800, "competition": "medium", "rank": 8},
    ],
    "B08WORKOUTSET1": [
        {"keyword": "exercise resistance bands", "search_volume": 18000, "competition": "medium", "rank": 2},
        {"keyword": "resistance bands for women", "search_volume": 14000, "competition": "medium", "rank": 1},
        {"keyword": "workout resistance bands", "search_volume": 10500, "competition": "medium", "rank": 3},
        {"keyword": "loop resistance bands", "search_volume": 8500, "competition": "medium", "rank": 5},
        {"keyword": "stretching bands", "search_volume": 2800, "competition": "low", "rank": 7},
        {"keyword": "resistance band exercises", "search_volume": 1900, "competition": "low", "rank": 14},
        {"keyword": "light resistance bands", "search_volume": 2100, "competition": "low", "rank": 10},
    ],
}

@app.route("/amazon_keyword_research", methods=["POST"])
def keyword_research():
    data = request.get_json()
    asins = data.get("asins", [])
    
    result = {
        "status": "success",
        "asins_analyzed": asins,
        "keywords": {}
    }
    
    for asin in asins:
        if asin in KEYWORD_DATA:
            result["keywords"][asin] = KEYWORD_DATA[asin]
    
    return jsonify(result)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "launchfast-mcp-mock"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7771, debug=False)
'''

(workspace / "tools" / "mcp_server.py").write_text(mock_server)

# ── agent-facing config ───────────────────────────────────────────────────────
config = {
    "mcp_endpoint": "http://localhost:7771/amazon_keyword_research",
    "health_check": "http://localhost:7771/health",
    "tool_name": "mcp__launchfast__amazon_keyword_research",
    "note": "POST JSON body: {\"asins\": [\"B0...\", ...]}  returns keyword data per ASIN"
}
(workspace / "tools" / "mcp_config.json").write_text(json.dumps(config, indent=2))

# ── task brief (business context only, no implementation hints) ───────────────
brief = """TASK BRIEF — Resistance Bands PPC Campaign
==========================================

Product Launch: FitCore Resistance Band Set (B0MYOWNBAND1)

Competitor ASINs to analyze:
  B09RESISTANCE1, B08FITNESSBAND, B07RUBBERBAND1, B09GYMBAND001, B08WORKOUTSET1

Campaign settings:
  Campaign name : ResistanceBands-Q3
  Default bid   : $0.85
  Daily budget  : $40.00
  Start date    : 20240801

Deliverable:
  A single bulk upload file named: launchfast-ppc-bulk-20240801.txt
  Place it in ~/Downloads/

NOTE: The keyword research MCP service config is at /workspace/tools/mcp_config.json
"""
(workspace / "task_brief.txt").write_text(brief)

print("Workspace initialized.")
print(f"Files created: {list(workspace.rglob('*'))}")