import sys
import os
import json
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

def find_skill_package(workspace):
    """Find the csv-transformer skill directory (must contain SKILL.md with correct name)."""
    candidates = []
    for skill_md_path in Path(workspace).rglob("SKILL.md"):
        # Skip the broken attempt and legacy files
        if "scratch" in str(skill_md_path) or "legacy" in str(skill_md_path):
            continue
        candidates.append(skill_md_path)
    return candidates

def parse_frontmatter(content):
    """Extract YAML frontmatter from markdown content."""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return None, content
    fm_str = match.group(1)
    try:
        fm = yaml.safe_load(fm_str) if yaml else None
        return fm, content[match.end():]
    except Exception as e:
        return None, content

def run_checks(workspace):
    checks = []

    # ── Find skill package ──────────────────────────────────────────────────
    candidates = find_skill_package(workspace)
    
    skill_md_path = None
    skill_dir = None
    for c in candidates:
        try:
            raw = c.read_text()
            fm, _ = parse_frontmatter(raw)
            if fm and isinstance(fm, dict) and fm.get("name") == "csv-transformer":
                skill_md_path = c
                skill_dir = c.parent
                break
        except Exception:
            pass

    checks.append({
        "name": "skill_package_found",
        "passed": skill_md_path is not None,
        "detail": f"Found csv-transformer SKILL.md at: {skill_md_path}" if skill_md_path else "No SKILL.md with name=csv-transformer found (excluding scratch/legacy dirs)"
    })

    if skill_md_path is None:
        # Cannot continue without the base file
        for name in ["frontmatter_name_kebab", "frontmatter_description", "frontmatter_metadata_author",
                     "frontmatter_metadata_version", "frontmatter_metadata_emoji",
                     "frontmatter_openclaw_requires_bins", "frontmatter_install_block_complete",
                     "frontmatter_install_kind_node", "frontmatter_install_bins_array",
                     "md_section_when_to_use", "md_section_workflow", "md_section_error_handling",
                     "md_section_examples", "dir_structure_index_js", "dir_structure_references",
                     "dir_structure_scripts", "publish_script_exists", "publish_script_slug",
                     "publish_script_name_flag", "publish_script_version_flag", "publish_script_changelog_flag"]:
            checks.append({"name": name, "passed": False, "detail": "Skipped: skill package not found"})
        return checks

    # ── Read and parse SKILL.md ─────────────────────────────────────────────
    try:
        raw_content = skill_md_path.read_text()
        fm, body = parse_frontmatter(raw_content)
    except Exception as e:
        fm, body = None, ""
        checks.append({"name": "skill_md_readable", "passed": False, "detail": str(e)})

    # Check 1: name is kebab-case and correct
    name_val = fm.get("name", "") if fm else ""
    checks.append({
        "name": "frontmatter_name_kebab",
        "passed": name_val == "csv-transformer",
        "detail": f"name='{name_val}', expected 'csv-transformer' (kebab-case)"
    })

    # Check 2: description present and non-trivial
    desc_val = fm.get("description", "") if fm else ""
    desc_ok = isinstance(desc_val, str) and len(desc_val.strip()) > 10
    checks.append({
        "name": "frontmatter_description",
        "passed": desc_ok,
        "detail": f"description='{str(desc_val)[:80]}'"
    })

    # Check 3: metadata.author
    meta = fm.get("metadata", {}) if fm else {}
    author_val = meta.get("author", "") if isinstance(meta, dict) else ""
    checks.append({
        "name": "frontmatter_metadata_author",
        "passed": bool(author_val),
        "detail": f"metadata.author='{author_val}'"
    })

    # Check 4: metadata.version = "2.3.0"
    version_val = str(meta.get("version", "")) if isinstance(meta, dict) else ""
    checks.append({
        "name": "frontmatter_metadata_version",
        "passed": version_val == "2.3.0",
        "detail": f"metadata.version='{version_val}', expected '2.3.0'"
    })

    # Check 5: metadata.emoji present
    emoji_val = meta.get("emoji", "") if isinstance(meta, dict) else ""
    checks.append({
        "name": "frontmatter_metadata_emoji",
        "passed": bool(emoji_val) and isinstance(emoji_val, str),
        "detail": f"metadata.emoji='{emoji_val}'"
    })

    # Check 6: openclaw.requires.bins is a list
    openclaw = meta.get("openclaw", {}) if isinstance(meta, dict) else {}
    requires = openclaw.get("requires", {}) if isinstance(openclaw, dict) else {}
    bins_val = requires.get("bins", []) if isinstance(requires, dict) else []
    bins_ok = isinstance(bins_val, list) and len(bins_val) > 0
    checks.append({
        "name": "frontmatter_openclaw_requires_bins",
        "passed": bins_ok,
        "detail": f"openclaw.requires.bins={bins_val}"
    })

    # Check 7: install block has all required sub-fields (id, kind, package, bins, label)
    install_list = openclaw.get("install", []) if isinstance(openclaw, dict) else []
    required_install_fields = {"id", "kind", "package", "bins", "label"}
    install_complete = False
    install_detail = "install block missing or empty"
    if isinstance(install_list, list) and len(install_list) > 0:
        entry = install_list[0]
        if isinstance(entry, dict):
            present = set(entry.keys())
            missing = required_install_fields - present
            install_complete = len(missing) == 0
            install_detail = f"present fields: {sorted(present)}, missing: {sorted(missing)}"
    checks.append({
        "name": "frontmatter_install_block_complete",
        "passed": install_complete,
        "detail": install_detail
    })

    # Check 8: install[0].kind == "node"
    kind_val = install_list[0].get("kind", "") if (isinstance(install_list, list) and install_list and isinstance(install_list[0], dict)) else ""
    checks.append({
        "name": "frontmatter_install_kind_node",
        "passed": kind_val == "node",
        "detail": f"install[0].kind='{kind_val}', expected 'node'"
    })

    # Check 9: install[0].bins is a list
    inst_bins = install_list[0].get("bins", []) if (isinstance(install_list, list) and install_list and isinstance(install_list[0], dict)) else []
    checks.append({
        "name": "frontmatter_install_bins_array",
        "passed": isinstance(inst_bins, list) and len(inst_bins) > 0,
        "detail": f"install[0].bins={inst_bins}"
    })

    # ── Markdown body section checks ────────────────────────────────────────
    def has_section(b, heading):
        return bool(re.search(r'##\s+' + re.escape(heading), b, re.IGNORECASE))

    checks.append({
        "name": "md_section_when_to_use",
        "passed": has_section(body, "When to Use"),
        "detail": "Body must contain '## When to Use' section"
    })
    checks.append({
        "name": "md_section_workflow",
        "passed": has_section(body, "Workflow"),
        "detail": "Body must contain '## Workflow' section"
    })
    checks.append({
        "name": "md_section_error_handling",
        "passed": has_section(body, "Error Handling"),
        "detail": "Body must contain '## Error Handling' section"
    })
    checks.append({
        "name": "md_section_examples",
        "passed": has_section(body, "Examples"),
        "detail": "Body must contain '## Examples' section"
    })

    # ── Directory structure checks ───────────────────────────────────────────
    index_js = skill_dir / "index.js"
    checks.append({
        "name": "dir_structure_index_js",
        "passed": index_js.exists(),
        "detail": f"index.js {'found' if index_js.exists() else 'NOT found'} at {index_js}"
    })

    references_dir = skill_dir / "references"
    refs_ok = references_dir.is_dir() and any(references_dir.iterdir())
    checks.append({
        "name": "dir_structure_references",
        "passed": refs_ok,
        "detail": f"references/ dir {'found with files' if refs_ok else 'missing or empty'}"
    })

    scripts_dir = skill_dir / "scripts"
    scripts_ok = scripts_dir.is_dir() and any(scripts_dir.iterdir())
    checks.append({
        "name": "dir_structure_scripts",
        "passed": scripts_ok,
        "detail": f"scripts/ dir {'found with files' if scripts_ok else 'missing or empty'}"
    })

    # ── Publish script check ────────────────────────────────────────────────
    # Agent should produce a publish script (any .sh or similar) containing the clawhub publish command
    publish_script = None
    for candidate in Path(workspace).rglob("*.sh"):
        if "legacy" in str(candidate) or "scratch" in str(candidate) or "linters" in str(candidate) or "deploy" in str(candidate):
            continue
        try:
            content = candidate.read_text()
            if "clawhub" in content and "publish" in content:
                publish_script = candidate
                break
        except Exception:
            pass

    # Also check inside the skill dir for any file containing clawhub publish
    if publish_script is None:
        for candidate in skill_dir.rglob("*"):
            if candidate.is_file():
                try:
                    content = candidate.read_text()
                    if "clawhub" in content and "publish" in content:
                        publish_script = candidate
                        break
                except Exception:
                    pass

    checks.append({
        "name": "publish_script_exists",
        "passed": publish_script is not None,
        "detail": f"Publish script {'found at ' + str(publish_script) if publish_script else 'NOT found (expected a file with clawhub publish command)'}"
    })

    pub_content = ""
    if publish_script:
        try:
            pub_content = publish_script.read_text()
        except Exception:
            pass

    # Check --slug csv-transformer
    slug_ok = bool(re.search(r'--slug\s+csv-transformer', pub_content))
    checks.append({
        "name": "publish_script_slug",
        "passed": slug_ok,
        "detail": f"--slug csv-transformer {'found' if slug_ok else 'NOT found'} in publish script"
    })

    # Check --name flag present
    name_flag_ok = bool(re.search(r'--name\s+', pub_content))
    checks.append({
        "name": "publish_script_name_flag",
        "passed": name_flag_ok,
        "detail": f"--name flag {'found' if name_flag_ok else 'NOT found'} in publish script"
    })

    # Check --version 2.3.0
    version_flag_ok = bool(re.search(r'--version\s+2\.3\.0', pub_content))
    checks.append({
        "name": "publish_script_version_flag",
        "passed": version_flag_ok,
        "detail": f"--version 2.3.0 {'found' if version_flag_ok else 'NOT found'} in publish script"
    })

    # Check --changelog present
    changelog_ok = bool(re.search(r'--changelog\s+', pub_content))
    checks.append({
        "name": "publish_script_changelog_flag",
        "passed": changelog_ok,
        "detail": f"--changelog flag {'found' if changelog_ok else 'NOT found'} in publish script"
    })

    return checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    try:
        checks = run_checks(workspace)
    except Exception as e:
        checks = [{"name": "eval_error", "passed": False, "detail": f"Eval crashed: {e}"}]

    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall = (score >= 0.85)

    result = {
        "passed": overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()