import sys
import json
import os
import re
from pathlib import Path

def compute_expected(hour: int, minute: int):
    upper_raw = hour % 8
    upper = 8 if upper_raw == 0 else upper_raw
    lower_raw = minute % 8
    lower = 8 if lower_raw == 0 else lower_raw
    yao_raw = (hour + minute) % 6
    yao = 6 if yao_raw == 0 else yao_raw
    return upper, lower, yao

def parse_datetime(dt_str: str):
    """Parse YYYY-MM-DD HH:MM, return (hour, minute) or None if invalid."""
    if not dt_str or not isinstance(dt_str, str):
        return None
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})$', dt_str.strip())
    if not m:
        return None
    hour = int(m.group(4))
    minute = int(m.group(5))
    if hour > 23 or minute > 59:
        return None
    return hour, minute

# Ground truth for each session
SESSIONS = [
    ("C001", "2024-11-05 09:15"),
    ("C002", "2024-11-05 14:32"),
    ("C003", "2024-11-06 16:45"),
    ("C004", "2024-11-06 08:00"),
    ("C005", "2024-11-07 23:59"),
    ("C006", "2024-11-07 12:24"),
    ("C007", "2024-11-08 03:03"),
    ("C008", "2024-11-08 00:48"),
    ("C009", "2024-11-09 17:08"),
    ("C010", "2024-11-09 06:12"),
]
INVALID_IDS = {"C011", "C012", "C013", "C014", "C015"}

def main(workspace: str):
    checks = []
    total_score = 0.0

    # ── Find output file ──────────────────────────────────────────────────────
    output_files = list(Path(workspace).rglob("divination_report.json"))
    if not output_files:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": "divination_report.json not found anywhere in workspace"
        })
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    output_file = output_files[0]
    checks.append({
        "name": "output_file_exists",
        "passed": True,
        "detail": f"Found at {output_file}"
    })

    # ── Load JSON ─────────────────────────────────────────────────────────────
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        checks.append({
            "name": "json_parseable",
            "passed": False,
            "detail": f"Could not parse JSON: {e}"
        })
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "json_parseable", "passed": True, "detail": "JSON loaded successfully"})

    # ── Check that invalid sessions are excluded ───────────────────────────────
    if isinstance(data, list):
        result_ids = {str(item.get("session_id", "")) for item in data if isinstance(item, dict)}
    elif isinstance(data, dict):
        # Maybe it's keyed by session_id
        result_ids = set(data.keys())
    else:
        checks.append({"name": "data_structure", "passed": False, "detail": f"Unexpected JSON root type: {type(data)}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    invalid_included = result_ids & INVALID_IDS
    invalid_excluded_check = len(invalid_included) == 0
    checks.append({
        "name": "invalid_sessions_excluded",
        "passed": invalid_excluded_check,
        "detail": f"Invalid sessions found in output: {invalid_included}" if not invalid_excluded_check else "All malformed sessions correctly excluded"
    })
    if invalid_excluded_check:
        total_score += 10.0

    # ── Check count of valid sessions ─────────────────────────────────────────
    expected_valid_count = len(SESSIONS)
    if isinstance(data, list):
        actual_count = len(data)
    else:
        actual_count = len(data)

    count_check = actual_count == expected_valid_count
    checks.append({
        "name": "valid_session_count",
        "passed": count_check,
        "detail": f"Expected {expected_valid_count} valid sessions, got {actual_count}"
    })
    if count_check:
        total_score += 10.0

    # ── Helper to get a session's data ────────────────────────────────────────
    def get_session(sid):
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and str(item.get("session_id", "")) == sid:
                    return item
            return None
        elif isinstance(data, dict):
            return data.get(sid)
        return None

    # ── Per-session proprietary logic checks ──────────────────────────────────
    # Key sessions that test the "0 → max" edge case:
    edge_case_sessions = {
        # upper=0→8 trap
        "C003": ("2024-11-06 16:45", "upper trigram 0→8 trap (16%8=0)"),
        "C004": ("2024-11-06 08:00", "both upper and lower 0→8 trap"),
        "C008": ("2024-11-08 00:48", "all three 0→max trap"),
        # lower=0→8 trap
        "C002": ("2024-11-05 14:32", "lower trigram 0→8 trap (32%8=0)"),
        "C006": ("2024-11-07 12:24", "lower 0→8 + yao 0→6"),
        # yao=0→6 trap
        "C001": ("2024-11-05 09:15", "yao 0→6 trap (9+15=24, 24%6=0)"),
        "C005": ("2024-11-07 23:59", "yao 0→6 trap (23+59=82, 82%6=4… actually 82%6=4)"),
    }

    per_session_score = 0.0
    for sid, dt_str in SESSIONS:
        parsed = parse_datetime(dt_str)
        if parsed is None:
            continue
        hour, minute = parsed
        exp_upper, exp_lower, exp_yao = compute_expected(hour, minute)

        session_data = get_session(sid)
        if session_data is None:
            checks.append({
                "name": f"session_{sid}_present",
                "passed": False,
                "detail": f"Session {sid} not found in output"
            })
            continue

        # Extract values — try multiple key conventions
        def extract_int(d, *keys):
            for k in keys:
                v = d.get(k)
                if v is not None:
                    try:
                        return int(v)
                    except:
                        pass
            return None

        if isinstance(session_data, dict):
            got_upper = extract_int(session_data, "upper_trigram", "upper", "上卦", "shangua")
            got_lower = extract_int(session_data, "lower_trigram", "lower", "下卦", "xiagua")
            got_yao   = extract_int(session_data, "moving_line", "yao", "动爻", "dongyao", "moving_yao")
        else:
            checks.append({
                "name": f"session_{sid}_structure",
                "passed": False,
                "detail": f"Session {sid} data is not a dict: {type(session_data)}"
            })
            continue

        upper_ok = (got_upper == exp_upper)
        lower_ok = (got_lower == exp_lower)
        yao_ok   = (got_yao == exp_yao)
        session_ok = upper_ok and lower_ok and yao_ok

        detail_parts = []
        if not upper_ok:
            detail_parts.append(f"upper_trigram: expected {exp_upper}, got {got_upper}")
        if not lower_ok:
            detail_parts.append(f"lower_trigram: expected {exp_lower}, got {got_lower}")
        if not yao_ok:
            detail_parts.append(f"moving_yao: expected {exp_yao}, got {got_yao}")

        checks.append({
            "name": f"session_{sid}_values",
            "passed": session_ok,
            "detail": f"{dt_str} (h={hour},m={minute}) → upper={exp_upper},lower={exp_lower},yao={exp_yao}. " +
                      ("CORRECT" if session_ok else " | ".join(detail_parts))
        })
        if session_ok:
            per_session_score += 8.0

    total_score += per_session_score

    # ── Specific edge-case checks (the "proprietary trap") ────────────────────
    edge_cases = [
        # (session_id, description, expected_upper, expected_lower, expected_yao)
        ("C003", "hour=16: 16%8=0→upper must be 8 (not 0)", 8, 5, 5),
        ("C004", "hour=8,min=0: both must be 8 (not 0)", 8, 8, 2),
        ("C008", "hour=0,min=48: upper=8,lower=8,yao=6", 8, 8, 6),
        ("C002", "min=32: 32%8=0→lower must be 8 (not 0)", 6, 8, 4),
        ("C001", "h=9,m=15: (9+15)%6=0→yao must be 6 (not 0)", 1, 7, 6),
    ]

    edge_score = 0.0
    for sid, desc, exp_u, exp_l, exp_y in edge_cases:
        sd = get_session(sid)
        if sd is None or not isinstance(sd, dict):
            checks.append({"name": f"edge_case_{sid}", "passed": False, "detail": f"{desc} — session not found"})
            continue
        def ei(d, *keys):
            for k in keys:
                v = d.get(k)
                if v is not None:
                    try: return int(v)
                    except: pass
            return None
        gu = ei(sd, "upper_trigram","upper","上卦","shangua")
        gl = ei(sd, "lower_trigram","lower","下卦","xiagua")
        gy = ei(sd, "moving_line","yao","动爻","dongyao","moving_yao")
        ok = (gu == exp_u and gl == exp_l and gy == exp_y)
        checks.append({
            "name": f"edge_case_{sid}",
            "passed": ok,
            "detail": f"{desc}. Expected u={exp_u},l={exp_l},y={exp_y}. Got u={gu},l={gl},y={gy}"
        })
        if ok:
            edge_score += 4.0

    total_score += edge_score

    # ── Final verdict ─────────────────────────────────────────────────────────
    max_score = 10.0 + 10.0 + (len(SESSIONS) * 8.0) + (len(edge_cases) * 4.0)
    # max = 10+10+80+20 = 120 → normalize to 0..1
    normalized = min(total_score / max_score, 1.0)

    # Must pass: invalid excluded, correct count, and at least 7/10 sessions correct, all edge cases
    critical_passed = (
        invalid_excluded_check and
        count_check and
        (per_session_score >= 56.0) and  # at least 7 sessions
        (edge_score >= 16.0)             # at least 4/5 edge cases
    )

    print(json.dumps({
        "passed": critical_passed,
        "score": round(normalized, 3),
        "checks": checks
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    main(workspace)