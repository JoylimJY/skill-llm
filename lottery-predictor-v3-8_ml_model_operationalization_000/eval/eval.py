import sys
import os
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
total_score = 0.0
max_score = 0.0


def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global total_score, max_score
    max_score += weight
    if passed:
        total_score += weight


# ── Helper ────────────────────────────────────────────────────────────────────
def find_file(pattern):
    """Search recursively for a file matching a glob pattern."""
    results = list(workspace.rglob(pattern))
    return results[0] if results else None


# ══════════════════════════════════════════════════════════════════════════════
# CHECK 1: Prediction output file exists
# ══════════════════════════════════════════════════════════════════════════════
pred_file = find_file("prediction_result.txt")
if pred_file is None:
    # Also accept common alternative names
    for alt in ["prediction.txt", "v3.8_prediction.txt", "predict_result.txt", "output_prediction.txt"]:
        pred_file = find_file(alt)
        if pred_file:
            break

add_check(
    "prediction_output_exists",
    pred_file is not None,
    f"Found prediction file at: {pred_file}" if pred_file else "No prediction output file found (expected prediction_result.txt or similar)",
    weight=1.5
)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 2: Prediction output contains V3.8 header
# ══════════════════════════════════════════════════════════════════════════════
pred_content = ""
if pred_file:
    try:
        pred_content = pred_file.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        pred_content = ""
        add_check("prediction_readable", False, f"Could not read prediction file: {e}", weight=0.5)

has_v38_header = "V3.8" in pred_content and "预测结果" in pred_content
add_check(
    "prediction_has_v38_header",
    has_v38_header,
    f"V3.8 header found: {has_v38_header}. Content snippet: {pred_content[:200] if pred_content else 'EMPTY'}",
    weight=1.5
)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 3: Prediction contains exactly 6 valid red balls (01-33)
# ══════════════════════════════════════════════════════════════════════════════
red_balls_found = []
blue_ball_found = None

if pred_content:
    # Match 【红球推荐】XX, XX, XX, XX, XX, XX
    red_match = re.search(r'【红球推荐】\s*([\d,\s]+)', pred_content)
    blue_match = re.search(r'【蓝球推荐】\s*(\d+)', pred_content)

    if red_match:
        red_str = red_match.group(1)
        red_balls_found = [int(x.strip()) for x in red_str.split(',') if x.strip().isdigit()]

    if blue_match:
        blue_ball_found = int(blue_match.group(1))

exactly_6_reds = len(red_balls_found) == 6
all_reds_valid = all(1 <= r <= 33 for r in red_balls_found)
reds_unique = len(set(red_balls_found)) == 6

add_check(
    "prediction_exactly_6_red_balls",
    exactly_6_reds and all_reds_valid and reds_unique,
    f"Red balls: {red_balls_found} - count={len(red_balls_found)}, valid={all_reds_valid}, unique={reds_unique}",
    weight=2.0
)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 4: Prediction contains valid blue ball (01-16)
# ══════════════════════════════════════════════════════════════════════════════
blue_valid = blue_ball_found is not None and 1 <= blue_ball_found <= 16
add_check(
    "prediction_valid_blue_ball",
    blue_valid,
    f"Blue ball: {blue_ball_found} - valid range 1-16: {blue_valid}",
    weight=1.5
)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 5: Prediction mentions ML models (RandomForest + GradientBoosting)
# ══════════════════════════════════════════════════════════════════════════════
mentions_rf = "随机森林" in pred_content or "RandomForest" in pred_content or "random forest" in pred_content.lower()
mentions_gb = "Gradient Boosting" in pred_content or "gradient boosting" in pred_content.lower() or "梯度提升" in pred_content
mentions_rules = "规则引擎" in pred_content or "规则" in pred_content
mentions_training = "2000" in pred_content or "训练数据" in pred_content

add_check(
    "prediction_mentions_ml_models",
    mentions_rf and mentions_gb,
    f"RandomForest mentioned: {mentions_rf}, GradientBoosting mentioned: {mentions_gb}, Rules mentioned: {mentions_rules}",
    weight=1.0
)

add_check(
    "prediction_mentions_training_window",
    mentions_training,
    f"Training window (2000期) mentioned: {mentions_training}",
    weight=0.5
)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 6: Backtest output file exists
# ══════════════════════════════════════════════════════════════════════════════
backtest_file = find_file("backtest_result.txt")
if backtest_file is None:
    for alt in ["backtest.txt", "v3.8_backtest.txt", "backtest_report.txt", "backtest_output.txt", "backtest_1000.txt"]:
        backtest_file = find_file(alt)
        if backtest_file:
            break

add_check(
    "backtest_output_exists",
    backtest_file is not None,
    f"Found backtest file at: {backtest_file}" if backtest_file else "No backtest output file found (expected backtest_result.txt or similar)",
    weight=1.5
)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 7: Backtest content has V3.8 report format with 1000-period run
# ══════════════════════════════════════════════════════════════════════════════
backtest_content = ""
if backtest_file:
    try:
        backtest_content = backtest_file.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        backtest_content = ""

has_backtest_header = "V3.8" in backtest_content and "回测" in backtest_content
has_1000_periods = "1000" in backtest_content
has_red_accuracy = "红球命中率" in backtest_content or "命中" in backtest_content
has_blue_accuracy = "蓝球命中" in backtest_content or "蓝球" in backtest_content

add_check(
    "backtest_has_v38_report_format",
    has_backtest_header and has_red_accuracy,
    f"V3.8 backtest header: {has_backtest_header}, Red accuracy reported: {has_red_accuracy}, Blue accuracy: {has_blue_accuracy}",
    weight=2.0
)

add_check(
    "backtest_1000_periods",
    has_1000_periods,
    f"1000-period backtest confirmed in output: {has_1000_periods}. Content snippet: {backtest_content[:300] if backtest_content else 'EMPTY'}",
    weight=1.5
)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 8: Backtest mentions ML model config (RandomForest 100 trees, GradientBoosting)
# ══════════════════════════════════════════════════════════════════════════════
bt_mentions_rf = "RandomForest" in backtest_content or "随机森林" in backtest_content
bt_mentions_100trees = "100" in backtest_content
bt_mentions_gb = "Gradient Boosting" in backtest_content or "GradientBoosting" in backtest_content
bt_mentions_50pct = "50%" in backtest_content

add_check(
    "backtest_mentions_model_config",
    bt_mentions_rf and bt_mentions_100trees,
    f"RF mentioned: {bt_mentions_rf}, 100-trees: {bt_mentions_100trees}, GB: {bt_mentions_gb}, 50% hybrid: {bt_mentions_50pct}",
    weight=1.0
)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 9: Database was actually used (LOTTERY_DB_PATH set correctly)
# ══════════════════════════════════════════════════════════════════════════════
db_file = workspace / "lottery-predictor-v3-8/data/lottery_history.db"
db_exists = db_file.exists()
add_check(
    "lottery_database_exists",
    db_exists,
    f"SQLite DB at expected path {db_file}: {db_exists}",
    weight=0.5
)

# Verify DB has data
if db_exists:
    try:
        import sqlite3
        conn = sqlite3.connect(str(db_file))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM lottery_history")
        count = cur.fetchone()[0]
        conn.close()
        add_check(
            "database_has_sufficient_data",
            count >= 3000,
            f"Database has {count} historical draws (need ≥3000)",
            weight=0.5
        )
    except Exception as e:
        add_check(
            "database_has_sufficient_data",
            False,
            f"Could not query DB: {e}",
            weight=0.5
        )

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 10: No errors in output (scripts ran successfully)
# ══════════════════════════════════════════════════════════════════════════════
pred_no_error = pred_content and "ERROR" not in pred_content and "Traceback" not in pred_content
backtest_no_error = backtest_content and "ERROR" not in backtest_content and "Traceback" not in backtest_content

add_check(
    "prediction_script_no_errors",
    bool(pred_no_error),
    f"Prediction output is error-free: {bool(pred_no_error)}",
    weight=1.0
)

add_check(
    "backtest_script_no_errors",
    bool(backtest_no_error),
    f"Backtest output is error-free: {bool(backtest_no_error)}",
    weight=1.0
)

# ══════════════════════════════════════════════════════════════════════════════
# Final score
# ══════════════════════════════════════════════════════════════════════════════
score = round(total_score / max_score, 4) if max_score > 0 else 0.0
passed = score >= 0.75 and has_v38_header and blue_valid and exactly_6_reds

result = {
    "passed": passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, ensure_ascii=False, indent=2))