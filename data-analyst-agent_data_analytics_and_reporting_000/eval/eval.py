import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1]

checks = []
score_weights = []

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    score_weights.append((passed, weight))

# ── Find the output report ───────────────────────────────────────────────────
report_files = list(Path(workspace).rglob("book_performance_report.json"))

if not report_files:
    add_check("report_file_exists", False, "book_performance_report.json not found anywhere in workspace", weight=3)
    result = {
        "passed": False,
        "score": 0.0,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)

report_path = report_files[0]
add_check("report_file_exists", True, f"Found at {report_path}", weight=3)

try:
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
except Exception as e:
    add_check("report_parseable", False, f"JSON parse error: {e}", weight=3)
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)

add_check("report_parseable", True, "Valid JSON", weight=1)

# ── Helper: find book entry ───────────────────────────────────────────────────
def find_book(book_id):
    """Search for book entry in report, supporting various structures."""
    # Top-level list
    if isinstance(report, list):
        for item in report:
            if isinstance(item, dict) and item.get("book_id") == book_id:
                return item
    # Top-level dict with 'books' key
    if isinstance(report, dict):
        for key in ["books", "data", "results", "书籍分析", "analysis"]:
            if key in report and isinstance(report[key], list):
                for item in report[key]:
                    if isinstance(item, dict) and item.get("book_id") == book_id:
                        return item
        # Direct book_id keys
        if book_id in report:
            return report[book_id]
    return None

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 1: ROI Calculations
# Formula: ROI = total_revenue / (word_count * time_per_thousand_words_hours / 1000 * hourly_rate)
# ══════════════════════════════════════════════════════════════════════════════

BOOKS_META = {
    "book_001": {"word_count": 300000, "tpk": 2.0, "rate": 50, "revenue": 45000},
    "book_002": {"word_count": 120000, "tpk": 1.5, "rate": 80, "revenue": 9600},
    "book_003": {"word_count": 200000, "tpk": 2.5, "rate": 40, "revenue": 22000},
    "book_004": {"word_count": 80000,  "tpk": 3.0, "rate": 100, "revenue": 38000},
}

EXPECTED_ROI = {}
EXPECTED_COST = {}
for bid, m in BOOKS_META.items():
    cost = m["word_count"] * (m["tpk"] / 1000.0) * m["rate"]
    roi = m["revenue"] / cost
    EXPECTED_ROI[bid] = round(roi, 4)
    EXPECTED_COST[bid] = round(cost, 2)

# book_001: cost = 300000 * 0.002 * 50 = 30000, ROI = 45000/30000 = 1.5
# book_002: cost = 120000 * 0.0015 * 80 = 14400, ROI = 9600/14400 = 0.6667
# book_003: cost = 200000 * 0.0025 * 40 = 20000, ROI = 22000/20000 = 1.1
# book_004: cost = 80000  * 0.003  * 100= 24000, ROI = 38000/24000 = 1.5833

for bid in ["book_001", "book_002", "book_003", "book_004"]:
    book_entry = find_book(bid)
    if book_entry is None:
        add_check(f"roi_{bid}", False, f"No entry found for {bid} in report", weight=2)
        continue

    # Search for ROI value in entry
    roi_val = None
    for key in ["roi", "ROI", "return_on_investment", "投资回报率", "收益率"]:
        if key in book_entry:
            try:
                roi_val = float(book_entry[key])
            except (ValueError, TypeError):
                pass
            break

    if roi_val is None:
        add_check(f"roi_{bid}", False, f"{bid}: ROI field not found in entry: {list(book_entry.keys())}", weight=2)
        continue

    expected = EXPECTED_ROI[bid]
    tolerance = 0.05  # allow 5% relative tolerance
    rel_err = abs(roi_val - expected) / expected if expected != 0 else abs(roi_val)
    passed = rel_err <= tolerance
    add_check(
        f"roi_{bid}",
        passed,
        f"{bid}: expected ROI≈{expected:.4f}, got {roi_val:.4f} (rel_err={rel_err:.4f})",
        weight=2
    )

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 2: Performance Grading (use last day values or average of 7 days)
# Thresholds from SKILL.md:
#   completion_rate: <45% => below, 45%-60% => 合格, >=60% => 优秀
#   follow_rate:     <30% => below, 30%-50% => 合格, >=50% => 优秀
#   rating:          <8.0 => below, 8.0-9.0 => 合格, >=9.0 => 优秀
#   daily_revenue:   <100 => below, 100-500 => 合格, >=500 => 优秀
# We evaluate using the LATEST (last) day data for grading:
# ══════════════════════════════════════════════════════════════════════════════

# Last day values (2024-06-16):
LAST_DAY_METRICS = {
    "book_001": {"follow_rate": 0.25, "completion_rate": 0.44, "rating": 8.5, "daily_revenue_cny": 210},
    "book_002": {"follow_rate": 0.29, "completion_rate": 0.41, "rating": 7.5, "daily_revenue_cny": 85},
    "book_003": {"follow_rate": 0.60, "completion_rate": 0.70, "rating": 9.3, "daily_revenue_cny": 650},
    "book_004": {"follow_rate": 0.56, "completion_rate": 0.66, "rating": 9.2, "daily_revenue_cny": 810},
}

def grade_metric(value, low, high):
    """Returns 'below'/'合格'/'优秀' for a metric."""
    if value < low:
        return "below"
    elif value < high:
        return "合格"
    else:
        return "优秀"

# We'll check that the report contains grading information for each book
# and that at least key threshold crossings are correctly identified.
# Key discriminative assertions:
# book_001 completion_rate=0.44 => below 合格线(0.45) => NOT 合格 or 优秀
# book_002 rating=7.5 => below 合格线(8.0)
# book_003 follow_rate=0.60 => 优秀 (>=0.50)
# book_003 daily_revenue=650 => 优秀 (>=500)
# book_004 completion_rate=0.66 => 优秀 (>=0.60)

GRADE_ASSERTIONS = [
    # (book_id, metric_hint_keys, expected_grade, description)
    ("book_001", ["completion_rate", "完读率"], ["below", "不合格", "低于", "未达标", "未达合格线", "below_standard", "fail"],
     "book_001 completion_rate=44% is below 合格线 45%"),
    ("book_002", ["rating", "评分"], ["below", "不合格", "低于", "未达标", "below_standard", "fail"],
     "book_002 rating=7.5 is below 合格线 8.0"),
    ("book_003", ["follow_rate", "追读率", "completion_rate", "完读率", "daily_revenue", "日均收入"],
     ["优秀", "excellent", "优", "达优", "超优秀线", "above_excellent"],
     "book_003 has excellent metrics"),
    ("book_004", ["completion_rate", "完读率", "daily_revenue", "日均收入"],
     ["优秀", "excellent", "优", "达优"],
     "book_004 has excellent completion_rate and revenue"),
]

def entry_contains_grade_hint(book_entry, metric_keys, expected_grades):
    """Check if the book entry's string representation contains grade signals."""
    entry_str = json.dumps(book_entry, ensure_ascii=False).lower()
    # Check grade keywords
    for grade in expected_grades:
        if grade.lower() in entry_str:
            return True
    return False

for book_id, metric_keys, expected_grades, desc in GRADE_ASSERTIONS:
    book_entry = find_book(book_id)
    if book_entry is None:
        add_check(f"grading_{book_id}", False, f"No entry for {book_id}", weight=1.5)
        continue
    found = entry_contains_grade_hint(book_entry, metric_keys, expected_grades)
    add_check(f"grading_{book_id}", found,
              f"{desc}: {'found grade indicator' if found else 'no matching grade indicator found in entry'}", weight=1.5)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 3: Alert Generation
# Rules from SKILL.md:
#   数据暴跌: single-day drop > 30% => book_001 reads: 55000->33000 = -40%
#   收入异常: single-day revenue > 2x average => book_003: avg(first6)≈154.67, last=650 > 2*154.67=309.33
# ══════════════════════════════════════════════════════════════════════════════

# Find alerts section
def find_alerts(report):
    if isinstance(report, list):
        # Maybe alerts are embedded in book entries
        all_alerts = []
        for item in report:
            if isinstance(item, dict):
                for k in ["alerts", "预警", "warnings", "anomalies"]:
                    if k in item and isinstance(item[k], list):
                        all_alerts.extend(item[k])
        return all_alerts
    if isinstance(report, dict):
        for k in ["alerts", "预警", "warnings", "anomalies", "alert_list", "预警列表"]:
            if k in report and isinstance(report[k], list):
                return report[k]
        # alerts inside each book entry
        all_alerts = []
        for key in ["books", "data", "results"]:
            if key in report and isinstance(report[key], list):
                for item in report[key]:
                    for ak in ["alerts", "预警", "warnings"]:
                        if ak in item and isinstance(item[ak], list):
                            all_alerts.extend(item[ak])
        if all_alerts:
            return all_alerts
    return []

alerts = find_alerts(report)
alerts_str = json.dumps(alerts, ensure_ascii=False).lower() if alerts else ""

# Also search in whole report string for alert-related content
full_report_str = json.dumps(report, ensure_ascii=False).lower()

# Check 1: 数据暴跌 alert for book_001
has_drop_alert_book001 = False
# Must mention book_001 AND a drop/暴跌 type indicator
if ("book_001" in full_report_str and 
    any(kw in full_report_str for kw in ["数据暴跌", "暴跌", "drop", "数据下降", "reads_drop", "阅读量下降", "单日下降"])):
    # More specific: check they're in proximity in alerts or book_001 entry
    b001 = find_book("book_001")
    if b001:
        b001_str = json.dumps(b001, ensure_ascii=False).lower()
        if any(kw in b001_str for kw in ["数据暴跌", "暴跌", "drop", "数据下降", "阅读量下降", "单日下降"]):
            has_drop_alert_book001 = True
    # Also check in alerts list for book_001 reference
    for alert in alerts:
        alert_s = json.dumps(alert, ensure_ascii=False).lower()
        if "book_001" in alert_s and any(kw in alert_s for kw in ["数据暴跌", "暴跌", "drop", "数据下降"]):
            has_drop_alert_book001 = True

add_check(
    "alert_data_drop_book001",
    has_drop_alert_book001,
    f"book_001 reads dropped 40% (33000 from 55000): {'alert found' if has_drop_alert_book001 else 'NO drop alert found'}",
    weight=3
)

# Check 2: 收入异常 alert for book_003
has_revenue_alert_book003 = False
b003 = find_book("book_003")
if b003:
    b003_str = json.dumps(b003, ensure_ascii=False).lower()
    if any(kw in b003_str for kw in ["收入异常", "revenue", "income", "异常", "spike", "暴增", "2倍", "两倍"]):
        has_revenue_alert_book003 = True
for alert in alerts:
    alert_s = json.dumps(alert, ensure_ascii=False).lower()
    if "book_003" in alert_s and any(kw in alert_s for kw in ["收入异常", "revenue", "income", "异常", "spike", "暴增"]):
        has_revenue_alert_book003 = True

add_check(
    "alert_revenue_spike_book003",
    has_revenue_alert_book003,
    f"book_003 revenue 650 > 2x avg(154.67)=309.33: {'alert found' if has_revenue_alert_book003 else 'NO revenue anomaly alert found'}",
    weight=3
)

# Check 3: Alert JSON structure quality (must have 预警类型 or type field)
alert_has_structure = False
if alerts:
    for alert in alerts:
        if isinstance(alert, dict):
            keys_lower = [k.lower() for k in alert.keys()]
            if any(k in keys_lower for k in ["预警类型", "alert_type", "type", "warning_type", "kind"]):
                alert_has_structure = True
                break
add_check(
    "alert_json_structure",
    alert_has_structure,
    f"Alerts list has structured dicts with type fields: {alert_has_structure}. Alerts sample: {str(alerts[:1])[:200]}",
    weight=1.5
)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 4: ROI below 1.0 identification for book_002
# book_002 ROI = 9600 / 14400 = 0.667 => negative ROI (loss)
# ══════════════════════════════════════════════════════════════════════════════
b002 = find_book("book_002")
roi_loss_noted = False
if b002:
    b002_str = json.dumps(b002, ensure_ascii=False).lower()
    # ROI < 1 means cost > revenue
    if any(kw in b002_str for kw in ["亏损", "loss", "negative", "roi", "不盈利", "0.6", "0.67", "赤字"]):
        roi_loss_noted = True
    # Check if ROI value is correctly < 1
    for key in ["roi", "ROI", "return_on_investment"]:
        if key in b002:
            try:
                v = float(b002[key])
                if v < 1.0:
                    roi_loss_noted = True
            except:
                pass
add_check(
    "roi_below_1_book002",
    roi_loss_noted,
    f"book_002 ROI=0.667<1.0 (operating at a loss): {'identified' if roi_loss_noted else 'NOT identified'}",
    weight=2
)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 5: No alerts for book_004 (stable, no anomaly)
# book_004 is all healthy — no drops > 30%, no revenue spikes
# ══════════════════════════════════════════════════════════════════════════════
false_alert_book004 = False
for alert in alerts:
    alert_s = json.dumps(alert, ensure_ascii=False).lower()
    if "book_004" in alert_s and any(kw in alert_s for kw in ["数据暴跌", "drop", "收入异常", "spike"]):
        false_alert_book004 = True

add_check(
    "no_false_alert_book004",
    not false_alert_book004,
    f"book_004 stable - {'correctly no false alert' if not false_alert_book004 else 'FALSE ALERT triggered incorrectly'}",
    weight=1.5
)

# ══════════════════════════════════════════════════════════════════════════════
# Final Score
# ══════════════════════════════════════════════════════════════════════════════
total_weight = sum(w for _, w in score_weights)
passed_weight = sum(w for p, w in score_weights if p)
score = round(passed_weight / total_weight, 4) if total_weight > 0 else 0.0
overall_passed = score >= 0.70

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, ensure_ascii=False, indent=2))