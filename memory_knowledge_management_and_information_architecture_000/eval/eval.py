import sys
import os
import json
import re
from pathlib import Path

def load_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return None

def check_markdown_table(content):
    """Check if content contains a markdown table (header row with |)."""
    lines = content.split("\n")
    table_lines = [l for l in lines if "|" in l and l.strip().startswith("|")]
    return len(table_lines) >= 3  # header + separator + at least one row

def run_eval(workspace):
    checks = []
    memory_root = Path.home() / "memory"

    # ── CHECK 1: ~/memory/ directory exists ──────────────────────────────────
    c1_pass = memory_root.is_dir()
    checks.append({
        "name": "memory_root_exists",
        "passed": c1_pass,
        "detail": f"~/memory/ directory {'exists' if c1_pass else 'MISSING'} at {memory_root}"
    })

    # ── CHECK 2: ~/memory/config.md exists ───────────────────────────────────
    config_path = memory_root / "config.md"
    c2_pass = config_path.is_file()
    checks.append({
        "name": "config_md_exists",
        "passed": c2_pass,
        "detail": f"~/memory/config.md {'exists' if c2_pass else 'MISSING'}"
    })

    # ── CHECK 3: ~/memory/INDEX.md exists and references all 4 categories ────
    root_index_path = memory_root / "INDEX.md"
    root_index_content = load_file(root_index_path)
    if root_index_content is None:
        c3_pass = False
        c3_detail = "~/memory/INDEX.md MISSING"
    else:
        categories_found = []
        for cat in ["people", "grants", "publications", "equipment"]:
            if cat.lower() in root_index_content.lower():
                categories_found.append(cat)
        c3_pass = len(categories_found) == 4
        c3_detail = f"Root INDEX.md references categories: {categories_found} (need all 4: people, grants, publications, equipment)"
    checks.append({
        "name": "root_index_lists_all_categories",
        "passed": c3_pass,
        "detail": c3_detail
    })

    # ── CHECK 4: ~/memory/people/ exists with INDEX.md ───────────────────────
    people_dir = memory_root / "people"
    people_index_path = people_dir / "INDEX.md"
    people_index_content = load_file(people_index_path)
    if people_index_content is None:
        c4_pass = False
        c4_detail = "~/memory/people/INDEX.md MISSING"
    else:
        has_table = check_markdown_table(people_index_content)
        # Check for all 8 people (by last name or partial name)
        people_names = ["Reyes", "Webb", "Nair", "Okafor", "Zhang", "Diallo", "Herrera", "Tanaka"]
        found_names = [n for n in people_names if n.lower() in people_index_content.lower()]
        c4_pass = has_table and len(found_names) >= 7  # allow 1 miss for flexibility
        c4_detail = f"people/INDEX.md: table={'yes' if has_table else 'NO'}, names found: {found_names} ({len(found_names)}/8)"
    checks.append({
        "name": "people_index_with_all_entries",
        "passed": c4_pass,
        "detail": c4_detail
    })

    # ── CHECK 5: Individual people .md files exist (at least 6 of 8) ─────────
    people_files = list(people_dir.glob("*.md")) if people_dir.is_dir() else []
    people_md_files = [f for f in people_files if f.name.lower() != "index.md"]
    c5_pass = len(people_md_files) >= 6
    checks.append({
        "name": "people_individual_files",
        "passed": c5_pass,
        "detail": f"Found {len(people_md_files)} individual people .md files (need at least 6)"
    })

    # ── CHECK 6: ~/memory/grants/ exists with INDEX.md listing grants ─────────
    grants_dir = memory_root / "grants"
    grants_index_path = grants_dir / "INDEX.md"
    grants_index_content = load_file(grants_index_path)
    if grants_index_content is None:
        c6_pass = False
        c6_detail = "~/memory/grants/INDEX.md MISSING"
    else:
        has_table = check_markdown_table(grants_index_content)
        grant_ids = ["NSF", "DOE", "NASA", "NOAA", "UNIVERSITY", "SEED"]
        found_grants = [g for g in grant_ids if g.lower() in grants_index_content.lower()]
        c6_pass = has_table and len(found_grants) >= 4
        c6_detail = f"grants/INDEX.md: table={'yes' if has_table else 'NO'}, grant refs found: {found_grants}"
    checks.append({
        "name": "grants_index_with_entries",
        "passed": c6_pass,
        "detail": c6_detail
    })

    # ── CHECK 7: ~/memory/publications/ exists with INDEX.md ─────────────────
    pubs_dir = memory_root / "publications"
    pubs_index_path = pubs_dir / "INDEX.md"
    pubs_index_content = load_file(pubs_index_path)
    if pubs_index_content is None:
        c7_pass = False
        c7_detail = "~/memory/publications/INDEX.md MISSING"
    else:
        has_table = check_markdown_table(pubs_index_content)
        # Check for publications (by journal or title keywords)
        pub_keywords = ["Turbulence", "Seasonal", "Urban Heat", "Remote Sensing", "Ocean", "Atmospheric Chemistry"]
        found_pubs = [p for p in pub_keywords if p.lower() in pubs_index_content.lower()]
        c7_pass = has_table and len(found_pubs) >= 4
        c7_detail = f"publications/INDEX.md: table={'yes' if has_table else 'NO'}, pub refs: {found_pubs}"
    checks.append({
        "name": "publications_index_with_entries",
        "passed": c7_pass,
        "detail": c7_detail
    })

    # ── CHECK 8: CRITICAL — equipment category is SPLIT into subcategories ───
    # The equipment has 150 items (>100), so equipment/INDEX.md must NOT list all
    # items directly but instead point to subcategories
    equip_dir = memory_root / "equipment"
    equip_index_path = equip_dir / "INDEX.md"
    equip_index_content = load_file(equip_index_path)

    if equip_index_content is None:
        c8_pass = False
        c8_detail = "~/memory/equipment/INDEX.md MISSING — equipment category not created"
    else:
        # Count how many equipment item IDs (LAB-XXX or FIELD-XXX) appear directly in the equipment root index
        direct_item_count = len(re.findall(r'(LAB|FIELD)-\d{3}', equip_index_content, re.IGNORECASE))
        # Find subdirectories inside equipment/
        if equip_dir.is_dir():
            subdirs = [d for d in equip_dir.iterdir() if d.is_dir()]
        else:
            subdirs = []
        has_subdirs = len(subdirs) >= 2
        # The root equipment INDEX should point to subcategories, not list all 150 items
        # We allow up to 20 direct item refs (some agents may include a few examples)
        c8_pass = has_subdirs and direct_item_count <= 20
        c8_detail = (
            f"equipment/INDEX.md: direct item IDs listed={direct_item_count} (should be <=20 for split structure), "
            f"subdirectories found: {[d.name for d in subdirs]} (need at least 2)"
        )
    checks.append({
        "name": "equipment_split_into_subcategories",
        "passed": c8_pass,
        "detail": c8_detail
    })

    # ── CHECK 9: Each equipment subcategory has its own INDEX.md ─────────────
    if equip_dir.is_dir():
        equip_subdirs = [d for d in equip_dir.iterdir() if d.is_dir()]
    else:
        equip_subdirs = []

    sub_indexes_found = []
    sub_indexes_missing = []
    for sub in equip_subdirs:
        sub_idx = sub / "INDEX.md"
        if sub_idx.is_file():
            sub_indexes_found.append(sub.name)
        else:
            sub_indexes_missing.append(sub.name)

    c9_pass = len(sub_indexes_found) >= 2 and len(sub_indexes_missing) == 0
    checks.append({
        "name": "equipment_subcategory_indexes",
        "passed": c9_pass,
        "detail": f"Sub-INDEX.md present in: {sub_indexes_found}, missing in: {sub_indexes_missing}"
    })

    # ── CHECK 10: Equipment items exist as .md files in subcategories ─────────
    equip_item_files = []
    for sub in equip_subdirs:
        item_files = [f for f in sub.glob("*.md") if f.name.lower() != "index.md"]
        equip_item_files.extend(item_files)

    c10_pass = len(equip_item_files) >= 40  # Expect most items to be written as individual files
    checks.append({
        "name": "equipment_individual_item_files",
        "passed": c10_pass,
        "detail": f"Found {len(equip_item_files)} individual equipment .md files in subcategories (need at least 40)"
    })

    # ── CHECK 11: workspace-level MEMORY.md NOT modified ─────────────────────
    workspace = Path(workspace)
    workspace_memory_md = workspace / "MEMORY.md"
    try:
        original_stat = open("/tmp/original_memory_md_stat.txt").read()
        current_content = load_file(workspace_memory_md)
        # Check content hasn't changed (compare modification time via stat)
        import subprocess
        result = subprocess.run(["stat", str(workspace_memory_md)], capture_output=True, text=True)
        current_stat = result.stdout
        # Simple check: if the file still contains the original marker text
        c11_pass = current_content is not None and "Agent Memory" in current_content and "Prof. Chen" in current_content
        c11_detail = f"workspace/MEMORY.md {'intact' if c11_pass else 'MODIFIED or MISSING'}"
    except Exception as e:
        c11_pass = False
        c11_detail = f"Could not verify MEMORY.md integrity: {e}"
    checks.append({
        "name": "workspace_memory_md_not_modified",
        "passed": c11_pass,
        "detail": c11_detail
    })

    # ── CHECK 12: workspace-level memory/ folder NOT modified ────────────────
    workspace_mem_dir = workspace / "memory"
    ws_daily_log = workspace_mem_dir / "2026-01-15.md"
    try:
        daily_content = load_file(ws_daily_log)
        c12_pass = daily_content is not None and "Daily Log 2026-01-15" in daily_content
        c12_detail = f"workspace/memory/2026-01-15.md {'intact' if c12_pass else 'MODIFIED or MISSING'}"
    except Exception as e:
        c12_pass = False
        c12_detail = f"Could not verify workspace memory/ integrity: {e}"
    checks.append({
        "name": "workspace_memory_folder_not_modified",
        "passed": c12_pass,
        "detail": c12_detail
    })

    # ── CHECK 13: ~/memory is SEPARATE from /workspace ───────────────────────
    # Make sure agent didn't put memory inside /workspace
    workspace_memory_subdir = workspace / "memory"
    # The skill memory should be at ~/memory, not /workspace/memory
    # Check that ~/memory exists AND has the expected structure (not just workspace/memory/)
    memory_in_home = (Path.home() / "memory").is_dir()
    equip_in_home = (Path.home() / "memory" / "equipment").is_dir()
    c13_pass = memory_in_home and equip_in_home
    checks.append({
        "name": "memory_located_in_home_not_workspace",
        "passed": c13_pass,
        "detail": (
            f"~/memory exists: {memory_in_home}, "
            f"~/memory/equipment exists: {equip_in_home}. "
            f"(If agent put memory in /workspace/memory it would fail this check and check 12)"
        )
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    # Weighted scoring: checks 8,9,10 (splitting) worth more as the key proprietary trap
    weights = {
        "memory_root_exists": 1.0,
        "config_md_exists": 0.5,
        "root_index_lists_all_categories": 1.0,
        "people_index_with_all_entries": 1.0,
        "people_individual_files": 0.75,
        "grants_index_with_entries": 1.0,
        "publications_index_with_entries": 1.0,
        "equipment_split_into_subcategories": 2.0,  # KEY PROPRIETARY TRAP
        "equipment_subcategory_indexes": 1.5,
        "equipment_individual_item_files": 1.5,
        "workspace_memory_md_not_modified": 1.0,
        "workspace_memory_folder_not_modified": 1.0,
        "memory_located_in_home_not_workspace": 0.75,
    }

    total_weight = sum(weights.values())
    earned_weight = sum(weights[c["name"]] for c in checks if c["passed"])
    score = round(earned_weight / total_weight, 4)

    # Must pass critical checks to overall pass
    critical_checks = [
        "memory_root_exists",
        "equipment_split_into_subcategories",
        "equipment_subcategory_indexes",
        "workspace_memory_md_not_modified",
        "workspace_memory_folder_not_modified",
        "memory_located_in_home_not_workspace",
    ]
    all_critical_pass = all(c["passed"] for c in checks if c["name"] in critical_checks)
    # Also need at least 75% score to pass overall
    passed = all_critical_pass and score >= 0.75

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_arg = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_arg)
    print(json.dumps(result, indent=2))