import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

checks = []

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ── 1. Check that huectl skill directory was scaffolded ──────────────────
skills_base = Path(os.path.expanduser("~/.openclaw/workspace/skills"))
huectl_dir = skills_base / "huectl"

dir_exists = huectl_dir.exists() and huectl_dir.is_dir()
check(
    "huectl_directory_created",
    dir_exists,
    f"Expected ~/.openclaw/workspace/skills/huectl/ — {'found' if dir_exists else 'NOT found'}"
)

# ── 2. SKILL.md exists and contains 'huectl' ─────────────────────────────
skill_md_path = huectl_dir / "SKILL.md"
try:
    if not skill_md_path.exists():
        raise FileNotFoundError("SKILL.md not found")
    skill_md_content = skill_md_path.read_text()
    has_name = "huectl" in skill_md_content.lower()
    check(
        "huectl_SKILL_md_exists_and_named",
        has_name,
        f"SKILL.md {'contains' if has_name else 'does NOT contain'} 'huectl' in content"
    )
except Exception as e:
    check("huectl_SKILL_md_exists_and_named", False, f"Error reading SKILL.md: {e}")

# ── 3. main.js exists ────────────────────────────────────────────────────
main_js_path = huectl_dir / "main.js"
try:
    if not main_js_path.exists():
        raise FileNotFoundError("main.js not found")
    main_js_content = main_js_path.read_text()
    has_content = len(main_js_content.strip()) > 10
    check(
        "huectl_main_js_exists",
        has_content,
        f"main.js {'has content' if has_content else 'is empty or missing'}"
    )
except Exception as e:
    check("huectl_main_js_exists", False, f"Error reading main.js: {e}")

# ── 4. config.json exists and has name 'huectl' ──────────────────────────
config_json_path = huectl_dir / "config.json"
try:
    if not config_json_path.exists():
        raise FileNotFoundError("config.json not found")
    cfg = json.loads(config_json_path.read_text())
    name_correct = cfg.get("name") == "huectl"
    check(
        "huectl_config_json_valid",
        name_correct,
        f"config.json name field: '{cfg.get('name')}' (expected 'huectl')"
    )
except Exception as e:
    check("huectl_config_json_valid", False, f"Error reading config.json: {e}")

# ── 5. skillstore config.json records 'huectl' as installed ─────────────
skillstore_config_path = Path(workspace) / "skillstore" / "config.json"
try:
    sc = json.loads(skillstore_config_path.read_text())
    installed = sc.get("installed", [])
    huectl_recorded = "huectl" in installed
    check(
        "skillstore_config_records_huectl",
        huectl_recorded,
        f"skillstore/config.json installed list: {installed}"
    )
except Exception as e:
    check("skillstore_config_records_huectl", False, f"Error reading skillstore/config.json: {e}")

# ── 6. research_notes.md exists somewhere in workspace ──────────────────
notes_files = list(Path(workspace).rglob("research_notes.md"))
notes_found = len(notes_files) > 0
check(
    "research_notes_md_exists",
    notes_found,
    f"research_notes.md {'found at: ' + str(notes_files[0]) if notes_found else 'NOT found anywhere in workspace'}"
)

# ── 7. research_notes.md references relevant known skills ────────────────
REQUIRED_SKILLS = ["homeassistant", "sonoscli", "blucli"]
if notes_found:
    try:
        notes_content = notes_files[0].read_text().lower()
        matched = [s for s in REQUIRED_SKILLS if s in notes_content]
        enough = len(matched) >= 2
        check(
            "research_notes_references_related_skills",
            enough,
            f"research_notes.md mentions {len(matched)}/{len(REQUIRED_SKILLS)} required skills: {matched}. "
            f"Required at least 2 of: {REQUIRED_SKILLS}"
        )
    except Exception as e:
        check("research_notes_references_related_skills", False, f"Error reading research_notes.md: {e}")
else:
    check(
        "research_notes_references_related_skills",
        False,
        "research_notes.md not found, cannot check content"
    )

# ── 8. research_notes.md mentions the total count of known skills ─────────
# The agent should have run 'skillstore known' and noted 20 built-in skills
if notes_found:
    try:
        notes_content = notes_files[0].read_text()
        mentions_count = "20" in notes_content or "twenty" in notes_content.lower()
        check(
            "research_notes_mentions_known_count",
            mentions_count,
            f"research_notes.md {'mentions' if mentions_count else 'does NOT mention'} total skill count (20)"
        )
    except Exception as e:
        check("research_notes_mentions_known_count", False, f"Error: {e}")
else:
    check("research_notes_mentions_known_count", False, "research_notes.md not found")

# ── 9. research_notes.md mentions hue/light search results ───────────────
if notes_found:
    try:
        notes_content = notes_files[0].read_text().lower()
        # Agent must have run a search for hue/lights/philips and documented results
        search_documented = any(kw in notes_content for kw in ["hue", "philips", "light control", "no result", "threshold", "30%", "below"])
        check(
            "research_notes_documents_search",
            search_documented,
            f"research_notes.md {'documents' if search_documented else 'does NOT document'} search findings (hue/lights/threshold)"
        )
    except Exception as e:
        check("research_notes_documents_search", False, f"Error: {e}")
else:
    check("research_notes_documents_search", False, "research_notes.md not found")

# ── Compute final score ───────────────────────────────────────────────────
passed_checks = [c for c in checks if c["passed"]]
total = len(checks)
score = len(passed_checks) / total

# Must pass core structural checks to pass overall
core_checks = [
    "huectl_directory_created",
    "huectl_SKILL_md_exists_and_named",
    "huectl_main_js_exists",
    "huectl_config_json_valid",
    "research_notes_md_exists",
    "research_notes_references_related_skills",
]
core_passed = all(c["passed"] for c in checks if c["name"] in core_checks)

result = {
    "passed": core_passed and score >= 0.75,
    "score": round(score, 3),
    "checks": checks
}

print(json.dumps(result, indent=2))