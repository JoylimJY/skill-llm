import os
import json
import random

random.seed(42)

workspace = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "data/raw",
    "data/processed",
    "data/archive",
    "reports/2024",
    "reports/2025",
    "members/active",
    "members/inactive",
    "config",
    "logs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Main analysis script (already "exists" per SKILL.md) ────────────────────
ghin_script = r'''#!/usr/bin/env python3
"""GHIN Golf Statistics Analyzer"""
import json
import sys
import argparse
import statistics
from datetime import datetime
from pathlib import Path
from collections import Counter, defaultdict
import re

def parse_score(score_str):
    """Parse score string like '82A' or '79' into integer."""
    if score_str is None:
        return None
    m = re.match(r'^(\d+)', str(score_str))
    return int(m.group(1)) if m else None

def compute_trend(handicap_history):
    if not handicap_history or len(handicap_history) < 2:
        return "stable"
    recent = sorted(handicap_history, key=lambda x: x.get("date",""), reverse=True)[:5]
    if len(recent) < 2:
        return "stable"
    newest = recent[0]["index"]
    oldest = recent[-1]["index"]
    diff = newest - oldest
    if diff < -0.5:
        return "improving"
    elif diff > 0.5:
        return "declining"
    return "stable"

def trend_arrow(trend):
    arrows = {"improving": "↗️  Improving", "declining": "↘️  Declining", "stable": "→  Stable"}
    return arrows.get(trend, "→  Stable")

def analyze(data):
    handicap_index = data.get("handicap_index")
    lifetime_rounds = data.get("lifetime_rounds", 0)
    handicap_history = data.get("handicap_history", [])
    stats = data.get("stats", {})
    scores = data.get("scores", [])

    trend = compute_trend(handicap_history)

    numeric_scores = []
    for s in scores:
        v = parse_score(s.get("score"))
        if v is not None:
            numeric_scores.append(v)

    best_score = min(numeric_scores) if numeric_scores else None
    worst_score = max(numeric_scores) if numeric_scores else None

    # Best differentials
    scored = [(s.get("differential"), s.get("course","Unknown"), s.get("date","")) 
              for s in scores if s.get("differential") is not None]
    scored_sorted = sorted(scored, key=lambda x: x[0])
    best_5 = scored_sorted[:5]

    # Most played courses
    course_scores = defaultdict(list)
    for s in scores:
        v = parse_score(s.get("score"))
        if v is not None:
            course_scores[s.get("course","Unknown")].append(v)
    course_counts = {c: len(vs) for c, vs in course_scores.items()}
    sorted_courses = sorted(course_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Yearly breakdown
    yearly = defaultdict(list)
    for s in scores:
        date = s.get("date","")
        v = parse_score(s.get("score"))
        if date and v is not None:
            year = date[:4]
            yearly[year].append(v)
    yearly_sorted = sorted(yearly.items(), reverse=True)

    # Handicap range
    if handicap_history:
        indices = [h["index"] for h in handicap_history if "index" in h]
        hmin = min(indices) if indices else None
        hmax = max(indices) if indices else None
    else:
        hmin = hmax = None

    return {
        "handicap_index": handicap_index,
        "trend": trend,
        "lifetime_rounds": lifetime_rounds,
        "best_score": best_score,
        "worst_score": worst_score,
        "best_differentials": [{"differential": d, "course": c, "date": dt} for d,c,dt in best_5],
        "most_played_courses": [
            {"course": c, "rounds": course_counts[c],
             "avg_score": round(statistics.mean(course_scores[c]), 1)}
            for c, _ in sorted_courses
        ],
        "yearly_breakdown": [
            {"year": y, "rounds": len(vs), "avg_score": round(statistics.mean(vs), 1)}
            for y, vs in yearly_sorted
        ],
        "stats": stats,
        "handicap_range": {"min": hmin, "max": hmax},
    }

def print_text(result):
    print("GHIN Golf Statistics Report")
    print("=" * 30)
    print()
    hi = result["handicap_index"]
    print(f"Current Handicap: {hi}")
    print(f"Trend (last 5): {trend_arrow(result['trend'])}")
    print()
    print("LIFETIME TOTALS")
    print("-" * 15)
    print(f"Total Rounds: {result['lifetime_rounds']}")
    if result["best_score"] is not None:
        print(f"Best Score: {result['best_score']}")
    if result["worst_score"] is not None:
        print(f"Worst Score: {result['worst_score']}")
    print()
    print("BEST DIFFERENTIALS")
    print("-" * 17)
    for i, d in enumerate(result["best_differentials"], 1):
        print(f"{i}. {d['differential']} - {d['course']} ({d['date']})")
    print()
    print("MOST PLAYED COURSES")
    print("-" * 19)
    for c in result["most_played_courses"]:
        print(f"{c['course']}: {c['rounds']} rounds (avg {c['avg_score']})")
    print()
    print("YEARLY BREAKDOWN")
    print("-" * 16)
    for y in result["yearly_breakdown"]:
        print(f"{y['year']}: {y['rounds']} rounds (avg {y['avg_score']})")
    print()
    s = result.get("stats", {})
    if s:
        print("PERFORMANCE STATS")
        print("-" * 17)
        if "par3_avg" in s: print(f"Par 3 Avg: {s['par3_avg']}")
        if "par4_avg" in s: print(f"Par 4 Avg: {s['par4_avg']}")
        if "par5_avg" in s: print(f"Par 5 Avg: {s['par5_avg']}")
        if "gir_pct" in s: print(f"GIR%: {s['gir_pct']}%")
        if "fairways_pct" in s: print(f"Fairways%: {s['fairways_pct']}%")
        if "putts_avg" in s: print(f"Putts Avg: {s['putts_avg']}")

def main():
    parser = argparse.ArgumentParser(description="GHIN Golf Statistics Analyzer")
    parser.add_argument("data_file", help="Path to GHIN data JSON file")
    parser.add_argument("--format", choices=["text","json"], default="text")
    args = parser.parse_args()

    path = Path(args.data_file)
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    result = analyze(data)

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print_text(result)

if __name__ == "__main__":
    main()
'''

with open(os.path.join(workspace, "scripts", "ghin_stats.py"), "w") as f:
    f.write(ghin_script)

# ── Fragmented raw data files (the "messy" inputs the agent must consolidate) ─
# These are partial/fragmented pieces of a player's data — agent must assemble
# them into the correct schema understood by ghin_stats.py

# Fragment 1: basic player info
frag1 = {
    "player_id": "GH-20041",
    "name": "Marcus Bellweather",
    "club": "Ridgeline Country Club",
    "current_handicap": 14.2,
    "total_rounds_played": 57,
}
with open(os.path.join(workspace, "data/raw", "player_info.json"), "w") as f:
    json.dump(frag1, f, indent=2)

# Fragment 2: handicap history (recent-first, some entries have 'idx' instead of 'index' — trap)
frag2 = [
    {"date": "2025-11-10", "index": 14.2},
    {"date": "2025-10-15", "index": 14.8},
    {"date": "2025-09-20", "index": 15.1},
    {"date": "2025-08-05", "index": 15.6},
    {"date": "2025-07-01", "index": 15.9},
    {"date": "2025-05-12", "index": 16.4},
    {"date": "2025-03-08", "index": 16.1},
    {"date": "2024-12-20", "index": 16.8},
    {"date": "2024-10-05", "index": 17.2},
    {"date": "2024-07-18", "index": 17.5},
]
with open(os.path.join(workspace, "data/raw", "handicap_history.json"), "w") as f:
    json.dump(frag2, f, indent=2)

# Fragment 3: score records — score stored as plain integer (missing letter suffix in some),
# cr_slope stored as two fields (must be merged into "68.0/117" format), some missing differentials
frag3 = [
    {"date": "2025-11-08", "score_val": 78, "score_suffix": "A", "course": "Ridgeline Country Club", "course_rating": 71.2, "slope": 128, "differential": 6.1},
    {"date": "2025-10-22", "score_val": 80, "score_suffix": "A", "course": "Ridgeline Country Club", "course_rating": 71.2, "slope": 128, "differential": 8.4},
    {"date": "2025-10-05", "score_val": 83, "score_suffix": "",  "course": "Desert Pines Golf Club", "course_rating": 72.1, "slope": 133, "differential": 10.2},
    {"date": "2025-09-18", "score_val": 77, "score_suffix": "A", "course": "Paiute Wolf Creek",     "course_rating": 73.4, "slope": 140, "differential": 5.2},
    {"date": "2025-09-01", "score_val": 85, "score_suffix": "",  "course": "Desert Pines Golf Club", "course_rating": 72.1, "slope": 133, "differential": 12.1},
    {"date": "2025-08-14", "score_val": 81, "score_suffix": "A", "course": "Ridgeline Country Club", "course_rating": 71.2, "slope": 128, "differential": 9.0},
    {"date": "2025-07-30", "score_val": 88, "score_suffix": "",  "course": "Las Vegas Golf Club",    "course_rating": 69.8, "slope": 120, "differential": 17.6},
    {"date": "2025-07-12", "score_val": 84, "score_suffix": "",  "course": "Las Vegas Golf Club",    "course_rating": 69.8, "slope": 120, "differential": 13.8},
    {"date": "2025-06-28", "score_val": 79, "score_suffix": "A", "course": "Paiute Wolf Creek",     "course_rating": 73.4, "slope": 140, "differential": 7.1},
    {"date": "2025-06-10", "score_val": 82, "score_suffix": "",  "course": "Ridgeline Country Club", "course_rating": 71.2, "slope": 128, "differential": 10.5},
    {"date": "2025-05-25", "score_val": 91, "score_suffix": "",  "course": "Las Vegas Golf Club",    "course_rating": 69.8, "slope": 120, "differential": 20.9},
    {"date": "2025-04-18", "score_val": 86, "score_suffix": "",  "course": "Desert Pines Golf Club", "course_rating": 72.1, "slope": 133, "differential": 13.0},
    {"date": "2025-03-05", "score_val": 89, "score_suffix": "",  "course": "Las Vegas Golf Club",    "course_rating": 69.8, "slope": 120, "differential": 18.9},
    {"date": "2025-02-15", "score_val": 87, "score_suffix": "",  "course": "Ridgeline Country Club", "course_rating": 71.2, "slope": 128, "differential": 15.2},
    {"date": "2025-01-20", "score_val": 90, "score_suffix": "",  "course": "Desert Pines Golf Club", "course_rating": 72.1, "slope": 133, "differential": 17.1},
    {"date": "2024-12-15", "score_val": 92, "score_suffix": "",  "course": "Las Vegas Golf Club",    "course_rating": 69.8, "slope": 120, "differential": 22.4},
    {"date": "2024-11-20", "score_val": 88, "score_suffix": "",  "course": "Ridgeline Country Club", "course_rating": 71.2, "slope": 128, "differential": 16.3},
    {"date": "2024-10-10", "score_val": 85, "score_suffix": "",  "course": "Paiute Wolf Creek",     "course_rating": 73.4, "slope": 140, "differential": 12.8},
    {"date": "2024-09-05", "score_val": 94, "score_suffix": "",  "course": "Las Vegas Golf Club",    "course_rating": 69.8, "slope": 120, "differential": 24.1},
    {"date": "2024-08-22", "score_val": 89, "score_suffix": "",  "course": "Desert Pines Golf Club", "course_rating": 72.1, "slope": 133, "differential": 16.1},
    {"date": "2024-07-04", "score_val": 91, "score_suffix": "",  "course": "Ridgeline Country Club", "course_rating": 71.2, "slope": 128, "differential": 19.5},
    {"date": "2024-06-18", "score_val": 86, "score_suffix": "",  "course": "Paiute Wolf Creek",     "course_rating": 73.4, "slope": 140, "differential": 13.5},
    {"date": "2024-05-30", "score_val": 95, "score_suffix": "",  "course": "Las Vegas Golf Club",    "course_rating": 69.8, "slope": 120, "differential": 25.8},
    {"date": "2024-04-12", "score_val": 93, "score_suffix": "",  "course": "Desert Pines Golf Club", "course_rating": 72.1, "slope": 133, "differential": 20.3},
    {"date": "2024-03-08", "score_val": 90, "score_suffix": "",  "course": "Ridgeline Country Club", "course_rating": 71.2, "slope": 128, "differential": 18.2},
    {"date": "2024-02-20", "score_val": 88, "score_suffix": "",  "course": "Las Vegas Golf Club",    "course_rating": 69.8, "slope": 120, "differential": 17.9},
    {"date": "2024-01-15", "score_val": 86, "score_suffix": "",  "course": "Paiute Wolf Creek",     "course_rating": 73.4, "slope": 140, "differential": 14.2},
]
with open(os.path.join(workspace, "data/raw", "score_records.json"), "w") as f:
    json.dump(frag3, f, indent=2)

# Fragment 4: performance stats (separate file)
frag4 = {
    "par3_scoring_avg": 3.82,
    "par4_scoring_avg": 4.71,
    "par5_scoring_avg": 5.44,
    "greens_in_regulation_pct": 38,
    "fairway_hit_pct": 58,
    "average_putts_per_round": 30.7,
}
with open(os.path.join(workspace, "data/raw", "performance_stats.json"), "w") as f:
    json.dump(frag4, f, indent=2)

# ── Distractor files ──────────────────────────────────────────────────────────
# Archive reports (old format, wrong schema)
with open(os.path.join(workspace, "data/archive", "old_handicap_2022.json"), "w") as f:
    json.dump({"year": 2022, "avg_handicap": 21.3, "rounds": 14}, f)

with open(os.path.join(workspace, "data/archive", "old_handicap_2023.json"), "w") as f:
    json.dump({"year": 2023, "avg_handicap": 19.1, "rounds": 22}, f)

# Processed stubs
with open(os.path.join(workspace, "data/processed", "export_stub.csv"), "w") as f:
    f.write("date,score,course\n2023-01-01,88,Unknown Course\n")

# Reports placeholders
with open(os.path.join(workspace, "reports/2024", "annual_summary.txt"), "w") as f:
    f.write("Annual summary for 2024 - PENDING generation\n")

with open(os.path.join(workspace, "reports/2025", "annual_summary.txt"), "w") as f:
    f.write("Annual summary for 2025 - PENDING generation\n")

# Member files
with open(os.path.join(workspace, "members/active", "bellweather_m.txt"), "w") as f:
    f.write("Marcus Bellweather\nMember since: 2018\nHome course: Ridgeline Country Club\nGHIN: 20041\n")

with open(os.path.join(workspace, "members/inactive", "jones_t.txt"), "w") as f:
    f.write("Timothy Jones\nMember since: 2015\nStatus: Inactive 2023\n")

# Config files
with open(os.path.join(workspace, "config", "club_config.json"), "w") as f:
    json.dump({"club_name": "Ridgeline Country Club", "season_start": "March", "season_end": "November"}, f)

# Logs
with open(os.path.join(workspace, "logs", "data_collection.log"), "w") as f:
    f.write("[2025-11-10 09:14:22] INFO: Data collection job initiated for member GH-20041\n")
    f.write("[2025-11-10 09:14:45] INFO: Retrieved 27 score records\n")
    f.write("[2025-11-10 09:15:01] INFO: Handicap history retrieved: 10 entries\n")
    f.write("[2025-11-10 09:15:02] INFO: Job completed successfully\n")

# Another distractor: a different schema JSON that looks like it might work but won't
with open(os.path.join(workspace, "data/raw", "wrong_schema_attempt.json"), "w") as f:
    json.dump({
        "handicap": 14.2,
        "rounds": 57,
        "history": [{"dt": "2025-11-10", "hcp": 14.2}],
        "scores": [{"dt": "2025-11-08", "gross": 78, "venue": "Ridgeline Country Club"}]
    }, f, indent=2)

print("Workspace generated successfully.")
print(f"Workspace root: {workspace}")