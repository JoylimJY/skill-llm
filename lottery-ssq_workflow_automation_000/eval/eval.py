import sys
import json
import os
import glob
from pathlib import Path

workspace = sys.argv[1]
base = os.path.join(workspace, "lottery-ssq")

checks = []
total_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ── Check 1: config.json has strategy=aggressive ──────────────────────────────
try:
    config_path = os.path.join(base, "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    strategy = cfg.get("strategy", "")
    passed = (strategy == "aggressive")
    total_score += add_check(
        "config_strategy_aggressive",
        passed,
        f"config.json strategy={strategy!r}, expected 'aggressive'",
        weight=1.5
    )
except Exception as e:
    total_score += add_check("config_strategy_aggressive", False, f"Exception reading config.json: {e}", weight=1.5)

# ── Check 2: data was updated (more rows than original 3420) ──────────────────
try:
    import csv
    data_path = os.path.join(base, "data", "ssq_history.csv")
    with open(data_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    row_count = len(rows)
    passed = row_count > 3420
    total_score += add_check(
        "history_data_updated",
        passed,
        f"History rows={row_count}, expected >3420 (update script should have added at least 1 row)",
        weight=1.0
    )
except Exception as e:
    total_score += add_check("history_data_updated", False, f"Exception reading ssq_history.csv: {e}", weight=1.0)

# ── Check 3: outputs/ directory has at least one ssq_*.json file ──────────────
try:
    output_dir = os.path.join(base, "outputs")
    output_files = sorted(glob.glob(os.path.join(output_dir, "ssq_*.json")))
    passed = len(output_files) > 0
    total_score += add_check(
        "output_file_exists",
        passed,
        f"Found {len(output_files)} output file(s) in outputs/: {[os.path.basename(f) for f in output_files]}",
        weight=1.0
    )
    latest_output = output_files[-1] if output_files else None
except Exception as e:
    total_score += add_check("output_file_exists", False, f"Exception scanning outputs/: {e}", weight=1.0)
    latest_output = None

# ── Check 4: output JSON has correct structure (2 main + 3 backup) ────────────
try:
    if latest_output:
        with open(latest_output, "r", encoding="utf-8") as f:
            sel = json.load(f)
        main_picks = sel.get("main_picks", [])
        backup_picks = sel.get("backup_picks", [])
        main_ok = len(main_picks) == 2
        backup_ok = len(backup_picks) == 3
        passed = main_ok and backup_ok
        total_score += add_check(
            "output_structure_2plus3",
            passed,
            f"main_picks={len(main_picks)} (expected 2), backup_picks={len(backup_picks)} (expected 3)",
            weight=2.0
        )
    else:
        total_score += add_check("output_structure_2plus3", False, "No output file to check", weight=2.0)
except Exception as e:
    total_score += add_check("output_structure_2plus3", False, f"Exception reading output JSON: {e}", weight=2.0)

# ── Check 5: output strategy field is aggressive ──────────────────────────────
try:
    if latest_output:
        with open(latest_output, "r", encoding="utf-8") as f:
            sel = json.load(f)
        out_strategy = sel.get("strategy", "")
        passed = (out_strategy == "aggressive")
        total_score += add_check(
            "output_strategy_aggressive",
            passed,
            f"Output file strategy={out_strategy!r}, expected 'aggressive'",
            weight=1.5
        )
    else:
        total_score += add_check("output_strategy_aggressive", False, "No output file to check", weight=1.5)
except Exception as e:
    total_score += add_check("output_strategy_aggressive", False, f"Exception: {e}", weight=1.5)

# ── Check 6: each pick has required fields (reds, blue, score, ac, span) ──────
try:
    if latest_output:
        with open(latest_output, "r", encoding="utf-8") as f:
            sel = json.load(f)
        all_picks = sel.get("main_picks", []) + sel.get("backup_picks", [])
        required_fields = {"reds", "blue", "score", "ac", "span", "odd_even", "sum"}
        field_errors = []
        for i, pick in enumerate(all_picks):
            missing = required_fields - set(pick.keys())
            if missing:
                field_errors.append(f"pick#{i+1} missing: {missing}")
            # validate reds: 6 unique numbers 1-33
            reds = pick.get("reds", [])
            if len(reds) != 6 or len(set(reds)) != 6:
                field_errors.append(f"pick#{i+1} invalid reds count: {reds}")
            if not all(1 <= r <= 33 for r in reds):
                field_errors.append(f"pick#{i+1} reds out of range: {reds}")
            blue = pick.get("blue", 0)
            if not (1 <= blue <= 16):
                field_errors.append(f"pick#{i+1} blue out of range: {blue}")
        passed = len(field_errors) == 0
        total_score += add_check(
            "pick_fields_valid",
            passed,
            f"Field validation: {field_errors if field_errors else 'all OK'}",
            weight=1.5
        )
    else:
        total_score += add_check("pick_fields_valid", False, "No output file to check", weight=1.5)
except Exception as e:
    total_score += add_check("pick_fields_valid", False, f"Exception: {e}", weight=1.5)

# ── Check 7: backtests/ directory has at least one backtest_*.json ─────────────
try:
    backtest_dir = os.path.join(base, "backtests")
    bt_files = sorted(glob.glob(os.path.join(backtest_dir, "backtest_*.json")))
    passed = len(bt_files) > 0
    total_score += add_check(
        "backtest_file_exists",
        passed,
        f"Found {len(bt_files)} backtest file(s): {[os.path.basename(f) for f in bt_files]}",
        weight=1.0
    )
    latest_bt = bt_files[-1] if bt_files else None
except Exception as e:
    total_score += add_check("backtest_file_exists", False, f"Exception scanning backtests/: {e}", weight=1.0)
    latest_bt = None

# ── Check 8: backtest file has correct structure ──────────────────────────────
try:
    if latest_bt:
        with open(latest_bt, "r", encoding="utf-8") as f:
            bt = json.load(f)
        required_bt_fields = {"strategy", "tested_issues", "total_picks", "prize_summary"}
        missing_bt = required_bt_fields - set(bt.keys())
        bt_strategy = bt.get("strategy", "")
        passed = len(missing_bt) == 0 and bt_strategy == "aggressive"
        total_score += add_check(
            "backtest_structure_valid",
            passed,
            f"Backtest missing_fields={missing_bt}, strategy={bt_strategy!r}",
            weight=1.0
        )
    else:
        total_score += add_check("backtest_structure_valid", False, "No backtest file to check", weight=1.0)
except Exception as e:
    total_score += add_check("backtest_structure_valid", False, f"Exception reading backtest JSON: {e}", weight=1.0)

# ── Scoring ────────────────────────────────────────────────────────────────────
max_score = 1.5 + 1.0 + 1.0 + 2.0 + 1.5 + 1.5 + 1.0 + 1.0  # = 10.5
normalized = round(total_score / max_score, 4)
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": normalized,
    "checks": checks
}
print(json.dumps(result, ensure_ascii=False, indent=2))