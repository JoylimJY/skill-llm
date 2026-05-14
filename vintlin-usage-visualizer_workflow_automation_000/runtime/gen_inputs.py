#!/usr/bin/env python3
"""
Generates a realistic OpenClaw usage-visualizer workspace.
All random data uses a fixed seed for determinism.
"""
import os
import json
import random
import time
import datetime
from pathlib import Path

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")
BASE = Path(WORKSPACE)

# ── directory skeleton ─────────────────────────────────────────────────────────
dirs = [
    "scripts",
    "templates",
    "reports/2024-Q1",
    "reports/2024-Q2",
    "logs/raw",
    "logs/archive",
    "config",
    "tests",
    "docs",
    "assets/icons",
    "assets/css",
    ".openclaw/cache",
    ".openclaw/sync",
]
for d in dirs:
    (BASE / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ───────────────────────────────────────────────────────────
distractor_files = {
    "config/settings.yaml": "theme: dark\nlanguage: en\ntimezone: UTC\n",
    "config/legacy_report.cfg": "[report]\nformat=pdf\nperiod=monthly\n",
    "docs/CHANGELOG.md": "# Changelog\n## v2.1.0\n- Added week mode\n## v2.0.0\n- Initial release\n",
    "docs/architecture.txt": "Usage Visualizer uses a headless Chromium renderer.\nLogs are ingested from OPENCLAW_WORKSPACE/logs/.\n",
    "tests/test_parser.py": "# placeholder test\ndef test_noop(): pass\n",
    "assets/css/report.css": "body { font-family: sans-serif; color: #333; }\n",
    "assets/icons/logo.svg": "<svg></svg>\n",
    "reports/2024-Q1/summary.txt": "Q1 Total Sessions: 1204\nAvg Duration: 18m\n",
    "reports/2024-Q2/summary.txt": "Q2 Total Sessions: 1587\nAvg Duration: 21m\n",
    ".openclaw/cache/manifest.json": json.dumps({"version": "2.1.0", "last_sync": "2024-06-01T00:00:00Z"}),
    ".openclaw/sync/state.bin": "SYNC_STATE_BINARY_PLACEHOLDER",
    "logs/archive/2024-05.log.gz": "BINARY_PLACEHOLDER",
}
for rel_path, content in distractor_files.items():
    fpath = BASE / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# ── raw session log data (what run_usage_report.py reads) ──────────────────────
# Simulate 7 days of sessions
now = datetime.datetime.utcnow()
sessions = []
for day_offset in range(7):
    day = now - datetime.timedelta(days=day_offset)
    n_sessions = random.randint(3, 12)
    for _ in range(n_sessions):
        start_hour = random.randint(8, 20)
        start_min = random.randint(0, 59)
        duration_min = random.randint(5, 90)
        start_ts = day.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
        end_ts = start_ts + datetime.timedelta(minutes=duration_min)
        sessions.append({
            "session_id": f"sess_{abs(hash((day_offset, _, random.random())))%100000:05d}",
            "start": start_ts.isoformat() + "Z",
            "end": end_ts.isoformat() + "Z",
            "duration_seconds": duration_min * 60,
            "user": random.choice(["alice", "bob", "charlie", "diana"]),
            "project": random.choice(["infra-v2", "ml-pipeline", "data-lake", "api-gateway"]),
            "exit_code": random.choice([0, 0, 0, 1]),
        })

log_path = BASE / "logs" / "raw" / "sessions_current.jsonl"
with log_path.open("w") as f:
    for s in sessions:
        f.write(json.dumps(s) + "\n")

# ── requirements.txt ──────────────────────────────────────────────────────────
(BASE / "requirements.txt").write_text(
    "matplotlib\npandas\nnumpy\npillow\njinja2\npytz\n"
)

# ── The main script: scripts/run_usage_report.py ──────────────────────────────
# This is the proprietary script that the SKILL.md says "already exists".
# We generate it here to make the sandbox self-contained.

script_content = r'''#!/usr/bin/env python3
"""
OpenClaw Usage Visualizer - run_usage_report.py
Proprietary script. Reads sessions from $OPENCLAW_WORKSPACE/logs/raw/sessions_current.jsonl
"""
import argparse
import json
import os
import sys
import datetime
from pathlib import Path

def load_sessions(workspace: Path, period: str):
    log_file = workspace / "logs" / "raw" / "sessions_current.jsonl"
    if not log_file.exists():
        return []
    sessions = []
    now = datetime.datetime.utcnow()
    with log_file.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                s = json.loads(line)
            except json.JSONDecodeError:
                continue
            try:
                start = datetime.datetime.fromisoformat(s["start"].replace("Z", ""))
            except Exception:
                continue
            if period == "today":
                if start.date() == now.date():
                    sessions.append(s)
            elif period == "week":
                delta = now - start
                if delta.days < 7:
                    sessions.append(s)
            else:
                sessions.append(s)
    return sessions

def compute_stats(sessions):
    if not sessions:
        return {
            "total_sessions": 0,
            "total_duration_seconds": 0,
            "avg_duration_seconds": 0,
            "unique_users": 0,
            "unique_projects": 0,
            "success_rate": 0.0,
            "top_user": None,
            "top_project": None,
        }
    total = len(sessions)
    total_dur = sum(s.get("duration_seconds", 0) for s in sessions)
    avg_dur = total_dur / total if total else 0
    users = {}
    projects = {}
    successes = 0
    for s in sessions:
        u = s.get("user", "unknown")
        p = s.get("project", "unknown")
        users[u] = users.get(u, 0) + 1
        projects[p] = projects.get(p, 0) + 1
        if s.get("exit_code", 1) == 0:
            successes += 1
    top_user = max(users, key=users.get) if users else None
    top_project = max(projects, key=projects.get) if projects else None
    return {
        "total_sessions": total,
        "total_duration_seconds": total_dur,
        "avg_duration_seconds": round(avg_dur, 2),
        "unique_users": len(users),
        "unique_projects": len(projects),
        "success_rate": round(successes / total * 100, 2) if total else 0.0,
        "top_user": top_user,
        "top_project": top_project,
    }

def generate_image(stats, period, workspace: Path, output_json: bool):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError as e:
        if output_json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"ERROR: {e}")
        sys.exit(1)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(f"OpenClaw Usage Report — {period.capitalize()}", fontsize=16, fontweight="bold")

    # Bar chart: sessions by user
    ax1 = axes[0]
    labels = ["total_sessions", "unique_users", "unique_projects"]
    values = [stats["total_sessions"], stats["unique_users"], stats["unique_projects"]]
    bars = ax1.bar(labels, values, color=["#4C72B0", "#DD8452", "#55A868"])
    ax1.set_title("Activity Overview")
    ax1.set_ylabel("Count")
    for bar, val in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.1,
                 str(val), ha="center", va="bottom", fontweight="bold")

    # Pie chart: success vs failure
    ax2 = axes[1]
    sr = stats["success_rate"]
    fr = 100.0 - sr
    if sr > 0 or fr > 0:
        wedges, texts, autotexts = ax2.pie(
            [sr, fr],
            labels=["Success", "Failure"],
            autopct="%1.1f%%",
            colors=["#55A868", "#C44E52"],
            startangle=90,
        )
    ax2.set_title("Session Success Rate")

    plt.tight_layout()

    reports_dir = workspace / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    image_filename = f"usage_report_{period}_{ts}.png"
    image_path = reports_dir / image_filename
    plt.savefig(str(image_path), dpi=150, bbox_inches="tight")
    plt.close()

    result = {
        "status": "success",
        "period": period,
        "image_path": str(image_path),
        "stats": stats,
    }
    if output_json:
        print(json.dumps(result))
    else:
        print(f"Report saved to: {image_path}")
    return str(image_path)

def generate_text(stats, period, output_json: bool):
    result = {
        "status": "success",
        "period": period,
        "mode": "text",
        "stats": stats,
    }
    if output_json:
        print(json.dumps(result))
    else:
        print(f"=== OpenClaw Usage Report ({period}) ===")
        for k, v in stats.items():
            print(f"  {k}: {v}")
    return result

def main():
    parser = argparse.ArgumentParser(description="OpenClaw Usage Visualizer")
    parser.add_argument("--mode", choices=["image", "text"], required=True)
    parser.add_argument("--period", choices=["today", "week", "all"], required=True)
    parser.add_argument("--json", action="store_true", dest="output_json",
                        help="Output results as JSON")
    args = parser.parse_args()

    workspace_env = os.environ.get("OPENCLAW_WORKSPACE")
    if not workspace_env:
        err = {"error": "OPENCLAW_WORKSPACE environment variable not set"}
        if args.output_json:
            print(json.dumps(err))
        else:
            print("ERROR: OPENCLAW_WORKSPACE not set")
        sys.exit(1)

    workspace = Path(workspace_env)
    sessions = load_sessions(workspace, args.period)
    stats = compute_stats(sessions)

    if args.mode == "image":
        generate_image(stats, args.period, workspace, args.output_json)
    else:
        generate_text(stats, args.period, args.output_json)

if __name__ == "__main__":
    main()
'''

script_path = BASE / "scripts" / "run_usage_report.py"
script_path.write_text(script_content)
os.chmod(script_path, 0o755)

print(f"[gen_inputs] Workspace prepared at {WORKSPACE}")
print(f"[gen_inputs] Sessions written: {len(sessions)}")
print(f"[gen_inputs] Script: {script_path}")