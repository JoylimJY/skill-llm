import sys
import json
import traceback
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
total_score = 0.0
max_score = 0.0

def check(name, weight, condition_fn):
    global total_score, max_score
    max_score += weight
    try:
        passed, detail = condition_fn()
    except Exception as e:
        passed = False
        detail = f"Exception: {traceback.format_exc()}"
    checks.append({"name": name, "passed": passed, "detail": detail})
    if passed:
        total_score += weight
    return passed

# ── Load helper ──────────────────────────────────────────────────────
def load_json(rel_path):
    p = workspace / rel_path
    if not p.exists():
        raise FileNotFoundError(f"{rel_path} not found")
    return json.loads(p.read_text(encoding="utf-8"))

# ════════════════════════════════════════════════════════════════════
# CHECK 1: predictions.json exists and is a non-empty list/dict
# ════════════════════════════════════════════════════════════════════
def c1():
    data = load_json("memory/predictions.json")
    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        entries = list(data.values()) if data else []
    else:
        return False, f"Unexpected type: {type(data)}"
    if len(entries) == 0:
        return False, "predictions.json is empty — no predictions recorded"
    return True, f"predictions.json contains {len(entries)} prediction(s)"

check("predictions.json exists and is non-empty", 1.5, c1)

# ════════════════════════════════════════════════════════════════════
# CHECK 2: Each prediction entry contains the required schema fields
# covering: 比赛信息, 分析摘要 (with sub-fields), 预测结论, 投注建议
# ════════════════════════════════════════════════════════════════════
REQUIRED_TOP_FIELDS = ["比赛信息", "分析摘要", "预测结论", "投注建议"]

def get_prediction_entries():
    data = load_json("memory/predictions.json")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # could be dict keyed by id
        vals = list(data.values())
        if vals and isinstance(vals[0], dict):
            return vals
    return []

def c2():
    entries = get_prediction_entries()
    if not entries:
        return False, "No entries to validate"
    missing_per_entry = []
    for i, entry in enumerate(entries):
        missing = [f for f in REQUIRED_TOP_FIELDS if f not in entry]
        if missing:
            missing_per_entry.append(f"entry[{i}] missing: {missing}")
    if missing_per_entry:
        return False, "Missing required fields: " + "; ".join(missing_per_entry[:3])
    return True, f"All {len(entries)} prediction entries have required top-level fields"

check("Prediction entries have all required schema fields (比赛信息/分析摘要/预测结论/投注建议)", 2.0, c2)

# ════════════════════════════════════════════════════════════════════
# CHECK 3: 分析摘要 contains at least two of: 基本面, 赔率, 风险评估
# ════════════════════════════════════════════════════════════════════
ANALYSIS_SUBFIELDS = ["基本面", "赔率", "风险评估"]

def c3():
    entries = get_prediction_entries()
    if not entries:
        return False, "No entries"
    good = 0
    for entry in entries:
        summary = entry.get("分析摘要", {})
        if isinstance(summary, dict):
            found = [f for f in ANALYSIS_SUBFIELDS if f in summary]
            if len(found) >= 2:
                good += 1
        elif isinstance(summary, str) and len(summary) > 0:
            # string form: check sub-keywords present
            found = [f for f in ANALYSIS_SUBFIELDS if f in summary]
            if len(found) >= 2:
                good += 1
    if good == 0:
        return False, f"No entries have ≥2 of {ANALYSIS_SUBFIELDS} in 分析摘要"
    return True, f"{good}/{len(entries)} entries have proper 分析摘要 sub-fields"

check("分析摘要 contains 基本面/赔率/风险评估 sub-fields", 1.5, c3)

# ════════════════════════════════════════════════════════════════════
# CHECK 4: 预测结论 contains a prediction direction AND 信心指数
# ════════════════════════════════════════════════════════════════════
DIRECTIONS = ["主胜", "客胜", "平局"]

def c4():
    entries = get_prediction_entries()
    if not entries:
        return False, "No entries"
    good = 0
    for entry in entries:
        conclusion = entry.get("预测结论", {})
        text = json.dumps(conclusion, ensure_ascii=False) if isinstance(conclusion, dict) else str(conclusion)
        has_direction = any(d in text for d in DIRECTIONS)
        has_confidence = "信心" in text or "confidence" in text.lower() or "指数" in text
        if has_direction and has_confidence:
            good += 1
    if good == 0:
        return False, "No entries have both a prediction direction (主胜/客胜/平局) and 信心指数 in 预测结论"
    return True, f"{good}/{len(entries)} entries have valid 预测结论 with direction + 信心指数"

check("预测结论 contains direction (主胜/客胜/平局) and 信心指数", 1.5, c4)

# ════════════════════════════════════════════════════════════════════
# CHECK 5: 投注建议 contains 比分推荐 AND 投注金额
# ════════════════════════════════════════════════════════════════════
def c5():
    entries = get_prediction_entries()
    if not entries:
        return False, "No entries"
    good = 0
    for entry in entries:
        bet = entry.get("投注建议", {})
        text = json.dumps(bet, ensure_ascii=False) if isinstance(bet, dict) else str(bet)
        has_score = "比分" in text
        has_amount = "金额" in text or "投注" in text
        if has_score and has_amount:
            good += 1
    if good == 0:
        return False, "No entries have both 比分推荐 and 投注金额建议 in 投注建议"
    return True, f"{good}/{len(entries)} entries have valid 投注建议"

check("投注建议 contains 比分推荐 and 投注金额建议", 1.5, c5)

# ════════════════════════════════════════════════════════════════════
# CHECK 6: results.json exists and contains actual match outcomes
# with at least 3 matches from the raw data
# ════════════════════════════════════════════════════════════════════
def c6():
    data = load_json("memory/results.json")
    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        entries = list(data.values())
    else:
        return False, f"Unexpected type: {type(data)}"
    if len(entries) < 3:
        return False, f"Only {len(entries)} results recorded; expected ≥3"
    # Check that results reference the raw data matches (at least some)
    raw_teams = ["曼城", "曼联", "皇马", "利物浦", "切尔西", "富勒姆", "瓦伦西亚", "阿森纳", "布莱顿"]
    all_text = json.dumps(entries, ensure_ascii=False)
    found_teams = [t for t in raw_teams if t in all_text]
    if len(found_teams) < 3:
        return False, f"results.json doesn't seem to reference the provided match data. Found teams: {found_teams}"
    return True, f"results.json has {len(entries)} entries referencing teams: {found_teams}"

check("results.json exists with ≥3 actual results from provided raw data", 2.0, c6)

# ════════════════════════════════════════════════════════════════════
# CHECK 7: stats.json exists with accuracy rate and prediction count
# ════════════════════════════════════════════════════════════════════
def c7():
    data = load_json("memory/stats.json")
    text = json.dumps(data, ensure_ascii=False)
    has_accuracy = any(k in text for k in ["准确率", "accuracy", "correct_rate", "win_rate", "胜率"])
    has_count = any(k in text for k in ["总计", "total", "count", "次数", "预测次数", "total_predictions"])
    if not has_accuracy:
        return False, f"stats.json missing accuracy metric. Keys found: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}"
    if not has_count:
        return False, f"stats.json missing count metric. Content: {text[:200]}"
    return True, "stats.json has accuracy rate and prediction count metrics"

check("stats.json exists with accuracy rate and prediction count", 2.0, c7)

# ════════════════════════════════════════════════════════════════════
# CHECK 8: model.json exists with model parameters / weights
# indicating the learning/optimization cycle has been run
# ════════════════════════════════════════════════════════════════════
def c8():
    data = load_json("memory/model.json")
    if not isinstance(data, dict) or len(data) == 0:
        return False, "model.json is empty or not a dict"
    text = json.dumps(data, ensure_ascii=False)
    weight_keywords = ["权重", "weight", "参数", "param", "基本面", "赔率", "学习", "learn", "version", "updated"]
    found = [k for k in weight_keywords if k in text]
    if len(found) == 0:
        return False, f"model.json doesn't contain any weight/parameter keys. Content: {text[:300]}"
    return True, f"model.json contains model parameters. Matching keywords: {found}"

check("model.json exists with model parameters reflecting learning cycle", 2.0, c8)

# ════════════════════════════════════════════════════════════════════
# CHECK 9: Cross-validation — predictions are linked/correlated to
# results (at least one match appears in both files)
# ════════════════════════════════════════════════════════════════════
def c9():
    try:
        pred_data = load_json("memory/predictions.json")
        res_data  = load_json("memory/results.json")
    except FileNotFoundError as e:
        return False, str(e)

    pred_text = json.dumps(pred_data, ensure_ascii=False)
    res_text  = json.dumps(res_data,  ensure_ascii=False)

    all_teams = ["曼城", "曼联", "切尔西", "富勒姆", "皇马", "利物浦", "阿森纳", "布莱顿", "瓦伦西亚"]
    shared = [t for t in all_teams if t in pred_text and t in res_text]
    if len(shared) < 1:
        return False, "No common team/match found across predictions.json and results.json — they appear disconnected"
    return True, f"Cross-validated: teams {shared} appear in both predictions and results"

check("Cross-validation: predictions and results share common match data", 1.5, c9)

# ════════════════════════════════════════════════════════════════════
# CHECK 10: At least 3 predictions recorded (depth of work)
# ════════════════════════════════════════════════════════════════════
def c10():
    entries = get_prediction_entries()
    if len(entries) < 3:
        return False, f"Only {len(entries)} prediction(s) found; expected ≥3 to demonstrate proper bootstrapping"
    return True, f"{len(entries)} predictions recorded — sufficient depth"

check("At least 3 predictions recorded (demonstrates system bootstrapping)", 1.5, c10)

# ════════════════════════════════════════════════════════════════════
# Final score
# ════════════════════════════════════════════════════════════════════
final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0
overall_passed = final_score >= 0.70

result = {
    "passed": overall_passed,
    "score": final_score,
    "checks": checks
}
print(json.dumps(result, ensure_ascii=False, indent=2))