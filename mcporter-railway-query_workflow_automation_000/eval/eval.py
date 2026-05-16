#!/usr/bin/env python3
import sys
import json
from pathlib import Path

def main(workspace):
    checks = []
    total_score = 0.0
    weights = {
        "file_exists": 0.10,
        "valid_json": 0.10,
        "correct_count": 0.20,
        "only_gd_trains": 0.20,
        "time_window": 0.20,
        "sorted_by_duration": 0.20,
    }

    def check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # ── Locate the output file ─────────────────────────────────────────────
    workspace_path = Path(workspace)
    found_files = list(workspace_path.rglob("rail_options.json"))

    file_ok = check(
        "file_exists",
        len(found_files) >= 1,
        f"Found {len(found_files)} file(s) named 'rail_options.json'" if found_files else "rail_options.json not found anywhere in workspace"
    )
    if file_ok:
        total_score += weights["file_exists"]

    if not file_ok:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    target_file = found_files[0]

    # ── Parse JSON ─────────────────────────────────────────────────────────
    try:
        raw = target_file.read_text(encoding="utf-8")
        data = json.loads(raw)
        valid_json = check("valid_json", True, f"Valid JSON parsed from {target_file}")
        total_score += weights["valid_json"]
    except Exception as e:
        check("valid_json", False, f"JSON parse error: {e}")
        check("correct_count", False, "Cannot check — invalid JSON")
        check("only_gd_trains", False, "Cannot check — invalid JSON")
        check("time_window", False, "Cannot check — invalid JSON")
        check("sorted_by_duration", False, "Cannot check — invalid JSON")
        print(json.dumps({"passed": False, "score": total_score, "checks": checks}))
        return

    # ── Extract trains list ────────────────────────────────────────────────
    # Accept either {"trains": [...]} or a direct list [...]
    trains = None
    if isinstance(data, dict) and "trains" in data:
        trains = data["trains"]
    elif isinstance(data, list):
        trains = data
    else:
        # Try to find a list value in the dict
        for v in data.values():
            if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                trains = v
                break

    if trains is None:
        check("correct_count", False, f"Could not find a list of trains in the JSON. Keys found: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
        check("only_gd_trains", False, "Cannot check — no trains list")
        check("time_window", False, "Cannot check — no trains list")
        check("sorted_by_duration", False, "Cannot check — no trains list")
        print(json.dumps({"passed": False, "score": total_score, "checks": checks}))
        return

    # ── Check 1: Exactly 3 results ─────────────────────────────────────────
    count_ok = check(
        "correct_count",
        len(trains) == 3,
        f"Expected exactly 3 trains (limitedNum=3), got {len(trains)}"
    )
    if count_ok:
        total_score += weights["correct_count"]

    # ── Check 2: Only G or D trains ────────────────────────────────────────
    def get_train_type(t):
        # trainType field, or infer from trainNo prefix
        if "trainType" in t:
            return str(t["trainType"]).upper()
        train_no = str(t.get("trainNo", ""))
        for prefix in ["G", "D", "K", "Z", "T"]:
            if train_no.startswith(prefix):
                return prefix
        return "UNKNOWN"

    types = [get_train_type(t) for t in trains]
    bad_types = [tp for tp in types if tp not in ("G", "D")]
    gd_ok = check(
        "only_gd_trains",
        len(bad_types) == 0,
        f"All trains are G or D: {types}" if not bad_types else f"Non-GD trains found: {bad_types} in {types}"
    )
    if gd_ok:
        total_score += weights["only_gd_trains"]

    # ── Check 3: Time window 18:00-23:00 ──────────────────────────────────
    def parse_hour(t):
        st = t.get("startTime", "")
        if not st:
            return None
        try:
            h, m = st.split(":")
            return int(h) + int(m) / 60.0
        except Exception:
            return None

    hours = [parse_hour(t) for t in trains]
    outside = [(trains[i].get("startTime"), h) for i, h in enumerate(hours) if h is not None and not (18.0 <= h < 23.0)]
    time_ok = check(
        "time_window",
        len(outside) == 0 and all(h is not None for h in hours),
        f"All departure times within 18:00-23:00: {[t.get('startTime') for t in trains]}" if not outside else f"Trains outside 18:00-23:00 window: {outside}"
    )
    if time_ok:
        total_score += weights["time_window"]

    # ── Check 4: Sorted by duration ascending ─────────────────────────────
    def get_duration(t):
        # Accept durationMinutes or duration field
        for key in ("durationMinutes", "duration", "durationMins"):
            if key in t:
                try:
                    return int(t[key])
                except (ValueError, TypeError):
                    pass
        # Try to compute from startTime and arriveTime if both present
        return None

    durations = [get_duration(t) for t in trains]
    if all(d is not None for d in durations):
        is_sorted_asc = all(durations[i] <= durations[i + 1] for i in range(len(durations) - 1))
        sort_ok = check(
            "sorted_by_duration",
            is_sorted_asc,
            f"Durations (ascending expected): {durations}" if is_sorted_asc else f"NOT sorted by duration ascending: {durations}"
        )
    else:
        # Check by train order known from mock data (G7007=126, G7009=125, G7011=122 min — sorted asc: G7011, G7009, G7007)
        # Expected correct answer after filtering 18-23 GD trains and sorting by duration:
        # G7007 (18:05, 126min), G7009 (20:00, 125min), G7011 (21:30, 122min), D3055 (19:22, 203min)
        # Sorted asc by duration, limit 3: G7011(122), G7009(125), G7007(126)
        train_nos = [t.get("trainNo", "") for t in trains]
        expected_order = ["G7011", "G7009", "G7007"]
        sort_ok = check(
            "sorted_by_duration",
            train_nos == expected_order,
            f"Train order (expected G7011,G7009,G7007 by duration asc): got {train_nos}"
        )
    if sort_ok:
        total_score += weights["sorted_by_duration"]

    # ── Final verdict ──────────────────────────────────────────────────────
    all_passed = all(c["passed"] for c in checks)
    print(json.dumps({
        "passed": all_passed,
        "score": round(total_score, 3),
        "checks": checks
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    main(sys.argv[1])