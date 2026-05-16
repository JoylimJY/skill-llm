import sys
import os
import re
import json
from pathlib import Path

workspace = sys.argv[1]

checks = []
score = 0.0
max_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global score, max_score
    max_score += weight
    if passed:
        score += weight

# ─────────────────────────────────────────────────────────────
# HELPER: read file safely
# ─────────────────────────────────────────────────────────────
def read_file(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return None

# ─────────────────────────────────────────────────────────────
# 1. tasks/todo.md checks
# ─────────────────────────────────────────────────────────────
todo_path = os.path.join(workspace, "tasks", "todo.md")
todo_content = read_file(todo_path)

if todo_content is None:
    add_check("todo.md exists", False, "tasks/todo.md not found", weight=1.0)
    # add dummy checks so they all fail
    for name in ["todo.md has checkable items", "todo.md has review section"]:
        add_check(name, False, "tasks/todo.md missing", weight=1.0)
else:
    add_check("todo.md exists", True, "tasks/todo.md found", weight=1.0)

    # checkable items: lines starting with "- [ ]" or "- [x]"
    checkable = re.findall(r'- \[[ xX]\]', todo_content)
    add_check(
        "todo.md has checkable items",
        len(checkable) >= 3,
        f"Found {len(checkable)} checkable items (need ≥3)",
        weight=1.0
    )

    # review section
    has_review = bool(re.search(r'##\s*(review|results|outcome)', todo_content, re.IGNORECASE))
    add_check(
        "todo.md has review section",
        has_review,
        "Review/Results section found" if has_review else "No review/results section found in todo.md",
        weight=1.0
    )

# ─────────────────────────────────────────────────────────────
# 2. tasks/lessons.md checks  (Phase 1+2 Enhanced Format)
# ─────────────────────────────────────────────────────────────
lessons_path = os.path.join(workspace, "tasks", "lessons.md")
lessons_content = read_file(lessons_path)

if lessons_content is None:
    add_check("lessons.md exists", False, "tasks/lessons.md not found", weight=1.0)
    for name in [
        "lessons.md has LRN-YYYYMMDD-XXX ID",
        "lessons.md has Priority field",
        "lessons.md has Status field with valid value",
        "lessons.md has Area field",
        "lessons.md has Pattern-Key field",
        "lessons.md has Summary section",
        "lessons.md has Details section",
        "lessons.md has Applied to section",
        "lessons.md has Metadata section with Recurrence-Count",
        "lessons.md has Source field",
        "lessons.md Status is valid lesson status (not error/feat status)",
    ]:
        add_check(name, False, "tasks/lessons.md missing", weight=1.0)
else:
    add_check("lessons.md exists", True, "tasks/lessons.md found", weight=1.0)

    # LRN ID format
    lrn_id_match = re.search(r'LRN-\d{8}-[A-Za-z0-9]{3}', lessons_content)
    add_check(
        "lessons.md has LRN-YYYYMMDD-XXX ID",
        bool(lrn_id_match),
        f"Found ID: {lrn_id_match.group(0) if lrn_id_match else 'NONE'}",
        weight=2.0
    )

    # Priority field
    priority_match = re.search(r'\*\*Priority\*\*\s*:\s*(low|medium|high|critical)', lessons_content, re.IGNORECASE)
    add_check(
        "lessons.md has Priority field",
        bool(priority_match),
        f"Priority value: {priority_match.group(1) if priority_match else 'NOT FOUND'}",
        weight=1.5
    )

    # Status with valid LESSON values (pending | in_progress | resolved | promoted)
    status_match = re.search(r'\*\*Status\*\*\s*:\s*(pending|in_progress|resolved|promoted)', lessons_content, re.IGNORECASE)
    add_check(
        "lessons.md has Status field with valid value",
        bool(status_match),
        f"Status value: {status_match.group(1) if status_match else 'NOT FOUND or invalid (monitored/on_roadmap not valid here)'}",
        weight=1.5
    )

    # Area field
    area_match = re.search(r'\*\*Area\*\*\s*:\s*(backend|infra|tests|docs|config)', lessons_content, re.IGNORECASE)
    add_check(
        "lessons.md has Area field",
        bool(area_match),
        f"Area value: {area_match.group(1) if area_match else 'NOT FOUND'}",
        weight=1.5
    )

    # Pattern-Key field
    pattern_key_match = re.search(r'\*\*Pattern-Key\*\*\s*:\s*\S+\.\S+', lessons_content)
    add_check(
        "lessons.md has Pattern-Key field",
        bool(pattern_key_match),
        f"Pattern-Key: {pattern_key_match.group(0) if pattern_key_match else 'NOT FOUND or malformed (should be category.pattern_name)'}",
        weight=1.5
    )

    # ### Summary section
    has_summary = bool(re.search(r'###\s*Summary', lessons_content, re.IGNORECASE))
    add_check("lessons.md has Summary section", has_summary,
              "### Summary found" if has_summary else "### Summary section missing", weight=1.0)

    # ### Details section
    has_details = bool(re.search(r'###\s*Details', lessons_content, re.IGNORECASE))
    add_check("lessons.md has Details section", has_details,
              "### Details found" if has_details else "### Details section missing", weight=1.0)

    # ### Applied to section
    has_applied = bool(re.search(r'###\s*Applied\s+to', lessons_content, re.IGNORECASE))
    add_check("lessons.md has Applied to section", has_applied,
              "### Applied to found" if has_applied else "### Applied to section missing", weight=1.0)

    # ### Metadata section with Recurrence-Count
    has_metadata_section = bool(re.search(r'###\s*Metadata', lessons_content, re.IGNORECASE))
    has_recurrence = bool(re.search(r'Recurrence-Count\s*:\s*\d+', lessons_content))
    add_check(
        "lessons.md has Metadata section with Recurrence-Count",
        has_metadata_section and has_recurrence,
        f"Metadata section: {has_metadata_section}, Recurrence-Count: {has_recurrence}",
        weight=1.5
    )

    # Source field in Metadata
    source_match = re.search(r'Source\s*:\s*(correction|insight|user_feedback)', lessons_content, re.IGNORECASE)
    add_check(
        "lessons.md has Source field",
        bool(source_match),
        f"Source: {source_match.group(1) if source_match else 'NOT FOUND'}",
        weight=1.0
    )

    # Confirm Status is NOT an error/feature status value
    wrong_status = re.search(r'\*\*Status\*\*\s*:\s*(monitored|on_roadmap)', lessons_content, re.IGNORECASE)
    add_check(
        "lessons.md Status is valid lesson status (not error/feat status)",
        not bool(wrong_status),
        "Status correctly uses lesson values (not error/feature-specific values)" if not wrong_status
        else f"Wrong status value for lessons.md: {wrong_status.group(1)}",
        weight=1.5
    )

# ─────────────────────────────────────────────────────────────
# 3. tasks/errors.md checks  (Phase 2 ERR format)
# ─────────────────────────────────────────────────────────────
errors_path = os.path.join(workspace, "tasks", "errors.md")
errors_content = read_file(errors_path)

if errors_content is None:
    add_check("errors.md exists", False, "tasks/errors.md not found", weight=1.0)
    for name in [
        "errors.md has ERR-YYYYMMDD-XXX ID",
        "errors.md has Reproducible field",
        "errors.md has Status with valid error status",
        "errors.md has error output/detail section",
        "errors.md does NOT use LRN or FEAT prefix",
    ]:
        add_check(name, False, "tasks/errors.md missing", weight=1.0)
else:
    add_check("errors.md exists", True, "tasks/errors.md found", weight=1.0)

    # ERR ID format
    err_id_match = re.search(r'ERR-\d{8}-[A-Za-z0-9]{3}', errors_content)
    add_check(
        "errors.md has ERR-YYYYMMDD-XXX ID",
        bool(err_id_match),
        f"Found ID: {err_id_match.group(0) if err_id_match else 'NONE - must use ERR- prefix not LRN- or FEAT-'}",
        weight=2.0
    )

    # Reproducible field (unique to errors)
    reproducible_match = re.search(r'\*\*Reproducible\*\*\s*:\s*(yes|no|unknown)', errors_content, re.IGNORECASE)
    add_check(
        "errors.md has Reproducible field",
        bool(reproducible_match),
        f"Reproducible: {reproducible_match.group(1) if reproducible_match else 'NOT FOUND - this field is unique to errors.md'}",
        weight=2.0
    )

    # Status valid for errors: pending | in_progress | resolved | monitored
    err_status_match = re.search(r'\*\*Status\*\*\s*:\s*(pending|in_progress|resolved|monitored)', errors_content, re.IGNORECASE)
    add_check(
        "errors.md has Status with valid error status",
        bool(err_status_match),
        f"Status: {err_status_match.group(1) if err_status_match else 'NOT FOUND or invalid (promoted/on_roadmap not valid here)'}",
        weight=1.5
    )

    # Error output section (Summary or Error Output)
    has_err_output = bool(re.search(r'###\s*(Summary|Error Output|Context)', errors_content, re.IGNORECASE))
    add_check(
        "errors.md has error output/detail section",
        has_err_output,
        "Error detail sections found" if has_err_output else "No ### Summary / Error Output / Context sections",
        weight=1.0
    )

    # Does NOT use LRN or FEAT prefix  
    wrong_prefix = re.search(r'(LRN|FEAT)-\d{8}-', errors_content)
    add_check(
        "errors.md does NOT use LRN or FEAT prefix",
        not bool(wrong_prefix),
        "Correct ERR prefix used" if not wrong_prefix else f"Wrong prefix found: {wrong_prefix.group(0)}",
        weight=1.0
    )

# ─────────────────────────────────────────────────────────────
# 4. tasks/feature_requests.md checks  (Phase 2 FEAT format)
# ─────────────────────────────────────────────────────────────
feat_path = os.path.join(workspace, "tasks", "feature_requests.md")
feat_content = read_file(feat_path)

if feat_content is None:
    add_check("feature_requests.md exists", False, "tasks/feature_requests.md not found", weight=1.0)
    for name in [
        "feature_requests.md has FEAT-YYYYMMDD-XXX ID",
        "feature_requests.md has Frequency field",
        "feature_requests.md has Complexity Estimate",
        "feature_requests.md has Status with valid feature status",
        "feature_requests.md does NOT use LRN or ERR prefix",
    ]:
        add_check(name, False, "tasks/feature_requests.md missing", weight=1.0)
else:
    add_check("feature_requests.md exists", True, "tasks/feature_requests.md found", weight=1.0)

    # FEAT ID format
    feat_id_match = re.search(r'FEAT-\d{8}-[A-Za-z0-9]{3}', feat_content)
    add_check(
        "feature_requests.md has FEAT-YYYYMMDD-XXX ID",
        bool(feat_id_match),
        f"Found ID: {feat_id_match.group(0) if feat_id_match else 'NONE - must use FEAT- prefix'}",
        weight=2.0
    )

    # Frequency field (unique to features): first_time | recurring | blocker
    freq_match = re.search(r'\*\*Frequency\*\*\s*:\s*(first_time|recurring|blocker)', feat_content, re.IGNORECASE)
    add_check(
        "feature_requests.md has Frequency field",
        bool(freq_match),
        f"Frequency: {freq_match.group(1) if freq_match else 'NOT FOUND - this field is unique to feature_requests.md'}",
        weight=2.0
    )

    # Complexity Estimate
    complexity_match = re.search(r'Complexity\s+Estimate[:\s]*(simple|medium|complex)', feat_content, re.IGNORECASE)
    add_check(
        "feature_requests.md has Complexity Estimate",
        bool(complexity_match),
        f"Complexity: {complexity_match.group(1) if complexity_match else 'NOT FOUND'}",
        weight=1.5
    )

    # Status valid for features: pending | in_progress | on_roadmap
    feat_status_match = re.search(r'\*\*Status\*\*\s*:\s*(pending|in_progress|on_roadmap)', feat_content, re.IGNORECASE)
    add_check(
        "feature_requests.md has Status with valid feature status",
        bool(feat_status_match),
        f"Status: {feat_status_match.group(1) if feat_status_match else 'NOT FOUND or invalid (promoted/monitored not valid here)'}",
        weight=1.5
    )

    # Does NOT use LRN or ERR prefix
    wrong_feat_prefix = re.search(r'(LRN|ERR)-\d{8}-', feat_content)
    add_check(
        "feature_requests.md does NOT use LRN or ERR prefix",
        not bool(wrong_feat_prefix),
        "Correct FEAT prefix used" if not wrong_feat_prefix else f"Wrong prefix: {wrong_feat_prefix.group(0)}",
        weight=1.0
    )

# ─────────────────────────────────────────────────────────────
# 5. File separation cross-check
# ─────────────────────────────────────────────────────────────
# Ensure lessons.md doesn't contain ERR/FEAT entries and vice versa
if lessons_content:
    no_err_in_lessons = not bool(re.search(r'ERR-\d{8}-', lessons_content))
    no_feat_in_lessons = not bool(re.search(r'FEAT-\d{8}-', lessons_content))
    add_check(
        "lessons.md does not contain ERR or FEAT entries (proper file separation)",
        no_err_in_lessons and no_feat_in_lessons,
        "Proper separation: errors/features not mixed into lessons.md"
        if (no_err_in_lessons and no_feat_in_lessons)
        else "lessons.md incorrectly contains ERR or FEAT entries",
        weight=1.5
    )

if errors_content and feat_content:
    # Errors and features shouldn't contain LRN entries  
    no_lrn_in_errors = not bool(re.search(r'LRN-\d{8}-', errors_content))
    no_lrn_in_feats = not bool(re.search(r'LRN-\d{8}-', feat_content))
    add_check(
        "errors.md and feature_requests.md do not contain LRN entries",
        no_lrn_in_errors and no_lrn_in_feats,
        "Proper file separation maintained" if (no_lrn_in_errors and no_lrn_in_feats)
        else "LRN entries incorrectly placed in errors or feature_requests files",
        weight=1.0
    )

# ─────────────────────────────────────────────────────────────
# Final scoring
# ─────────────────────────────────────────────────────────────
final_score = round(score / max_score, 4) if max_score > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed and final_score >= 0.80,
    "score": final_score,
    "checks": checks
}

print(json.dumps(result, indent=2))