import sys
import json
import os
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0
    max_checks = 10

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── Locate output file ────────────────────────────────────────────────────
    candidates = list(Path(workspace).rglob("starlogic_moat_analysis.json"))
    if not candidates:
        checks.append({"name": "output_file_exists", "passed": False,
                        "detail": "starlogic_moat_analysis.json not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}

    output_path = candidates[0]
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        checks.append({"name": "output_file_valid_json", "passed": False,
                        "detail": f"Failed to parse JSON: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    total_score += add_check("output_file_exists", True, f"Found at {output_path}")
    total_score += add_check("output_file_valid_json", True, "Valid JSON")

    # ── Navigate to data payload ──────────────────────────────────────────────
    try:
        data = raw.get("data", raw)  # accept both {"status":..,"data":{..}} and flat
    except Exception:
        data = raw

    # ── CHECK 1: moat_types array structure ──────────────────────────────────
    moat_types = data.get("moat_types", [])
    expected_type_names = {"品牌优势", "网络效应", "转换成本", "规模优势", "特许经营权"}
    found_type_names = set()
    if isinstance(moat_types, list):
        for item in moat_types:
            if isinstance(item, dict):
                t = item.get("type", "")
                found_type_names.add(t)

    types_complete = expected_type_names.issubset(found_type_names)
    total_score += add_check(
        "moat_types_all_five_present",
        types_complete,
        f"Expected {expected_type_names}, found {found_type_names}"
    )

    # Build lookup for moat types
    moat_map = {}
    for item in moat_types if isinstance(moat_types, list) else []:
        if isinstance(item, dict):
            moat_map[item.get("type", "")] = item

    # ── CHECK 2: Network effect = 否, strength = 0 ────────────────────────────
    # The skill doc and company profile BOTH state no network effect exists
    net = moat_map.get("网络效应", {})
    net_exists = net.get("exists", None)
    net_strength = net.get("strength", -1)
    net_correct = (net_exists == False or net_exists == "否") and (net_strength == 0)
    total_score += add_check(
        "network_effect_correctly_absent",
        net_correct,
        f"网络效应 exists={net_exists} strength={net_strength}; expected exists=False/否, strength=0"
    )

    # ── CHECK 3: 特许经营权 = 是, strength >= 3 ──────────────────────────────
    # SCA exclusive licence + 47 patents → franchise/special rights exists
    fran = moat_map.get("特许经营权", {})
    fran_exists = fran.get("exists", None)
    fran_strength = fran.get("strength", 0)
    fran_correct = (fran_exists == True or fran_exists == "是") and fran_strength >= 3
    total_score += add_check(
        "franchise_correctly_identified",
        fran_correct,
        f"特许经营权 exists={fran_exists} strength={fran_strength}; expected exists=True/是, strength>=3"
    )

    # ── CHECK 4: 转换成本 = 是, strength >= 4 ────────────────────────────────
    # HIGH switching cost explicitly stated ($2.1M re-design cost)
    sw = moat_map.get("转换成本", {})
    sw_exists = sw.get("exists", None)
    sw_strength = sw.get("strength", 0)
    sw_correct = (sw_exists == True or sw_exists == "是") and sw_strength >= 4
    total_score += add_check(
        "switching_cost_correctly_high",
        sw_correct,
        f"转换成本 exists={sw_exists} strength={sw_strength}; expected exists=True/是, strength>=4"
    )

    # ── CHECK 5: Total score is in [10, 22] range and max_score = 25 ─────────
    total_sc = data.get("total_score", None)
    max_sc = data.get("max_score", None)
    # The sum of realistic scores: brand~3, network=0, switching~4-5, scale~2-3, franchise~3-4
    # Reasonable range: 12–18; we accept 10–22 to allow legitimate variation
    score_valid = (
        isinstance(total_sc, (int, float)) and
        isinstance(max_sc, (int, float)) and
        10 <= total_sc <= 22 and
        max_sc == 25
    )
    total_score += add_check(
        "total_score_and_max_score_valid",
        score_valid,
        f"total_score={total_sc}, max_score={max_sc}; expected total in [10,22], max=25"
    )

    # ── CHECK 6: Level matches score using exact SKILL thresholds ─────────────
    level = data.get("level", "")
    level_correct = False
    if isinstance(total_sc, (int, float)):
        if 20 <= total_sc <= 25:
            level_correct = level in ("极强",)
        elif 15 <= total_sc <= 19:
            level_correct = level in ("强",)
        elif 10 <= total_sc <= 14:
            level_correct = level in ("中等",)
        elif 5 <= total_sc <= 9:
            level_correct = level in ("弱",)
        else:
            level_correct = level in ("无",)
    total_score += add_check(
        "level_matches_score_thresholds",
        level_correct,
        f"level='{level}' for total_score={total_sc}; must match SKILL.md thresholds exactly"
    )

    # ── CHECK 7: investment_advice matches level exactly ─────────────────────
    investment_advice = data.get("investment_advice", "")
    level_to_advice = {
        "极强": "强烈推荐",
        "强": "推荐",
        "中等": "观察",
        "弱": "谨慎",
        "无": "不推荐",
    }
    expected_advice = level_to_advice.get(level, None)
    advice_correct = (expected_advice is not None) and (investment_advice == expected_advice)
    total_score += add_check(
        "investment_advice_matches_level",
        advice_correct,
        f"investment_advice='{investment_advice}', expected='{expected_advice}' for level='{level}'"
    )

    # ── CHECK 8: Trend is 收窄 (narrowing) ───────────────────────────────────
    # Market share 38%→31% (DOWN), ROE 21.3%→14.1% (DOWN), retention 91%→87% (DOWN)
    # Gross margin 53.8%→54.2% (stable/slight up). Majority of indicators deteriorating → 收窄
    trend = data.get("trend", "")
    trend_correct = "收窄" in str(trend)
    total_score += add_check(
        "trend_is_narrowing",
        trend_correct,
        f"trend='{trend}'; historical data shows market share 38→31%, ROE 21.3→14.1%, retention 91→87%, so trend must be '收窄'"
    )

    # ── CHECK 9: key_metrics populated with historical data ──────────────────
    key_metrics = data.get("key_metrics", {})
    # Accept either a dict with some metrics or a list of dicts (table format)
    metrics_populated = False
    if isinstance(key_metrics, dict) and len(key_metrics) >= 2:
        metrics_populated = True
    elif isinstance(key_metrics, list) and len(key_metrics) >= 2:
        metrics_populated = True
    total_score += add_check(
        "key_metrics_populated",
        metrics_populated,
        f"key_metrics has {len(key_metrics) if isinstance(key_metrics, (dict,list)) else 0} entries; need >=2"
    )

    # ── CHECK 10: risks is non-empty list ─────────────────────────────────────
    risks = data.get("risks", [])
    risks_ok = isinstance(risks, list) and len(risks) >= 1
    total_score += add_check(
        "risks_non_empty",
        risks_ok,
        f"risks has {len(risks) if isinstance(risks, list) else 0} entries; need >=1"
    )

    # ── Final verdict ─────────────────────────────────────────────────────────
    final_score = total_score / max_checks
    passed = final_score >= 0.75  # must pass at least 7.5/10 weighted checks

    return {
        "passed": passed,
        "score": round(final_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))