import sys
import json
import pathlib
import traceback

workspace = sys.argv[1] if len(sys.argv) > 1 else "/root"
home = pathlib.Path("/root")

checks = []
total_score = 0.0
max_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global total_score, max_score
    max_score += weight
    if passed:
        total_score += weight

# =====================================================================
# LOCATE THE NURSE CONFIG FILE
# =====================================================================
nurse_config_path = home / ".openclaw" / "workspace-nurse" / "auto-responder.json"

config = None
try:
    if not nurse_config_path.exists():
        add_check("nurse_config_exists", False, 
                  f"File not found at expected path: {nurse_config_path}", weight=3.0)
    else:
        with open(nurse_config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        add_check("nurse_config_exists", True, f"Found and parsed {nurse_config_path}", weight=3.0)
except json.JSONDecodeError as e:
    add_check("nurse_config_exists", False, f"JSON parse error: {e}", weight=3.0)
    config = None
except Exception as e:
    add_check("nurse_config_exists", False, f"Unexpected error: {e}", weight=3.0)
    config = None

if config is None:
    # Can't continue further checks
    result = {
        "passed": False,
        "score": 0.0,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)

# =====================================================================
# CHECK 1: enabled must be True (boolean)
# =====================================================================
try:
    enabled = config.get("enabled")
    passed = (enabled is True)
    add_check("enabled_is_true", passed,
              f"'enabled' = {repr(enabled)} (must be boolean true)", weight=1.0)
except Exception as e:
    add_check("enabled_is_true", False, f"Error: {e}", weight=1.0)

# =====================================================================
# CHECK 2: respectRequireMention must be False (boolean)
# =====================================================================
try:
    rrm = config.get("respectRequireMention")
    passed = (rrm is False)
    add_check("respectRequireMention_is_false", passed,
              f"'respectRequireMention' = {repr(rrm)} (must be boolean false to allow unreferenced triggers)", weight=1.0)
except Exception as e:
    add_check("respectRequireMention_is_false", False, f"Error: {e}", weight=1.0)

# =====================================================================
# CHECK 3: globalCooldownMinutes must be a number (int/float), not string
# =====================================================================
try:
    gcm = config.get("globalCooldownMinutes")
    passed = isinstance(gcm, (int, float)) and not isinstance(gcm, bool)
    add_check("globalCooldownMinutes_is_number", passed,
              f"'globalCooldownMinutes' = {repr(gcm)} (must be int/float, not string)", weight=1.0)
except Exception as e:
    add_check("globalCooldownMinutes_is_number", False, f"Error: {e}", weight=1.0)

# =====================================================================
# CHECK 4: maxResponsesPerMinute must be present and be a positive integer
# =====================================================================
try:
    mrpm = config.get("maxResponsesPerMinute")
    passed = isinstance(mrpm, int) and not isinstance(mrpm, bool) and mrpm > 0
    add_check("maxResponsesPerMinute_present_and_valid", passed,
              f"'maxResponsesPerMinute' = {repr(mrpm)} (must be positive int)", weight=0.5)
except Exception as e:
    add_check("maxResponsesPerMinute_present_and_valid", False, f"Error: {e}", weight=0.5)

# =====================================================================
# CHECK 5: topics must be a dict with at least 2 topics
# =====================================================================
topics = None
try:
    topics = config.get("topics")
    passed = isinstance(topics, dict) and len(topics) >= 2
    add_check("topics_is_dict_with_min_2", passed,
              f"'topics' has {len(topics) if isinstance(topics, dict) else 'N/A'} entries (need >= 2)", weight=1.5)
except Exception as e:
    add_check("topics_is_dict_with_min_2", False, f"Error: {e}", weight=1.5)
    topics = None

# =====================================================================
# CHECK 6: Each topic must have thread_ids as a list of INTEGERS (not strings)
# =====================================================================
if topics:
    try:
        all_ok = True
        details = []
        for tname, t in topics.items():
            if not isinstance(t, dict):
                all_ok = False
                details.append(f"Topic '{tname}' is not a dict")
                continue
            tids = t.get("thread_ids")
            if not isinstance(tids, list):
                all_ok = False
                details.append(f"Topic '{tname}' thread_ids is not a list: {repr(tids)}")
            else:
                for tid in tids:
                    if not isinstance(tid, int) or isinstance(tid, bool):
                        all_ok = False
                        details.append(f"Topic '{tname}' thread_ids contains non-int: {repr(tid)}")
        add_check("topic_thread_ids_are_int_lists", all_ok,
                  "All thread_ids are lists of integers" if all_ok else "; ".join(details), weight=2.0)
    except Exception as e:
        add_check("topic_thread_ids_are_int_lists", False, f"Error: {e}", weight=2.0)

# =====================================================================
# CHECK 7: Each topic must have keywords as a LIST (not a string)
# =====================================================================
if topics:
    try:
        all_ok = True
        details = []
        for tname, t in topics.items():
            if not isinstance(t, dict):
                continue
            kw = t.get("keywords")
            if not isinstance(kw, list):
                all_ok = False
                details.append(f"Topic '{tname}' keywords is {type(kw).__name__}, must be list")
            elif len(kw) == 0:
                all_ok = False
                details.append(f"Topic '{tname}' keywords list is empty")
        add_check("topic_keywords_are_lists", all_ok,
                  "All keywords are non-empty lists" if all_ok else "; ".join(details), weight=2.0)
    except Exception as e:
        add_check("topic_keywords_are_lists", False, f"Error: {e}", weight=2.0)

# =====================================================================
# CHECK 8: Each topic must have a responseTemplate string
# =====================================================================
if topics:
    try:
        all_ok = True
        details = []
        for tname, t in topics.items():
            if not isinstance(t, dict):
                continue
            rt = t.get("responseTemplate")
            if not isinstance(rt, str) or len(rt.strip()) == 0:
                all_ok = False
                details.append(f"Topic '{tname}' missing or empty responseTemplate")
        add_check("topic_responseTemplate_present", all_ok,
                  "All topics have responseTemplate" if all_ok else "; ".join(details), weight=1.5)
    except Exception as e:
        add_check("topic_responseTemplate_present", False, f"Error: {e}", weight=1.5)

# =====================================================================
# CHECK 9: At least one topic has 'exclude' list (for spam filtering)
# =====================================================================
if topics:
    try:
        has_exclude = any(
            isinstance(t, dict) and isinstance(t.get("exclude"), list) and len(t.get("exclude", [])) > 0
            for t in topics.values()
        )
        add_check("at_least_one_topic_has_exclude", has_exclude,
                  "At least one topic defines an 'exclude' list to filter noise" if has_exclude
                  else "No topic defines an 'exclude' list (required to filter spam/noise)", weight=1.0)
    except Exception as e:
        add_check("at_least_one_topic_has_exclude", False, f"Error: {e}", weight=1.0)

# =====================================================================
# CHECK 10: personalidades must be a dict matching topic names
# =====================================================================
try:
    personalidades = config.get("personalidades")
    if not isinstance(personalidades, dict) or len(personalidades) == 0:
        add_check("personalidades_is_valid_dict", False,
                  f"'personalidades' = {repr(personalidades)} (must be non-empty dict)", weight=1.0)
    else:
        # Must have entries corresponding to topic names
        topic_names = set(topics.keys()) if topics else set()
        persona_names = set(personalidades.keys())
        overlap = topic_names & persona_names
        passed = len(overlap) >= 1
        add_check("personalidades_is_valid_dict", passed,
                  f"personalidades keys {list(persona_names)} overlap with topics {list(topic_names)}: {list(overlap)}",
                  weight=1.0)
except Exception as e:
    add_check("personalidades_is_valid_dict", False, f"Error: {e}", weight=1.0)

# =====================================================================
# CHECK 11: At least one topic has mustInclude list (for agent-mention filtering)
# =====================================================================
if topics:
    try:
        has_must_include = any(
            isinstance(t, dict) and isinstance(t.get("mustInclude"), list) and len(t.get("mustInclude", [])) > 0
            for t in topics.values()
        )
        add_check("at_least_one_topic_has_mustInclude", has_must_include,
                  "At least one topic defines a 'mustInclude' list" if has_must_include
                  else "No topic defines 'mustInclude' (optional but expected for critical topics)", weight=0.5)
    except Exception as e:
        add_check("at_least_one_topic_has_mustInclude", False, f"Error: {e}", weight=0.5)

# =====================================================================
# CHECK 12: The responseTemplates contain meaningful content
#           (not just the bare broken "Nurse here" from old config)
# =====================================================================
if topics:
    try:
        trivial_templates = []
        for tname, t in topics.items():
            if not isinstance(t, dict):
                continue
            rt = t.get("responseTemplate", "")
            if isinstance(rt, str) and rt.strip().lower() in ["nurse here", "hello", "hi", ""]:
                trivial_templates.append(tname)
        passed = len(trivial_templates) == 0
        add_check("responseTemplates_not_trivial", passed,
                  "All responseTemplates have meaningful content" if passed
                  else f"Topics {trivial_templates} have trivial/empty responseTemplates", weight=1.0)
    except Exception as e:
        add_check("responseTemplates_not_trivial", False, f"Error: {e}", weight=1.0)

# =====================================================================
# CHECK 13: thread_ids must match the nurse's assigned topics
#           (urgencias: 201, bienestar: 89, general: 1 from profile.json)
# =====================================================================
EXPECTED_THREAD_IDS = {201, 89, 1}
if topics:
    try:
        found_tids = set()
        for t in topics.values():
            if isinstance(t, dict) and isinstance(t.get("thread_ids"), list):
                for tid in t["thread_ids"]:
                    if isinstance(tid, int):
                        found_tids.add(tid)
        coverage = len(found_tids & EXPECTED_THREAD_IDS)
        passed = coverage >= 2  # at least 2 of the 3 assigned thread_ids
        add_check("thread_ids_match_nurse_assignments", passed,
                  f"Found thread_ids {sorted(found_tids)} cover {coverage}/3 of nurse's assignments {sorted(EXPECTED_THREAD_IDS)}",
                  weight=2.0)
    except Exception as e:
        add_check("thread_ids_match_nurse_assignments", False, f"Error: {e}", weight=2.0)

# =====================================================================
# CHECK 14: The old broken config fields are FIXED (enabled=True, etc.)
#           Specifically: globalCooldownMinutes was "10" (string) in broken config
# =====================================================================
try:
    gcm = config.get("globalCooldownMinutes")
    rrm = config.get("respectRequireMention")
    enabled = config.get("enabled")
    fixed = (enabled is True) and (rrm is False) and isinstance(gcm, (int, float)) and not isinstance(gcm, bool)
    add_check("broken_config_fields_fixed", fixed,
              f"Fixed: enabled={enabled}, respectRequireMention={rrm}, globalCooldownMinutes={repr(gcm)}" if fixed
              else f"NOT fixed: enabled={enabled}, respectRequireMention={rrm}, globalCooldownMinutes={repr(gcm)}",
              weight=1.5)
except Exception as e:
    add_check("broken_config_fields_fixed", False, f"Error: {e}", weight=1.5)

# =====================================================================
# FINAL SCORE
# =====================================================================
final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0
passed_overall = final_score >= 0.75

result = {
    "passed": passed_overall,
    "score": final_score,
    "checks": checks
}

print(json.dumps(result, ensure_ascii=False, indent=2))