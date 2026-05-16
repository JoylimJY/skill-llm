import sys
import json
import os
from pathlib import Path
from datetime import datetime

def evaluate(workspace_dir: str) -> dict:
    workspace = Path(workspace_dir)
    opencode_dir = workspace / ".opencode"
    home = Path("/home/agent")
    skills_knowledge = home / ".config" / "opencode" / "skills" / "evolving-agent" / "data" / "knowledge" / "entries.json"

    checks = []
    total_score = 0.0

    # ─── Check 1: .evolution_mode_active exists ───────────────────────────────
    evolution_flag = opencode_dir / ".evolution_mode_active"
    try:
        if evolution_flag.exists():
            content = evolution_flag.read_text().strip()
            # Should be valid JSON with 'status' or at minimum non-empty
            if len(content) > 0:
                try:
                    data = json.loads(content)
                    has_status = "status" in data or "activated_at" in data
                    checks.append({
                        "name": "evolution_mode_active_file_exists_and_valid",
                        "passed": True,
                        "detail": f"Found valid JSON marker file. Keys: {list(data.keys())}"
                    })
                    total_score += 25.0
                except json.JSONDecodeError:
                    # Accept non-JSON too (agent may have written plain text)
                    checks.append({
                        "name": "evolution_mode_active_file_exists_and_valid",
                        "passed": True,
                        "detail": f"Marker file exists with content (non-JSON): {content[:100]}"
                    })
                    total_score += 20.0
            else:
                checks.append({
                    "name": "evolution_mode_active_file_exists_and_valid",
                    "passed": False,
                    "detail": "Marker file exists but is empty"
                })
        else:
            checks.append({
                "name": "evolution_mode_active_file_exists_and_valid",
                "passed": False,
                "detail": f"Missing: {evolution_flag}. Agent must run 'python run.py mode --init' or equivalent."
            })
    except Exception as e:
        checks.append({
            "name": "evolution_mode_active_file_exists_and_valid",
            "passed": False,
            "detail": f"Error reading evolution flag: {e}"
        })

    # ─── Check 2: feature_list.json - all statuses are 'completed' ───────────
    feature_list_path = opencode_dir / "feature_list.json"
    try:
        if feature_list_path.exists():
            data = json.loads(feature_list_path.read_text())
            features = data.get("features", [])
            if not features:
                checks.append({
                    "name": "feature_list_all_completed",
                    "passed": False,
                    "detail": "feature_list.json exists but 'features' array is empty"
                })
            else:
                statuses = [f.get("status", "") for f in features]
                all_completed = all(s == "completed" for s in statuses)
                non_completed = [f["id"] for f in features if f.get("status") != "completed"]
                if all_completed:
                    checks.append({
                        "name": "feature_list_all_completed",
                        "passed": True,
                        "detail": f"All {len(features)} features have status='completed'"
                    })
                    total_score += 30.0
                else:
                    checks.append({
                        "name": "feature_list_all_completed",
                        "passed": False,
                        "detail": f"Not all completed. Non-completed: {non_completed}. Statuses: {statuses}"
                    })
        else:
            checks.append({
                "name": "feature_list_all_completed",
                "passed": False,
                "detail": f"feature_list.json not found at {feature_list_path}"
            })
    except Exception as e:
        checks.append({
            "name": "feature_list_all_completed",
            "passed": False,
            "detail": f"Error reading feature_list.json: {e}"
        })

    # ─── Check 3: progress.txt exists and has content ─────────────────────────
    progress_path = opencode_dir / "progress.txt"
    try:
        if progress_path.exists():
            content = progress_path.read_text().strip()
            if len(content) >= 10:
                checks.append({
                    "name": "progress_txt_exists_and_populated",
                    "passed": True,
                    "detail": f"progress.txt exists with {len(content)} chars. Preview: {content[:120]}"
                })
                total_score += 20.0
            else:
                checks.append({
                    "name": "progress_txt_exists_and_populated",
                    "passed": False,
                    "detail": f"progress.txt exists but content too short: '{content}'"
                })
        else:
            checks.append({
                "name": "progress_txt_exists_and_populated",
                "passed": False,
                "detail": f"progress.txt not found at {progress_path}. Agent must write progress updates."
            })
    except Exception as e:
        checks.append({
            "name": "progress_txt_exists_and_populated",
            "passed": False,
            "detail": f"Error reading progress.txt: {e}"
        })

    # ─── Check 4: Knowledge base has at least 1 new entry ─────────────────────
    try:
        if skills_knowledge.exists():
            entries = json.loads(skills_knowledge.read_text())
            if len(entries) >= 1:
                # Verify structure of at least one entry
                entry = entries[0]
                has_required_fields = all(
                    k in entry for k in ["id", "category", "summary", "created_at"]
                )
                valid_categories = {"bug-fix", "architecture", "best-practice", "performance"}
                valid_category = entry.get("category", "") in valid_categories

                if has_required_fields:
                    checks.append({
                        "name": "knowledge_base_has_entries",
                        "passed": True,
                        "detail": f"Knowledge base has {len(entries)} entries. First: id={entry.get('id')}, category={entry.get('category')}"
                    })
                    total_score += 25.0
                else:
                    checks.append({
                        "name": "knowledge_base_has_entries",
                        "passed": False,
                        "detail": f"Knowledge entry missing required fields. Found keys: {list(entry.keys())}"
                    })
            else:
                checks.append({
                    "name": "knowledge_base_has_entries",
                    "passed": False,
                    "detail": "Knowledge base entries.json is empty. Agent must run 'knowledge trigger' command."
                })
        else:
            checks.append({
                "name": "knowledge_base_has_entries",
                "passed": False,
                "detail": f"Knowledge base file not found at {skills_knowledge}"
            })
    except Exception as e:
        checks.append({
            "name": "knowledge_base_has_entries",
            "passed": False,
            "detail": f"Error reading knowledge base: {e}"
        })

    # ─── Check 5: Correct SKILLS_DIR resolution (verify skill was used) ────────
    # Indirectly: if evolution_mode_active was created in the RIGHT path
    # The marker must be in .opencode/ inside the project workspace (cwd-relative)
    try:
        correct_location = (opencode_dir / ".evolution_mode_active").exists()
        wrong_location_global = (home / ".opencode" / ".evolution_mode_active").exists()
        if correct_location and not wrong_location_global:
            checks.append({
                "name": "correct_path_resolution_and_scope",
                "passed": True,
                "detail": "Evolution mode marker correctly placed in project .opencode/ (not global home)"
            })
            # No extra score - already counted above
        elif correct_location:
            checks.append({
                "name": "correct_path_resolution_and_scope",
                "passed": True,
                "detail": "Marker in correct project location (also exists globally but that's OK)"
            })
        else:
            checks.append({
                "name": "correct_path_resolution_and_scope",
                "passed": False,
                "detail": "Evolution mode marker not found in expected project .opencode/ directory"
            })
    except Exception as e:
        checks.append({
            "name": "correct_path_resolution_and_scope",
            "passed": False,
            "detail": f"Path resolution check error: {e}"
        })

    # ─── Compute final pass/fail ───────────────────────────────────────────────
    # Must pass checks 1 (evolution mode), 2 (all completed), 4 (knowledge entry)
    critical_checks = [
        "evolution_mode_active_file_exists_and_valid",
        "feature_list_all_completed",
        "knowledge_base_has_entries",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    score = min(total_score, 100.0) / 100.0
    passed = critical_passed and score >= 0.75

    return {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "args", "passed": False, "detail": "Usage: eval_script.py <workspace_dir>"}
        ]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)