import sys
import json
import os
import re
from pathlib import Path

def evaluate(workspace: str) -> dict:
    checks = []
    total_score = 0.0
    max_score = 6.0

    home = Path.home()
    openclaw_agents = home / ".openclaw" / "workspace" / "agents"
    openclaw_skills = home / ".openclaw" / "workspace" / "skills"

    # ── Check 1: Agent directory exists with correct name ────────────────────
    # The task requires creating "pipeline-watcher" agent
    # We look for any agent directory that is NOT "legacy-ops-agent"
    try:
        all_agents = [d for d in openclaw_agents.iterdir() if d.is_dir() and d.name != "legacy-ops-agent"]
        
        # The correct name pattern: lowercase + hyphens
        valid_name_re = re.compile(r'^[a-z][a-z0-9-]+$')
        valid_agents = [d for d in all_agents if valid_name_re.match(d.name)]
        
        if not valid_agents:
            checks.append({"name": "agent_directory_exists", "passed": False,
                           "detail": f"No valid agent directory found under {openclaw_agents}. Found: {[d.name for d in all_agents]}"})
        else:
            agent_dir = valid_agents[0]
            checks.append({"name": "agent_directory_exists", "passed": True,
                           "detail": f"Agent directory found: {agent_dir.name}"})
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "agent_directory_exists", "passed": False,
                       "detail": f"Error scanning agents directory: {e}"})
        agent_dir = None

    if agent_dir is None:
        # Can't proceed with other checks
        for name in ["soul_md_exists", "soul_frontmatter_valid", "soul_sections_valid",
                     "skills_symlinks_exist", "readme_exists"]:
            checks.append({"name": name, "passed": False, "detail": "Skipped: no valid agent directory found."})
        return {
            "passed": False,
            "score": total_score / max_score,
            "checks": checks
        }

    # ── Check 2: SOUL.md exists ───────────────────────────────────────────────
    soul_path = agent_dir / "SOUL.md"
    try:
        soul_exists = soul_path.is_file()
        checks.append({"name": "soul_md_exists", "passed": soul_exists,
                       "detail": f"SOUL.md {'found' if soul_exists else 'NOT found'} at {soul_path}"})
        if soul_exists:
            total_score += 0.5
    except Exception as e:
        checks.append({"name": "soul_md_exists", "passed": False, "detail": str(e)})
        soul_exists = False

    # ── Check 3: SOUL.md YAML front-matter is valid ──────────────────────────
    soul_content = ""
    try:
        if soul_exists:
            soul_content = soul_path.read_text(encoding="utf-8")
            # Must have --- delimited front-matter with name, description, created_at
            fm_pattern = re.compile(r'^---\s*\n(.*?)\n---', re.DOTALL)
            fm_match = fm_pattern.match(soul_content)
            if not fm_match:
                checks.append({"name": "soul_frontmatter_valid", "passed": False,
                               "detail": "SOUL.md does not start with a valid YAML front-matter block (--- ... ---)"})
            else:
                fm_text = fm_match.group(1)
                has_name        = bool(re.search(r'^name\s*:', fm_text, re.MULTILINE))
                has_description = bool(re.search(r'^description\s*:', fm_text, re.MULTILINE))
                has_created_at  = bool(re.search(r'^created_at\s*:', fm_text, re.MULTILINE))
                all_fields = has_name and has_description and has_created_at
                detail = (f"name={'✓' if has_name else '✗'}, "
                          f"description={'✓' if has_description else '✗'}, "
                          f"created_at={'✓' if has_created_at else '✗'}")
                checks.append({"name": "soul_frontmatter_valid", "passed": all_fields, "detail": detail})
                if all_fields:
                    total_score += 1.0
        else:
            checks.append({"name": "soul_frontmatter_valid", "passed": False,
                           "detail": "Skipped: SOUL.md does not exist."})
    except Exception as e:
        checks.append({"name": "soul_frontmatter_valid", "passed": False, "detail": str(e)})

    # ── Check 4: SOUL.md has all required Chinese-named sections ─────────────
    try:
        if soul_exists and soul_content:
            required_sections = ["## 职责", "## 可用 Skill", "## 运行规则", "## 使用示例"]
            section_results = {}
            for sec in required_sections:
                section_results[sec] = sec in soul_content

            # Also check usage example format: @{agent_name} [你的指令]
            agent_name_val = agent_dir.name
            usage_pattern = re.compile(rf'@{re.escape(agent_name_val)}\s*\[你的指令\]')
            has_usage = bool(usage_pattern.search(soul_content))
            section_results["@agent usage example"] = has_usage

            all_sections_ok = all(section_results.values())
            detail = ", ".join(f"{k}={'✓' if v else '✗'}" for k, v in section_results.items())
            checks.append({"name": "soul_sections_valid", "passed": all_sections_ok, "detail": detail})
            if all_sections_ok:
                total_score += 1.5
            elif sum(section_results.values()) >= 3:
                total_score += 0.5  # partial credit
        else:
            checks.append({"name": "soul_sections_valid", "passed": False,
                           "detail": "Skipped: SOUL.md does not exist or is empty."})
    except Exception as e:
        checks.append({"name": "soul_sections_valid", "passed": False, "detail": str(e)})

    # ── Check 5: skills/ subdirectory with symlinks to existing skills ────────
    try:
        skills_subdir = agent_dir / "skills"
        if not skills_subdir.is_dir():
            checks.append({"name": "skills_symlinks_exist", "passed": False,
                           "detail": f"skills/ subdirectory not found under {agent_dir}"})
        else:
            # Find symlinks in skills/
            symlinks = [p for p in skills_subdir.iterdir() if p.is_symlink()]
            # Verify they point to valid existing skill directories
            valid_symlinks = []
            for link in symlinks:
                target = link.resolve()
                if target.is_dir() and (openclaw_skills / link.name).is_dir():
                    valid_symlinks.append(link.name)

            if len(valid_symlinks) >= 2:
                checks.append({"name": "skills_symlinks_exist", "passed": True,
                               "detail": f"Found {len(valid_symlinks)} valid skill symlink(s): {valid_symlinks}"})
                total_score += 1.5
            elif len(valid_symlinks) == 1:
                checks.append({"name": "skills_symlinks_exist", "passed": False,
                               "detail": f"Only 1 valid symlink found ({valid_symlinks}); at least 2 required."})
                total_score += 0.5
            else:
                all_items = list(skills_subdir.iterdir())
                checks.append({"name": "skills_symlinks_exist", "passed": False,
                               "detail": f"No valid skill symlinks found. Items in skills/: {[p.name for p in all_items]}"})
    except Exception as e:
        checks.append({"name": "skills_symlinks_exist", "passed": False, "detail": str(e)})

    # ── Check 6: README.md exists ─────────────────────────────────────────────
    try:
        readme_path = agent_dir / "README.md"
        readme_exists = readme_path.is_file()
        if readme_exists:
            readme_content = readme_path.read_text(encoding="utf-8")
            has_agent_name = agent_dir.name in readme_content
            checks.append({"name": "readme_exists", "passed": readme_exists,
                           "detail": f"README.md found, mentions agent name: {'✓' if has_agent_name else '✗'}"})
            total_score += 0.5
        else:
            checks.append({"name": "readme_exists", "passed": False,
                           "detail": f"README.md not found at {agent_dir / 'README.md'}"})
    except Exception as e:
        checks.append({"name": "readme_exists", "passed": False, "detail": str(e)})

    final_score = round(total_score / max_score, 3)
    passed = final_score >= 0.75 and all(
        c["passed"] for c in checks if c["name"] in [
            "agent_directory_exists", "soul_md_exists", "soul_sections_valid", "skills_symlinks_exist"
        ]
    )

    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))