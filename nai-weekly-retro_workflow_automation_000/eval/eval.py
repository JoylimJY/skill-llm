#!/usr/bin/env python3
"""
Evaluation script for the weekly-retro skill task.
Checks:
1. Retrospective file exists at vault/weekly-retro/2024-03-17.md
2. YAML frontmatter is present with required fields
3. All required sections are present in the markdown
4. Content is derived from the correct memory directory and date range
5. History was recorded via history.py (vault/retro-history/history.json exists and has entries)
"""

import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str) -> dict:
    ws = Path(workspace)
    checks = []

    # ── Check 1: Retro file exists at the correct vault path ──
    retro_path = ws / "vault" / "weekly-retro" / "2024-03-17.md"
    if not retro_path.exists():
        # Search for any 2024-03-17.md in case agent placed it elsewhere
        found = list(ws.rglob("2024-03-17.md"))
        if found:
            retro_content = found[0].read_text()
            checks.append({
                "name": "retro_file_correct_path",
                "passed": False,
                "detail": f"File found at {found[0]} but expected at vault/weekly-retro/2024-03-17.md"
            })
        else:
            checks.append({
                "name": "retro_file_correct_path",
                "passed": False,
                "detail": "No 2024-03-17.md found anywhere in the workspace"
            })
            # Can't proceed with content checks
            return {
                "passed": False,
                "score": 0.0,
                "checks": checks + [
                    {"name": c, "passed": False, "detail": "File missing — cannot evaluate"}
                    for c in ["yaml_frontmatter_present", "frontmatter_date_range", "frontmatter_week_score",
                              "frontmatter_tags", "section_week_at_a_glance", "section_wins",
                              "section_patterns", "section_friction_points", "section_recommendations",
                              "section_week_score", "content_references_accomplishments",
                              "content_references_friction", "history_recorded"]
                ]
            }
        retro_content = found[0].read_text()
    else:
        retro_content = retro_path.read_text()
        checks.append({
            "name": "retro_file_correct_path",
            "passed": True,
            "detail": f"Retrospective found at correct path: vault/weekly-retro/2024-03-17.md"
        })

    # ── Check 2: YAML frontmatter present ──
    has_frontmatter = retro_content.strip().startswith("---")
    checks.append({
        "name": "yaml_frontmatter_present",
        "passed": has_frontmatter,
        "detail": "YAML frontmatter (starts with ---) is present" if has_frontmatter
                  else "No YAML frontmatter found — required by skill spec"
    })

    # ── Check 3: Frontmatter contains date_range ──
    try:
        fm_match = re.search(r"^---\s*\n(.*?)\n---", retro_content, re.DOTALL)
        fm_text = fm_match.group(1) if fm_match else ""
        has_date_range = "date_range" in fm_text and "2024-03-11" in fm_text and "2024-03-17" in fm_text
        checks.append({
            "name": "frontmatter_date_range",
            "passed": has_date_range,
            "detail": f"Frontmatter date_range covers 2024-03-11 to 2024-03-17: {has_date_range}"
        })
    except Exception as e:
        checks.append({"name": "frontmatter_date_range", "passed": False, "detail": f"Error parsing frontmatter: {e}"})

    # ── Check 4: Frontmatter contains week_score ──
    try:
        has_score = "week_score" in fm_text and re.search(r"week_score:\s*\d+\.?\d*", fm_text) is not None
        score_match = re.search(r"week_score:\s*(\d+\.?\d*)", fm_text)
        score_val = float(score_match.group(1)) if score_match else None
        score_in_range = score_val is not None and 1.0 <= score_val <= 10.0
        checks.append({
            "name": "frontmatter_week_score",
            "passed": has_score and score_in_range,
            "detail": f"week_score found: {score_val}, in valid range 1-10: {score_in_range}"
        })
    except Exception as e:
        checks.append({"name": "frontmatter_week_score", "passed": False, "detail": f"Error parsing week_score: {e}"})

    # ── Check 5: Frontmatter contains tags ──
    try:
        has_tags = "tags" in fm_text and "weekly-retro" in fm_text
        checks.append({
            "name": "frontmatter_tags",
            "passed": has_tags,
            "detail": f"tags field present with 'weekly-retro' tag: {has_tags}"
        })
    except Exception as e:
        checks.append({"name": "frontmatter_tags", "passed": False, "detail": f"Error: {e}"})

    # ── Check 6: Required sections present ──
    required_sections = {
        "section_week_at_a_glance": r"##\s+Week at a Glance",
        "section_wins": r"##\s+Wins",
        "section_patterns": r"##\s+Patterns",
        "section_friction_points": r"##\s+Friction Points",
        "section_recommendations": r"##\s+Recommendations",
        "section_week_score": r"##\s+Week Score",
    }
    for check_name, pattern in required_sections.items():
        found = bool(re.search(pattern, retro_content, re.IGNORECASE))
        checks.append({
            "name": check_name,
            "passed": found,
            "detail": f"Section '{check_name}' {'found' if found else 'MISSING'} in retrospective"
        })

    # ── Check 7: Content references actual accomplishments from memory logs ──
    try:
        accomplishment_signals = [
            "collision", "tilemap", "prototype", "level editor", "pathfinding",
            "particle", "shipped", "fixed", "built", "published", "vertical slice",
            "save system", "optimization", "hotfix", "steering"
        ]
        content_lower = retro_content.lower()
        found_signals = [sig for sig in accomplishment_signals if sig.lower() in content_lower]
        has_real_content = len(found_signals) >= 3
        checks.append({
            "name": "content_references_accomplishments",
            "passed": has_real_content,
            "detail": f"Found {len(found_signals)} accomplishment signals from memory logs: {found_signals[:5]}"
        })
    except Exception as e:
        checks.append({"name": "content_references_accomplishments", "passed": False, "detail": f"Error: {e}"})

    # ── Check 8: Content references friction points (audio blocker is the major recurring one) ──
    try:
        friction_signals = ["audio", "blocked", "middleware", "license", "licensing", "friction", "render", "clipping"]
        found_friction = [sig for sig in friction_signals if sig.lower() in content_lower]
        has_friction_content = len(found_friction) >= 2
        checks.append({
            "name": "content_references_friction",
            "passed": has_friction_content,
            "detail": f"Found {len(found_friction)} friction signals in retro: {found_friction}"
        })
    except Exception as e:
        checks.append({"name": "content_references_friction", "passed": False, "detail": f"Error: {e}"})

    # ── Check 9: History was recorded (history.py --record was run) ──
    try:
        history_path = ws / "vault" / "retro-history" / "history.json"
        if not history_path.exists():
            # Also search in other common locations
            alt_paths = list(ws.rglob("history.json"))
            # Filter out the distractor at workspace root
            alt_paths = [p for p in alt_paths if "retro-history" in str(p) or "history" in str(p.parent)]
            if alt_paths:
                history_data = json.loads(alt_paths[0].read_text())
            else:
                checks.append({
                    "name": "history_recorded",
                    "passed": False,
                    "detail": "No history.json found in retro-history directory. history.py --record was not run."
                })
                history_data = None
        else:
            history_data = json.loads(history_path.read_text())

        if history_data is not None:
            entries = history_data.get("entries", [])
            has_entry_for_week = any(
                e.get("period", {}).get("end") == "2024-03-17" or
                e.get("period", {}).get("start") == "2024-03-11"
                for e in entries
            )
            checks.append({
                "name": "history_recorded",
                "passed": len(entries) > 0 and has_entry_for_week,
                "detail": f"History has {len(entries)} entries. Entry for target week found: {has_entry_for_week}"
            })
    except Exception as e:
        checks.append({"name": "history_recorded", "passed": False, "detail": f"Error reading history: {e}"})

    # ── Compute final score ──
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / total if total > 0 else 0.0

    # Must pass critical checks to pass overall
    critical_checks = [
        "retro_file_correct_path",
        "yaml_frontmatter_present",
        "frontmatter_date_range",
        "section_wins",
        "section_recommendations",
        "content_references_accomplishments",
        "history_recorded"
    ]
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )

    return {
        "passed": critical_passed and score >= 0.75,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))