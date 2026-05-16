#!/usr/bin/env python3
"""Evaluation script for the olympic-alert Norway reconfiguration task."""

import sys
import json
import subprocess
from pathlib import Path

def run(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def load_events_json(workspace: Path):
    p = workspace / "skills" / "olympic-alert" / "scripts" / "events.json"
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def main():
    workspace = Path(sys.argv[1])
    skill_dir = workspace / "skills" / "olympic-alert"
    script = skill_dir / "scripts" / "check_olympic.py"
    checks = []

    # ── CHECK 1: events.json is valid JSON and country is Norway ────────────
    try:
        data = load_events_json(workspace)
        c1_pass = data.get("country", "").lower() == "norway"
        checks.append({
            "name": "country_set_to_norway",
            "passed": c1_pass,
            "detail": f"country = '{data.get('country')}' (expected 'Norway')"
        })
    except Exception as e:
        checks.append({"name": "country_set_to_norway", "passed": False, "detail": str(e)})
        data = None

    # ── CHECK 2: flag is Norwegian flag emoji ────────────────────────────────
    try:
        data = data or load_events_json(workspace)
        c2_pass = data.get("flag", "") == "🇳🇴"
        checks.append({
            "name": "flag_set_to_norway",
            "passed": c2_pass,
            "detail": f"flag = '{data.get('flag')}' (expected '🇳🇴')"
        })
    except Exception as e:
        checks.append({"name": "flag_set_to_norway", "passed": False, "detail": str(e)})

    # ── CHECK 3: links updated (no Korean links remain) ───────────────────────
    try:
        data = load_events_json(workspace)
        links = data.get("links", {})
        korean_links = [v for v in links.values()
                        if "naver.com" in v or "chzzk" in v]
        has_norway_links = len(links) >= 1 and len(korean_links) == 0
        checks.append({
            "name": "links_updated_no_korean",
            "passed": has_norway_links,
            "detail": f"links = {links}; korean_links_found = {korean_links}"
        })
    except Exception as e:
        checks.append({"name": "links_updated_no_korean", "passed": False, "detail": str(e)})

    # ── CHECK 4: Korean default events are gone ───────────────────────────────
    try:
        data = load_events_json(workspace)
        events = data.get("events", [])
        korean_athletes = ["최민정", "차준환", "김보름"]
        remaining_korean = [e for e in events if any(a in e.get("athletes", "") for a in korean_athletes)]
        c4_pass = len(remaining_korean) == 0
        checks.append({
            "name": "korean_default_events_removed",
            "passed": c4_pass,
            "detail": f"Remaining Korean events: {remaining_korean}"
        })
    except Exception as e:
        checks.append({"name": "korean_default_events_removed", "passed": False, "detail": str(e)})

    # ── CHECK 5: At least 2 Norwegian events added with correct schema ────────
    try:
        data = load_events_json(workspace)
        events = data.get("events", [])
        valid_events = []
        for ev in events:
            has_keys = all(k in ev for k in ("time", "name", "athletes"))
            if not has_keys:
                continue
            try:
                from datetime import datetime
                datetime.strptime(ev["time"], "%Y-%m-%d %H:%M")
                valid_events.append(ev)
            except ValueError:
                pass
        c5_pass = len(valid_events) >= 2
        checks.append({
            "name": "at_least_two_valid_norway_events",
            "passed": c5_pass,
            "detail": f"{len(valid_events)} valid events found (need >= 2); events: {events}"
        })
    except Exception as e:
        checks.append({"name": "at_least_two_valid_norway_events", "passed": False, "detail": str(e)})

    # ── CHECK 6: `list` command works and outputs Norway flag/country ─────────
    try:
        out, err, rc = run(
            f"python3 {script} list",
            cwd=str(skill_dir)
        )
        c6_pass = "🇳🇴" in out or "Norway" in out
        checks.append({
            "name": "list_command_shows_norway",
            "passed": c6_pass,
            "detail": f"stdout: {out!r} | stderr: {err!r}"
        })
    except Exception as e:
        checks.append({"name": "list_command_shows_norway", "passed": False, "detail": str(e)})

    # ── CHECK 7: Biathlon event present (Norway's iconic sport) ──────────────
    try:
        data = load_events_json(workspace)
        events = data.get("events", [])
        has_biathlon = any("biathlon" in e.get("name", "").lower() or
                           "바이애슬론" in e.get("name", "") or
                           "Biathlon" in e.get("name", "")
                           for e in events)
        checks.append({
            "name": "biathlon_event_present",
            "passed": has_biathlon,
            "detail": f"Events names: {[e.get('name') for e in events]}"
        })
    except Exception as e:
        checks.append({"name": "biathlon_event_present", "passed": False, "detail": str(e)})

    # ── CHECK 8: `add` subcommand was used (verify via a round-trip add+list) ──
    # We test idempotently: add a test event using the script, verify it appears
    try:
        add_out, add_err, add_rc = run(
            f'python3 {script} add "2026-02-20 10:00" "🎿 Nordic Combined Test" "Test Athlete"',
            cwd=str(skill_dir)
        )
        added = "추가됨" in add_out
        # verify it's in the list now
        data2 = load_events_json(workspace)
        in_file = any("Nordic Combined Test" in e.get("name", "") for e in data2.get("events", []))
        # clean up the test event
        run(f'python3 {script} remove "Nordic Combined Test"', cwd=str(skill_dir))
        c8_pass = added and in_file
        checks.append({
            "name": "add_subcommand_functional",
            "passed": c8_pass,
            "detail": f"add stdout: {add_out!r}; in_file: {in_file}; add_rc: {add_rc}; add_err: {add_err!r}"
        })
    except Exception as e:
        checks.append({"name": "add_subcommand_functional", "passed": False, "detail": str(e)})

    # ── CHECK 9: `remove` subcommand was used (pattern-based removal) ─────────
    # Verify remove works: add a dummy event, remove it, confirm gone
    try:
        run(f'python3 {script} add "2026-02-21 11:00" "🏒 DummyRemoveTest" "Nobody"',
            cwd=str(skill_dir))
        rm_out, rm_err, rm_rc = run(
            f'python3 {script} remove "DummyRemoveTest"',
            cwd=str(skill_dir)
        )
        data3 = load_events_json(workspace)
        still_there = any("DummyRemoveTest" in e.get("name", "") for e in data3.get("events", []))
        c9_pass = "삭제됨" in rm_out and not still_there
        checks.append({
            "name": "remove_subcommand_functional",
            "passed": c9_pass,
            "detail": f"remove stdout: {rm_out!r}; still_there: {still_there}; rc: {rm_rc}"
        })
    except Exception as e:
        checks.append({"name": "remove_subcommand_functional", "passed": False, "detail": str(e)})

    # ── CHECK 10: events.json has correct top-level schema keys ───────────────
    try:
        data = load_events_json(workspace)
        required_keys = {"country", "flag", "links", "events"}
        present = set(data.keys())
        c10_pass = required_keys.issubset(present)
        checks.append({
            "name": "events_json_schema_correct",
            "passed": c10_pass,
            "detail": f"Keys present: {sorted(present)}; required: {sorted(required_keys)}"
        })
    except Exception as e:
        checks.append({"name": "events_json_schema_correct", "passed": False, "detail": str(e)})

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    overall_passed = passed_count >= 7  # require at least 7/10

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()