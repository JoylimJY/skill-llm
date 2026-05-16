import sys
import json
import re
from pathlib import Path

workspace = sys.argv[1]

checks = []
passed_all = True
score = 0.0

def add_check(name, passed, detail):
    global passed_all, score
    checks.append({"name": name, "passed": passed, "detail": detail})
    if not passed:
        passed_all = False

# --- Find the output file ---
try:
    candidates = list(Path(workspace).rglob("principles_library.json"))
    if not candidates:
        add_check("file_exists", False, "principles_library.json not found anywhere in workspace")
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        sys.exit(0)
    
    lib_path = candidates[0]
    add_check("file_exists", True, f"Found at {lib_path}")
    score += 0.05
except Exception as e:
    add_check("file_exists", False, f"Exception searching for file: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# --- Parse JSON ---
try:
    with open(lib_path, "r") as f:
        raw = f.read()
    data = json.loads(raw)
    add_check("valid_json", True, "File parses as valid JSON")
    score += 0.05
except Exception as e:
    add_check("valid_json", False, f"JSON parse error: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# --- Must be a list with 5 entries (one per raw input entry) ---
try:
    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict) and any(isinstance(v, list) for v in data.values()):
        # Allow wrapping key like {"principles": [...]}
        for v in data.values():
            if isinstance(v, list):
                entries = v
                break
    else:
        entries = [data]
    
    count_ok = len(entries) >= 5
    add_check("entry_count", count_ok, f"Found {len(entries)} entries (expected at least 5)")
    if count_ok:
        score += 0.05
except Exception as e:
    add_check("entry_count", False, f"Exception counting entries: {e}")
    entries = []

# --- Required fields check ---
REQUIRED_FIELDS = [
    "title", "source_type", "source_note", "original_idea",
    "historical_meaning", "modern_interpretation", "example",
    "tags", "confidence"
]

try:
    all_have_required = True
    missing_report = []
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            missing_report.append(f"Entry {i} is not a dict")
            all_have_required = False
            continue
        entry_keys_lower = {k.lower().replace(" ", "_").replace("-", "_"): k for k in entry.keys()}
        for field in REQUIRED_FIELDS:
            if field not in entry and field not in entry_keys_lower:
                missing_report.append(f"Entry {i} missing field: {field}")
                all_have_required = False
    
    add_check("required_fields_present", all_have_required, 
              "All required fields present" if all_have_required else "; ".join(missing_report[:5]))
    if all_have_required:
        score += 0.10
except Exception as e:
    add_check("required_fields_present", False, f"Exception: {e}")

# --- Confidence values must be exactly high/medium/low ---
VALID_CONFIDENCE = {"high", "medium", "low"}
try:
    confidence_ok = True
    bad_conf = []
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        conf_val = entry.get("confidence", entry.get("Confidence", ""))
        if isinstance(conf_val, str):
            if conf_val.strip().lower() not in VALID_CONFIDENCE:
                confidence_ok = False
                bad_conf.append(f"Entry {i}: '{conf_val}'")
    
    add_check("confidence_valid_values", confidence_ok, 
              "All confidence values are high/medium/low" if confidence_ok else f"Invalid values: {bad_conf}")
    if confidence_ok:
        score += 0.10
except Exception as e:
    add_check("confidence_valid_values", False, f"Exception: {e}")

# --- Entry 3 (folklore/internet) must be confidence=low ---
# The internet quote with no classical backing MUST be marked low
try:
    folklore_entry = None
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        # Detect entry 3: internet/folklore/guru-mantra quote
        combined_text = " ".join(str(v) for v in entry.values()).lower()
        if any(kw in combined_text for kw in ["guru", "secret", "guru-mantra", "secrets with anybody"]):
            folklore_entry = entry
            break
    
    if folklore_entry is None:
        add_check("folklore_entry_found", False, "Could not find the internet/folklore entry (guru-mantra) in library")
    else:
        conf = folklore_entry.get("confidence", folklore_entry.get("Confidence", "")).strip().lower()
        is_low = conf == "low"
        add_check("folklore_marked_low_confidence", is_low, 
                  f"Folklore/internet entry confidence = '{conf}' (must be 'low' per source discipline rules)")
        if is_low:
            score += 0.15
        add_check("folklore_entry_found", True, "Found folklore entry in library")
except Exception as e:
    add_check("folklore_entry_found", False, f"Exception: {e}")

# --- Entry 1 and 4 (Arthashastra, well-documented) must be confidence=high ---
try:
    arthashastra_high_count = 0
    arthashastra_entries = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        combined_text = " ".join(str(v) for v in entry.values()).lower()
        # Entry 1: loyalty/secret agents/high officials
        # Entry 4: departments/officials/meddling/service boundary
        is_entry1 = any(kw in combined_text for kw in ["secret agent", "loyalty", "high official", "tested in loyalty"])
        is_entry4 = any(kw in combined_text for kw in ["confine", "department", "meddle", "meddl", "own department"])
        if is_entry1 or is_entry4:
            arthashastra_entries.append(entry)
            conf = entry.get("confidence", entry.get("Confidence", "")).strip().lower()
            if conf == "high":
                arthashastra_high_count += 1
    
    good = arthashastra_high_count >= 2
    add_check("arthashastra_entries_marked_high", good,
              f"Found {len(arthashastra_entries)} Arthashastra entries, {arthashastra_high_count} marked 'high' (need 2)")
    if good:
        score += 0.10
except Exception as e:
    add_check("arthashastra_entries_marked_high", False, f"Exception: {e}")

# --- source_type field must use trust-hierarchy language, not generic ---
# Must distinguish between classical/scholarly/encyclopedic/modern commentary types
VALID_SOURCE_TYPES = [
    "direct classical", "classical", "primary", 
    "scholarly summary", "scholarly", "secondary scholarly",
    "encyclopedic", "wiki", "reference",
    "modern commentary", "commentary", "internet", "folklore", "unverified"
]
try:
    source_type_ok = True
    bad_sources = []
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        st = entry.get("source_type", entry.get("sourceType", entry.get("source_type", ""))).strip().lower()
        # Must be non-empty and must contain meaningful type language
        if not st:
            source_type_ok = False
            bad_sources.append(f"Entry {i}: empty source_type")
        else:
            # Check it's not just "arthashastra" or "chanakya" (too vague, not a type)
            if st in ["arthashastra", "chanakya", "chanakya niti", "book", "text", "unknown"]:
                # "unknown" alone is borderline acceptable for folklore
                if st != "unknown":
                    bad_sources.append(f"Entry {i}: source_type='{st}' is a source name, not a trust-tier type")
                    source_type_ok = False
    
    add_check("source_type_uses_trust_hierarchy", source_type_ok,
              "source_type fields use trust-hierarchy tier labels" if source_type_ok else f"Problems: {bad_sources[:3]}")
    if source_type_ok:
        score += 0.10
except Exception as e:
    add_check("source_type_uses_trust_hierarchy", False, f"Exception: {e}")

# --- Tags must come from approved theme taxonomy ---
APPROVED_THEMES = {
    "discipline", "governance", "incentives", "structure",
    "secrecy", "information control", "information_control",
    "placement", "right role", "right_role", "timing", "alliances",
    "risk", "resource management", "resource_management",
    "execution", "learning"
}
try:
    tags_from_taxonomy = True
    rogue_tags = []
    any_tags_found = False
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        tags_val = entry.get("tags", entry.get("Tags", []))
        if isinstance(tags_val, str):
            # Could be comma-separated
            tags_list = [t.strip().lower() for t in re.split(r"[,;|]", tags_val) if t.strip()]
        elif isinstance(tags_val, list):
            tags_list = [str(t).strip().lower() for t in tags_val]
        else:
            tags_list = []
        
        if tags_list:
            any_tags_found = True
        
        for tag in tags_list:
            # Check if tag is close to any approved theme
            tag_clean = tag.replace(" ", "_").replace("-", "_")
            match = any(
                tag in th or th in tag or tag_clean in th or th in tag_clean
                for th in APPROVED_THEMES
            )
            if not match and len(tag) > 2:
                rogue_tags.append(f"Entry {i}: '{tag}'")
    
    if not any_tags_found:
        add_check("tags_from_approved_taxonomy", False, "No tags found in any entry")
    else:
        ok = len(rogue_tags) <= 3  # allow up to 3 minor deviations across all entries
        add_check("tags_from_approved_taxonomy", ok,
                  "Tags align with approved theme taxonomy" if ok else f"Off-taxonomy tags: {rogue_tags[:5]}")
        if ok:
            score += 0.10
except Exception as e:
    add_check("tags_from_approved_taxonomy", False, f"Exception: {e}")

# --- modern_interpretation must reference software/systems domain for at least 2 entries ---
SOFTWARE_KEYWORDS = [
    "service", "microservice", "api", "queue", "deploy", "pipeline", "infra", "infrastructure",
    "access", "permission", "architecture", "system", "backend", "frontend", "database",
    "boundary", "ownership", "module", "component", "engineer", "software", "product",
    "roadmap", "release", "staging", "production", "monitoring", "circuit", "latency"
]
try:
    software_domain_count = 0
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        modern = str(entry.get("modern_interpretation", entry.get("modernInterpretation", ""))).lower()
        example = str(entry.get("example", "")).lower()
        combined = modern + " " + example
        if any(kw in combined for kw in SOFTWARE_KEYWORDS):
            software_domain_count += 1
    
    ok = software_domain_count >= 2
    add_check("modern_interpretation_software_domain", ok,
              f"{software_domain_count} entries have software/systems domain in modern interpretation (need ≥2)")
    if ok:
        score += 0.10
except Exception as e:
    add_check("modern_interpretation_software_domain", False, f"Exception: {e}")

# --- original_idea, historical_meaning, modern_interpretation must be separate non-empty fields ---
try:
    separation_ok = True
    collapse_issues = []
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        oi = str(entry.get("original_idea", "")).strip()
        hm = str(entry.get("historical_meaning", "")).strip()
        mi = str(entry.get("modern_interpretation", "")).strip()
        
        if not oi:
            separation_ok = False
            collapse_issues.append(f"Entry {i}: empty original_idea")
        if not hm:
            separation_ok = False
            collapse_issues.append(f"Entry {i}: empty historical_meaning")
        if not mi:
            separation_ok = False
            collapse_issues.append(f"Entry {i}: empty modern_interpretation")
        
        # Check they're not identical (collapse anti-pattern)
        if oi and hm and oi.lower()[:50] == hm.lower()[:50]:
            separation_ok = False
            collapse_issues.append(f"Entry {i}: original_idea and historical_meaning appear identical")
        if hm and mi and hm.lower()[:50] == mi.lower()[:50]:
            separation_ok = False
            collapse_issues.append(f"Entry {i}: historical_meaning and modern_interpretation appear identical")
    
    add_check("field_separation_not_collapsed", separation_ok,
              "original_idea / historical_meaning / modern_interpretation are distinct and non-empty" 
              if separation_ok else "; ".join(collapse_issues[:4]))
    if separation_ok:
        score += 0.10
except Exception as e:
    add_check("field_separation_not_collapsed", False, f"Exception: {e}")

# --- Entry 2 (Chanakya Niti - honest people quote) must NOT be described as advocating dishonesty ---
# The SKILL.md / source note says it relates to strategic restraint, commonly misread
try:
    entry2 = None
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        combined = " ".join(str(v) for v in entry.values()).lower()
        if any(kw in combined for kw in ["straight tree", "honest people", "too honest", "cut first"]):
            entry2 = entry
            break
    
    if entry2 is None:
        add_check("entry2_nuanced_interpretation", False, "Could not find the 'too honest' / straight trees entry")
    else:
        modern_int = str(entry2.get("modern_interpretation", "")).lower()
        hist_mean = str(entry2.get("historical_meaning", "")).lower()
        combined_entry2 = modern_int + " " + hist_mean
        
        # Should NOT say "be dishonest" or "advocate dishonesty" as the takeaway
        misread_phrases = ["be dishonest", "advocate dishonesty", "dishonesty is good", "lie to succeed", "should be dishonest"]
        has_misread = any(p in combined_entry2 for p in misread_phrases)
        
        # Should contain nuance about strategic restraint or not showing all capabilities
        nuance_phrases = ["strategic", "restraint", "reveal", "conceal", "position", "capability", "timing", "expose"]
        has_nuance = any(p in combined_entry2 for p in nuance_phrases)
        
        ok = (not has_misread) and has_nuance
        add_check("entry2_nuanced_interpretation", ok,
                  "Entry 2 correctly avoids misreading as 'be dishonest' and captures strategic restraint" 
                  if ok else f"Misread present: {has_misread}, Nuance present: {has_nuance}")
        if ok:
            score += 0.10
except Exception as e:
    add_check("entry2_nuanced_interpretation", False, f"Exception: {e}")

# Normalize score to 1.0
score = min(score, 1.0)

# Final pass/fail: need 70%+ score
final_pass = passed_all and score >= 0.70

print(json.dumps({
    "passed": final_pass,
    "score": round(score, 3),
    "checks": checks
}))