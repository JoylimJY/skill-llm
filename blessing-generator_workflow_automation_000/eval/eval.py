import sys
import json
import subprocess
import hashlib
from pathlib import Path

workspace = Path(sys.argv[1])

results = []

def check(name, passed, detail=""):
    results.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ── locate output file ────────────────────────────────────────────────
report_files = list(workspace.rglob("blessings_report.json"))

if not report_files:
    check("output_file_exists", False, "blessings_report.json not found anywhere in workspace")
    print(json.dumps({"passed": False, "score": 0.0, "checks": results}))
    sys.exit(0)

report_path = report_files[0]
check("output_file_exists", True, str(report_path))

try:
    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)
except Exception as e:
    check("output_file_parseable", False, f"JSON parse error: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": results}))
    sys.exit(0)

check("output_file_parseable", True)

# ── expected mapping (what the agent MUST resolve from SKILL.md) ──────
# Maps each request to the canonical CLI parameters the script enforces.
EXPECTED_PARAMS = {
    "req_001": {"festival": "春节",    "target": "爸爸",    "relation": "长辈", "style": "正式", "length": "short"},
    "req_002": {"festival": "妇女节",  "target": "同事小李","relation": "平辈", "style": "幽默", "length": "medium"},
    "req_003": {"festival": "生日",    "target": "外孙女",  "relation": "晚辈", "style": "押韵", "length": "long"},
    "req_004": {"festival": "升职加薪","target": "老板",    "relation": "长辈", "style": "文艺", "length": "medium"},
    "req_005": {"festival": "中秋节",  "target": "奶奶",    "relation": "长辈", "style": "温情", "length": "short"},
}

def compute_expected_seed(festival, target, relation, style, length):
    raw = f"{festival}{target}{relation}{style}{length}"
    return hashlib.md5(raw.encode()).hexdigest()[:6]

# ── check report structure ────────────────────────────────────────────
has_top_level_list = isinstance(report, list)
has_top_level_dict = isinstance(report, dict)

if has_top_level_dict:
    # Accept {"req_001": {...}, ...} or {"results": [...], ...}
    if "results" in report and isinstance(report["results"], list):
        entries_raw = {e.get("id") or e.get("request_id"): e for e in report["results"] if isinstance(e, dict)}
    else:
        entries_raw = report  # keyed by req_id directly
elif has_top_level_list:
    entries_raw = {e.get("id") or e.get("request_id"): e for e in report if isinstance(e, dict)}
else:
    check("report_structure_valid", False, "Report must be a JSON object or list of objects")
    print(json.dumps({"passed": False, "score": 0.0, "checks": results}))
    sys.exit(0)

check("report_structure_valid", True, f"Detected {len(entries_raw)} entries")

# ── per-request validation ─────────────────────────────────────────────
all_req_passed = True
req_scores = []

for req_id, exp in EXPECTED_PARAMS.items():
    entry = entries_raw.get(req_id)
    if entry is None:
        c = check(f"{req_id}_present", False, f"Entry for {req_id} missing from report")
        all_req_passed = False
        req_scores.append(0)
        continue
    check(f"{req_id}_present", True)

    # The script produces a deterministic seed from exact params.
    # If the agent called the script with correct canonical params,
    # the output will contain the expected seed.
    expected_seed = compute_expected_seed(
        exp["festival"], exp["target"], exp["relation"], exp["style"], exp["length"]
    )

    # Find blessing content: could be stored as "versions", "content", "output", "text", or the raw string.
    content_blob = ""
    if isinstance(entry, dict):
        for key in ("versions", "content", "output", "text", "blessing", "result", "body"):
            val = entry.get(key)
            if val:
                content_blob = str(val)
                break
        if not content_blob:
            # Flatten all string values
            content_blob = " ".join(str(v) for v in entry.values() if isinstance(v, str))
    else:
        content_blob = str(entry)

    # Check that the seed from correct params appears in the content
    seed_found = expected_seed in content_blob
    check(
        f"{req_id}_correct_params_used",
        seed_found,
        f"Expected seed '{expected_seed}' (from correct canonical params: festival={exp['festival']}, "
        f"relation={exp['relation']}, style={exp['style']}, length={exp['length']}) "
        f"{'found' if seed_found else 'NOT found'} in entry content"
    )
    if not seed_found:
        all_req_passed = False
        req_scores.append(0)
    else:
        req_scores.append(1)

    # Check that all 3 versions are present
    has_v1 = "版本一" in content_blob or "v1" in content_blob
    has_v2 = "版本二" in content_blob or "v2" in content_blob
    has_v3 = "版本三" in content_blob or "v3" in content_blob
    three_versions = has_v1 and has_v2 and has_v3
    check(
        f"{req_id}_three_versions_captured",
        three_versions,
        f"3 versions present: v1={has_v1}, v2={has_v2}, v3={has_v3}"
    )
    if not three_versions:
        all_req_passed = False

# ── scoring ───────────────────────────────────────────────────────────
param_score = sum(req_scores) / len(req_scores) if req_scores else 0.0
structure_bonus = 0.1 if len(entries_raw) >= 5 else 0.0
final_score = round(min(1.0, param_score * 0.9 + structure_bonus), 3)

overall_passed = all_req_passed and final_score >= 0.85

print(json.dumps({
    "passed": overall_passed,
    "score": final_score,
    "checks": results
}, ensure_ascii=False, indent=2))