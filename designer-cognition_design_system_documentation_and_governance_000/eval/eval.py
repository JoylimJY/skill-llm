import sys
import os
import re
import json
from pathlib import Path
from datetime import datetime, date

workspace = sys.argv[1]
checks = []

def check(name, condition, detail):
    checks.append({"name": name, "passed": bool(condition), "detail": detail})
    return bool(condition)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 1: design_log/{date}.md exists
# The file must be in a design_log/ subdirectory and named with a date pattern
# ─────────────────────────────────────────────────────────────────────────────
try:
    design_log_dir = Path(workspace) / "design_log"
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}\.md$')
    # Also accept YYYY_MM_DD or YYYYMMDD
    date_pattern2 = re.compile(r'^\d{4}[_\-]\d{2}[_\-]\d{2}\.md$')
    date_pattern3 = re.compile(r'^\d{8}\.md$')
    
    log_files = []
    if design_log_dir.exists():
        log_files = [f for f in design_log_dir.iterdir() 
                     if f.is_file() and (
                         date_pattern.match(f.name) or 
                         date_pattern2.match(f.name) or
                         date_pattern3.match(f.name)
                     )]
    
    log_exists = len(log_files) > 0
    log_file = log_files[0] if log_files else None
    check("design_log_date_file_exists",
          log_exists,
          f"Found {len(log_files)} date-named log file(s) in design_log/: {[f.name for f in log_files]}")
except Exception as e:
    log_file = None
    check("design_log_date_file_exists", False, f"Exception: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 2: design_log file contains 四向碰撞 (four-direction collision) 
# Must have all four Chinese headers: 正面, 反面, 侧面, 整体
# ─────────────────────────────────────────────────────────────────────────────
try:
    if log_file and log_file.exists():
        log_content = log_file.read_text(encoding="utf-8")
    else:
        # Try to find ANY recently created .md in design_log regardless of name
        log_content = ""
        if design_log_dir.exists():
            all_mds = list(design_log_dir.glob("*.md"))
            if all_mds:
                log_content = all_mds[0].read_text(encoding="utf-8")
    
    has_zhengmian = "正面" in log_content
    has_fanmian = "反面" in log_content
    has_cemian = "侧面" in log_content
    has_zhengti = "整体" in log_content
    all_four = has_zhengmian and has_fanmian and has_cemian and has_zhengti
    
    check("four_direction_collision_all_present",
          all_four,
          f"正面={has_zhengmian}, 反面={has_fanmian}, 侧面={has_cemian}, 整体={has_zhengti}")
except Exception as e:
    log_content = ""
    check("four_direction_collision_all_present", False, f"Exception: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 3: [已知依据] annotation appears at least once in log content
# ─────────────────────────────────────────────────────────────────────────────
try:
    known_tag = "[已知依据]" in log_content
    check("known_basis_annotation_present",
          known_tag,
          f"'[已知依据]' tag found: {known_tag}. Content sample: {log_content[:200]!r}")
except Exception as e:
    check("known_basis_annotation_present", False, f"Exception: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 4: [UNKNOWN-需用户测试] annotation appears at least once
# ─────────────────────────────────────────────────────────────────────────────
try:
    unknown_tag = "[UNKNOWN-需用户测试]" in log_content
    check("unknown_user_test_annotation_present",
          unknown_tag,
          f"'[UNKNOWN-需用户测试]' tag found: {unknown_tag}")
except Exception as e:
    check("unknown_user_test_annotation_present", False, f"Exception: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 5: WCAG 2.1 AA explicitly mentioned in design_log or design_decisions
# The red line mandates WCAG 2.1 AA as the minimum standard
# ─────────────────────────────────────────────────────────────────────────────
try:
    decisions_path = Path(workspace) / "design_decisions.md"
    decisions_content = ""
    if decisions_path.exists():
        decisions_content = decisions_path.read_text(encoding="utf-8")
    
    combined_content = log_content + decisions_content
    
    # Accept various formats: "WCAG 2.1 AA", "WCAG2.1 AA", "WCAG 2.1AA"
    wcag_pattern = re.compile(r'WCAG\s*2\.1\s*AA', re.IGNORECASE)
    wcag_found = bool(wcag_pattern.search(combined_content))
    
    check("wcag_21_aa_explicitly_mentioned",
          wcag_found,
          f"WCAG 2.1 AA reference found in log+decisions: {wcag_found}")
except Exception as e:
    check("wcag_21_aa_explicitly_mentioned", False, f"Exception: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 6: design_decisions.md updated with the new decision (not just the old stub)
# Must contain a decision entry related to the button color change
# AND must reference the color values (#1A73E8 or brand blue)
# ─────────────────────────────────────────────────────────────────────────────
try:
    decisions_path = Path(workspace) / "design_decisions.md"
    if decisions_path.exists():
        decisions_content = decisions_path.read_text(encoding="utf-8")
        
        # Must reference the new color
        has_new_color = "#1A73E8" in decisions_content or "1A73E8" in decisions_content or "brand blue" in decisions_content.lower() or "品牌蓝" in decisions_content
        # Must have more content than the original stub (original was ~200 chars)
        is_expanded = len(decisions_content) > 400
        
        decisions_updated = has_new_color and is_expanded
        check("design_decisions_updated_with_button_change",
              decisions_updated,
              f"New color referenced: {has_new_color}, content expanded beyond stub: {is_expanded} (len={len(decisions_content)})")
    else:
        check("design_decisions_updated_with_button_change", False,
              "design_decisions.md not found")
except Exception as e:
    check("design_decisions_updated_with_button_change", False, f"Exception: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 7: 不可逆决策 (irreversible decision) label present in design_decisions.md
# The skill spec says: 不可逆决策必须记录
# Since changing a design system component color is system-wide, it qualifies
# ─────────────────────────────────────────────────────────────────────────────
try:
    decisions_path = Path(workspace) / "design_decisions.md"
    if decisions_path.exists():
        decisions_content = decisions_path.read_text(encoding="utf-8")
        # Accept: 不可逆决策, 不可逆, irreversible
        irreversible_marked = ("不可逆" in decisions_content or 
                               "irreversible" in decisions_content.lower())
        check("irreversible_decision_marked",
              irreversible_marked,
              f"Irreversible decision label found: {irreversible_marked}")
    else:
        check("irreversible_decision_marked", False, "design_decisions.md not found")
except Exception as e:
    check("irreversible_decision_marked", False, f"Exception: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 8: iteration_history entry created for v2 of button component
# Must have a file in iteration_history/ referencing the button change
# ─────────────────────────────────────────────────────────────────────────────
try:
    iter_dir = Path(workspace) / "iteration_history"
    iter_files = list(iter_dir.glob("*.md")) + list(iter_dir.glob("*.txt"))
    
    # Filter to files NOT in the original setup (original: button_v1_spec.txt)
    new_iter_files = [f for f in iter_files if f.name != "button_v1_spec.txt"]
    
    has_new_iter = False
    iter_detail = f"New iteration files: {[f.name for f in new_iter_files]}"
    
    for f in new_iter_files:
        content = f.read_text(encoding="utf-8")
        if any(kw in content for kw in ["#1A73E8", "1A73E8", "v2", "button", "Button", "CTA", "按钮"]):
            has_new_iter = True
            iter_detail += f" | {f.name} contains button/version reference"
            break
    
    check("iteration_history_entry_created",
          has_new_iter,
          iter_detail)
except Exception as e:
    check("iteration_history_entry_created", False, f"Exception: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 9: 反面 section mentions failure conditions 
# Must address color-blind users, small screens, or low-network — from the skill's
# specific failure scenario list in the 四向碰撞 definition
# ─────────────────────────────────────────────────────────────────────────────
try:
    failure_keywords = [
        "色盲", "colorblind", "colour blind", "color blind",
        "小屏幕", "small screen", "低网速", "low network", "移动端", "mobile",
        "deuteranopia", "protanopia"
    ]
    
    # Find the 反面 section in log_content
    fanmian_match = re.search(r'反面[：:](.*?)(?=侧面[：:]|整体[：:]|##|\Z)', 
                               log_content, re.DOTALL)
    
    if fanmian_match:
        fanmian_text = fanmian_match.group(1).lower()
        has_failure_scenario = any(kw.lower() in fanmian_text for kw in failure_keywords)
    else:
        # Search entire log for failure keywords near 反面
        fanmian_idx = log_content.find("反面")
        if fanmian_idx >= 0:
            surrounding = log_content[fanmian_idx:fanmian_idx+500].lower()
            has_failure_scenario = any(kw.lower() in surrounding for kw in failure_keywords)
        else:
            has_failure_scenario = False
    
    check("fanmian_failure_scenarios_documented",
          has_failure_scenario,
          f"Failure scenario (color-blind/small-screen/low-network/mobile) mentioned: {has_failure_scenario}")
except Exception as e:
    check("fanmian_failure_scenarios_documented", False, f"Exception: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 10: 侧面 section addresses component reusability / design system impact
# Must mention component, reuse, or design system
# ─────────────────────────────────────────────────────────────────────────────
try:
    reuse_keywords = [
        "组件", "component", "复用", "reusable", "reuse", "design system", 
        "设计系统", "token", "全局", "global", "系统级"
    ]
    
    cemian_match = re.search(r'侧面[：:](.*?)(?=整体[：:]|##|\Z)',
                              log_content, re.DOTALL)
    
    if cemian_match:
        cemian_text = cemian_match.group(1).lower()
        has_reuse = any(kw.lower() in cemian_text for kw in reuse_keywords)
    else:
        cemian_idx = log_content.find("侧面")
        if cemian_idx >= 0:
            surrounding = log_content[cemian_idx:cemian_idx+500].lower()
            has_reuse = any(kw.lower() in surrounding for kw in reuse_keywords)
        else:
            has_reuse = False
    
    check("cemian_component_reusability_addressed",
          has_reuse,
          f"Component/reusability/design-system keyword found in 侧面: {has_reuse}")
except Exception as e:
    check("cemian_component_reusability_addressed", False, f"Exception: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# SCORING
# ─────────────────────────────────────────────────────────────────────────────
passed_checks = [c for c in checks if c["passed"]]
total = len(checks)
score = round(len(passed_checks) / total, 4)

# Hard gates: structural requirements that MUST pass for overall pass
hard_gate_names = [
    "design_log_date_file_exists",
    "four_direction_collision_all_present",
    "known_basis_annotation_present",
    "unknown_user_test_annotation_present",
    "design_decisions_updated_with_button_change",
    "irreversible_decision_marked",
]
hard_gates_passed = all(c["passed"] for c in checks if c["name"] in hard_gate_names)
overall_passed = hard_gates_passed and score >= 0.75

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, ensure_ascii=False, indent=2))