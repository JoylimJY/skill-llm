import sys
import os
import json
import re
from pathlib import Path

def run_checks(workspace):
    checks = []
    passed_all = True

    # --- Locate the generated skill bundle ---
    # The agent should have run skill_maker.py with --output pointing to a new directory.
    # We look for a SKILL.md that is NOT in archive/ and is NOT the original skill_maker.py output dir.
    
    skill_md_candidates = [
        p for p in Path(workspace).rglob("SKILL.md")
        if "archive" not in str(p) and "old_skills" not in str(p)
    ]

    # Filter out any pre-existing ones (archive)
    # The valid output should be in a subdirectory that also contains README.md and references/overview.md
    valid_bundle_root = None
    for candidate in skill_md_candidates:
        candidate_dir = candidate.parent
        has_readme = (candidate_dir / "README.md").exists()
        has_overview = (candidate_dir / "references" / "overview.md").exists()
        if has_readme and has_overview:
            valid_bundle_root = candidate_dir
            break

    # CHECK 1: Bundle directory structure exists
    check_bundle = {
        "name": "skill_bundle_structure_complete",
        "passed": valid_bundle_root is not None,
        "detail": f"Found complete bundle (SKILL.md + README.md + references/overview.md) at: {valid_bundle_root}" if valid_bundle_root else "Could not find a complete skill bundle with SKILL.md, README.md, and references/overview.md in the same directory."
    }
    checks.append(check_bundle)
    if not check_bundle["passed"]:
        passed_all = False
        return passed_all, 0.0, checks

    # Read the generated SKILL.md
    skill_md_path = valid_bundle_root / "SKILL.md"
    try:
        skill_md_content = skill_md_path.read_text()
    except Exception as e:
        checks.append({"name": "skill_md_readable", "passed": False, "detail": str(e)})
        return False, 0.0, checks

    # CHECK 2: Frontmatter exists (YAML block between --- markers)
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', skill_md_content, re.DOTALL)
    check_frontmatter = {
        "name": "skill_md_has_frontmatter",
        "passed": frontmatter_match is not None,
        "detail": "SKILL.md contains valid YAML frontmatter block." if frontmatter_match else "SKILL.md is missing the --- frontmatter block."
    }
    checks.append(check_frontmatter)
    if not check_frontmatter["passed"]:
        passed_all = False

    # CHECK 3: skill name is lowercase and URL-safe
    name_match = re.search(r'name:\s*(.+)', skill_md_content)
    skill_name = name_match.group(1).strip() if name_match else ""
    name_valid = bool(re.match(r'^[a-z0-9\-]+$', skill_name)) if skill_name else False
    check_name = {
        "name": "skill_name_lowercase_urlsafe",
        "passed": name_valid,
        "detail": f"Skill name is '{skill_name}' — valid URL-safe lowercase." if name_valid else f"Skill name '{skill_name}' is NOT lowercase/URL-safe (must match [a-z0-9\\-]+)."
    }
    checks.append(check_name)
    if not check_name["passed"]:
        passed_all = False

    # CHECK 4: Description is present and strictly less than 50 characters
    desc_match = re.search(r'description:\s*(.+)', skill_md_content)
    desc = desc_match.group(1).strip() if desc_match else ""
    desc_len_valid = 0 < len(desc) < 50
    check_desc = {
        "name": "skill_desc_under_50_chars",
        "passed": desc_len_valid,
        "detail": f"Description: '{desc}' ({len(desc)} chars) — {'VALID (<50)' if desc_len_valid else 'INVALID (must be <50 chars)'}."
    }
    checks.append(check_desc)
    if not check_desc["passed"]:
        passed_all = False

    # CHECK 5: Category is one of the valid values and is trading (appropriate for the use case)
    valid_categories = ["productivity", "trading", "research", "automation"]
    category_match = re.search(r'category:\s*(\S+)', skill_md_content)
    category = category_match.group(1).strip() if category_match else ""
    category_valid = category in valid_categories
    # For the portfolio rebalancing use case, trading is the correct category
    category_correct = (category == "trading")
    check_category = {
        "name": "skill_category_is_trading",
        "passed": category_correct,
        "detail": f"Category is '{category}' — {'correct (trading)' if category_correct else 'WRONG (expected trading for a portfolio rebalancing skill)'}."
    }
    checks.append(check_category)
    if not check_category["passed"]:
        passed_all = False

    # CHECK 6: Emoji present in frontmatter
    emoji_match = re.search(r'emoji:\s*["\']?(\S+)["\']?', skill_md_content)
    emoji_val = emoji_match.group(1).strip('"\'') if emoji_match else ""
    # Check it's non-empty and is an actual emoji (not the default robot if agent just copy-pasted without using --emoji)
    has_emoji = bool(emoji_val) and emoji_val != ""
    # The task calls for a chart/trading emoji - we check any emoji is present (non-ASCII character or emoji)
    has_nontrivial_emoji = has_emoji and not emoji_val.isascii()
    check_emoji = {
        "name": "skill_has_emoji_in_frontmatter",
        "passed": has_nontrivial_emoji,
        "detail": f"Emoji found: '{emoji_val}' — {'valid emoji' if has_nontrivial_emoji else 'missing or ASCII-only (must be an actual emoji character)'}."
    }
    checks.append(check_emoji)
    if not check_emoji["passed"]:
        passed_all = False

    # CHECK 7: references/overview.md exists and is non-empty
    overview_path = valid_bundle_root / "references" / "overview.md"
    try:
        overview_content = overview_path.read_text()
        overview_ok = len(overview_content.strip()) > 20
    except Exception as e:
        overview_ok = False
        overview_content = ""
    check_overview = {
        "name": "references_overview_md_exists_and_nonempty",
        "passed": overview_ok,
        "detail": f"references/overview.md exists and has content ({len(overview_content)} chars)." if overview_ok else "references/overview.md is missing or empty."
    }
    checks.append(check_overview)
    if not check_overview["passed"]:
        passed_all = False

    # CHECK 8: README.md exists and is non-empty
    readme_path = valid_bundle_root / "README.md"
    try:
        readme_content = readme_path.read_text()
        readme_ok = len(readme_content.strip()) > 20
    except Exception as e:
        readme_ok = False
        readme_content = ""
    check_readme = {
        "name": "readme_md_exists_and_nonempty",
        "passed": readme_ok,
        "detail": f"README.md exists and has content ({len(readme_content)} chars)." if readme_ok else "README.md is missing or empty."
    }
    checks.append(check_readme)
    if not check_readme["passed"]:
        passed_all = False

    # CHECK 9: The skill name in SKILL.md matches the output directory name (bundle naming convention)
    dir_name = valid_bundle_root.name
    name_matches_dir = (dir_name == skill_name) if skill_name else False
    check_dir_name = {
        "name": "bundle_dir_matches_skill_name",
        "passed": name_matches_dir,
        "detail": f"Bundle directory '{dir_name}' matches skill name '{skill_name}'." if name_matches_dir else f"Bundle directory '{dir_name}' does NOT match skill name '{skill_name}'."
    }
    checks.append(check_dir_name)
    if not check_dir_name["passed"]:
        passed_all = False

    # CHECK 10: MIT-0 license mentioned somewhere in the bundle
    all_content = skill_md_content
    try:
        all_content += (valid_bundle_root / "README.md").read_text()
    except:
        pass
    has_mit0 = "MIT-0" in all_content
    check_license = {
        "name": "mit0_license_present",
        "passed": has_mit0,
        "detail": "MIT-0 license found in generated files." if has_mit0 else "MIT-0 license NOT found. skill_maker should output MIT-0 by default."
    }
    checks.append(check_license)
    if not check_license["passed"]:
        passed_all = False

    # Calculate score
    num_checks = len(checks)
    num_passed = sum(1 for c in checks if c["passed"])
    score = round(num_passed / num_checks, 4)

    return passed_all, score, checks


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "workspace_arg", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)

    workspace = sys.argv[1]

    try:
        passed_all, score, checks = run_checks(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crashed", "passed": False, "detail": f"Evaluator crashed: {str(e)}"}]
        }
        print(json.dumps(result))
        sys.exit(0)

    result = {
        "passed": passed_all,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()