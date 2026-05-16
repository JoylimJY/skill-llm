import os
import json
import random
import stat
from pathlib import Path

random.seed(42)

# ── root workspace ──────────────────────────────────────────────────────────
workspace = Path(os.environ.get("WORKSPACE", "/workspace"))
workspace.mkdir(parents=True, exist_ok=True)

# ── skill directory structure ────────────────────────────────────────────────
skill_dir = workspace / "skills" / "olympic-alert"
scripts_dir = skill_dir / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# ── events.json  (Korea defaults — agent must reconfigure for Norway) ────────
events_json = {
    "country": "Korea",
    "flag": "🇰🇷",
    "links": {
        "네이버 스포츠": "https://m.sports.naver.com/milanocortina2026",
        "치지직": "https://chzzk.naver.com/search?query=올림픽"
    },
    "events": [
        {"time": "2026-02-10 18:00", "name": "🏒 쇼트트랙", "athletes": "최민정"},
        {"time": "2026-02-12 20:30", "name": "⛸️ 피겨스케이팅", "athletes": "차준환"},
        {"time": "2026-02-14 09:00", "name": "🎿 바이애슬론", "athletes": "김보름"}
    ]
}
(scripts_dir / "events.json").write_text(
    json.dumps(events_json, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

# ── main script: check_olympic.py ────────────────────────────────────────────
check_script = r'''#!/usr/bin/env python3
"""Olympic Alert - check_olympic.py"""
import json, sys, os
from pathlib import Path
from datetime import datetime, timedelta

SKILL_DIR = Path(__file__).parent.parent
EVENTS_FILE = SKILL_DIR / "scripts" / "events.json"
STATE_DIR = Path.home() / ".config" / "olympic-alert"
STATE_FILE = STATE_DIR / "state.json"

def load_events():
    with open(EVENTS_FILE, encoding="utf-8") as f:
        return json.load(f)

def save_events(data):
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"notified": []}

def save_state(state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def cmd_list():
    data = load_events()
    if not data["events"]:
        print("경기 없음")
        return
    print(f"{data['flag']} {data['country']} 올림픽 일정")
    for ev in sorted(data["events"], key=lambda e: e["time"]):
        print(f"  {ev['time']}  {ev['name']}  ({ev['athletes']})")

def cmd_add(time_str, name, athletes):
    data = load_events()
    # validate format
    try:
        datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    except ValueError:
        print(f"오류: 시간 형식은 YYYY-MM-DD HH:MM 이어야 합니다. 입력값: {time_str}")
        sys.exit(1)
    data["events"].append({"time": time_str, "name": name, "athletes": athletes})
    save_events(data)
    print(f"추가됨: {time_str} {name} ({athletes})")

def cmd_remove(pattern):
    data = load_events()
    before = len(data["events"])
    data["events"] = [e for e in data["events"] if pattern not in e["name"]]
    removed = before - len(data["events"])
    save_events(data)
    print(f"삭제됨: {removed}개 (패턴: '{pattern}')")

def cmd_check():
    data = load_events()
    state = load_state()
    now = datetime.now()
    alerts = []
    for ev in data["events"]:
        ev_time = datetime.strptime(ev["time"], "%Y-%m-%d %H:%M")
        delta = ev_time - now
        minutes = delta.total_seconds() / 60
        key = f"{ev['time']}_{ev['name']}"
        if 0 <= minutes <= 15 and key not in state["notified"]:
            alerts.append((ev, int(minutes)))
            state["notified"].append(key)
    if not alerts:
        print("알림 없음")
        return
    save_state(state)
    for ev, mins in alerts:
        link_str = " | ".join(data["links"].values())
        print(f"{data['flag']} {mins}분 후\n{ev['name']}\n👤 {ev['athletes']}\n\n📺 {link_str}")

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        cmd_check()
    elif args[0] == "list":
        cmd_list()
    elif args[0] == "add" and len(args) == 4:
        cmd_add(args[1], args[2], args[3])
    elif args[0] == "remove" and len(args) == 2:
        cmd_remove(args[1])
    else:
        print("사용법: check_olympic.py [list|add|remove] ...")
        sys.exit(1)
'''
(scripts_dir / "check_olympic.py").write_text(check_script, encoding="utf-8")
(scripts_dir / "check_olympic.py").chmod(
    (scripts_dir / "check_olympic.py").stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
)

# ── SKILL.md ─────────────────────────────────────────────────────────────────
skill_md = """\
# Olympic Alert Skill
See SKILL.md documentation for usage.
"""
(skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

# ── distractor files ─────────────────────────────────────────────────────────
distractor_root = workspace / "project"
distractor_root.mkdir(exist_ok=True)

# sports data dir (misleading)
sports_dir = distractor_root / "sports_data"
sports_dir.mkdir(exist_ok=True)

(sports_dir / "norway_athletes_2025.csv").write_text(
    "name,sport,bib\nJohannes Boe,Biathlon,1\nMarte Olsbu Roiseland,Biathlon,2\nViktor Hovland,Golf,99\n",
    encoding="utf-8"
)
(sports_dir / "schedule_draft.txt").write_text(
    "Draft schedule - NOT FINAL\n2026-02-10: Opening Ceremony\n2026-02-11: Alpine Ski\n",
    encoding="utf-8"
)
(sports_dir / "broadcast_links.yaml").write_text(
    "nrk: https://nrk.no/sport\nviaplay: https://viaplay.no/sport\n",
    encoding="utf-8"
)

# config dir
config_dir = distractor_root / "config"
config_dir.mkdir(exist_ok=True)
(config_dir / "alert_thresholds.json").write_text(
    json.dumps({"warning_minutes": 30, "critical_minutes": 10}, indent=2),
    encoding="utf-8"
)
(config_dir / "notification_channels.json").write_text(
    json.dumps({"sms": True, "email": False, "push": True}, indent=2),
    encoding="utf-8"
)
(config_dir / "old_events_backup.json").write_text(
    json.dumps({"events": [], "country": "Norway", "flag": "🇳🇴"}, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

# logs dir
logs_dir = distractor_root / "logs"
logs_dir.mkdir(exist_ok=True)
(logs_dir / "alert_log_2025-12-01.txt").write_text(
    "[2025-12-01 08:00] System started\n[2025-12-01 08:01] No events scheduled\n",
    encoding="utf-8"
)
(logs_dir / "error_log.txt").write_text(
    "No errors recorded\n",
    encoding="utf-8"
)

# scripts dir with red-herring scripts
misc_scripts = distractor_root / "tools"
misc_scripts.mkdir(exist_ok=True)
(misc_scripts / "send_notification.sh").write_text(
    "#!/bin/bash\necho 'Notification sent'\n",
    encoding="utf-8"
)
(misc_scripts / "fetch_schedule.py").write_text(
    "# Placeholder: fetches schedule from external source\nprint('Not implemented')\n",
    encoding="utf-8"
)
(misc_scripts / "validate_json.py").write_text(
    "import json, sys\nwith open(sys.argv[1]) as f: json.load(f)\nprint('Valid JSON')\n",
    encoding="utf-8"
)

# docs dir
docs_dir = distractor_root / "docs"
docs_dir.mkdir(exist_ok=True)
(docs_dir / "architecture.md").write_text(
    "# System Architecture\nThis system sends alerts for Olympic events.\n",
    encoding="utf-8"
)
(docs_dir / "api_draft.md").write_text(
    "# API Draft\nPOST /events\nGET /events\nDELETE /events/{id}\n",
    encoding="utf-8"
)
(docs_dir / "requirements_spec.txt").write_text(
    "Alert must fire 15 minutes before event start.\nSupport for multiple national teams.\n",
    encoding="utf-8"
)

print("Workspace generated successfully.")
print(f"Skill dir: {skill_dir}")
print(f"Events JSON: {scripts_dir / 'events.json'}")