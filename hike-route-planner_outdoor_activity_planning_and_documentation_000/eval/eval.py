import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)

    # --- Find the output file ---
    candidates = list(workspace.rglob("shimen_forest_hike_brief.md"))
    if not candidates:
        # Also try any .md file that is NOT the template or archive files
        all_md = [
            p for p in workspace.rglob("*.md")
            if "plan-template" not in p.name
            and "archive" not in str(p)
            and "sample" not in p.name.lower()
        ]
        candidates = all_md

    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False,
                         "detail": "No output .md file found (expected shimen_forest_hike_brief.md or similar non-template .md)"}]
        }

    # Use the most recently modified candidate
    output_file = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]

    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_readable", "passed": False,
                         "detail": f"Could not read output file: {e}"}]
        }

    checks.append({"name": "output_file_exists", "passed": True,
                    "detail": f"Found output file at: {output_file}"})

    # --- Check 1: All 7 required emoji headings present ---
    required_emojis = ["🥾", "👀", "📅", "📍", "⏰", "🎒", "🌤"]
    emoji_names = ["路线概览(🥾)", "路线亮点(👀)", "行程安排(📅)", "交通方案(📍)", "风险提示(⏰)", "装备与费用(🎒)", "假设前提(🌤)"]
    missing_emojis = [e for e in required_emojis if e not in content]
    emoji_check_passed = len(missing_emojis) == 0
    checks.append({
        "name": "seven_emoji_headings_present",
        "passed": emoji_check_passed,
        "detail": f"Missing emojis: {missing_emojis}" if missing_emojis else "All 7 emoji headings found"
    })

    # --- Check 2: Information classification (已核实/估算/假设 labels) ---
    has_yeheshi = "已核实" in content
    has_gusuan = "估算" in content
    has_jiashe = "假设" in content
    info_class_passed = has_yeheshi and has_gusuan and has_jiashe
    checks.append({
        "name": "tripartite_info_classification",
        "passed": info_class_passed,
        "detail": (
            f"已核实={'present' if has_yeheshi else 'MISSING'}, "
            f"估算={'present' if has_gusuan else 'MISSING'}, "
            f"假设={'present' if has_jiashe else 'MISSING'}"
        )
    })

    # --- Check 3: Large group regroup policy (every 45-60 min for >12 people) ---
    regroup_patterns = [
        r"45.{0,10}分钟",
        r"60.{0,10}分钟",
        r"regroup",
        r"集合点",
        r"收队",
    ]
    regroup_matches = [p for p in regroup_patterns if re.search(p, content, re.IGNORECASE)]
    regroup_passed = len(regroup_matches) >= 2
    checks.append({
        "name": "large_group_regroup_policy",
        "passed": regroup_passed,
        "detail": (
            f"Regroup-related terms found: {regroup_matches}. "
            f"Expected at least 2 regroup indicators for 15-person group."
        )
    })

    # --- Check 4: Beginner / no technical sections constraint applied ---
    no_tech_patterns = [
        r"新手",
        r"初级",
        r"无技术路段",
        r"不涉及.{0,8}攀爬",
        r"避免.{0,15}(陡|技术|手脚|铁链|绳索|裸岩|断崖)",
        r"平缓",
        r"坡度.{0,8}(低|缓|小)",
        r"不允许技术",
    ]
    no_tech_matches = [p for p in no_tech_patterns if re.search(p, content, re.IGNORECASE)]
    no_tech_passed = len(no_tech_matches) >= 1
    checks.append({
        "name": "beginner_no_technical_sections",
        "passed": no_tech_passed,
        "detail": (
            f"Beginner/no-technical constraint indicators found: {no_tech_matches}"
        )
    })

    # --- Check 5: Transit priority (public transport) included ---
    transit_patterns = [
        r"地铁",
        r"公交",
        r"公共交通",
        r"班次",
        r"首班",
        r"末班",
    ]
    transit_matches = [p for p in transit_patterns if re.search(p, content)]
    transit_passed = len(transit_matches) >= 2
    checks.append({
        "name": "public_transit_priority",
        "passed": transit_passed,
        "detail": f"Transit-related terms found: {transit_matches}"
    })

    # --- Check 6: Three-layer transport plan (去程, 返程, 兜底/打车) ---
    has_qucheng = bool(re.search(r"去程", content))
    has_fancheng = bool(re.search(r"返程", content))
    has_daoche = bool(re.search(r"(打车|滴滴|兜底|taxi|Taxi)", content, re.IGNORECASE))
    three_layer_passed = has_qucheng and has_fancheng and has_daoche
    checks.append({
        "name": "three_layer_transport_plan",
        "passed": three_layer_passed,
        "detail": (
            f"去程={'found' if has_qucheng else 'MISSING'}, "
            f"返程={'found' if has_fancheng else 'MISSING'}, "
            f"打车兜底={'found' if has_daoche else 'MISSING'}"
        )
    })

    # --- Check 7: Cost breakdown into 4 categories ---
    cost_categories = ["交通", "门票", "补给", "打车"]
    cost_found = [c for c in cost_categories if c in content]
    cost_passed = len(cost_found) >= 3
    checks.append({
        "name": "cost_breakdown_four_categories",
        "passed": cost_passed,
        "detail": f"Cost categories found: {cost_found} (need at least 3 of: 交通, 门票, 补给, 打车)"
    })

    # --- Check 8: Leader execution section with actionable content ---
    leader_patterns = [
        r"领队",
        r"签到",
        r"分组",
        r"口令",
        r"补水",
        r"掉队",
        r"应急触发",
        r"取消.{0,8}(条件|降级)",
    ]
    leader_matches = [p for p in leader_patterns if re.search(p, content)]
    leader_passed = len(leader_matches) >= 4
    checks.append({
        "name": "leader_execution_section",
        "passed": leader_passed,
        "detail": f"Leader execution indicators found ({len(leader_matches)}/8): {leader_matches}"
    })

    # --- Check 9: No-night-hiking constraint (must finish before sunset) ---
    sunset_patterns = [
        r"日落",
        r"天黑",
        r"夜行",
        r"(16|17|18)[:：][0-5][0-9].{0,10}(前|之前|返回|下山)",
        r"(前|之前|返回|下山).{0,10}(16|17|18)[:：][0-5][0-9]",
        r"不允许夜行",
        r"避免夜行",
    ]
    sunset_matches = [p for p in sunset_patterns if re.search(p, content)]
    sunset_passed = len(sunset_matches) >= 1
    checks.append({
        "name": "no_night_hiking_constraint",
        "passed": sunset_passed,
        "detail": f"Sunset/no-night-hike constraint indicators: {sunset_matches}"
    })

    # --- Check 10: Risk section is terrain/weather/group-specific (not generic slogans) ---
    generic_slogan_patterns = [
        r"安全第一",
        r"请注意安全",
        r"务必小心",
    ]
    specific_risk_patterns = [
        r"(地形|湿滑|落石|裸岩|断崖|涉水|坡度|路况)",
        r"(天气|降雨|气温|风速|能见度|紫外线|中暑|失温)",
        r"(新手|经验|节奏|体力|脱队|掉队|队伍)",
        r"(返程|班次|末班|时间窗口|赶不上)",
    ]
    generic_count = sum(1 for p in generic_slogan_patterns if re.search(p, content))
    specific_count = sum(1 for p in specific_risk_patterns if re.search(p, content))
    risk_passed = specific_count >= 2 and generic_count <= 2
    checks.append({
        "name": "specific_risk_notes",
        "passed": risk_passed,
        "detail": (
            f"Specific risk categories covered: {specific_count}/4. "
            f"Generic slogans found: {generic_count}. "
            f"Need >=2 specific, <=2 generic."
        )
    })

    # --- Compute score ---
    total = len(checks) - 1  # exclude file-exists check from scoring
    scored_checks = checks[1:]  # skip first
    passed_count = sum(1 for c in scored_checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0

    overall_passed = (
        checks[0]["passed"] and  # file exists
        emoji_check_passed and   # template structure
        info_class_passed and    # tripartite classification
        regroup_passed and       # large group rule
        three_layer_passed       # transport plan
    )

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                           "checks": [{"name": "invocation", "passed": False,
                                        "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))