import sys
import os
import json
import re
from pathlib import Path

def load_yaml_frontmatter(content: str):
    """Extract and parse YAML frontmatter from a markdown file."""
    import yaml
    if not content.startswith('---'):
        return None, content
    # Find closing ---
    end = content.find('\n---', 3)
    if end == -1:
        return None, content
    frontmatter_str = content[3:end].strip()
    body = content[end+4:].strip()
    try:
        data = yaml.safe_load(frontmatter_str)
        return data, body
    except Exception as e:
        return None, content

def evaluate(workspace: str):
    checks = []
    workspace = Path(workspace)

    # ── HELPER ────────────────────────────────────────────────────────────────
    def add(name, passed, detail=""):
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 1: Find a skill directory with a SKILL.md file
    # The skill MUST be in its own directory (not in tmp/ or distractor dirs)
    # ─────────────────────────────────────────────────────────────────────────
    skill_mds = list(workspace.rglob("SKILL.md"))
    # Filter out the legacy distractor
    skill_mds = [p for p in skill_mds if "legacy" not in str(p) and "old-skills" not in str(p)]

    if not skill_mds:
        add("skill_md_exists", False, "No SKILL.md found outside of legacy/ directories")
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    # Pick the most likely candidate (newest or deepest)
    skill_md_path = sorted(skill_mds, key=lambda p: len(p.parts))[-1]
    skill_dir = skill_md_path.parent
    add("skill_md_exists", True, f"Found SKILL.md at {skill_md_path.relative_to(workspace)}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 2: SKILL.md must have valid YAML frontmatter
    # ─────────────────────────────────────────────────────────────────────────
    try:
        content = skill_md_path.read_text(encoding="utf-8")
        frontmatter, body = load_yaml_frontmatter(content)
    except Exception as e:
        add("frontmatter_parseable", False, f"Could not read/parse SKILL.md: {e}")
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    has_fm = frontmatter is not None
    add("frontmatter_parseable", has_fm, 
        "Frontmatter parsed successfully" if has_fm else "Missing or malformed YAML frontmatter (must start with ---)")

    if not has_fm:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 3: `name` field — required, lowercase+hyphens only, 1-64 chars,
    #           must match the directory name
    # ─────────────────────────────────────────────────────────────────────────
    name_val = frontmatter.get("name", "")
    name_valid_chars = bool(re.match(r'^[a-z0-9][a-z0-9\-]{0,63}$', str(name_val))) if name_val else False
    name_len_ok = 1 <= len(str(name_val)) <= 64 if name_val else False

    add("name_lowercase_hyphens_only", name_valid_chars,
        f"name='{name_val}' — must be lowercase letters, digits, hyphens only, 1-64 chars")

    dir_name = skill_dir.name
    name_matches_dir = (str(name_val) == dir_name)
    add("name_matches_directory", name_matches_dir,
        f"name='{name_val}', directory='{dir_name}' — must match exactly")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 4: `description` field — required, 1-1024 chars, keyword-rich
    # ─────────────────────────────────────────────────────────────────────────
    desc_val = str(frontmatter.get("description", "")).strip()
    desc_len_ok = 1 <= len(desc_val) <= 1024
    add("description_length_valid", desc_len_ok,
        f"description length={len(desc_val)} (must be 1-1024 chars)")

    # Check it contains backup-related keywords (keyword-rich for activation trigger)
    backup_keywords = ["backup", "postgres", "pg_dump", "database", "dump", "backup"]
    keyword_hits = sum(1 for kw in backup_keywords if kw.lower() in desc_val.lower())
    desc_keyword_rich = keyword_hits >= 2
    add("description_keyword_rich", desc_keyword_rich,
        f"description contains {keyword_hits}/5 expected backup-related keywords")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 5: SKILL.md line count ≤ 500
    # ─────────────────────────────────────────────────────────────────────────
    line_count = len(content.splitlines())
    under_500 = line_count <= 500
    add("skill_md_under_500_lines", under_500,
        f"SKILL.md has {line_count} lines (must be ≤ 500)")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 6: Directory structure — must have scripts/ subdirectory
    # ─────────────────────────────────────────────────────────────────────────
    scripts_dir = skill_dir / "scripts"
    has_scripts = scripts_dir.is_dir()
    add("scripts_directory_exists", has_scripts,
        f"scripts/ directory {'found' if has_scripts else 'missing'} under {skill_dir.relative_to(workspace)}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 7: Directory structure — must have references/ subdirectory
    # (because the skill has detailed technical content that should be offloaded)
    # ─────────────────────────────────────────────────────────────────────────
    refs_dir = skill_dir / "references"
    has_refs = refs_dir.is_dir()
    add("references_directory_exists", has_refs,
        f"references/ directory {'found' if has_refs else 'missing'} — detailed appendix content should be here, not inline")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 8: references/ must actually have content (the detailed appendix 
    #           material from Jordan's notes belongs there, not in SKILL.md)
    # ─────────────────────────────────────────────────────────────────────────
    if has_refs:
        ref_files = list(refs_dir.iterdir())
        refs_has_content = len(ref_files) > 0
        add("references_has_content", refs_has_content,
            f"references/ contains {len(ref_files)} file(s) — detailed pg_dump flags, S3 policy, rotation logic belong here")
    else:
        add("references_has_content", False,
            "references/ directory does not exist, cannot check content")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 9: Low-freedom form — since this is critical/fragile infrastructure,
    #           the SKILL.md body must contain a concrete script or exact commands
    #           (not just vague text guidance), consistent with low-freedom level
    # ─────────────────────────────────────────────────────────────────────────
    # Look for code blocks or explicit command snippets in the body
    has_code_block = bool(re.search(r'```', body))
    has_pg_dump_ref = bool(re.search(r'pg_dump|pg_restore|SKILL\.md', body, re.IGNORECASE))
    # At minimum, a concrete script reference or code block should appear
    has_concrete_guidance = has_code_block or has_pg_dump_ref
    add("low_freedom_concrete_guidance", has_concrete_guidance,
        f"Body contains code blocks: {has_code_block}, pg_dump reference: {has_pg_dump_ref} — "
        f"critical fragile tasks require concrete scripts/commands, not vague prose")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 10: SKILL.md body must NOT contain excessive historical/contextual 
    #            filler content (agent already knows Python/bash; no bloat)
    #            Heuristic: body should not contain multi-paragraph historical 
    #            narrative unrelated to agent instructions
    # ─────────────────────────────────────────────────────────────────────────
    # Check for known bloat phrases from Jordan's notes
    bloat_phrases = [
        "switched from mysqldump",
        "incident in 2021",
        "historical context",
        "PagerDuty API",
        "IAM role needs",
        "versioning enabled",
        "s3:PutObject",
        "bucket policy",
    ]
    bloat_found = [p for p in bloat_phrases if p.lower() in body.lower()]
    no_bloat = len(bloat_found) == 0
    add("no_implementation_bloat_in_skill_md", no_bloat,
        f"SKILL.md body should not contain low-level infra details / historical context. "
        f"Found bloat: {bloat_found if bloat_found else 'none'} — these belong in references/")

    # ─────────────────────────────────────────────────────────────────────────
    # SCORING
    # ─────────────────────────────────────────────────────────────────────────
    weights = {
        "skill_md_exists": 1,
        "frontmatter_parseable": 1,
        "name_lowercase_hyphens_only": 2,
        "name_matches_directory": 2,
        "description_length_valid": 1,
        "description_keyword_rich": 1,
        "skill_md_under_500_lines": 2,
        "scripts_directory_exists": 1,
        "references_directory_exists": 2,
        "references_has_content": 2,
        "low_freedom_concrete_guidance": 2,
        "no_implementation_bloat_in_skill_md": 2,
    }
    total_weight = sum(weights.values())
    earned = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    score = round(earned / total_weight, 4)
    passed = score >= 0.75 and all(
        c["passed"] for c in checks
        if c["name"] in {"skill_md_exists", "frontmatter_parseable",
                         "name_lowercase_hyphens_only", "name_matches_directory",
                         "description_length_valid", "skill_md_under_500_lines"}
    )

    result = {"passed": passed, "score": score, "checks": checks}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(ws)