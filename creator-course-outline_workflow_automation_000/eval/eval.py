import sys
import json
import pathlib

workspace = pathlib.Path(sys.argv[1])

checks = []
passed_all = True

def fail(name, detail):
    global passed_all
    passed_all = False
    checks.append({"name": name, "passed": False, "detail": detail})

def ok(name, detail):
    checks.append({"name": name, "passed": True, "detail": detail})

# ── 1. Find the output file ──────────────────────────────────────────────────
OUTPUT_FILENAME = "course_outline_urban-vertical-farming-community.json"
candidates = list(workspace.rglob(OUTPUT_FILENAME))
if not candidates:
    # Also accept reasonable slug variants
    candidates = list(workspace.rglob("course_outline_urban*.json"))

if not candidates:
    fail("output_file_exists", f"Could not find any file matching 'course_outline_urban*.json' under {workspace}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

output_file = candidates[0]
ok("output_file_exists", f"Found output file: {output_file}")

# ── 2. Parse JSON ────────────────────────────────────────────────────────────
try:
    with open(output_file, encoding="utf-8") as f:
        data = json.load(f)
    ok("output_parseable", "Output file is valid JSON.")
except Exception as e:
    fail("output_parseable", f"Failed to parse JSON: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── 3. Required sections present ─────────────────────────────────────────────
REQUIRED_SECTIONS = [
    "task_brief",
    "pending_confirmations",
    "course_objectives",
    "module_structure",
    "unit_objectives",
    "assignments",
    "milestones",
    "common_blockers"
]
missing_sections = [s for s in REQUIRED_SECTIONS if s not in data]
if missing_sections:
    fail("required_sections", f"Missing required sections: {missing_sections}")
else:
    ok("required_sections", "All 8 required sections are present.")

# ── 4. task_brief is a non-empty string ──────────────────────────────────────
try:
    tb = data.get("task_brief", "")
    if isinstance(tb, str) and len(tb.strip()) >= 20:
        ok("task_brief_present", f"task_brief is present and non-trivial (len={len(tb)}).")
    else:
        fail("task_brief_present", f"task_brief is missing or too short: {repr(tb)[:80]}")
except Exception as e:
    fail("task_brief_present", f"Error reading task_brief: {e}")

# ── 5. pending_confirmations is a list (may be empty but must exist) ─────────
try:
    pc = data.get("pending_confirmations", None)
    if isinstance(pc, list):
        ok("pending_confirmations_is_list", f"pending_confirmations is a list with {len(pc)} items.")
    else:
        fail("pending_confirmations_is_list", f"pending_confirmations must be a list, got: {type(pc)}")
except Exception as e:
    fail("pending_confirmations_is_list", f"Error: {e}")

# ── 6. course_objectives: 2–6 items ──────────────────────────────────────────
try:
    co = data.get("course_objectives", [])
    if isinstance(co, list) and 2 <= len(co) <= 6:
        ok("course_objectives_count", f"course_objectives has {len(co)} items (valid: 2–6).")
    else:
        fail("course_objectives_count", f"course_objectives must have 2–6 items, got {len(co) if isinstance(co, list) else co}.")
except Exception as e:
    fail("course_objectives_count", f"Error: {e}")

# ── 7. module_structure: 3–8 modules with correct schema ─────────────────────
try:
    ms = data.get("module_structure", [])
    valid_diffs = {"beginner", "intermediate", "advanced"}
    if not isinstance(ms, list) or not (3 <= len(ms) <= 8):
        fail("module_structure_count", f"module_structure must have 3–8 items, got {len(ms) if isinstance(ms, list) else ms}.")
    else:
        ok("module_structure_count", f"module_structure has {len(ms)} modules.")
        # Check module_id format: M01, M02, ...
        bad_ids = [m.get("module_id", "") for m in ms if not str(m.get("module_id","")).startswith("M") or len(str(m.get("module_id",""))) != 3]
        if bad_ids:
            fail("module_id_format", f"Some module_ids have wrong format (expected M01...M08): {bad_ids}")
        else:
            ok("module_id_format", "All module_ids use correct zero-padded format (M01, M02, ...).")
        # Check difficulty_level values
        bad_diffs = [m.get("difficulty_level","") for m in ms if m.get("difficulty_level","") not in valid_diffs]
        if bad_diffs:
            fail("module_difficulty_level", f"Invalid difficulty_level values found: {bad_diffs}. Must be one of {valid_diffs}.")
        else:
            ok("module_difficulty_level", "All modules have valid difficulty_level values.")
        # Check duration_hours is a number
        bad_dur = [m for m in ms if not isinstance(m.get("duration_hours", None), (int, float))]
        if bad_dur:
            fail("module_duration_hours", f"{len(bad_dur)} modules have non-numeric duration_hours.")
        else:
            ok("module_duration_hours", "All modules have numeric duration_hours.")
except Exception as e:
    fail("module_structure_schema", f"Error validating module_structure: {e}")

# ── 8. assignments: min 2, correct format enum, correct id format ─────────────
try:
    asn = data.get("assignments", [])
    valid_formats = {"written", "project", "quiz", "peer-review", "presentation"}
    if not isinstance(asn, list) or len(asn) < 2:
        fail("assignments_count", f"assignments must have at least 2 items, got {len(asn) if isinstance(asn,list) else asn}.")
    else:
        ok("assignments_count", f"assignments has {len(asn)} items.")
        bad_fmt = [a.get("format","") for a in asn if a.get("format","") not in valid_formats]
        if bad_fmt:
            fail("assignment_format_enum", f"Invalid assignment format(s): {bad_fmt}. Valid: {valid_formats}.")
        else:
            ok("assignment_format_enum", "All assignments use valid format enum values.")
        # Check A01, A02, ...
        bad_aids = [a.get("assignment_id","") for a in asn if not str(a.get("assignment_id","")).startswith("A") or len(str(a.get("assignment_id",""))) != 3]
        if bad_aids:
            fail("assignment_id_format", f"Invalid assignment_id format(s): {bad_aids}. Expected A01, A02, ...")
        else:
            ok("assignment_id_format", "All assignment_ids use correct zero-padded format.")
        # due_after_module must be boolean
        bad_dam = [a for a in asn if not isinstance(a.get("due_after_module", None), bool)]
        if bad_dam:
            fail("assignment_due_after_module", f"{len(bad_dam)} assignments have non-boolean due_after_module.")
        else:
            ok("assignment_due_after_module", "All assignments have boolean due_after_module.")
except Exception as e:
    fail("assignments_schema", f"Error validating assignments: {e}")

# ── 9. milestones: min 2, correct milestone_type enum, correct id format ──────
try:
    mls = data.get("milestones", [])
    valid_types = {"checkpoint", "capstone", "review", "onboarding"}
    if not isinstance(mls, list) or len(mls) < 2:
        fail("milestones_count", f"milestones must have at least 2 items, got {len(mls) if isinstance(mls,list) else mls}.")
    else:
        ok("milestones_count", f"milestones has {len(mls)} items.")
        bad_mt = [m.get("milestone_type","") for m in mls if m.get("milestone_type","") not in valid_types]
        if bad_mt:
            fail("milestone_type_enum", f"Invalid milestone_type value(s): {bad_mt}. Valid: {valid_types}.")
        else:
            ok("milestone_type_enum", "All milestones use valid milestone_type enum values.")
        # Check MS01, MS02, ...
        bad_mids = [m.get("milestone_id","") for m in mls if not str(m.get("milestone_id","")).startswith("MS") or len(str(m.get("milestone_id",""))) < 4]
        if bad_mids:
            fail("milestone_id_format", f"Invalid milestone_id format(s): {bad_mids}. Expected MS01, MS02, ...")
        else:
            ok("milestone_id_format", "All milestone_ids use correct zero-padded format.")
except Exception as e:
    fail("milestones_schema", f"Error validating milestones: {e}")

# ── 10. common_blockers: min 3 items ─────────────────────────────────────────
try:
    cb = data.get("common_blockers", [])
    if isinstance(cb, list) and len(cb) >= 3:
        ok("common_blockers_count", f"common_blockers has {len(cb)} items (≥3 required).")
    else:
        fail("common_blockers_count", f"common_blockers must have ≥3 items, got {len(cb) if isinstance(cb,list) else cb}.")
except Exception as e:
    fail("common_blockers_count", f"Error: {e}")

# ── 11. unit_objectives linked to existing module_ids ─────────────────────────
try:
    ms_data = data.get("module_structure", [])
    existing_mids = {m.get("module_id") for m in ms_data}
    uo = data.get("unit_objectives", [])
    if not isinstance(uo, list) or len(uo) == 0:
        fail("unit_objectives_present", "unit_objectives must be a non-empty list.")
    else:
        bad_links = [u for u in uo if u.get("module_id") not in existing_mids]
        if bad_links:
            fail("unit_objectives_module_links", f"{len(bad_links)} unit_objectives reference non-existent module_ids.")
        else:
            ok("unit_objectives_module_links", "All unit_objectives are correctly linked to existing module_ids.")
        # Each unit must have at least 1 objective
        bad_obj = [u for u in uo if not isinstance(u.get("objectives",[]), list) or len(u.get("objectives",[])) < 1]
        if bad_obj:
            fail("unit_objectives_min_objectives", f"{len(bad_obj)} units have fewer than 1 objective.")
        else:
            ok("unit_objectives_min_objectives", "All units have at least 1 objective.")
except Exception as e:
    fail("unit_objectives_schema", f"Error validating unit_objectives: {e}")

# ── 12. Content relevance: course is about vertical farming / urban farming ────
try:
    course_text = json.dumps(data, ensure_ascii=False).lower()
    keywords = ["vertical", "farm", "urban", "community", "hydroponics", "plant", "grow", "soil", "crop", "agricult"]
    hits = [kw for kw in keywords if kw in course_text]
    if len(hits) >= 3:
        ok("content_relevance", f"Output content is relevant to vertical farming (matched keywords: {hits}).")
    else:
        fail("content_relevance", f"Output content does not appear relevant to urban vertical farming. Only matched: {hits}.")
except Exception as e:
    fail("content_relevance", f"Error checking content relevance: {e}")

# ── 13. Script was invoked (not hand-crafted naively): _meta present ──────────
try:
    meta = data.get("_meta", {})
    if isinstance(meta, dict) and "generated_by" in meta:
        ok("generated_by_run_script", f"_meta.generated_by present: {meta.get('generated_by')}. Script was likely invoked.")
    else:
        fail("generated_by_run_script", 
             "_meta.generated_by is missing. The agent likely did not invoke run.py and instead hand-crafted the output. "
             "The skill mandates using 'python3 scripts/run.py --input <...> --output <...>' when shell execution is available.")
except Exception as e:
    fail("generated_by_run_script", f"Error checking _meta: {e}")

# ── Scoring ───────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4) if total > 0 else 0.0
final_passed = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": final_passed,
    "score": score,
    "checks": checks
}, ensure_ascii=False, indent=2))