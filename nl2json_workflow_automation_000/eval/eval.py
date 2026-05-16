import sys
import json
import os
from pathlib import Path

def load_json_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def check_time_format(value):
    """Check if a time string matches YYYY-mm-dd H:i:s pattern (PHP style)."""
    import re
    # Pattern: YYYY-mm-dd H:MM:SS where H can be 1 or 2 digits (0-23)
    pattern = r'^\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}:\d{2}$'
    return bool(re.match(pattern, value))

def evaluate(workspace):
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, max_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        max_score += weight
        if passed:
            total_score += weight

    # ── Find output files ──────────────────────────────────────────────────────
    ws = Path(workspace)
    turn1_candidates = list(ws.rglob("turn1_output.json"))
    turn2_candidates = list(ws.rglob("turn2_output.json"))
    turn3_candidates = list(ws.rglob("turn3_output.json"))

    # Check existence
    add_check("turn1_output.json exists", len(turn1_candidates) > 0,
              f"Found {len(turn1_candidates)} file(s)" if turn1_candidates else "File not found", 1.0)
    add_check("turn2_output.json exists", len(turn2_candidates) > 0,
              f"Found {len(turn2_candidates)} file(s)" if turn2_candidates else "File not found", 1.0)
    add_check("turn3_output.json exists", len(turn3_candidates) > 0,
              f"Found {len(turn3_candidates)} file(s)" if turn3_candidates else "File not found", 1.0)

    # ── Load files ─────────────────────────────────────────────────────────────
    t1 = t2 = t3 = None
    try:
        if turn1_candidates:
            t1 = load_json_file(turn1_candidates[0])
        if turn2_candidates:
            t2 = load_json_file(turn2_candidates[0])
        if turn3_candidates:
            t3 = load_json_file(turn3_candidates[0])
    except Exception as e:
        add_check("JSON files are parseable", False, f"Parse error: {e}", 1.0)

    # ── TEMPLATE COMPLIANCE: Must use custom template fields, NOT legacy ones ──
    # The template is: {"raw_input": "string", "query_label": "string", "params": {}}
    # NOT the legacy: {"input": ..., "question_name": ..., "other": ...}

    REQUIRED_TOP_KEYS = {"raw_input", "query_label", "params"}
    LEGACY_KEYS = {"input", "question_name", "other"}

    for turn_label, turn_data in [("Turn1", t1), ("Turn2", t2), ("Turn3", t3)]:
        if turn_data is None:
            add_check(f"{turn_label}: uses correct template fields (raw_input/query_label/params)",
                      False, "File missing or unparseable", 2.0)
            continue
        has_correct = REQUIRED_TOP_KEYS.issubset(set(turn_data.keys()))
        uses_legacy = bool(LEGACY_KEYS.intersection(set(turn_data.keys())))
        detail = f"Keys found: {list(turn_data.keys())}"
        add_check(f"{turn_label}: uses correct template fields (raw_input/query_label/params)",
                  has_correct and not uses_legacy, detail, 2.0)

    # ── TURN 1: Full query extraction ─────────────────────────────────────────
    # Input: "帮我转成JSON：查询微博上最近7天关于新能源汽车的负面舆情top20"
    # Reference date: 2026-03-04
    # Expected params:
    #   source = 微博
    #   subject = 新能源汽车
    #   sentiment = 负面
    #   data_type contains 舆情
    #   limit = top20
    #   start_time = 2026-02-25 00:00:00  (最近7天: 2026-03-04 - 7 + 1 = 2026-02-25)
    #   end_time = 2026-03-04 23:59:59

    if t1 is not None:
        params1 = t1.get("params", {})

        # raw_input should preserve original query text
        raw_input_1 = t1.get("raw_input", "")
        add_check("Turn1: raw_input contains original user query",
                  "新能源汽车" in raw_input_1 or "微博" in raw_input_1,
                  f"raw_input='{raw_input_1}'", 1.0)

        # query_label should be a descriptive label (not empty)
        query_label_1 = t1.get("query_label", "")
        add_check("Turn1: query_label is non-empty string",
                  isinstance(query_label_1, str) and len(query_label_1) > 0,
                  f"query_label='{query_label_1}'", 1.0)

        add_check("Turn1: params.source = 微博",
                  params1.get("source", "") == "微博",
                  f"source='{params1.get('source', '')}'", 2.0)

        add_check("Turn1: params.subject contains 新能源汽车",
                  "新能源汽车" in str(params1.get("subject", "")),
                  f"subject='{params1.get('subject', '')}'", 2.0)

        add_check("Turn1: params.sentiment = 负面",
                  "负面" in str(params1.get("sentiment", "")),
                  f"sentiment='{params1.get('sentiment', '')}'", 1.5)

        add_check("Turn1: params.limit = top20",
                  "top20" in str(params1.get("limit", "")).lower(),
                  f"limit='{params1.get('limit', '')}'", 1.5)

        # Time: 最近7天 from 2026-03-04 = 2026-02-25 00:00:00 to 2026-03-04 23:59:59
        start1 = params1.get("start_time", "")
        end1 = params1.get("end_time", "")
        add_check("Turn1: start_time = 2026-02-25 00:00:00",
                  start1 == "2026-02-25 00:00:00",
                  f"start_time='{start1}'", 2.0)

        add_check("Turn1: end_time = 2026-03-04 23:59:59",
                  end1 == "2026-03-04 23:59:59",
                  f"end_time='{end1}'", 2.0)

        add_check("Turn1: time values follow YYYY-mm-dd H:i:s format",
                  check_time_format(start1) and check_time_format(end1),
                  f"start='{start1}', end='{end1}'", 1.0)
    else:
        for check_name in [
            "Turn1: raw_input contains original user query",
            "Turn1: query_label is non-empty string",
            "Turn1: params.source = 微博",
            "Turn1: params.subject contains 新能源汽车",
            "Turn1: params.sentiment = 负面",
            "Turn1: params.limit = top20",
            "Turn1: start_time = 2026-02-25 00:00:00",
            "Turn1: end_time = 2026-03-04 23:59:59",
            "Turn1: time values follow YYYY-mm-dd H:i:s format"
        ]:
            add_check(check_name, False, "turn1_output.json missing", 1.5)

    # ── TURN 2: Partial query - only time changes to 本月 ─────────────────────
    # Input: "改成本月"
    # Reference date: 2026-03-04
    # Context inheritance: keep source=微博, subject=新能源汽车, sentiment=负面, data_type, limit=top20
    # Update: start_time=2026-03-01 00:00:00, end_time=2026-03-31 23:59:59
    # query_label must reflect updated time (本月)

    if t2 is not None:
        params2 = t2.get("params", {})

        # raw_input should contain "改成本月" (original turn 2 input)
        raw_input_2 = t2.get("raw_input", "")
        add_check("Turn2: raw_input reflects turn 2 user input",
                  "本月" in raw_input_2 or "改成" in raw_input_2,
                  f"raw_input='{raw_input_2}'", 1.0)

        # Context inheritance: source must still be 微博
        add_check("Turn2: params.source inherited = 微博",
                  params2.get("source", "") == "微博",
                  f"source='{params2.get('source', '')}'", 2.0)

        # Context inheritance: subject must still be 新能源汽车
        add_check("Turn2: params.subject inherited = 新能源汽车",
                  "新能源汽车" in str(params2.get("subject", "")),
                  f"subject='{params2.get('subject', '')}'", 2.0)

        # Context inheritance: sentiment must still be 负面
        add_check("Turn2: params.sentiment inherited = 负面",
                  "负面" in str(params2.get("sentiment", "")),
                  f"sentiment='{params2.get('sentiment', '')}'", 1.5)

        # Context inheritance: limit must still be top20
        add_check("Turn2: params.limit inherited = top20",
                  "top20" in str(params2.get("limit", "")).lower(),
                  f"limit='{params2.get('limit', '')}'", 1.5)

        # Time UPDATED to 本月 (2026-03-01 ~ 2026-03-31)
        start2 = params2.get("start_time", "")
        end2 = params2.get("end_time", "")
        add_check("Turn2: start_time updated to 2026-03-01 00:00:00 (本月)",
                  start2 == "2026-03-01 00:00:00",
                  f"start_time='{start2}'", 2.0)

        add_check("Turn2: end_time updated to 2026-03-31 23:59:59 (本月)",
                  end2 == "2026-03-31 23:59:59",
                  f"end_time='{end2}'", 2.0)

        # query_label must be updated to reflect the new time period and inherited context
        query_label_2 = t2.get("query_label", "")
        label_has_time_update = ("本月" in query_label_2 or "3月" in query_label_2 or "三月" in query_label_2)
        label_has_inherited = ("新能源汽车" in query_label_2 or "微博" in query_label_2)
        add_check("Turn2: query_label updated to reflect new time + inherited context",
                  label_has_time_update and label_has_inherited,
                  f"query_label='{query_label_2}'", 2.0)
    else:
        for check_name in [
            "Turn2: raw_input reflects turn 2 user input",
            "Turn2: params.source inherited = 微博",
            "Turn2: params.subject inherited = 新能源汽车",
            "Turn2: params.sentiment inherited = 负面",
            "Turn2: params.limit inherited = top20",
            "Turn2: start_time updated to 2026-03-01 00:00:00 (本月)",
            "Turn2: end_time updated to 2026-03-31 23:59:59 (本月)",
            "Turn2: query_label updated to reflect new time + inherited context"
        ]:
            add_check(check_name, False, "turn2_output.json missing", 1.5)

    # ── TURN 3: Partial query - only source changes to 人民网 ─────────────────
    # Input: "换成人民网"
    # Context inheritance from Turn 2: keep subject=新能源汽车, sentiment=负面, data_type, limit=top20
    # Also inherit time from Turn 2: start=2026-03-01, end=2026-03-31
    # Update: source=人民网
    # query_label must reflect 人民网 + inherited context

    if t3 is not None:
        params3 = t3.get("params", {})

        # raw_input should contain turn 3 input
        raw_input_3 = t3.get("raw_input", "")
        add_check("Turn3: raw_input reflects turn 3 user input",
                  "人民网" in raw_input_3 or "换成" in raw_input_3,
                  f"raw_input='{raw_input_3}'", 1.0)

        # Source UPDATED to 人民网
        add_check("Turn3: params.source updated = 人民网",
                  params3.get("source", "") == "人民网",
                  f"source='{params3.get('source', '')}'", 2.5)

        # Context inheritance: subject must still be 新能源汽车
        add_check("Turn3: params.subject inherited = 新能源汽车",
                  "新能源汽车" in str(params3.get("subject", "")),
                  f"subject='{params3.get('subject', '')}'", 2.0)

        # Context inheritance: sentiment must still be 负面
        add_check("Turn3: params.sentiment inherited = 负面",
                  "负面" in str(params3.get("sentiment", "")),
                  f"sentiment='{params3.get('sentiment', '')}'", 1.5)

        # Context inheritance: limit must still be top20
        add_check("Turn3: params.limit inherited = top20",
                  "top20" in str(params3.get("limit", "")).lower(),
                  f"limit='{params3.get('limit', '')}'", 1.5)

        # Context inheritance: time must come from Turn 2 (本月)
        start3 = params3.get("start_time", "")
        end3 = params3.get("end_time", "")
        add_check("Turn3: start_time inherited from Turn2 = 2026-03-01 00:00:00",
                  start3 == "2026-03-01 00:00:00",
                  f"start_time='{start3}'", 2.0)

        add_check("Turn3: end_time inherited from Turn2 = 2026-03-31 23:59:59",
                  end3 == "2026-03-31 23:59:59",
                  f"end_time='{end3}'", 2.0)

        # query_label must reflect 人民网 + inherited context
        query_label_3 = t3.get("query_label", "")
        label_has_new_source = "人民网" in query_label_3
        label_has_inherited_t3 = ("新能源汽车" in query_label_3 or "top20" in query_label_3.lower())
        add_check("Turn3: query_label updated to reflect 人民网 + inherited context",
                  label_has_new_source and label_has_inherited_t3,
                  f"query_label='{query_label_3}'", 2.0)
    else:
        for check_name in [
            "Turn3: raw_input reflects turn 3 user input",
            "Turn3: params.source updated = 人民网",
            "Turn3: params.subject inherited = 新能源汽车",
            "Turn3: params.sentiment inherited = 负面",
            "Turn3: params.limit inherited = top20",
            "Turn3: start_time inherited from Turn2 = 2026-03-01 00:00:00",
            "Turn3: end_time inherited from Turn2 = 2026-03-31 23:59:59",
            "Turn3: query_label updated to reflect 人民网 + inherited context"
        ]:
            add_check(check_name, False, "turn3_output.json missing", 1.5)

    # ── DEFAULT VALUE COMPLIANCE ───────────────────────────────────────────────
    # All three outputs must have params as an object (not null, not array)
    for turn_label, turn_data in [("Turn1", t1), ("Turn2", t2), ("Turn3", t3)]:
        if turn_data is not None:
            params = turn_data.get("params")
            add_check(f"{turn_label}: params field is a non-empty object",
                      isinstance(params, dict) and len(params) > 0,
                      f"params type={type(params).__name__}, value={params}", 1.0)

    # ── FINAL SCORE ────────────────────────────────────────────────────────────
    score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    passed = score >= 0.75

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))