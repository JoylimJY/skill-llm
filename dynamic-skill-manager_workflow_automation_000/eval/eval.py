import sys
import json
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta

def load_json(path):
    with open(path) as f:
        return json.load(f)

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/root")
    HOME = Path("/root")
    DATA_DIR = HOME / ".openclaw" / "workspace" / ".skill-manager"
    REGISTRY_FILE = DATA_DIR / "registry.json"
    ARCHIVE_DIR = DATA_DIR / "archive"
    SKILLS_DIR = HOME / ".openclaw" / "workspace" / "skills"
    USAGE_LOG = DATA_DIR / "usage-log.jsonl"

    checks = []
    now_utc = datetime.now(timezone.utc)

    # ── Check 1: Registry exists and has valid structure ──────────────────────
    try:
        reg = load_json(REGISTRY_FILE)
        assert "skills" in reg and isinstance(reg["skills"], dict)
        checks.append({"name": "registry_exists_and_valid", "passed": True,
                        "detail": "registry.json exists and has 'skills' dict."})
    except Exception as e:
        checks.append({"name": "registry_exists_and_valid", "passed": False,
                        "detail": f"Failed to load registry: {e}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    skills = reg["skills"]

    # ── Check 2: csv-merger was synced into registry ───────────────────────────
    try:
        assert "csv-merger" in skills, "csv-merger not found in registry"
        entry = skills["csv-merger"]
        assert "installed_at" in entry, "Missing installed_at"
        assert "pinned" in entry, "Missing pinned field"
        assert entry["pinned"] == False, "csv-merger should not be pinned"
        checks.append({"name": "csv_merger_synced", "passed": True,
                        "detail": "csv-merger correctly synced into registry."})
    except Exception as e:
        checks.append({"name": "csv_merger_synced", "passed": False,
                        "detail": f"sync check failed: {e}"})

    # ── Check 3: Active skills were tracked (report-generator and/or api-tester) ──
    # The agent should have tracked at least one of the active skills
    try:
        tracked_recently = []
        for sname in ["report-generator", "api-tester"]:
            if sname in skills:
                s = skills[sname]
                lu = s.get("last_used")
                if lu:
                    lu_dt = datetime.fromisoformat(lu)
                    # The agent should have run track, so last_used should be very recent (within last hour)
                    if (now_utc - lu_dt).total_seconds() < 3600:
                        tracked_recently.append(sname)
        assert len(tracked_recently) >= 1, f"None of the active skills were re-tracked recently. Checked: report-generator, api-tester"
        checks.append({"name": "active_skills_tracked", "passed": True,
                        "detail": f"Active skills tracked recently: {tracked_recently}"})
    except Exception as e:
        checks.append({"name": "active_skills_tracked", "passed": False,
                        "detail": f"Track check failed: {e}"})

    # ── Check 4: usage-log.jsonl has new entries ───────────────────────────────
    try:
        log_lines = USAGE_LOG.read_text().strip().split("\n")
        new_entries = []
        for line in log_lines:
            if not line.strip():
                continue
            entry = json.loads(line)
            ts = datetime.fromisoformat(entry["timestamp"])
            if (now_utc - ts).total_seconds() < 3600:
                new_entries.append(entry["skill"])
        assert len(new_entries) >= 1, "No new usage log entries found (within last hour)"
        checks.append({"name": "usage_log_updated", "passed": True,
                        "detail": f"New usage log entries: {new_entries}"})
    except Exception as e:
        checks.append({"name": "usage_log_updated", "passed": False,
                        "detail": f"Usage log check failed: {e}"})

    # ── Check 5: Idle skills were uninstalled (not in registry) ───────────────
    EXPECTED_UNINSTALLED = {"data-formatter", "log-analyzer", "pdf-converter", "image-resizer", "csv-merger"}
    try:
        still_in_registry = EXPECTED_UNINSTALLED & set(skills.keys())
        # Allow one grace: old-webhook-sender may or may not be uninstalled (it's a ghost, not on disk)
        # But the 5 main idle skills should be gone
        if still_in_registry:
            checks.append({"name": "idle_skills_uninstalled", "passed": False,
                            "detail": f"These idle skills are still in registry: {still_in_registry}"})
        else:
            checks.append({"name": "idle_skills_uninstalled", "passed": True,
                            "detail": f"All idle skills removed from registry: {EXPECTED_UNINSTALLED}"})
    except Exception as e:
        checks.append({"name": "idle_skills_uninstalled", "passed": False,
                        "detail": f"Idle check failed: {e}"})

    # ── Check 6: Idle skill directories removed from disk ─────────────────────
    try:
        still_on_disk = []
        for skill in EXPECTED_UNINSTALLED:
            skill_path = SKILLS_DIR / skill
            if skill_path.exists() and not skill_path.is_symlink():
                still_on_disk.append(skill)
        if still_on_disk:
            checks.append({"name": "idle_skills_dirs_removed", "passed": False,
                            "detail": f"Skill directories still on disk: {still_on_disk}"})
        else:
            checks.append({"name": "idle_skills_dirs_removed", "passed": True,
                            "detail": "All idle skill directories removed from disk."})
    except Exception as e:
        checks.append({"name": "idle_skills_dirs_removed", "passed": False,
                        "detail": f"Dir removal check failed: {e}"})

    # ── Check 7: Archive files created for uninstalled skills ─────────────────
    try:
        archived = []
        missing_archive = []
        for skill in EXPECTED_UNINSTALLED:
            af = ARCHIVE_DIR / f"{skill}.json"
            if af.exists():
                d = load_json(af)
                assert "skill" in d and "uninstalled_at" in d and "metadata" in d
                archived.append(skill)
            else:
                missing_archive.append(skill)
        if missing_archive:
            checks.append({"name": "archive_files_created", "passed": False,
                            "detail": f"Missing archive files for: {missing_archive}"})
        else:
            checks.append({"name": "archive_files_created", "passed": True,
                            "detail": f"Archive files created for all uninstalled skills: {archived}"})
    except Exception as e:
        checks.append({"name": "archive_files_created", "passed": False,
                        "detail": f"Archive check failed: {e}"})

    # ── Check 8: System/pinned skills PRESERVED in registry ───────────────────
    SYSTEM_SKILLS = {"self-improving-agent", "pahf", "error-log-selfcheck", "dynamic-skill-manager"}
    try:
        missing_system = SYSTEM_SKILLS - set(skills.keys())
        if missing_system:
            checks.append({"name": "system_skills_protected", "passed": False,
                            "detail": f"System skills were UNINSTALLED (critical failure!): {missing_system}"})
        else:
            for sname in SYSTEM_SKILLS:
                assert skills[sname].get("pinned") == True, f"{sname} lost pinned=True flag"
            checks.append({"name": "system_skills_protected", "passed": True,
                            "detail": f"All system skills intact and pinned: {SYSTEM_SKILLS}"})
    except Exception as e:
        checks.append({"name": "system_skills_protected", "passed": False,
                        "detail": f"System skill protection check failed: {e}"})

    # ── Check 9: Active skills NOT uninstalled ─────────────────────────────────
    ACTIVE_SKILLS = {"report-generator", "api-tester"}
    try:
        removed_active = ACTIVE_SKILLS - set(skills.keys())
        if removed_active:
            checks.append({"name": "active_skills_preserved", "passed": False,
                            "detail": f"Active skills were incorrectly uninstalled: {removed_active}"})
        else:
            checks.append({"name": "active_skills_preserved", "passed": True,
                            "detail": "Active skills (report-generator, api-tester) preserved."})
    except Exception as e:
        checks.append({"name": "active_skills_preserved", "passed": False,
                        "detail": f"Active skill preservation check failed: {e}"})

    # ── Check 10: usage_count incremented for tracked skills ──────────────────
    try:
        incremented = []
        for sname in ["report-generator", "api-tester"]:
            if sname in skills:
                count = skills[sname].get("usage_count", 0)
                # Original counts: report-generator=15, api-tester=22
                original = {"report-generator": 15, "api-tester": 22}
                if count > original.get(sname, 0):
                    incremented.append(sname)
        assert len(incremented) >= 1, "usage_count not incremented for any active skill"
        checks.append({"name": "usage_count_incremented", "passed": True,
                        "detail": f"usage_count incremented for: {incremented}"})
    except Exception as e:
        checks.append({"name": "usage_count_incremented", "passed": False,
                        "detail": f"usage_count check failed: {e}"})

    # ── Score ──────────────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)
    overall = score >= 0.8  # Pass if >=8/10 checks pass

    print(json.dumps({
        "passed": overall,
        "score": round(score, 3),
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()