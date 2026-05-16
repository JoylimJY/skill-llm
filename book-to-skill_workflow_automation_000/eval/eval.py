import sys
import os
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)

    # ── 1. Find the generated skill directory ──────────────────────────────────
    # The agent should have created a skill directory under skills/ or anywhere
    # We look for a SKILL.md that is NOT one of the pre-existing ones
    existing_skill_dirs = {
        "gtd-method", "servant-leadership", "active-listening"
    }

    # Find all SKILL.md files
    all_skill_files = list(workspace.rglob("SKILL.md"))
    # Filter out pre-existing ones
    new_skill_files = [
        f for f in all_skill_files
        if f.parent.name not in existing_skill_dirs
        and "drafts" not in str(f)
    ]

    if not new_skill_files:
        checks.append({"name": "skill_directory_created", "passed": False,
                        "detail": "No new SKILL.md file found in workspace."})
        return {"passed": False, "score": 0.0, "checks": checks}

    # Use the first new SKILL.md found (should be only one meaningful one)
    # Prefer one that has 'pomodoro' in path or name
    skill_md_path = None
    for f in new_skill_files:
        if "pomodoro" in str(f).lower() or "time" in str(f).lower() or "tomato" in str(f).lower():
            skill_md_path = f
            break
    if skill_md_path is None:
        skill_md_path = new_skill_files[0]

    skill_dir = skill_md_path.parent
    checks.append({"name": "skill_directory_created", "passed": True,
                   "detail": f"Found new skill at: {skill_md_path}"})

    # ── 2. Read SKILL.md content ───────────────────────────────────────────────
    try:
        content = skill_md_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "skill_md_readable", "passed": False,
                        "detail": f"Could not read SKILL.md: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "skill_md_readable", "passed": True, "detail": "SKILL.md is readable."})

    # ── 3. YAML frontmatter check ──────────────────────────────────────────────
    yaml_pattern = re.compile(r'^---\s*\n(.*?)\n---', re.DOTALL)
    yaml_match = yaml_pattern.match(content)

    has_frontmatter = yaml_match is not None
    checks.append({"name": "yaml_frontmatter_present", "passed": has_frontmatter,
                   "detail": "YAML frontmatter (--- ... ---) found." if has_frontmatter
                             else "Missing YAML frontmatter block."})

    has_name_field = False
    has_description_field = False
    name_is_kebab_or_reasonable = False
    description_has_usage_hint = False

    if yaml_match:
        yaml_body = yaml_match.group(1)
        # Check for name field
        name_match = re.search(r'^name:\s*(.+)$', yaml_body, re.MULTILINE)
        has_name_field = name_match is not None
        if name_match:
            name_val = name_match.group(1).strip()
            # Name should be kebab-case English or reasonable Chinese/mixed
            name_is_kebab_or_reasonable = (
                bool(re.match(r'^[a-z][a-z0-9\-]+$', name_val)) or
                len(name_val) > 3  # Chinese name
            )
            # Name should relate to pomodoro or time management
            name_lower = name_val.lower()

        # Check for description field
        desc_match = re.search(r'^description:\s*(.+)$', yaml_body, re.MULTILINE)
        has_description_field = desc_match is not None
        if desc_match:
            desc_val = desc_match.group(1).strip()
            # Description should have usage context (用于 pattern from SKILL.md)
            description_has_usage_hint = "用于" in desc_val or "when" in desc_val.lower() or "for" in desc_val.lower()

    checks.append({"name": "frontmatter_name_field", "passed": has_name_field,
                   "detail": "name: field present in YAML frontmatter." if has_name_field
                             else "Missing name: field in frontmatter."})
    checks.append({"name": "name_follows_convention", "passed": name_is_kebab_or_reasonable,
                   "detail": "Name follows naming convention." if name_is_kebab_or_reasonable
                             else "Name does not follow kebab-case or reasonable naming convention."})
    checks.append({"name": "frontmatter_description_field", "passed": has_description_field,
                   "detail": "description: field present in YAML frontmatter." if has_description_field
                             else "Missing description: field in frontmatter."})
    checks.append({"name": "description_has_usage_context", "passed": description_has_usage_hint,
                   "detail": "Description includes usage context." if description_has_usage_hint
                             else "Description missing usage context (should indicate when to use this skill)."})

    # ── 4. Template A section checks (方法论型) ────────────────────────────────
    body = content[yaml_match.end():] if yaml_match else content

    # Required sections for Template A
    required_sections = {
        "核心方法论": r'##\s*核心方法论|##\s*Core Method|##\s*方法',
        "具体步骤": r'##\s*具体步骤|##\s*Steps|##\s*步骤',
        "实践技巧": r'##\s*实践技巧|##\s*Tips|##\s*技巧|##\s*Practice',
        "应用场景": r'##\s*应用场景|##\s*Use Cases|##\s*场景|##\s*Application',
        "常见误区": r'##\s*常见误区|##\s*Common Mistakes|##\s*误区|##\s*Pitfalls',
    }

    section_results = {}
    for section_name, pattern in required_sections.items():
        found = bool(re.search(pattern, body, re.IGNORECASE))
        section_results[section_name] = found
        checks.append({
            "name": f"section_{section_name}",
            "passed": found,
            "detail": f"Section '{section_name}' found." if found
                      else f"Section '{section_name}' missing from SKILL.md."
        })

    # ── 5. Content quality: Must contain Pomodoro-specific content ────────────
    pomodoro_keywords = ["pomodoro", "番茄", "25分钟", "25 min", "timer", "计时", "专注",
                         "中断", "休息", "break", "focused", "时间管理"]
    content_lower = content.lower()
    keyword_hits = [kw for kw in pomodoro_keywords if kw.lower() in content_lower]
    has_relevant_content = len(keyword_hits) >= 3

    checks.append({"name": "content_is_pomodoro_relevant", "passed": has_relevant_content,
                   "detail": f"Found {len(keyword_hits)} Pomodoro-relevant keywords: {keyword_hits[:5]}"
                             if has_relevant_content
                             else f"Content lacks Pomodoro-specific keywords. Only found: {keyword_hits}"})

    # ── 6. Numbered steps present ──────────────────────────────────────────────
    has_numbered_steps = bool(re.search(r'^\s*\d+\.\s+.+', body, re.MULTILINE))
    checks.append({"name": "has_numbered_steps", "passed": has_numbered_steps,
                   "detail": "Numbered steps found in skill body." if has_numbered_steps
                             else "No numbered steps found. Template A requires numbered steps."})

    # ── 7. references/ subdirectory check ─────────────────────────────────────
    references_dir = skill_dir / "references"
    has_references_dir = references_dir.exists() and references_dir.is_dir()

    if has_references_dir:
        ref_files = list(references_dir.glob("*.md"))
        has_ref_files = len(ref_files) >= 1
        checks.append({"name": "references_directory_exists", "passed": True,
                        "detail": f"references/ directory found with {len(ref_files)} markdown file(s)."})
        checks.append({"name": "references_has_content", "passed": has_ref_files,
                        "detail": f"references/ contains {len(ref_files)} .md files." if has_ref_files
                                  else "references/ directory is empty."})
    else:
        checks.append({"name": "references_directory_exists", "passed": False,
                        "detail": "references/ subdirectory not found inside the skill directory."})
        checks.append({"name": "references_has_content", "passed": False,
                        "detail": "No references/ directory — cannot check for content files."})

    # ── 8. Skill must NOT be verbatim copy of book text ───────────────────────
    # Check that it's distilled, not just a dump
    # A verbatim copy would have very long consecutive lines from the book
    verbatim_phrases = [
        "The Pomodoro Technique was invented in the late 1980s",
        "then university student Francesco Cirillo",
        "Feeling overwhelmed, he asked himself to commit",
    ]
    is_verbatim = any(phrase in content for phrase in verbatim_phrases)
    checks.append({"name": "content_is_distilled_not_verbatim", "passed": not is_verbatim,
                   "detail": "Content is distilled/summarized (not verbatim copy)." if not is_verbatim
                             else "Content contains verbatim passages from book — should be distilled."})

    # ── 9. Skill file is concise (not just dumped book text) ──────────────────
    word_count = len(content.split())
    is_concise = word_count < 2000  # SKILL.md says "concise is key"
    checks.append({"name": "skill_is_concise", "passed": is_concise,
                   "detail": f"SKILL.md has {word_count} words — {'concise' if is_concise else 'too verbose (should be distilled, not a full book dump)'}."})

    # ── Scoring ────────────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = len(passed_checks) / total

    # Must pass these critical checks to overall pass
    critical = [
        "skill_directory_created",
        "yaml_frontmatter_present",
        "frontmatter_name_field",
        "frontmatter_description_field",
        "content_is_pomodoro_relevant",
        "has_numbered_steps",
        "section_具体步骤",
        "section_应用场景",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical
    )

    overall_passed = critical_passed and score >= 0.70

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(ws)
    print(json.dumps(result, ensure_ascii=False, indent=2))