import sys
import os
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def evaluate(workspace: str):
    checks = []
    workspace = Path(workspace)
    skill_dir = workspace / "skills" / "db-backup"

    # --- CHECK 1: SKILL.md exists in the correct location ---
    skill_md_path = skill_dir / "SKILL.md"
    if not skill_md_path.exists():
        checks.append(check("SKILL.md exists at skills/db-backup/SKILL.md", False, "File not found"))
        # Can't proceed without it
        score = sum(1 for c in checks if c["passed"]) / 15
        return {"passed": False, "score": score, "checks": checks}
    
    try:
        skill_md = skill_md_path.read_text()
    except Exception as e:
        checks.append(check("SKILL.md readable", False, str(e)))
        score = sum(1 for c in checks if c["passed"]) / 15
        return {"passed": False, "score": score, "checks": checks}
    
    checks.append(check("SKILL.md exists at skills/db-backup/SKILL.md", True, "Found"))

    # --- CHECK 2: SKILL.md has a frontmatter name field ---
    has_frontmatter = bool(re.search(r'^---\s*\n.*?name\s*:', skill_md, re.DOTALL | re.MULTILINE))
    checks.append(check("SKILL.md has YAML frontmatter with 'name'", has_frontmatter,
                         "Found frontmatter" if has_frontmatter else "Missing YAML frontmatter block with 'name:'"))

    # --- CHECK 3: Prerequisites section present ---
    has_prereqs = bool(re.search(r'##\s+prerequisites', skill_md, re.IGNORECASE))
    checks.append(check("SKILL.md has Prerequisites section", has_prereqs,
                         "Found" if has_prereqs else "Missing '## Prerequisites' section"))

    # --- CHECK 4: Prerequisites mention concrete checks for pg_dump and aws ---
    has_pgdump_check = bool(re.search(r'pg_dump', skill_md, re.IGNORECASE))
    has_aws_check = bool(re.search(r'aws', skill_md, re.IGNORECASE))
    prereq_concrete = has_pgdump_check and has_aws_check
    checks.append(check("Prerequisites mention pg_dump and aws CLI checks", prereq_concrete,
                         f"pg_dump mentioned: {has_pgdump_check}, aws mentioned: {has_aws_check}"))

    # --- CHECK 5: Configuration section present ---
    has_config_section = bool(re.search(r'##\s+config', skill_md, re.IGNORECASE))
    checks.append(check("SKILL.md has Configuration section", has_config_section,
                         "Found" if has_config_section else "Missing '## Configuration' section"))

    # --- CHECK 6: Config section documents both config.env.example and config.env ---
    has_example_ref = bool(re.search(r'config\.env\.example', skill_md))
    has_real_ref = bool(re.search(r'config\.env(?!\.example)', skill_md))
    checks.append(check("Configuration documents both config.env.example and config.env",
                         has_example_ref and has_real_ref,
                         f"config.env.example referenced: {has_example_ref}, config.env referenced: {has_real_ref}"))

    # --- CHECK 7: Onboarding / Initialization section present ---
    has_onboarding = bool(re.search(r'##\s+(init|install|onboard)', skill_md, re.IGNORECASE))
    checks.append(check("SKILL.md has Initialization/Onboarding section", has_onboarding,
                         "Found" if has_onboarding else "Missing Initialization/Onboarding section"))

    # --- CHECK 8: Chat-first onboarding documented (proprietary trap!) ---
    has_chat_first = bool(re.search(r'(chat.first|preferred.*chat|chat.*preferred)', skill_md, re.IGNORECASE))
    checks.append(check("SKILL.md documents 'Preferred (chat-first)' onboarding path",
                         has_chat_first,
                         "Found chat-first documentation" if has_chat_first else
                         "Missing required 'Preferred (chat-first)' onboarding path — this is a core skill-father requirement"))

    # --- CHECK 9: Reproducibility section present ---
    has_repro = bool(re.search(r'##\s+repro', skill_md, re.IGNORECASE))
    checks.append(check("SKILL.md has Reproducibility section", has_repro,
                         "Found" if has_repro else "Missing '## Reproducibility' section"))

    # --- CHECK 10: config.env.example exists and is NOT empty, has all required keys ---
    example_path = skill_dir / "config.env.example"
    if not example_path.exists():
        checks.append(check("config.env.example exists with required keys", False, "File not found"))
    else:
        try:
            example_content = example_path.read_text()
            required_keys = ["DB_HOST", "DB_PORT", "DB_USER", "DB_NAME", "S3_BUCKET", "S3_ENDPOINT", "BACKUP_RETENTION_DAYS"]
            missing = [k for k in required_keys if k not in example_content]
            passed_ex = len(missing) == 0
            checks.append(check("config.env.example exists with required keys", passed_ex,
                                 f"Missing keys: {missing}" if missing else "All required keys present"))
        except Exception as e:
            checks.append(check("config.env.example exists with required keys", False, str(e)))

    # --- CHECK 11: config.env.example uses placeholder/example values (not real machine values) ---
    if example_path.exists():
        try:
            example_content = example_path.read_text()
            # Should not contain obviously real values like actual IPs, real bucket names from a live system
            # More importantly, it should exist as a SEPARATE file from config.env
            # The key proprietary check: example file should NOT be the same as config.env
            config_env_path = skill_dir / "config.env"
            if config_env_path.exists():
                real_content = config_env_path.read_text()
                # They can differ or be same initially, but both must exist
                both_exist = True
                checks.append(check("Both config.env.example and config.env exist (split config pattern)",
                                     both_exist, "Both files present — correct split pattern"))
            else:
                checks.append(check("Both config.env.example and config.env exist (split config pattern)",
                                     False, "config.env missing — onboarding must create the real config file"))
        except Exception as e:
            checks.append(check("Both config.env.example and config.env exist (split config pattern)", False, str(e)))
    else:
        checks.append(check("Both config.env.example and config.env exist (split config pattern)", False,
                             "config.env.example missing"))

    # --- CHECK 12: config.env has real-ish (non-empty) values and does NOT have all-placeholder values ---
    config_env_path = skill_dir / "config.env"
    if not config_env_path.exists():
        checks.append(check("config.env exists with key=value entries", False, "File not found"))
    else:
        try:
            real_content = config_env_path.read_text()
            required_keys = ["DB_HOST", "DB_PORT", "DB_USER", "DB_NAME", "S3_BUCKET", "S3_ENDPOINT", "BACKUP_RETENTION_DAYS"]
            missing = [k for k in required_keys if not re.search(rf'^{k}\s*=', real_content, re.MULTILINE)]
            checks.append(check("config.env has all required key=value entries", len(missing) == 0,
                                 f"Missing keys: {missing}" if missing else "All keys present"))
        except Exception as e:
            checks.append(check("config.env has all required key=value entries", False, str(e)))

    # --- CHECK 13: references/ directory exists with at least one doc file ---
    refs_dir = skill_dir / "references"
    if refs_dir.exists() and refs_dir.is_dir():
        ref_files = list(refs_dir.iterdir())
        has_refs = len(ref_files) > 0
        checks.append(check("references/ directory exists with doc files (progressive disclosure)",
                             has_refs,
                             f"Found {len(ref_files)} file(s): {[f.name for f in ref_files]}" if has_refs else
                             "references/ directory is empty"))
    else:
        checks.append(check("references/ directory exists with doc files (progressive disclosure)",
                             False, "references/ directory not found"))

    # --- CHECK 14: Symlink in ~/.local/bin pointing to the skill's executable ---
    local_bin = Path.home() / ".local" / "bin"
    symlinks_found = []
    if local_bin.exists():
        for item in local_bin.iterdir():
            try:
                if item.is_symlink():
                    target = item.resolve()
                    # Check if it points somewhere inside the db-backup skill folder
                    try:
                        target.relative_to(skill_dir.resolve())
                        symlinks_found.append(str(item))
                    except ValueError:
                        pass
            except Exception:
                pass
    
    has_symlink = len(symlinks_found) > 0
    checks.append(check("Symlink in ~/.local/bin pointing to skill's script (canonical in skill folder)",
                         has_symlink,
                         f"Found symlinks: {symlinks_found}" if has_symlink else
                         "No symlink found in ~/.local/bin pointing to skills/db-backup/ — required by skill-father standard"))

    # --- CHECK 15: SKILL.md does NOT hardcode machine-specific values (portability check) ---
    # Check that SKILL.md doesn't contain hardcoded IPs, absolute paths with /home/username, etc.
    hardcoded_patterns = [
        r'/home/[a-zA-Z][a-zA-Z0-9_]+/',  # absolute home paths
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b',   # IP addresses (a sign of hardcoded machine config)
    ]
    violations = []
    for pattern in hardcoded_patterns:
        matches = re.findall(pattern, skill_md)
        if matches:
            violations.extend(matches)
    
    no_hardcoding = len(violations) == 0
    checks.append(check("SKILL.md does not hardcode machine-specific values (portability)",
                         no_hardcoding,
                         "No hardcoded values found" if no_hardcoding else
                         f"Potentially hardcoded machine-specific values found: {violations}"))

    # --- Final scoring ---
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total

    # Must pass at minimum: SKILL.md exists, has all 4 required sections,
    # chat-first onboarding, config split, and symlink (the core proprietary traps)
    critical_checks = [
        "SKILL.md exists at skills/db-backup/SKILL.md",
        "SKILL.md has Prerequisites section",
        "SKILL.md has Configuration section",
        "SKILL.md has Initialization/Onboarding section",
        "SKILL.md documents 'Preferred (chat-first)' onboarding path",
        "Both config.env.example and config.env exist (split config pattern)",
        "Symlink in ~/.local/bin pointing to skill's script (canonical in skill folder)",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )

    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))