import sys
import json
import os
import re
import subprocess
from pathlib import Path

workspace = sys.argv[1]
skill_base = os.path.join(workspace, "onboarding-journey-designer")
input_file = os.path.join(workspace, "intake_forms", "cdm_cohort_intake_2024.json")
spec_path = os.path.join(skill_base, "resources", "spec.json")

checks = []

def find_output_file(workspace):
    """Find onboarding_journey.md anywhere in workspace."""
    matches = list(Path(workspace).rglob("onboarding_journey.md"))
    return matches[0] if matches else None

def load_spec():
    with open(spec_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_sections(md_text):
    pattern = re.compile(r'^## (.+)$', re.MULTILINE)
    headers = list(pattern.finditer(md_text))
    sections = {}
    for i, m in enumerate(headers):
        title = m.group(1).strip()
        start = m.end()
        end = headers[i+1].start() if i+1 < len(headers) else len(md_text)
        sections[title] = md_text[start:end]
    return sections

def count_bullets(content):
    lines = content.split('\n')
    return sum(1 for l in lines if re.match(r'^\s*[-*]\s+\S', l))

# --- Check 1: Output file exists ---
output_file = find_output_file(workspace)
check1 = {
    "name": "output_file_exists",
    "passed": output_file is not None,
    "detail": f"Found: {output_file}" if output_file else "onboarding_journey.md not found anywhere in workspace."
}
checks.append(check1)

if not output_file:
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)

try:
    with open(output_file, "r", encoding="utf-8") as f:
        md_text = f.read()
except Exception as e:
    checks.append({"name": "output_file_readable", "passed": False, "detail": str(e)})
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)

checks.append({"name": "output_file_readable", "passed": True, "detail": f"Read {len(md_text)} chars from {output_file}"})

# --- Load spec ---
try:
    spec = load_spec()
    checks.append({"name": "spec_loaded", "passed": True, "detail": "spec.json loaded successfully."})
except Exception as e:
    checks.append({"name": "spec_loaded", "passed": False, "detail": str(e)})
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)

sections = get_sections(md_text)

# --- Check 2: All 6 required sections present ---
required_sections = spec["required_sections"]
missing_sections = [s for s in required_sections if s not in sections]
check2 = {
    "name": "all_six_sections_present",
    "passed": len(missing_sections) == 0,
    "detail": f"Missing: {missing_sections}" if missing_sections else f"All 6 sections present: {required_sections}"
}
checks.append(check2)

# --- Check 3: Each section has >= 3 bullet points ---
min_bullets = spec["min_bullets_per_section"]
bullet_failures = []
for sec in required_sections:
    if sec in sections:
        bc = count_bullets(sections[sec])
        if bc < min_bullets:
            bullet_failures.append(f"'## {sec}': {bc} bullets (need >= {min_bullets})")

check3 = {
    "name": "min_bullets_per_section",
    "passed": len(bullet_failures) == 0,
    "detail": "; ".join(bullet_failures) if bullet_failures else f"All sections have >= {min_bullets} bullets."
}
checks.append(check3)

# --- Check 4: Day 1 mentions target_audience token ---
target_audience = "临床数据管理员"
tokens = [t.strip() for t in re.split(r'[\s,、/]+', target_audience) if t.strip()]
day1_ok = False
day1_detail = "Section '## 第1天' not found."
if "第1天" in sections:
    day1_content = sections["第1天"]
    found = [tok for tok in tokens if tok in day1_content]
    day1_ok = len(found) > 0
    day1_detail = (
        f"Found tokens {found} from target_audience in ## 第1天." if day1_ok
        else f"None of {tokens} found in ## 第1天 content."
    )
check4 = {"name": "day1_mentions_target_audience", "passed": day1_ok, "detail": day1_detail}
checks.append(check4)

# --- Check 5: 阻塞预警 contains healthcare compliance keyword ---
healthcare_keywords = spec["industry_compliance_rules"]["healthcare"]["阻塞预警_must_contain_one_of"]
blocker_ok = False
blocker_detail = "Section '## 阻塞预警' not found."
if "阻塞预警" in sections:
    blocker_content = sections["阻塞预警"]
    found_kw = [kw for kw in healthcare_keywords if kw in blocker_content]
    blocker_ok = len(found_kw) > 0
    blocker_detail = (
        f"Found compliance keyword(s): {found_kw} in ## 阻塞预警." if blocker_ok
        else f"None of {healthcare_keywords} found in ## 阻塞预警. Healthcare industry compliance rule triggered."
    )
check5 = {"name": "blocker_section_healthcare_compliance", "passed": blocker_ok, "detail": blocker_detail}
checks.append(check5)

# --- Check 6: run.py validation passes on the output ---
run_py = os.path.join(skill_base, "scripts", "run.py")
runpy_passed = False
runpy_detail = "run.py validation not attempted."
try:
    result_proc = subprocess.run(
        ["python3", run_py, "--input", input_file, "--output", str(output_file)],
        capture_output=True, text=True, timeout=30
    )
    if result_proc.returncode == 0:
        runpy_passed = True
        runpy_detail = f"run.py PASSED. stdout: {result_proc.stdout.strip()}"
    else:
        runpy_detail = (
            f"run.py FAILED (exit {result_proc.returncode}). "
            f"stdout: {result_proc.stdout.strip()} | stderr: {result_proc.stderr.strip()}"
        )
except Exception as e:
    runpy_detail = f"run.py execution error: {str(e)}"
check6 = {"name": "runpy_validation_passes", "passed": runpy_passed, "detail": runpy_detail}
checks.append(check6)

# --- Check 7: Content is industry-specific (not a generic template) ---
# Must mention CDM-related terms: EDC, 数据, or 数据库 in body
cdm_terms = ["EDC", "数据管理", "数据清洗", "数据库", "21 CFR", "电子记录", "核查"]
full_text = md_text
found_cdm = [t for t in cdm_terms if t in full_text]
check7 = {
    "name": "content_is_industry_specific_not_generic",
    "passed": len(found_cdm) >= 2,
    "detail": (
        f"Found CDM-specific terms: {found_cdm}" if len(found_cdm) >= 2
        else f"Only found {found_cdm}; expected >= 2 of {cdm_terms}. Content appears too generic."
    )
}
checks.append(check7)

# --- Score calculation ---
passed_checks = [c for c in checks if c["passed"]]
score = round(len(passed_checks) / len(checks), 4)
all_passed = all(c["passed"] for c in checks)

final_result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(final_result, ensure_ascii=False, indent=2))