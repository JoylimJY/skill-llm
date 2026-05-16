#!/usr/bin/env python3
"""
Evaluation script for the researcher profile schema standardization task.
Checks:
1. schema/Person.md exists and has correct Picoschema structure
2. Required fields use correct syntax (plain name for required, name? for optional)
3. Enum, array, and relation syntax is correct
4. At least 2 person notes have been fixed (contain observation categories for 'role' and 'email')
5. Schema version has been bumped to 2 and 'homepage' optional field added (evolution step)
6. validation setting is present
"""
import sys
import os
import json
import re
import yaml
from pathlib import Path
from collections import defaultdict

def parse_note_file(filepath):
    """Parse markdown with YAML frontmatter."""
    try:
        with open(filepath) as f:
            content = f.read()
        fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
        if fm_match:
            try:
                frontmatter = yaml.safe_load(fm_match.group(1)) or {}
            except Exception as e:
                frontmatter = {"_parse_error": str(e)}
            body = fm_match.group(2)
        else:
            frontmatter = {}
            body = content
        
        observations = defaultdict(list)
        for line in body.split('\n'):
            obs_match = re.match(r'\s*-\s*\[(\w+)\]\s*(.*)', line)
            if obs_match:
                cat, val = obs_match.group(1), obs_match.group(2).strip()
                observations[cat].append(val)
        
        return frontmatter, body, dict(observations)
    except Exception as e:
        return {"_error": str(e)}, "", {}

def run_checks(workspace):
    checks = []
    
    # =========================================================
    # CHECK 1: schema/Person.md exists
    # =========================================================
    schema_candidates = list(Path(workspace).rglob("Person.md"))
    schema_path = None
    for c in schema_candidates:
        if "schema" in str(c).lower():
            schema_path = str(c)
            break
    if schema_path is None and schema_candidates:
        schema_path = str(schema_candidates[0])
    
    check1_passed = schema_path is not None and os.path.exists(str(schema_path))
    checks.append({
        "name": "schema/Person.md exists",
        "passed": check1_passed,
        "detail": f"Found at: {schema_path}" if check1_passed else "File not found anywhere in workspace"
    })
    
    if not check1_passed:
        # Can't proceed without schema file
        for remaining in ["Schema has correct type=schema and entity=Person",
                          "Schema contains required fields (role, email) without '?' marker",
                          "Schema contains optional fields with '?' marker (orcid, projects)",
                          "Schema uses array syntax for at least one field",
                          "Schema has validation settings block",
                          "frank-lee.md has role observation category",
                          "frank-lee.md has email observation category",
                          "grace-kim.md has role observation category",
                          "grace-kim.md has email observation category",
                          "Schema version bumped to 2",
                          "Schema includes homepage as optional field"]:
            checks.append({"name": remaining, "passed": False, "detail": "Cannot check: schema/Person.md missing"})
        
        total = sum(1 for c in checks if c["passed"])
        return {
            "passed": False,
            "score": total / len(checks),
            "checks": checks
        }
    
    # =========================================================
    # CHECK 2: Schema has correct type and entity
    # =========================================================
    fm, body, obs = parse_note_file(schema_path)
    
    has_schema_type = fm.get("type") == "schema"
    has_entity = fm.get("entity") == "Person"
    check2_passed = has_schema_type and has_entity
    checks.append({
        "name": "Schema has correct type=schema and entity=Person",
        "passed": check2_passed,
        "detail": f"type={fm.get('type')}, entity={fm.get('entity')}"
    })
    
    # =========================================================
    # CHECK 3: Required fields (role, email) without '?' 
    # =========================================================
    schema_def = fm.get("schema", {})
    if not isinstance(schema_def, dict):
        schema_def = {}
    
    schema_keys = list(schema_def.keys()) if schema_def else []
    
    # Check that 'role' and 'email' appear as required (no ?)
    def has_required_field(field_name, schema_keys):
        for k in schema_keys:
            base = k.replace("(array)", "").replace("(enum)", "").strip()
            if base == field_name and "?" not in k:
                return True
        return False
    
    def has_optional_field(field_name, schema_keys):
        for k in schema_keys:
            if field_name in k and "?" in k:
                return True
        return False
    
    has_role_required = has_required_field("role", schema_keys)
    has_email_required = has_required_field("email", schema_keys)
    check3_passed = has_role_required and has_email_required
    checks.append({
        "name": "Schema contains required fields (role, email) without '?' marker",
        "passed": check3_passed,
        "detail": f"role_required={has_role_required}, email_required={has_email_required}. Schema keys: {schema_keys}"
    })
    
    # =========================================================
    # CHECK 4: Optional fields with '?' (orcid or projects should be optional)
    # =========================================================
    has_orcid_optional = has_optional_field("orcid", schema_keys)
    has_projects_optional = has_optional_field("projects", schema_keys)
    check4_passed = has_orcid_optional or has_projects_optional
    checks.append({
        "name": "Schema contains optional fields with '?' marker (orcid or projects)",
        "passed": check4_passed,
        "detail": f"orcid_optional={has_orcid_optional}, projects_optional={has_projects_optional}"
    })
    
    # =========================================================
    # CHECK 5: Array syntax for at least one field (projects likely)
    # =========================================================
    has_array = any("(array)" in k for k in schema_keys)
    checks.append({
        "name": "Schema uses (array) syntax for at least one field",
        "passed": has_array,
        "detail": f"Schema keys: {schema_keys}"
    })
    
    # =========================================================
    # CHECK 6: Validation settings block present
    # =========================================================
    settings = fm.get("settings", {})
    if isinstance(settings, dict):
        has_validation_setting = "validation" in settings
        validation_value = settings.get("validation", None)
    else:
        has_validation_setting = False
        validation_value = None
    checks.append({
        "name": "Schema has validation settings block",
        "passed": has_validation_setting,
        "detail": f"settings={settings}"
    })
    
    # =========================================================
    # CHECK 7 & 8: frank-lee.md has been fixed (role + email observations)
    # =========================================================
    frank_path = os.path.join(workspace, "memory", "people", "frank-lee.md")
    if os.path.exists(frank_path):
        _, _, frank_obs = parse_note_file(frank_path)
        frank_has_role = "role" in frank_obs
        frank_has_email = "email" in frank_obs
    else:
        frank_has_role = False
        frank_has_email = False
    
    checks.append({
        "name": "frank-lee.md has role observation category",
        "passed": frank_has_role,
        "detail": f"Observations found: {list(frank_obs.keys()) if os.path.exists(frank_path) else 'FILE MISSING'}"
    })
    checks.append({
        "name": "frank-lee.md has email observation category",
        "passed": frank_has_email,
        "detail": f"Observations found: {list(frank_obs.keys()) if os.path.exists(frank_path) else 'FILE MISSING'}"
    })
    
    # =========================================================
    # CHECK 9 & 10: grace-kim.md has been fixed (role observation; email may be missing from FM too)
    # =========================================================
    grace_path = os.path.join(workspace, "memory", "people", "grace-kim.md")
    if os.path.exists(grace_path):
        grace_fm, _, grace_obs = parse_note_file(grace_path)
        grace_has_role = "role" in grace_obs
        # grace has no email in frontmatter originally, so we check if she was given one or
        # the note was edited to add a placeholder email observation
        grace_has_email = "email" in grace_obs
    else:
        grace_has_role = False
        grace_has_email = False
    
    checks.append({
        "name": "grace-kim.md has role observation category",
        "passed": grace_has_role,
        "detail": f"Observations found: {list(grace_obs.keys()) if os.path.exists(grace_path) else 'FILE MISSING'}"
    })
    checks.append({
        "name": "grace-kim.md has email observation category (added during fix)",
        "passed": grace_has_email,
        "detail": f"Observations found: {list(grace_obs.keys()) if os.path.exists(grace_path) else 'FILE MISSING'}"
    })
    
    # =========================================================
    # CHECK 11: Schema version bumped to 2 (evolution step)
    # =========================================================
    schema_version = fm.get("version", 1)
    try:
        version_int = int(schema_version)
    except:
        version_int = 0
    check11_passed = version_int >= 2
    checks.append({
        "name": "Schema version bumped to 2 (evolution after homepage discovery)",
        "passed": check11_passed,
        "detail": f"Current version: {schema_version}"
    })
    
    # =========================================================
    # CHECK 12: homepage optional field added to schema
    # =========================================================
    has_homepage = has_optional_field("homepage", schema_keys)
    # Also accept homepage without ? if it was added (but per skill guidelines, new fields should be optional)
    has_homepage_any = any("homepage" in k for k in schema_keys)
    checks.append({
        "name": "Schema includes homepage as optional field",
        "passed": has_homepage or has_homepage_any,
        "detail": f"homepage in schema keys: {has_homepage_any}, as optional (with ?): {has_homepage}. Keys: {schema_keys}"
    })
    
    # =========================================================
    # FINAL SCORE
    # =========================================================
    total_passed = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = total_passed / total
    
    # Task passes if core checks pass (schema exists, structure correct, notes fixed, evolution done)
    # We require at least 9/12 checks to pass for overall pass
    overall_pass = (
        check1_passed and       # schema file exists
        check2_passed and       # correct type/entity
        check3_passed and       # required fields correct
        (total_passed >= 9)     # at least 9/12 checks pass
    )
    
    return {
        "passed": overall_pass,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0, "checks": [], "error": "No workspace path provided"}))
        sys.exit(1)
    
    workspace = sys.argv[1]
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))