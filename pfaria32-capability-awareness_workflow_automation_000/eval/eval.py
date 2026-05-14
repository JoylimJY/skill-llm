import sys
import os
import re
import json
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0
    max_score = 0.0

    skills_base = Path(workspace) / "home/node/.openclaw/workspace/skills"
    agents_md_path = Path(workspace) / "home/node/.openclaw/workspace/AGENTS.md"

    skill_names = ["fraud-detection", "currency-converter", "compliance-checker"]

    # =========================================================================
    # CHECK GROUP 1: Each skill has a SKILL.md in the correct location
    # =========================================================================
    for skill in skill_names:
        max_score += 1.0
        skill_md_path = skills_base / skill / "SKILL.md"
        check_name = f"skill_md_exists_{skill}"
        try:
            if skill_md_path.exists() and skill_md_path.is_file():
                content = skill_md_path.read_text(encoding="utf-8")
                if len(content.strip()) > 50:
                    checks.append({"name": check_name, "passed": True, "detail": f"SKILL.md found at {skill_md_path} with {len(content)} chars"})
                    total_score += 1.0
                else:
                    checks.append({"name": check_name, "passed": False, "detail": f"SKILL.md at {skill_md_path} exists but is nearly empty ({len(content)} chars)"})
            else:
                checks.append({"name": check_name, "passed": False, "detail": f"SKILL.md missing at expected path: {skill_md_path}"})
        except Exception as e:
            checks.append({"name": check_name, "passed": False, "detail": f"Error reading {skill_md_path}: {e}"})

    # =========================================================================
    # CHECK GROUP 2: SKILL.md files contain meaningful content from the raw notes
    # (agent must have used the notes.txt to write each SKILL.md, not just copy it)
    # =========================================================================
    skill_keywords = {
        "fraud-detection": ["risk", "transaction", "fraud", "score"],
        "currency-converter": ["currency", "exchange", "convert", "rate"],
        "compliance-checker": ["compliance", "aml", "kyc", "regulatory"],
    }
    for skill, keywords in skill_keywords.items():
        max_score += 1.0
        skill_md_path = skills_base / skill / "SKILL.md"
        check_name = f"skill_md_content_{skill}"
        try:
            content = skill_md_path.read_text(encoding="utf-8").lower()
            matched = [kw for kw in keywords if kw in content]
            if len(matched) >= 2:
                checks.append({"name": check_name, "passed": True, "detail": f"SKILL.md for {skill} contains relevant keywords: {matched}"})
                total_score += 1.0
            else:
                checks.append({"name": check_name, "passed": False, "detail": f"SKILL.md for {skill} missing domain keywords. Found: {matched}, needed at least 2 of {keywords}"})
        except Exception as e:
            checks.append({"name": check_name, "passed": False, "detail": f"Cannot read SKILL.md for {skill}: {e}"})

    # =========================================================================
    # CHECK GROUP 3: AGENTS.md exists and is not the old broken version
    # =========================================================================
    max_score += 1.0
    check_name = "agents_md_exists"
    try:
        if agents_md_path.exists():
            content = agents_md_path.read_text(encoding="utf-8")
            # Check it's not just the old broken file
            if "DEPRECATED" in content or ("OLD" in content.upper() and len(content) < 300):
                checks.append({"name": check_name, "passed": False, "detail": "AGENTS.md still contains the old deprecated content. Agent must have updated it."})
            elif len(content.strip()) > 100:
                checks.append({"name": check_name, "passed": True, "detail": f"AGENTS.md exists and has been updated ({len(content)} chars)"})
                total_score += 1.0
            else:
                checks.append({"name": check_name, "passed": False, "detail": "AGENTS.md exists but is too short to be valid"})
        else:
            checks.append({"name": check_name, "passed": False, "detail": f"AGENTS.md not found at {agents_md_path}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error accessing AGENTS.md: {e}"})

    # =========================================================================
    # CHECK GROUP 4: AGENTS.md contains the "## Skills (mandatory)" section
    # This is the key proprietary trap from SKILL.md
    # =========================================================================
    max_score += 1.5
    check_name = "agents_md_skills_mandatory_header"
    try:
        content = agents_md_path.read_text(encoding="utf-8")
        # The SKILL.md says the section must be "## Skills (mandatory)"
        if re.search(r'##\s+Skills\s*\(mandatory\)', content, re.IGNORECASE):
            checks.append({"name": check_name, "passed": True, "detail": "Found '## Skills (mandatory)' section header in AGENTS.md"})
            total_score += 1.5
        else:
            checks.append({"name": check_name, "passed": False, "detail": "AGENTS.md is missing the required '## Skills (mandatory)' section. Found: " + str(content[:300])})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Cannot read AGENTS.md for section check: {e}"})

    # =========================================================================
    # CHECK GROUP 5: AGENTS.md contains the "Before replying: scan" instruction
    # with <available_skills> tag — exact workflow language from SKILL.md
    # =========================================================================
    max_score += 1.5
    check_name = "agents_md_scan_instruction"
    try:
        content = agents_md_path.read_text(encoding="utf-8")
        has_scan = "before replying" in content.lower() and "scan" in content.lower()
        has_available_skills_tag = "<available_skills>" in content
        if has_scan and has_available_skills_tag:
            checks.append({"name": check_name, "passed": True, "detail": "Found 'Before replying: scan <available_skills>' instruction pattern"})
            total_score += 1.5
        else:
            detail_parts = []
            if not has_scan:
                detail_parts.append("missing 'Before replying: scan' instruction")
            if not has_available_skills_tag:
                detail_parts.append("missing <available_skills> tag")
            checks.append({"name": check_name, "passed": False, "detail": "AGENTS.md is missing required elements: " + "; ".join(detail_parts)})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Cannot read AGENTS.md for instruction check: {e}"})

    # =========================================================================
    # CHECK GROUP 6: AGENTS.md <available_skills> block lists all 3 skills
    # with both <description> and <location> tags for each
    # =========================================================================
    max_score += 2.0
    check_name = "agents_md_capability_cards"
    try:
        content = agents_md_path.read_text(encoding="utf-8")
        
        has_description_tags = content.count("<description>") >= 3
        has_location_tags = content.count("<location>") >= 3
        
        all_skills_mentioned = all(skill in content for skill in skill_names)
        
        # Check that locations point to the skills directory
        locations_correct = all(
            f"skills/{skill}" in content or f"skills\\{skill}" in content
            for skill in skill_names
        )
        
        passed_sub = []
        failed_sub = []
        
        if has_description_tags:
            passed_sub.append("3+ <description> tags found")
        else:
            failed_sub.append(f"need 3 <description> tags, found {content.count('<description>')}")
        
        if has_location_tags:
            passed_sub.append("3+ <location> tags found")
        else:
            failed_sub.append(f"need 3 <location> tags, found {content.count('<location>')}")
        
        if all_skills_mentioned:
            passed_sub.append("all 3 skill names present")
        else:
            missing = [s for s in skill_names if s not in content]
            failed_sub.append(f"missing skill names: {missing}")
        
        if locations_correct:
            passed_sub.append("skill locations reference correct paths")
        else:
            failed_sub.append("skill locations don't reference skills/ directory")
        
        if len(failed_sub) == 0:
            checks.append({"name": check_name, "passed": True, "detail": "All capability card checks passed: " + "; ".join(passed_sub)})
            total_score += 2.0
        elif len(passed_sub) >= 2:
            checks.append({"name": check_name, "passed": False, "detail": f"Partial: {'; '.join(passed_sub)} | Failed: {'; '.join(failed_sub)}"})
            total_score += 0.5  # partial credit
        else:
            checks.append({"name": check_name, "passed": False, "detail": f"Failed: {'; '.join(failed_sub)} | Passed: {'; '.join(passed_sub)}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error checking capability cards: {e}"})

    # =========================================================================
    # CHECK GROUP 7: AGENTS.md references the SKILL.md read-on-demand pattern
    # ("read its SKILL.md at <location> with `read`")
    # =========================================================================
    max_score += 1.0
    check_name = "agents_md_read_on_demand"
    try:
        content = agents_md_path.read_text(encoding="utf-8")
        # Check for the read-on-demand pattern: read the SKILL.md when relevant
        has_read_skill = (
            ("skill.md" in content.lower() or "SKILL.md" in content) and
            ("read" in content.lower() or "load" in content.lower())
        )
        if has_read_skill:
            checks.append({"name": check_name, "passed": True, "detail": "AGENTS.md references read-on-demand SKILL.md loading pattern"})
            total_score += 1.0
        else:
            checks.append({"name": check_name, "passed": False, "detail": "AGENTS.md does not reference read-on-demand SKILL.md loading. Should instruct agent to read SKILL.md at <location> when skill applies."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error checking read-on-demand pattern: {e}"})

    # =========================================================================
    # FINAL SCORE
    # =========================================================================
    score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    all_passed = score >= 0.80  # 80% threshold to pass

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))