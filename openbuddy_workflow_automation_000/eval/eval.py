import sys
import json
import os
import subprocess
from pathlib import Path

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # ── Expected constants ────────────────────────────────────────────────────
    EMPLOYEE_ID = "charlie_qa_007"
    BUDDY_JS = workspace / "tools/companion_system/buddy.js"
    DATA_DIR = workspace / "tools/audit/charlie_buddy_data"
    SOUL_FILE = DATA_DIR / "buddy-soul.json"
    AUDIT_FILE = workspace / "tools/audit/companion_audit.json"
    REQUIRED_PETS = 5
    STAT_NAMES = ["DEBUGGING", "PATIENCE", "CHAOS", "WISDOM", "SNARK"]
    
    # ── Check 1: Soul file exists in the correct custom OPENBUDDY_DIR ─────────
    soul_exists = SOUL_FILE.exists()
    checks.append({
        "name": "soul_file_exists_in_custom_dir",
        "passed": soul_exists,
        "detail": f"Soul file at {SOUL_FILE}: {'found' if soul_exists else 'NOT found'}. "
                  f"Agent must use OPENBUDDY_DIR=/workspace/tools/audit/charlie_buddy_data"
    })
    
    # ── Check 2: Soul file is valid JSON with expected fields ─────────────────
    soul_valid = False
    soul_data = {}
    try:
        if soul_exists:
            soul_data = json.loads(SOUL_FILE.read_text())
            required_soul_fields = {"name", "personality", "hatchDate", "petCount", "muted", "visible"}
            missing = required_soul_fields - set(soul_data.keys())
            soul_valid = len(missing) == 0
            checks.append({
                "name": "soul_file_valid_structure",
                "passed": soul_valid,
                "detail": f"Soul fields: {list(soul_data.keys())}. Missing: {list(missing)}"
            })
        else:
            checks.append({
                "name": "soul_file_valid_structure",
                "passed": False,
                "detail": "Soul file not found, cannot validate structure."
            })
    except Exception as e:
        checks.append({
            "name": "soul_file_valid_structure",
            "passed": False,
            "detail": f"Error reading soul file: {e}"
        })

    # ── Check 3: Pet count is exactly REQUIRED_PETS ───────────────────────────
    pet_count_correct = False
    try:
        actual_pets = soul_data.get("petCount", -1)
        pet_count_correct = actual_pets == REQUIRED_PETS
        checks.append({
            "name": f"pet_count_equals_{REQUIRED_PETS}",
            "passed": pet_count_correct,
            "detail": f"Expected petCount={REQUIRED_PETS}, got {actual_pets}"
        })
    except Exception as e:
        checks.append({
            "name": f"pet_count_equals_{REQUIRED_PETS}",
            "passed": False,
            "detail": f"Error checking pet count: {e}"
        })

    # ── Check 4: Skeleton is deterministic for EMPLOYEE_ID ────────────────────
    skeleton_correct = False
    try:
        env = os.environ.copy()
        env["OPENBUDDY_USER_ID"] = EMPLOYEE_ID
        env["OPENBUDDY_DIR"] = str(DATA_DIR)
        
        result = subprocess.run(
            ["node", str(BUDDY_JS), "status"],
            capture_output=True, text=True, env=env, timeout=10
        )
        status_output = result.stdout.strip()
        
        # Re-run card to get skeleton data
        card_result = subprocess.run(
            ["node", str(BUDDY_JS), "card"],
            capture_output=True, text=True, env=env, timeout=10
        )
        card_output = card_result.stdout
        
        # The species and rarity must be consistent (skeleton = deterministic from user_id)
        # We verify by checking the soul name appears in status/card
        pet_name = soul_data.get("name", "")
        skeleton_correct = bool(status_output) and pet_name in status_output
        checks.append({
            "name": "skeleton_deterministic_for_employee_id",
            "passed": skeleton_correct,
            "detail": f"Status output with correct OPENBUDDY_USER_ID: '{status_output[:100]}'. Pet name '{pet_name}' found: {pet_name in status_output}"
        })
    except Exception as e:
        checks.append({
            "name": "skeleton_deterministic_for_employee_id",
            "passed": False,
            "detail": f"Error running node status check: {e}"
        })

    # ── Check 5: Audit file exists ────────────────────────────────────────────
    audit_exists = AUDIT_FILE.exists()
    checks.append({
        "name": "audit_file_exists",
        "passed": audit_exists,
        "detail": f"Audit file at {AUDIT_FILE}: {'found' if audit_exists else 'NOT found'}"
    })

    # ── Check 6: Audit file has correct employee_id ───────────────────────────
    audit_data = {}
    audit_employee_correct = False
    try:
        if audit_exists:
            audit_data = json.loads(AUDIT_FILE.read_text())
            audit_employee_correct = audit_data.get("employee_id") == EMPLOYEE_ID
            checks.append({
                "name": "audit_employee_id_correct",
                "passed": audit_employee_correct,
                "detail": f"Expected employee_id='{EMPLOYEE_ID}', got '{audit_data.get('employee_id')}'"
            })
        else:
            checks.append({
                "name": "audit_employee_id_correct",
                "passed": False,
                "detail": "Audit file not found."
            })
    except Exception as e:
        checks.append({
            "name": "audit_employee_id_correct",
            "passed": False,
            "detail": f"Error reading audit file: {e}"
        })

    # ── Check 7: Audit file has pet_name matching soul ────────────────────────
    try:
        if audit_exists and soul_data:
            expected_name = soul_data.get("name", "")
            actual_name = audit_data.get("pet_name", "")
            name_match = actual_name == expected_name and bool(actual_name)
            checks.append({
                "name": "audit_pet_name_matches_soul",
                "passed": name_match,
                "detail": f"Soul name='{expected_name}', audit pet_name='{actual_name}'"
            })
        else:
            checks.append({
                "name": "audit_pet_name_matches_soul",
                "passed": False,
                "detail": "Cannot verify: soul or audit file missing."
            })
    except Exception as e:
        checks.append({
            "name": "audit_pet_name_matches_soul",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ── Check 8: Audit file has species (skeleton field) ─────────────────────
    try:
        if audit_exists:
            species = audit_data.get("species", "")
            has_species = bool(species)
            checks.append({
                "name": "audit_has_species_field",
                "passed": has_species,
                "detail": f"audit.species='{species}'"
            })
        else:
            checks.append({
                "name": "audit_has_species_field",
                "passed": False,
                "detail": "Audit file missing."
            })
    except Exception as e:
        checks.append({
            "name": "audit_has_species_field",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ── Check 9: Audit file has rarity field ─────────────────────────────────
    try:
        if audit_exists:
            rarity = audit_data.get("rarity", "")
            valid_rarities = {"普通", "稀有", "罕见", "史诗", "传说"}
            rarity_valid = rarity in valid_rarities
            checks.append({
                "name": "audit_rarity_is_valid",
                "passed": rarity_valid,
                "detail": f"audit.rarity='{rarity}', valid values={valid_rarities}"
            })
        else:
            checks.append({
                "name": "audit_rarity_is_valid",
                "passed": False,
                "detail": "Audit file missing."
            })
    except Exception as e:
        checks.append({
            "name": "audit_rarity_is_valid",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ── Check 10: Audit reflects correct pet_count (5) ───────────────────────
    try:
        if audit_exists:
            audit_pets = audit_data.get("pet_count", audit_data.get("petCount", -1))
            audit_pets_correct = audit_pets == REQUIRED_PETS
            checks.append({
                "name": "audit_pet_count_equals_5",
                "passed": audit_pets_correct,
                "detail": f"Expected pet_count=5, got {audit_pets}"
            })
        else:
            checks.append({
                "name": "audit_pet_count_equals_5",
                "passed": False,
                "detail": "Audit file missing."
            })
    except Exception as e:
        checks.append({
            "name": "audit_pet_count_equals_5",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ── Check 11: Audit has stats (5 attributes from skeleton) ───────────────
    try:
        if audit_exists:
            stats = audit_data.get("stats", {})
            if stats:
                has_all_stats = all(s in stats for s in STAT_NAMES)
                stats_are_numbers = all(isinstance(stats.get(s), (int, float)) for s in STAT_NAMES if s in stats)
                stats_valid = has_all_stats and stats_are_numbers
                checks.append({
                    "name": "audit_has_all_five_stats",
                    "passed": stats_valid,
                    "detail": f"Stats found: {list(stats.keys())}. All valid numbers: {stats_are_numbers}"
                })
            else:
                checks.append({
                    "name": "audit_has_all_five_stats",
                    "passed": False,
                    "detail": f"audit.stats is empty or missing. audit keys: {list(audit_data.keys())}"
                })
        else:
            checks.append({
                "name": "audit_has_all_five_stats",
                "passed": False,
                "detail": "Audit file missing."
            })
    except Exception as e:
        checks.append({
            "name": "audit_has_all_five_stats",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ── Check 12: audit_complete flag is True ─────────────────────────────────
    try:
        if audit_exists:
            complete = audit_data.get("audit_complete", False)
            checks.append({
                "name": "audit_complete_flag_true",
                "passed": complete is True,
                "detail": f"audit_complete={complete}"
            })
        else:
            checks.append({
                "name": "audit_complete_flag_true",
                "passed": False,
                "detail": "Audit file missing."
            })
    except Exception as e:
        checks.append({
            "name": "audit_complete_flag_true",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = passed_count >= 10  # require at least 10/12

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    result = run_eval(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))