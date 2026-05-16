#!/usr/bin/env python3
import sys
import json
import subprocess
import os
from pathlib import Path

def run_buddy_script(user_id):
    """Run the buddy script and capture stdout and stderr separately."""
    result = subprocess.run(
        ["node", os.path.expanduser("~/.openclaw/workspace/skills/openclaw-buddy/scripts/buddy.js"), user_id],
        capture_output=True,
        text=True
    )
    return result.stdout, result.stderr

def main():
    workspace = sys.argv[1]
    workspace_path = Path(workspace)

    checks = []
    total_score = 0.0

    # The 5 user IDs from the task input
    user_ids = [
        "ou_54e680914a71dc8636180ce79cebdca8",
        "ou_7b3c92f0d1a4e865234abc901def5678",
        "ou_1a2b3c4d5e6f7890abcdef1234567890",
        "beta_tester_007",
        "ou_deadbeef12345678cafebabe90abcdef",
    ]

    # 1. Check that buddy_profiles directory exists
    buddy_profiles_dirs = list(workspace_path.rglob("buddy_profiles"))
    buddy_profiles_dir = None
    for d in buddy_profiles_dirs:
        if d.is_dir():
            buddy_profiles_dir = d
            break

    dir_exists = buddy_profiles_dir is not None
    checks.append({
        "name": "buddy_profiles_directory_exists",
        "passed": dir_exists,
        "detail": f"Found buddy_profiles directory at: {buddy_profiles_dir}" if dir_exists else "No 'buddy_profiles' directory found anywhere in workspace"
    })

    if not dir_exists:
        # Try to find .card.txt or .data.json files anywhere
        all_cards = list(workspace_path.rglob("*.card.txt"))
        all_data = list(workspace_path.rglob("*.data.json"))
        checks.append({
            "name": "fallback_files_check",
            "passed": False,
            "detail": f"No buddy_profiles dir. Found {len(all_cards)} .card.txt files and {len(all_data)} .data.json files elsewhere."
        })
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    # 2. For each user_id, check card.txt and data.json exist and are correct
    card_scores = []
    json_scores = []

    for uid in user_ids:
        # Get expected outputs from the script
        try:
            expected_stdout, expected_stderr = run_buddy_script(uid)
            expected_json = json.loads(expected_stderr.strip())
        except Exception as e:
            checks.append({
                "name": f"eval_script_error_{uid[:20]}",
                "passed": False,
                "detail": f"Could not run buddy.js for eval: {e}"
            })
            continue

        # --- Check card file ---
        card_file = buddy_profiles_dir / f"{uid}.card.txt"
        card_passed = False
        card_detail = ""

        try:
            card_content = card_file.read_text(encoding="utf-8")
            # Must contain the species Chinese name
            species_zh = expected_json["speciesZh"]
            rarity_zh = expected_json["rarityZh"]
            stars = expected_json["stars"]
            personality = expected_json["personality"]

            has_species = species_zh in card_content
            has_rarity = rarity_zh in card_content
            has_stars = stars in card_content
            has_personality = personality in card_content
            has_stats_header = "属性面板" in card_content

            # The card content should closely match expected stdout
            # We'll check key structural markers
            if has_species and has_rarity and has_stars and has_personality and has_stats_header:
                card_passed = True
                card_detail = f"Card for {uid[:20]} is correct. Species={species_zh}, Rarity={rarity_zh}"
            else:
                card_detail = (
                    f"Card for {uid[:20]} missing fields: "
                    f"species={has_species}, rarity={has_rarity}, stars={has_stars}, "
                    f"personality={has_personality}, stats_header={has_stats_header}"
                )
        except FileNotFoundError:
            card_detail = f"Card file not found: {card_file}"
        except Exception as e:
            card_detail = f"Error reading card file for {uid[:20]}: {e}"

        checks.append({
            "name": f"card_file_{uid[:30]}",
            "passed": card_passed,
            "detail": card_detail
        })
        card_scores.append(1.0 if card_passed else 0.0)

        # --- Check data.json file ---
        data_file = buddy_profiles_dir / f"{uid}.data.json"
        json_passed = False
        json_detail = ""

        try:
            data_content = data_file.read_text(encoding="utf-8")
            actual_json = json.loads(data_content)

            # Must be valid JSON with correct fields from stderr
            # Key fields to verify (deterministic check)
            checks_fields = ["species", "rarity", "shiny", "eyes", "hat", "stats"]
            field_ok = all(k in actual_json for k in checks_fields)

            species_match = actual_json.get("species") == expected_json.get("species")
            rarity_match = actual_json.get("rarity") == expected_json.get("rarity")
            shiny_match = actual_json.get("shiny") == expected_json.get("shiny")
            eyes_match = actual_json.get("eyes") == expected_json.get("eyes")
            hat_match = actual_json.get("hat") == expected_json.get("hat")

            # Stats must match exactly (deterministic)
            stats_match = actual_json.get("stats") == expected_json.get("stats")

            if field_ok and species_match and rarity_match and shiny_match and eyes_match and hat_match and stats_match:
                json_passed = True
                json_detail = f"JSON for {uid[:20]} is correct and deterministic. Species={actual_json.get('species')}"
            else:
                json_detail = (
                    f"JSON for {uid[:20]}: fields_present={field_ok}, "
                    f"species={species_match}(got={actual_json.get('species')},exp={expected_json.get('species')}), "
                    f"rarity={rarity_match}, shiny={shiny_match}, eyes={eyes_match}, "
                    f"hat={hat_match}, stats={stats_match}"
                )
        except FileNotFoundError:
            json_detail = f"Data JSON file not found: {data_file}"
        except json.JSONDecodeError as e:
            json_detail = f"Invalid JSON in data file for {uid[:20]}: {e}"
        except Exception as e:
            json_detail = f"Error reading data file for {uid[:20]}: {e}"

        checks.append({
            "name": f"data_json_{uid[:30]}",
            "passed": json_passed,
            "detail": json_detail
        })
        json_scores.append(1.0 if json_passed else 0.0)

    # 3. Critical check: stdout vs stderr separation
    # If all data.json files are valid but some card.txt files contain JSON,
    # the agent mixed up stdout/stderr
    confusion_check_passed = True
    confusion_detail = "No stdout/stderr confusion detected."
    for uid in user_ids:
        card_file = buddy_profiles_dir / f"{uid}.card.txt"
        try:
            content = card_file.read_text(encoding="utf-8")
            # If card file starts with { it's likely JSON (stderr) saved to card file
            if content.strip().startswith("{"):
                confusion_check_passed = False
                confusion_detail = f"Card file for {uid[:20]} appears to contain JSON (stderr) instead of formatted text (stdout)"
                break
        except Exception:
            pass

    checks.append({
        "name": "stdout_stderr_separation_correct",
        "passed": confusion_check_passed,
        "detail": confusion_detail
    })

    # 4. Check all 5 IDs were processed (not just some)
    all_processed = len(card_scores) == 5 and len(json_scores) == 5
    all_cards_passed = sum(card_scores) == 5
    all_jsons_passed = sum(json_scores) == 5

    checks.append({
        "name": "all_five_users_processed",
        "passed": all_processed and all_cards_passed and all_jsons_passed,
        "detail": f"Cards passed: {sum(card_scores)}/5, JSONs passed: {sum(json_scores)}/5"
    })

    # Score calculation
    # - Directory exists: 5%
    # - Per-user card correct: 8% each = 40%
    # - Per-user JSON correct: 9% each = 45%  
    # - stdout/stderr not confused: 5%
    # - All 5 processed: 5%

    score = 0.0
    if dir_exists:
        score += 0.05
    if card_scores:
        score += (sum(card_scores) / 5) * 0.40
    if json_scores:
        score += (sum(json_scores) / 5) * 0.45
    if confusion_check_passed:
        score += 0.05
    if all_processed and all_cards_passed and all_jsons_passed:
        score += 0.05

    passed = score >= 0.85

    result = {
        "passed": passed,
        "score": round(score, 4),
        "checks": checks
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()