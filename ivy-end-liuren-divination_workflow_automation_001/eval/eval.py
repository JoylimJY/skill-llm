import sys
import json
import subprocess
import os
from pathlib import Path

def run_liuren(workspace, datetime_str):
    """Run liuren.js with a given datetime and return parsed JSON output."""
    script = os.path.join(workspace, "liuren.js")
    result = subprocess.run(
        ["node", script, datetime_str],
        capture_output=True, text=True, timeout=15
    )
    if result.returncode != 0:
        raise RuntimeError(f"liuren.js failed: {result.stderr}")
    return json.loads(result.stdout)

def main():
    workspace = sys.argv[1]
    checks = []
    total_score = 0.0

    # ── Find the output file ──────────────────────────────────────────────────
    report_files = list(Path(workspace).rglob("divination_report.json"))
    file_found = len(report_files) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found {len(report_files)} file(s) named divination_report.json" if file_found else "divination_report.json not found anywhere in workspace"
    })
    if not file_found:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    report_path = report_files[0]

    # ── Parse the agent's report ──────────────────────────────────────────────
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            agent_report = json.load(f)
        checks.append({"name": "report_is_valid_json", "passed": True, "detail": str(report_path)})
        total_score += 0.5
    except Exception as e:
        checks.append({"name": "report_is_valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ── Verify report is a list / dict with 5 entries ─────────────────────────
    # Accept both a list of 5 entries OR a dict with a key containing 5 entries
    entries = None
    if isinstance(agent_report, list):
        entries = agent_report
    elif isinstance(agent_report, dict):
        # Try common wrapper keys
        for key in ["results", "divinations", "slots", "consultations", "data", "report"]:
            if key in agent_report and isinstance(agent_report[key], list):
                entries = agent_report[key]
                break
        if entries is None:
            # maybe it's a dict keyed by slot id
            # try to collect all dict values that are dicts themselves
            vals = [v for v in agent_report.values() if isinstance(v, dict)]
            if len(vals) == 5:
                entries = vals

    five_entries = entries is not None and len(entries) == 5
    checks.append({
        "name": "report_has_five_entries",
        "passed": five_entries,
        "detail": f"Found {len(entries) if entries is not None else 'N/A'} entries (expected 5)"
    })
    if not five_entries:
        print(json.dumps({"passed": False, "score": total_score, "checks": checks}))
        return
    total_score += 0.5

    # ── The 5 consultation slots ──────────────────────────────────────────────
    slots = [
        {"slot_id": "S001", "client": "Zhang Wei",   "datetime": "2025-03-15 09:30"},
        {"slot_id": "S002", "client": "Li Fang",     "datetime": "2025-06-21 14:00"},
        {"slot_id": "S003", "client": "Wang Hao",    "datetime": "2025-09-09 23:15"},
        {"slot_id": "S004", "client": "Chen Mei",    "datetime": "2025-11-01 06:45"},
        {"slot_id": "S005", "client": "Zhao Qiang",  "datetime": "2025-12-22 18:55"},
    ]

    # ── Generate ground truth by running liuren.js for each slot ─────────────
    ground_truth = {}
    for slot in slots:
        try:
            gt = run_liuren(workspace, slot["datetime"])
            ground_truth[slot["slot_id"]] = gt
        except Exception as e:
            checks.append({
                "name": f"ground_truth_{slot['slot_id']}",
                "passed": False,
                "detail": f"Could not generate ground truth for {slot['slot_id']}: {e}"
            })
            print(json.dumps({"passed": False, "score": total_score, "checks": checks}))
            return

    # ── Match agent entries against ground truth ───────────────────────────────
    def extract_text(obj, *keys):
        """Recursively search for any of the keys, case-insensitive."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.lower() in [key.lower() for key in keys]:
                    return v
                result = extract_text(v, *keys)
                if result is not None:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = extract_text(item, *keys)
                if result is not None:
                    return result
        return None

    per_slot_score = 1.5 / 5  # 1.5 points total for all 5 slots
    matched_slots = 0

    for slot in slots:
        sid = slot["slot_id"]
        gt = ground_truth[sid]
        gt_seq = gt.get("sequence", {})
        gt_month = gt_seq.get("month_palace", {})
        gt_day   = gt_seq.get("day_palace",   {})
        gt_hour  = gt_seq.get("hour_palace",  {})

        # Try to find the corresponding agent entry
        agent_entry = None
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            entry_str = json.dumps(entry, ensure_ascii=False)
            # Match by slot_id, client name, or datetime
            if (sid in entry_str or
                slot["client"] in entry_str or
                slot["datetime"] in entry_str or
                slot["datetime"].replace(" ", "T") in entry_str):
                agent_entry = entry
                break

        if agent_entry is None:
            checks.append({
                "name": f"slot_{sid}_found",
                "passed": False,
                "detail": f"No entry found in report matching slot {sid} ({slot['client']} @ {slot['datetime']})"
            })
            continue

        entry_str = json.dumps(agent_entry, ensure_ascii=False)

        # Check all three palace names are present
        month_ok = gt_month["name"] in entry_str
        day_ok   = gt_day["name"]   in entry_str
        hour_ok  = gt_hour["name"]  in entry_str

        # Check hour_palace meaning is present (proprietary: only hour_palace has meaning)
        meaning_ok = gt_hour["meaning"] in entry_str

        slot_passed = month_ok and day_ok and hour_ok
        detail_parts = []
        if not month_ok:
            detail_parts.append(f"month_palace expected '{gt_month['name']}'")
        if not day_ok:
            detail_parts.append(f"day_palace expected '{gt_day['name']}'")
        if not hour_ok:
            detail_parts.append(f"hour_palace expected '{gt_hour['name']}'")
        if not meaning_ok:
            detail_parts.append(f"hour_palace meaning missing")

        checks.append({
            "name": f"slot_{sid}_palaces_correct",
            "passed": slot_passed,
            "detail": (
                f"month={gt_month['name']}({'✓' if month_ok else '✗'}) "
                f"day={gt_day['name']}({'✓' if day_ok else '✗'}) "
                f"hour={gt_hour['name']}({'✓' if hour_ok else '✗'}) "
                f"meaning={'✓' if meaning_ok else '✗'}"
                + (f" | ERRORS: {'; '.join(detail_parts)}" if detail_parts else "")
            )
        })

        checks.append({
            "name": f"slot_{sid}_hour_meaning_present",
            "passed": meaning_ok,
            "detail": f"hour_palace meaning for {sid}: {'present' if meaning_ok else 'MISSING'}"
        })

        if slot_passed:
            matched_slots += 1
            total_score += per_slot_score

    # ── Bonus: check lunar_approx and earthly_branch are present for at least 3 slots ──
    approx_count = 0
    branch_count = 0
    for slot in slots:
        sid = slot["slot_id"]
        gt = ground_truth[sid]
        tt = gt.get("target_time", {})
        lunar_approx = tt.get("lunar_approx", "")
        branch = tt.get("earthly_branch", "")
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            entry_str = json.dumps(entry, ensure_ascii=False)
            if (sid in entry_str or slot["client"] in entry_str or slot["datetime"] in entry_str):
                if lunar_approx and lunar_approx in entry_str:
                    approx_count += 1
                if branch and branch in entry_str:
                    branch_count += 1
                break

    lunar_bonus = approx_count >= 3
    branch_bonus = branch_count >= 3
    if lunar_bonus:
        total_score += 0.25
    if branch_bonus:
        total_score += 0.25

    checks.append({
        "name": "lunar_approx_in_report",
        "passed": lunar_bonus,
        "detail": f"lunar_approx present for {approx_count}/5 slots (need ≥3)"
    })
    checks.append({
        "name": "earthly_branch_in_report",
        "passed": branch_bonus,
        "detail": f"earthly_branch present for {branch_count}/5 slots (need ≥3)"
    })

    # ── Final verdict ──────────────────────────────────────────────────────────
    total_score = min(total_score, 3.0)
    normalized = round(total_score / 3.0, 4)
    all_critical = (
        file_found and
        five_entries and
        matched_slots == 5
    )

    print(json.dumps({
        "passed": all_critical,
        "score": normalized,
        "checks": checks
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()