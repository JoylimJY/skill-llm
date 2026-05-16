import sys
import json
import pickle
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

SKILLS_ROOT    = Path("/root/.openclaw/workspace/skills")
SCRIPTS_DIR    = SKILLS_ROOT / "all-skill-list" / "scripts"
CACHE_FILE     = SCRIPTS_DIR / "skills_cache.pickle"
JSON_EXPORT    = SCRIPTS_DIR / "skills_export.json"
MD_EXPORT      = SCRIPTS_DIR / "all_skills.md"

EXPECTED_SKILLS = sorted([
    "web-crawler", "pdf-extractor", "db-connector",
    "email-sender", "image-resizer", "code-reviewer", "log-analyzer"
])

STALE_ONLY = ["old-skill-alpha", "dead-skill-beta"]

checks = []

# ── Check 1: Cache was refreshed (no longer stale) ────────────────────────────
def check_cache_refreshed():
    name = "cache_refreshed_and_accurate"
    try:
        assert CACHE_FILE.exists(), "Cache file does not exist"
        with open(CACHE_FILE, "rb") as f:
            data = pickle.load(f)
        cached_dirs = sorted(data.get("skill_dirs", []))
        for stale in STALE_ONLY:
            assert stale not in cached_dirs, f"Stale skill '{stale}' still in cache"
        assert "image-resizer" in cached_dirs, "'image-resizer' missing from refreshed cache"
        assert cached_dirs == EXPECTED_SKILLS, (
            f"Cache dirs mismatch.\n  Got:      {cached_dirs}\n  Expected: {EXPECTED_SKILLS}"
        )
        return {"name": name, "passed": True,
                "detail": f"Cache correctly reflects {cached_dirs}"}
    except AssertionError as e:
        return {"name": name, "passed": False, "detail": str(e)}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Unexpected error: {e}"}

# ── Check 2: JSON export exists and is valid ───────────────────────────────────
def check_json_export():
    name = "json_export_correct"
    try:
        assert JSON_EXPORT.exists(), f"JSON export not found at {JSON_EXPORT}"
        raw = JSON_EXPORT.read_text(encoding="utf-8")
        data = json.loads(raw)
        assert isinstance(data, list), "JSON root must be a list"
        exported_names = sorted(item["name"] for item in data)
        # Must NOT contain stale skills
        for stale in STALE_ONLY:
            assert stale not in exported_names, f"Stale skill '{stale}' present in JSON export"
        # Must contain all current skills
        assert "image-resizer" in exported_names, "'image-resizer' missing from JSON export"
        assert exported_names == EXPECTED_SKILLS, (
            f"JSON export names mismatch.\n  Got:      {exported_names}\n  Expected: {EXPECTED_SKILLS}"
        )
        # Each entry must have required fields
        for item in data:
            for field in ("name", "description", "has_skill_md", "path"):
                assert field in item, f"Missing field '{field}' in JSON entry for {item.get('name')}"
        # All should have SKILL.md
        for item in data:
            assert item["has_skill_md"] is True, f"Skill '{item['name']}' should have has_skill_md=True"
        return {"name": name, "passed": True,
                "detail": f"JSON export valid with {len(data)} skills: {exported_names}"}
    except AssertionError as e:
        return {"name": name, "passed": False, "detail": str(e)}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Unexpected error: {e}"}

# ── Check 3: Markdown export exists and contains expected skill names ──────────
def check_md_export():
    name = "markdown_export_correct"
    try:
        assert MD_EXPORT.exists(), f"Markdown export not found at {MD_EXPORT}"
        content = MD_EXPORT.read_text(encoding="utf-8")
        assert len(content.strip()) > 0, "Markdown file is empty"
        for skill in EXPECTED_SKILLS:
            assert skill in content, f"Skill '{skill}' not mentioned in Markdown export"
        for stale in STALE_ONLY:
            assert stale not in content, f"Stale skill '{stale}' present in Markdown export"
        # Check that image-resizer description appears
        assert "image-resizer" in content, "'image-resizer' missing from Markdown"
        assert "图像批量缩放" in content or "Image Resizer" in content, (
            "'image-resizer' description content missing from Markdown"
        )
        return {"name": name, "passed": True,
                "detail": f"Markdown export valid, {len(content)} chars, all current skills present"}
    except AssertionError as e:
        return {"name": name, "passed": False, "detail": str(e)}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Unexpected error: {e}"}

# ── Check 4: Export files are at canonical script-relative paths ───────────────
def check_file_locations():
    name = "export_files_at_canonical_paths"
    try:
        assert JSON_EXPORT.exists(), f"JSON not at canonical path {JSON_EXPORT}"
        assert MD_EXPORT.exists(), f"Markdown not at canonical path {MD_EXPORT}"
        return {"name": name, "passed": True,
                "detail": f"Both export files found at canonical paths under {SCRIPTS_DIR}"}
    except AssertionError as e:
        return {"name": name, "passed": False, "detail": str(e)}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Unexpected error: {e}"}

# ── Check 5: Cache skill count consistency ────────────────────────────────────
def check_cache_count():
    name = "cache_skills_data_count"
    try:
        with open(CACHE_FILE, "rb") as f:
            data = pickle.load(f)
        skill_list = data.get("skills", [])
        assert len(skill_list) == len(EXPECTED_SKILLS), (
            f"Cache skills list has {len(skill_list)} entries, expected {len(EXPECTED_SKILLS)}"
        )
        cache_names = sorted(s["name"] for s in skill_list)
        assert cache_names == EXPECTED_SKILLS, (
            f"Cache skills names: {cache_names} != expected: {EXPECTED_SKILLS}"
        )
        return {"name": name, "passed": True,
                "detail": f"Cache contains exactly {len(skill_list)} skill entries: {cache_names}"}
    except AssertionError as e:
        return {"name": name, "passed": False, "detail": str(e)}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Unexpected error: {e}"}


results = [
    check_cache_refreshed(),
    check_json_export(),
    check_md_export(),
    check_file_locations(),
    check_cache_count(),
]

passed_count = sum(1 for c in results if c["passed"])
total = len(results)
score = round(passed_count / total, 4)
all_passed = passed_count == total

output = {
    "passed": all_passed,
    "score": score,
    "checks": results
}

print(json.dumps(output, ensure_ascii=False, indent=2))