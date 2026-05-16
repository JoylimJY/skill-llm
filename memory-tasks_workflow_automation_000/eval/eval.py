#!/usr/bin/env python3
"""
Evaluation script for the drug-discovery task-tracking exam.

Checks:
1. Schema note at memory/schema/Task.md is complete and valid
2. Exactly 3 proper Task notes exist (excluding WRONG_EXAMPLE)
3. Each task note has BOTH frontmatter metadata fields AND observation-style body fields (dual-representation)
4. The crystallography task is marked 'blocked' with at least 1 entry in blockers
5. Each task has a steps array in frontmatter (list with ≥3 items)
6. Each task has current_step as an integer in frontmatter
7. Each task body contains step checkboxes [ ] or [x]
8. Each task body contains ## Steps and ## Context sections
"""

import sys
import json
import re
from pathlib import Path

try:
    import frontmatter
    import yaml
except ImportError:
    print(json.dumps({"passed": False, "score": 0.0, "checks": [
        {"name": "dependencies", "passed": False, "detail": "frontmatter or yaml not importable"}
    ]}))
    sys.exit(0)

def load_fm(path):
    """Load a markdown file with YAML frontmatter. Returns (metadata_dict, content_str)."""
    try:
        post = frontmatter.load(str(path))
        return dict(post.metadata), post.content
    except Exception as e:
        return None, str(e)

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []

# ── Helper ────────────────────────────────────────────────────────────────────
def make_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})
    return bool(passed)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 1: Schema note exists and is substantive
# ─────────────────────────────────────────────────────────────────────────────
schema_path = workspace / "memory" / "schema" / "Task.md"
schema_ok = False
try:
    meta, content = load_fm(schema_path)
    if meta is None:
        make_check("schema_exists_and_parseable", False, f"Could not parse schema file: {content}")
    else:
        # Must have type: schema, entity: Task, and a schema block
        has_type = str(meta.get("type", "")).lower() == "schema"
        has_entity = str(meta.get("entity", "")) == "Task"
        has_schema_block = "schema" in meta and isinstance(meta["schema"], dict)
        has_status_field = has_schema_block and "status?(enum)" in meta.get("schema", {})
        has_steps_field = has_schema_block and "steps?(array)" in meta.get("schema", {})
        # Also accept slight variations like 'status' or 'status?' 
        if not has_status_field:
            # try alternate keys
            schema_keys = list(meta.get("schema", {}).keys()) if has_schema_block else []
            has_status_field = any("status" in k for k in schema_keys)
            has_steps_field = any("steps" in k for k in schema_keys)

        stub_marker = "INCOMPLETE" in content or "DO NOT USE" in content
        schema_ok = has_type and has_entity and has_schema_block and has_status_field and has_steps_field and not stub_marker
        detail = (f"type={'schema' if has_type else meta.get('type','?')}, "
                  f"entity={'Task' if has_entity else meta.get('entity','?')}, "
                  f"has_schema_block={has_schema_block}, "
                  f"has_status={has_status_field}, has_steps={has_steps_field}, "
                  f"stub={stub_marker}")
        make_check("schema_complete_and_valid", schema_ok, detail)
except Exception as e:
    make_check("schema_complete_and_valid", False, f"Exception: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 2: Find all task notes (exclude WRONG_EXAMPLE)
# ─────────────────────────────────────────────────────────────────────────────
task_notes = []
try:
    # Search all markdown files for those with type: task (lowercase) in frontmatter
    # They may live in tasks/ or memory/ subdirectories
    for md_file in workspace.rglob("*.md"):
        if "WRONG_EXAMPLE" in md_file.name:
            continue
        if "schema" in str(md_file):
            continue
        meta, content = load_fm(md_file)
        if meta is None:
            continue
        note_type = str(meta.get("type", "")).lower().strip()
        if note_type == "task":
            task_notes.append((md_file, meta, content))

    make_check("three_task_notes_found",
               len(task_notes) >= 3,
               f"Found {len(task_notes)} task note(s) (need ≥3): {[str(p) for p,_,_ in task_notes]}")
except Exception as e:
    make_check("three_task_notes_found", False, f"Exception scanning for tasks: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 3: Dual-representation — frontmatter status + observation body field
# ─────────────────────────────────────────────────────────────────────────────
dual_rep_passed = 0
dual_rep_details = []
for path, meta, content in task_notes:
    fm_has_status = "status" in meta
    # Observation pattern: - [status] <value>
    body_has_status_obs = bool(re.search(r'-\s*\[status\]', content, re.IGNORECASE))
    ok = fm_has_status and body_has_status_obs
    if ok:
        dual_rep_passed += 1
    dual_rep_details.append(f"{path.name}: fm_status={fm_has_status}, obs_status={body_has_status_obs}")

make_check("dual_representation_status_field",
           dual_rep_passed == len(task_notes) and len(task_notes) >= 3,
           "; ".join(dual_rep_details))

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 4: One task is 'blocked' with non-empty blockers
# ─────────────────────────────────────────────────────────────────────────────
blocked_tasks = []
try:
    for path, meta, content in task_notes:
        status = str(meta.get("status", "")).lower()
        blockers = meta.get("blockers", [])
        if status == "blocked":
            if isinstance(blockers, list) and len(blockers) >= 1:
                blocked_tasks.append(path.name)
            elif isinstance(blockers, str) and blockers.strip():
                blocked_tasks.append(path.name)

    make_check("blocked_task_with_blockers",
               len(blocked_tasks) >= 1,
               f"Blocked tasks with blockers array: {blocked_tasks}")
except Exception as e:
    make_check("blocked_task_with_blockers", False, f"Exception: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 5: Steps array in frontmatter (≥3 items each)
# ─────────────────────────────────────────────────────────────────────────────
steps_fm_passed = 0
steps_details = []
for path, meta, content in task_notes:
    steps = meta.get("steps", None)
    if isinstance(steps, list) and len(steps) >= 3:
        steps_fm_passed += 1
        steps_details.append(f"{path.name}: {len(steps)} steps ✓")
    else:
        steps_details.append(f"{path.name}: steps={repr(steps)} ✗")

make_check("steps_array_in_frontmatter",
           steps_fm_passed == len(task_notes) and len(task_notes) >= 3,
           "; ".join(steps_details))

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 6: current_step is integer in frontmatter
# ─────────────────────────────────────────────────────────────────────────────
cur_step_passed = 0
cur_step_details = []
for path, meta, content in task_notes:
    cs = meta.get("current_step", None)
    if isinstance(cs, int):
        cur_step_passed += 1
        cur_step_details.append(f"{path.name}: current_step={cs} (int) ✓")
    else:
        cur_step_details.append(f"{path.name}: current_step={repr(cs)} (type={type(cs).__name__}) ✗")

make_check("current_step_is_integer_in_frontmatter",
           cur_step_passed == len(task_notes) and len(task_notes) >= 3,
           "; ".join(cur_step_details))

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 7: Body contains step checkboxes [ ] or [x]
# ─────────────────────────────────────────────────────────────────────────────
checkbox_passed = 0
checkbox_details = []
checkbox_pattern = re.compile(r'\d+\.\s+\[[ xX]\]')
for path, meta, content in task_notes:
    if checkbox_pattern.search(content):
        checkbox_passed += 1
        checkbox_details.append(f"{path.name}: checkboxes found ✓")
    else:
        checkbox_details.append(f"{path.name}: no '1. [ ] ...' pattern ✗")

make_check("step_checkboxes_in_body",
           checkbox_passed == len(task_notes) and len(task_notes) >= 3,
           "; ".join(checkbox_details))

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 8: Body has ## Steps and ## Context sections
# ─────────────────────────────────────────────────────────────────────────────
sections_passed = 0
sections_details = []
for path, meta, content in task_notes:
    has_steps_section = bool(re.search(r'^##\s+Steps', content, re.MULTILINE | re.IGNORECASE))
    has_context_section = bool(re.search(r'^##\s+Context', content, re.MULTILINE | re.IGNORECASE))
    if has_steps_section and has_context_section:
        sections_passed += 1
        sections_details.append(f"{path.name}: both sections ✓")
    else:
        sections_details.append(f"{path.name}: steps={has_steps_section}, context={has_context_section} ✗")

make_check("body_has_steps_and_context_sections",
           sections_passed == len(task_notes) and len(task_notes) >= 3,
           "; ".join(sections_details))

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 9: observation fields also include [description] and [current_step]
# ─────────────────────────────────────────────────────────────────────────────
obs_completeness_passed = 0
obs_details = []
for path, meta, content in task_notes:
    has_desc_obs = bool(re.search(r'-\s*\[description\]', content, re.IGNORECASE))
    has_cur_step_obs = bool(re.search(r'-\s*\[current_step\]', content, re.IGNORECASE))
    if has_desc_obs and has_cur_step_obs:
        obs_completeness_passed += 1
        obs_details.append(f"{path.name}: [description] and [current_step] obs ✓")
    else:
        obs_details.append(f"{path.name}: desc={has_desc_obs}, cur_step={has_cur_step_obs} ✗")

make_check("observation_fields_include_description_and_current_step",
           obs_completeness_passed == len(task_notes) and len(task_notes) >= 3,
           "; ".join(obs_details))

# ─────────────────────────────────────────────────────────────────────────────
# Score & result
# ─────────────────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 3) if total > 0 else 0.0

# Hard gates: must have 3 tasks AND dual-representation AND schema complete
hard_gate = (
    checks[1]["passed"] and   # three tasks found
    checks[2]["passed"] and   # dual representation
    checks[0]["passed"]       # schema complete
)

final_passed = hard_gate and score >= 0.75

print(json.dumps({
    "passed": final_passed,
    "score": score,
    "checks": checks
}, indent=2))