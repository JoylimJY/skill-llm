import sys
import json
import re
import subprocess
from pathlib import Path

def parse_frontmatter(text):
    """Returns (dict_of_keys, error_string_or_None)."""
    if not text.startswith("---"):
        return None, "Missing opening --- delimiter"
    lines = text.splitlines()
    try:
        end_idx = lines.index("---", 1)
    except ValueError:
        return None, "Missing closing --- delimiter"
    fm_lines = lines[1:end_idx]
    data = {}
    for line in fm_lines:
        if ":" in line:
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip().strip('"').strip("'")
    return data, None

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []

    # ── Locate the produced skill ──
    skills_lib = workspace / "codex_skills"
    candidate_dirs = [d for d in skills_lib.iterdir() if d.is_dir()] if skills_lib.exists() else []
    # Also search workspace top-level for any ledger-normalizer folder not in draft
    for p in workspace.rglob("SKILL.md"):
        parent = p.parent
        if "DRAFT" in str(parent) or "draft" in str(parent):
            continue
        if parent not in candidate_dirs:
            candidate_dirs.append(parent)

    ledger_dir = None
    for d in candidate_dirs:
        if "ledger" in d.name.lower() or "normalizer" in d.name.lower():
            ledger_dir = d
            break

    # ── CHECK 1: Skill folder exists in the skills library ──
    def check_skill_in_lib():
        target = skills_lib / "ledger-normalizer" if skills_lib.exists() else None
        # Be flexible: any ledger* folder under codex_skills counts
        if skills_lib.exists():
            for d in skills_lib.iterdir():
                if d.is_dir() and ("ledger" in d.name.lower() or "normalizer" in d.name.lower()):
                    return True, f"Found skill folder: {d}"
        return False, "No ledger-normalizer folder found under codex_skills/"

    checks.append(run_check("skill_folder_in_library", check_skill_in_lib))

    # Use the found dir for subsequent checks
    if ledger_dir is None and skills_lib.exists():
        for d in skills_lib.iterdir():
            if d.is_dir() and ("ledger" in d.name.lower() or "normalizer" in d.name.lower()):
                ledger_dir = d
                break

    # ── CHECK 2: SKILL.md exists ──
    def check_skill_md_exists():
        if ledger_dir is None:
            return False, "Skill directory not found"
        skill_md = ledger_dir / "SKILL.md"
        if skill_md.exists():
            return True, f"SKILL.md found at {skill_md}"
        return False, f"SKILL.md missing in {ledger_dir}"

    checks.append(run_check("skill_md_exists", check_skill_md_exists))

    # ── CHECK 3: Frontmatter has ONLY name and description ──
    def check_frontmatter_strict():
        if ledger_dir is None:
            return False, "Skill directory not found"
        skill_md = ledger_dir / "SKILL.md"
        if not skill_md.exists():
            return False, "SKILL.md missing"
        text = skill_md.read_text()
        fm, err = parse_frontmatter(text)
        if err:
            return False, f"Frontmatter parse error: {err}"
        allowed = {"name", "description"}
        extra = set(fm.keys()) - allowed
        if extra:
            return False, f"Frontmatter has disallowed keys: {sorted(extra)}. Only 'name' and 'description' are permitted."
        if "name" not in fm or not fm["name"]:
            return False, "Frontmatter missing 'name'"
        if "description" not in fm or not fm["description"]:
            return False, "Frontmatter missing 'description'"
        return True, f"Frontmatter clean. Keys: {sorted(fm.keys())}"

    checks.append(run_check("frontmatter_only_name_and_description", check_frontmatter_strict))

    # ── CHECK 4: description covers both function AND trigger scenarios ──
    def check_description_quality():
        if ledger_dir is None:
            return False, "Skill directory not found"
        skill_md = ledger_dir / "SKILL.md"
        if not skill_md.exists():
            return False, "SKILL.md missing"
        text = skill_md.read_text()
        fm, err = parse_frontmatter(text)
        if err or fm is None:
            return False, "Cannot parse frontmatter"
        desc = fm.get("description", "")
        if len(desc) < 40:
            return False, f"Description too short ({len(desc)} chars); must cover function and trigger scenarios."
        # Should mention usage/trigger language
        trigger_hints = ["use when", "use for", "trigger", "normalize", "convert", "transform", "ledger", "broker"]
        has_trigger = any(h in desc.lower() for h in trigger_hints)
        if not has_trigger:
            return False, f"Description does not appear to cover trigger scenarios. Got: '{desc}'"
        return True, f"Description adequate ({len(desc)} chars): '{desc[:80]}...'"

    checks.append(run_check("description_covers_triggers", check_description_quality))

    # ── CHECK 5: SKILL.md body is procedural (not documentary/project-description) ──
    def check_body_is_procedural():
        if ledger_dir is None:
            return False, "Skill directory not found"
        skill_md = ledger_dir / "SKILL.md"
        if not skill_md.exists():
            return False, "SKILL.md missing"
        text = skill_md.read_text()
        # Strip frontmatter
        lines = text.splitlines()
        try:
            end_idx = lines.index("---", 1)
            body = "\n".join(lines[end_idx+1:])
        except ValueError:
            body = text
        body_lower = body.lower()
        # Bad signals: project background, status sections, "this project was started"
        bad_patterns = [
            r"this project was",
            r"## background",
            r"## status",
            r"work in progress",
            r"see project\.md",
            r"## project overview",
        ]
        hits = [p for p in bad_patterns if re.search(p, body_lower)]
        if hits:
            return False, f"SKILL.md body appears documentary, not procedural. Bad patterns found: {hits}"
        # Good signals: step-oriented language
        good_patterns = [r"##\s*step", r"\d+\.", r"##\s*phase", r"##\s*how", r"##\s*usage", r"##\s*workflow"]
        good_hits = [p for p in good_patterns if re.search(p, body_lower)]
        if not good_hits:
            return False, "SKILL.md body lacks procedural structure (steps, numbered list, workflow phases)."
        return True, f"Body appears procedural. Procedural signals: {good_hits}"

    checks.append(run_check("skill_md_body_is_procedural", check_body_is_procedural))

    # ── CHECK 6: No README.md or PROJECT.md inside the skill folder ──
    def check_no_banned_docs():
        if ledger_dir is None:
            return False, "Skill directory not found"
        banned = ["README.md", "PROJECT.md", "STATUS.md", "notes.txt"]
        found = [f for f in banned if (ledger_dir / f).exists()]
        # Also check they aren't nested one level deep
        for child in ledger_dir.iterdir():
            if child.is_file() and child.name in banned:
                if child.name not in found:
                    found.append(child.name)
        if found:
            return False, f"Banned documentation files found inside skill folder: {found}"
        return True, "No banned auxiliary docs (README.md, PROJECT.md, etc.) found inside skill folder."

    checks.append(run_check("no_banned_auxiliary_docs", check_no_banned_docs))

    # ── CHECK 7: references/ directory exists with at least one real .md file ──
    def check_references_dir():
        if ledger_dir is None:
            return False, "Skill directory not found"
        refs = ledger_dir / "references"
        if not refs.exists():
            return False, "references/ directory missing from skill folder"
        md_files = list(refs.glob("*.md"))
        if not md_files:
            return False, "references/ exists but contains no .md files"
        # Check they're not empty
        non_empty = [f for f in md_files if f.stat().st_size > 30]
        if not non_empty:
            return False, f"All .md files in references/ appear empty or near-empty: {[f.name for f in md_files]}"
        return True, f"references/ has {len(non_empty)} substantive .md file(s): {[f.name for f in non_empty]}"

    checks.append(run_check("references_directory_with_content", check_references_dir))

    # ── CHECK 8: references are ONE hop (no deep chains from SKILL.md) ──
    def check_no_deep_reference_chains():
        if ledger_dir is None:
            return False, "Skill directory not found"
        skill_md = ledger_dir / "SKILL.md"
        if not skill_md.exists():
            return False, "SKILL.md missing"
        text = skill_md.read_text()
        # Find markdown links with path depth > 1 hop
        deep = re.findall(r'\[.*?\]\(((?:[^/()]+/){2,}[^()]+)\)', text)
        if deep:
            return False, f"Deep reference chain(s) detected in SKILL.md: {deep}. References must be one hop away."
        return True, "No deep reference chains detected. All links are one hop."

    checks.append(run_check("references_one_hop_only", check_no_deep_reference_chains))

    # ── CHECK 9: scripts/ directory exists in skill folder ──
    def check_scripts_dir():
        if ledger_dir is None:
            return False, "Skill directory not found"
        scripts = ledger_dir / "scripts"
        if not scripts.exists():
            return False, "scripts/ directory missing from skill folder"
        return True, f"scripts/ directory present at {scripts}"

    checks.append(run_check("scripts_directory_present", check_scripts_dir))

    # ── CHECK 10: agents/openai.yaml exists with display_name and short_description ──
    def check_openai_yaml():
        if ledger_dir is None:
            return False, "Skill directory not found"
        yaml_path = ledger_dir / "agents" / "openai.yaml"
        if not yaml_path.exists():
            return False, "agents/openai.yaml missing; --interface flags were required"
        content = yaml_path.read_text()
        has_display = "display_name" in content
        has_short = "short_description" in content
        if not has_display:
            return False, "agents/openai.yaml missing 'display_name' field (--interface display_name=... was required)"
        if not has_short:
            return False, "agents/openai.yaml missing 'short_description' field (--interface short_description=... was required)"
        return True, f"agents/openai.yaml present with display_name and short_description."

    checks.append(run_check("agents_openai_yaml_with_interface", check_openai_yaml))

    # ── CHECK 11: validate_skill.py passes against the produced skill ──
    def check_validation_passes():
        if ledger_dir is None:
            return False, "Skill directory not found"
        validate_script = workspace / "scripts" / "validate_skill.py"
        if not validate_script.exists():
            return False, "scripts/validate_skill.py not found in workspace"
        try:
            result = subprocess.run(
                ["python3", str(validate_script), str(ledger_dir)],
                capture_output=True, text=True, timeout=30
            )
            stdout = result.stdout + result.stderr
            if result.returncode == 0:
                return True, f"validate_skill.py PASSED. Output: {stdout[:300]}"
            else:
                return False, f"validate_skill.py FAILED (exit {result.returncode}). Output: {stdout[:400]}"
        except subprocess.TimeoutExpired:
            return False, "validate_skill.py timed out"

    checks.append(run_check("validation_script_passes", check_validation_passes))

    # ── CHECK 12: draft folder NOT modified (email-triage-DRAFT must be untouched) ──
    def check_other_draft_untouched():
        email_draft = workspace / "draft_submissions" / "email-triage-DRAFT" / "SKILL.md"
        if not email_draft.exists():
            return False, "email-triage-DRAFT/SKILL.md was deleted — must not be modified"
        content = email_draft.read_text()
        if "author: asmith" not in content:
            return False, "email-triage-DRAFT/SKILL.md was modified — only ledger-normalizer should be touched"
        return True, "email-triage-DRAFT is untouched."

    checks.append(run_check("other_draft_untouched", check_other_draft_untouched))

    # ── Score ──
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall = passed_count >= 9  # Must pass at least 9/12 checks, including critical ones

    # Critical checks must ALL pass for overall success
    critical_names = {
        "skill_folder_in_library",
        "frontmatter_only_name_and_description",
        "skill_md_body_is_procedural",
        "validation_script_passes",
    }
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_names)
    overall = overall and critical_passed

    output = {
        "passed": overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()