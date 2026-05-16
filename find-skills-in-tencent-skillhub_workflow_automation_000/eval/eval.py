#!/usr/bin/env python3
import sys
import json
import os
import subprocess
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception during check: {e}"}

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    
    # -------------------------------------------------------------------
    # CHECK 1: skill_inventory.json exists somewhere in the workspace
    # -------------------------------------------------------------------
    def check_inventory_exists():
        matches = list(Path(workspace).rglob("skill_inventory.json"))
        if not matches:
            return False, "skill_inventory.json not found anywhere in workspace."
        return True, f"Found at: {matches[0]}"

    checks.append(run_check("skill_inventory.json exists", check_inventory_exists))

    # Resolve path for downstream checks
    inventory_path = None
    matches = list(Path(workspace).rglob("skill_inventory.json"))
    if matches:
        inventory_path = matches[0]

    # -------------------------------------------------------------------
    # CHECK 2: skill_inventory.json is valid JSON
    # -------------------------------------------------------------------
    def check_inventory_is_valid_json():
        if inventory_path is None:
            return False, "File not found, cannot parse."
        try:
            with open(inventory_path, "r") as f:
                content = f.read().strip()
            data = json.loads(content)
            return True, f"Valid JSON parsed. Type: {type(data).__name__}"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}"

    checks.append(run_check("skill_inventory.json is valid JSON", check_inventory_is_valid_json))

    # Load data for further checks
    inventory_data = None
    if inventory_path:
        try:
            with open(inventory_path, "r") as f:
                inventory_data = json.loads(f.read().strip())
        except Exception:
            pass

    # -------------------------------------------------------------------
    # CHECK 3: Inventory is non-empty (has at least one skill listed)
    # -------------------------------------------------------------------
    def check_inventory_non_empty():
        if inventory_data is None:
            return False, "Could not load inventory data."
        # The list action returns an array or an object with a list
        # Accept: array with >=1 items, or dict with a key containing an array
        if isinstance(inventory_data, list):
            if len(inventory_data) >= 1:
                return True, f"Inventory contains {len(inventory_data)} skill(s)."
            else:
                return False, "Inventory list is empty — no skills appear to be installed."
        elif isinstance(inventory_data, dict):
            # Could be wrapped: {"skills": [...]} or similar
            for v in inventory_data.values():
                if isinstance(v, list) and len(v) >= 1:
                    return True, f"Inventory dict contains a list of {len(v)} skill(s)."
            # Or it might directly be a single-skill object
            if len(inventory_data) > 0:
                return True, f"Inventory dict has {len(inventory_data)} keys (may be single skill or wrapped)."
        return False, f"Inventory data structure unexpected or empty: {str(inventory_data)[:200]}"

    checks.append(run_check("Inventory is non-empty", check_inventory_non_empty))

    # -------------------------------------------------------------------
    # CHECK 4: A "search"-related skill is actually installed on the system
    #          (skillhub installs to ~/.openclaw/skills/ by default)
    # -------------------------------------------------------------------
    def check_search_skill_installed():
        skills_dir = Path.home() / ".openclaw" / "skills"
        if not skills_dir.exists():
            return False, f"Skills directory does not exist: {skills_dir}"
        
        installed = [d.name for d in skills_dir.iterdir() if d.is_dir()]
        if not installed:
            return False, f"No skills installed in {skills_dir}"
        
        # Check if any installed skill slug contains "search"
        search_skills = [s for s in installed if "search" in s.lower()]
        if search_skills:
            return True, f"Search-related skill(s) found: {search_skills}"
        
        # Accept any installation as partial credit signal
        return False, f"Installed skills: {installed} — none appear to be search-related."

    checks.append(run_check("Search skill installed in ~/.openclaw/skills/", check_search_skill_installed))

    # -------------------------------------------------------------------
    # CHECK 5: Inventory content reflects the installed skill(s) 
    #          (slug or name from the inventory matches what is on disk)
    # -------------------------------------------------------------------
    def check_inventory_matches_disk():
        if inventory_data is None:
            return False, "Could not load inventory data."
        
        skills_dir = Path.home() / ".openclaw" / "skills"
        if not skills_dir.exists():
            return False, f"Skills directory does not exist: {skills_dir}"
        
        installed_slugs = set(d.name for d in skills_dir.iterdir() if d.is_dir())
        if not installed_slugs:
            return False, "No skills on disk to match against."
        
        # Serialize inventory to string for broad matching
        inventory_str = json.dumps(inventory_data).lower()
        
        matches = []
        for slug in installed_slugs:
            if slug.lower() in inventory_str:
                matches.append(slug)
        
        if matches:
            return True, f"Inventory content references installed skill(s): {matches}"
        
        return False, (
            f"Installed slugs on disk: {installed_slugs}. "
            f"None found in inventory content: {inventory_str[:300]}"
        )

    checks.append(run_check("Inventory content matches installed skills on disk", check_inventory_matches_disk))

    # -------------------------------------------------------------------
    # CHECK 6: usage.sh script was used (indirectly verified by confirming
    #          the skillhub CLI is present and functional)
    # -------------------------------------------------------------------
    def check_skillhub_functional():
        try:
            result = subprocess.run(
                ["skillhub", "--skip-self-upgrade", "list"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0 or len(result.stdout.strip()) > 0:
                return True, f"skillhub CLI is functional. Output: {result.stdout[:200]}"
            return False, f"skillhub returned code {result.returncode}. stderr: {result.stderr[:200]}"
        except FileNotFoundError:
            return False, "skillhub binary not found — CLI was not installed."
        except subprocess.TimeoutExpired:
            return False, "skillhub command timed out."

    checks.append(run_check("skillhub CLI is installed and functional", check_skillhub_functional))

    # -------------------------------------------------------------------
    # CHECK 7: Verify the search was done with JSON output format
    #          (inventory must contain structured data, not raw text)
    # -------------------------------------------------------------------
    def check_inventory_is_structured():
        if inventory_data is None:
            return False, "Could not load inventory data."
        
        # The output should be a proper JSON structure, not a flat string
        if isinstance(inventory_data, str):
            return False, "Inventory is a raw string, not structured JSON data."
        
        # Check it has some recognizable fields from skillhub's list output
        inventory_str = json.dumps(inventory_data)
        structured_indicators = ["path", "slug", "version", "name", "skill"]
        found = [ind for ind in structured_indicators if ind in inventory_str.lower()]
        
        if len(found) >= 1:
            return True, f"Inventory contains structured fields: {found}"
        
        return False, f"Inventory lacks expected structured fields. Content: {inventory_str[:300]}"

    checks.append(run_check("Inventory contains structured skill metadata", check_inventory_is_structured))

    # -------------------------------------------------------------------
    # Score calculation
    # -------------------------------------------------------------------
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall_passed = passed_count >= 5  # Need at least 5/7 to pass

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()