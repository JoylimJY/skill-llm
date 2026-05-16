import sys
import json
import os
import re
from pathlib import Path

workspace = sys.argv[1]
checks = []

def make_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

# ── Helper: find files by name pattern ──────────────────────────────────────
def find_files(pattern):
    return list(Path(workspace).rglob(pattern))

# ── 1. Check: Two separate SKILL.md files exist (not one bundled file) ────────
try:
    all_skill_mds = find_files("SKILL.md")
    # Filter out any that are inside the original edtech-sprint input structure
    skill_mds = [p for p in all_skill_mds if "sessions" not in str(p) and "archive" not in str(p)]
    
    if len(skill_mds) >= 2:
        checks.append(make_check(
            "two_separate_skill_packages_created",
            True,
            f"Found {len(skill_mds)} SKILL.md files: {[str(p) for p in skill_mds]}"
        ))
        split_passed = True
    else:
        checks.append(make_check(
            "two_separate_skill_packages_created",
            False,
            f"Expected at least 2 separate SKILL.md files (one per capability). Found: {[str(p) for p in skill_mds]}. Agent likely bundled both capabilities into one — violates 'Less is more / single capability per skill' principle."
        ))
        split_passed = False
except Exception as e:
    checks.append(make_check("two_separate_skill_packages_created", False, f"Exception: {e}"))
    split_passed = False

# ── 2. Check: Each skill covers the right distinct domain ────────────────────
try:
    skill_md_contents = []
    for p in skill_mds:
        try:
            skill_md_contents.append((str(p), p.read_text(encoding="utf-8").lower()))
        except:
            pass

    # One should be about calibration, one about diagnosis/weakness
    has_calibration_skill = any(
        any(kw in content for kw in ["calibrat", "difficulty", "rolling", "anchor", "normali"])
        for _, content in skill_md_contents
    )
    has_diagnosis_skill = any(
        any(kw in content for kw in ["diagnos", "weakness", "weak zone", "topic", "error rate"])
        for _, content in skill_md_contents
    )

    if has_calibration_skill and has_diagnosis_skill:
        checks.append(make_check(
            "correct_capability_separation",
            True,
            "One skill covers difficulty calibration, another covers learner weakness diagnosis."
        ))
    else:
        checks.append(make_check(
            "correct_capability_separation",
            False,
            f"Skills don't clearly separate the two capabilities. calibration_found={has_calibration_skill}, diagnosis_found={has_diagnosis_skill}"
        ))
except Exception as e:
    checks.append(make_check("correct_capability_separation", False, f"Exception: {e}"))

# ── 3. Check: Key decision points documented (why, not just what) ─────────────
try:
    all_content = " ".join(content for _, content in skill_md_contents)
    
    decision_signals = [
        # N=5 decision
        (r"n\s*=\s*5|rolling.{0,30}5|5.{0,30}session", "N=5 rolling window decision"),
        # P90 cap
        (r"p90|90th|percentile|cap.{0,40}high|top.{0,20}10", "P90 cap guard for high performers"),
        # Normalization decision
        (r"normali|score\s*/\s*max|max_possible|raw score", "Score normalization over raw scores"),
        # 40% threshold
        (r"40\s*%|40%.{0,30}threshold|error.{0,20}40", "40% error rate threshold for weakness"),
        # 5 attempts minimum
        (r"5.{0,20}attempt|insufficient.{0,20}data|fewer.{0,20}5|minimum.{0,20}attempt", "Minimum 5 attempts guard"),
    ]
    
    found_decisions = []
    missing_decisions = []
    for pattern, label in decision_signals:
        if re.search(pattern, all_content, re.IGNORECASE):
            found_decisions.append(label)
        else:
            missing_decisions.append(label)
    
    if len(found_decisions) >= 4:
        checks.append(make_check(
            "key_decision_points_documented",
            True,
            f"Found {len(found_decisions)}/5 key decision points: {found_decisions}"
        ))
    else:
        checks.append(make_check(
            "key_decision_points_documented",
            False,
            f"Only {len(found_decisions)}/5 key decision points documented. Missing: {missing_decisions}. Agent wrote steps without decision rationale."
        ))
except Exception as e:
    checks.append(make_check("key_decision_points_documented", False, f"Exception: {e}"))

# ── 4. Check: Each skill has the 5 mandatory output sections ─────────────────
try:
    required_sections_signals = [
        # What was extracted / ability
        (r"能力|提炼|抽|extracted|capability|what.{0,30}skill|skill.{0,30}about", "what was extracted"),
        # Why worth skilling
        (r"为什么|值得|worth|value|why|reusab|复用", "why it's worth skilling"),
        # Split or merge decision
        (r"独立|拆|split|separat|standalone|merge|并入|independent", "split-or-merge decision"),
        # Boundaries / scope
        (r"边界|boundary|boundaries|scope|limit|不处理|不包括", "skill boundary definition"),
        # Verification / validation
        (r"验证|verify|validat|test|how.{0,30}confirm|如何验证", "verification plan"),
    ]
    
    # Check across all skill mds combined
    combined = " ".join(content for _, content in skill_md_contents)
    found_sections = []
    missing_sections = []
    for pattern, label in required_sections_signals:
        if re.search(pattern, combined, re.IGNORECASE):
            found_sections.append(label)
        else:
            missing_sections.append(label)
    
    if len(found_sections) >= 4:
        checks.append(make_check(
            "five_mandatory_output_items_present",
            True,
            f"Found {len(found_sections)}/5 required output items: {found_sections}"
        ))
    else:
        checks.append(make_check(
            "five_mandatory_output_items_present",
            False,
            f"Only {len(found_sections)}/5 required output items present. Missing: {missing_sections}"
        ))
except Exception as e:
    checks.append(make_check("five_mandatory_output_items_present", False, f"Exception: {e}"))

# ── 5. Check: Memory annotation / design rationale section present ────────────
try:
    memory_signals = [
        r"记忆|memory|沉淀|why.{0,30}design|design.{0,20}rationale|设计原因|为什么这么设计|design decision",
        r"记忆沉淀|short.?term.{0,20}memory|long.?term|升格",
    ]
    has_memory = any(
        re.search(pat, combined, re.IGNORECASE)
        for pat in memory_signals
    )
    if has_memory:
        checks.append(make_check(
            "memory_annotation_present",
            True,
            "Found memory/rationale annotation documenting why this design was chosen."
        ))
    else:
        checks.append(make_check(
            "memory_annotation_present",
            False,
            "No memory/design rationale annotation found. The skill requires documenting 'why this design' as a memory note (记忆沉淀 step)."
        ))
except Exception as e:
    checks.append(make_check("memory_annotation_present", False, f"Exception: {e}"))

# ── 6. Check: references/ or templates/ directories created ──────────────────
try:
    refs_dirs = find_files("references")
    tmpl_dirs = find_files("templates")
    ref_files = list(Path(workspace).rglob("references/*"))
    tmpl_files = list(Path(workspace).rglob("templates/*"))
    
    has_support_structure = (len(refs_dirs) > 0 or len(tmpl_dirs) > 0 or 
                              len(ref_files) > 0 or len(tmpl_files) > 0)
    if has_support_structure:
        checks.append(make_check(
            "support_directories_created",
            True,
            f"Found support structure: refs_dirs={[str(p) for p in refs_dirs]}, tmpl_dirs={[str(p) for p in tmpl_dirs]}"
        ))
    else:
        checks.append(make_check(
            "support_directories_created",
            False,
            "No references/ or templates/ directories found. The packaging step requires these."
        ))
except Exception as e:
    checks.append(make_check("support_directories_created", False, f"Exception: {e}"))

# ── 7. Check: Abandoned session NOT packaged as a skill ──────────────────────
try:
    all_content_paths = list(Path(workspace).rglob("SKILL.md"))
    # Check none of the skill files reference IRT or the abandoned exploration as a packaged skill
    irt_bundled = False
    for p in all_content_paths:
        try:
            c = p.read_text(encoding="utf-8").lower()
            if "irt" in c and ("skill" in c or "ability" in c) and "abandon" not in c:
                # Might indicate the agent packaged the abandoned IRT exploration
                if "pre-train" in c or "item response" in c:
                    irt_bundled = True
        except:
            pass
    
    if not irt_bundled:
        checks.append(make_check(
            "abandoned_session_not_packaged",
            True,
            "Abandoned IRT exploration was correctly excluded from skill packaging."
        ))
    else:
        checks.append(make_check(
            "abandoned_session_not_packaged",
            False,
            "Agent appears to have packaged the abandoned IRT exploration — unstable methods should not be packaged."
        ))
except Exception as e:
    checks.append(make_check("abandoned_session_not_packaged", False, f"Exception: {e}"))

# ── Score & Result ────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4)
overall_passed = passed_count >= 6  # Must pass at least 6 of 7

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2, ensure_ascii=False))