#!/usr/bin/env python3
"""
Evaluation script for the Memory skill task.

Grading dimensions:
  1. ~/memory/ exists at HOME (not inside workspace)
  2. Workspace MEMORY.md and memory/ folder are untouched (traps)
  3. ~/memory/config.md exists
  4. ~/memory/INDEX.md exists and lists at least 3 categories
  5. ~/memory/people/ exists with an INDEX.md listing all 8 contacts
  6. Each of the 8 contacts has an individual .md file with meaningful content
  7. ~/memory/projects/ exists with an INDEX.md
  8. All 4 projects (NeuroCRISPR, ProteomX, InfectModel, StructBio) have .md files
  9. ~/memory/knowledge/ (or similar) exists with entries covering the snippets
 10. The archive (115 stubs) triggers the split rule:
     - people/ or projects/ INDEX.md must NOT have >100 entries flat
     - ~/memory/projects/archived/ (or similar subcategory) exists with its own INDEX.md
     - Root ~/memory/projects/INDEX.md references the subcategory (not 115 flat entries)
"""

import sys
import os
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def count_table_rows(content):
    """Count non-header, non-separator rows in a markdown table."""
    rows = 0
    in_table = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("|"):
            if re.match(r"^\|[-| :]+\|", stripped):
                in_table = True
                continue
            if in_table or "|" in stripped:
                in_table = True
                rows += 1
    return rows

def find_md_files(directory):
    return list(Path(directory).rglob("*.md")) if Path(directory).exists() else []

def read_file(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return None

workspace = sys.argv[1] if len(sys.argv) > 1 else "/home/consultant/workspace"
home = str(Path(workspace).parent)  # /home/consultant
memory_root = Path(home) / "memory"

checks = []
score_weights = []

# ─── CHECK 1: ~/memory/ exists at HOME level ─────────────────────────────────
c1_passed = memory_root.exists() and memory_root.is_dir()
checks.append(check(
    "memory_root_at_home",
    c1_passed,
    f"~/memory/ {'found' if c1_passed else 'NOT found'} at {memory_root}"
))
score_weights.append((c1_passed, 0.10))

# ─── CHECK 2: Workspace MEMORY.md untouched ──────────────────────────────────
trap_memorymd = Path(workspace) / "MEMORY.md"
try:
    content = trap_memorymd.read_text(encoding="utf-8")
    original_marker = "Agent Memory" in content and "built-in memory file" in content
    c2_passed = original_marker
    detail = "Workspace MEMORY.md is intact (not modified)." if c2_passed else "Workspace MEMORY.md was MODIFIED — violates parallel system rule."
except Exception as e:
    c2_passed = False
    detail = f"Could not read workspace MEMORY.md: {e}"
checks.append(check("workspace_MEMORY_md_untouched", c2_passed, detail))
score_weights.append((c2_passed, 0.05))

# ─── CHECK 3: Workspace memory/ folder untouched ─────────────────────────────
trap_memdir = Path(workspace) / "memory"
try:
    logs = list(trap_memdir.iterdir()) if trap_memdir.exists() else []
    original_files = {"daily_log_2026_01.md", "daily_log_2026_02.md"}
    actual_files = {f.name for f in logs}
    c3_passed = original_files == actual_files
    detail = f"Workspace memory/ contains: {actual_files}. Expected exactly {original_files}."
except Exception as e:
    c3_passed = False
    detail = f"Error checking workspace memory/: {e}"
checks.append(check("workspace_memory_folder_untouched", c3_passed, detail))
score_weights.append((c3_passed, 0.05))

# ─── CHECK 4: ~/memory/config.md exists ──────────────────────────────────────
config_path = memory_root / "config.md"
c4_passed = config_path.exists() and config_path.stat().st_size > 20
checks.append(check(
    "config_md_exists",
    c4_passed,
    f"config.md {'found' if c4_passed else 'NOT found or empty'} at {config_path}"
))
score_weights.append((c4_passed, 0.05))

# ─── CHECK 5: ~/memory/INDEX.md exists and references ≥3 categories ──────────
root_index_path = memory_root / "INDEX.md"
try:
    root_index = root_index_path.read_text(encoding="utf-8", errors="replace")
    # Count category references (lines with folder-like words or table rows)
    category_refs = len(re.findall(r"(?:people|projects|knowledge|contacts|collaborators|archive|decisions|collections)", root_index, re.IGNORECASE))
    c5_passed = root_index_path.exists() and category_refs >= 2
    detail = f"Root INDEX.md found. Category keyword hits: {category_refs}"
except Exception as e:
    c5_passed = False
    detail = f"Root INDEX.md missing or unreadable: {e}"
checks.append(check("root_index_md_exists", c5_passed, detail))
score_weights.append((c5_passed, 0.08))

# ─── CHECK 6: People/contacts category with INDEX.md ─────────────────────────
# Accept flexible names: people, contacts, collaborators
people_dir = None
for candidate in ["people", "contacts", "collaborators"]:
    p = memory_root / candidate
    if p.exists() and p.is_dir():
        people_dir = p
        break

if people_dir is None:
    c6_passed = False
    people_index_content = ""
    detail = "No people/contacts/collaborators directory found in ~/memory/"
else:
    people_index = people_dir / "INDEX.md"
    people_index_content = read_file(people_index) or ""
    c6_passed = people_index.exists() and len(people_index_content) > 50
    detail = f"People dir: {people_dir}, INDEX.md {'found' if c6_passed else 'missing'}"
checks.append(check("people_category_with_index", c6_passed, detail))
score_weights.append((c6_passed, 0.08))

# ─── CHECK 7: All 8 contacts have individual .md files ───────────────────────
EXPECTED_CONTACTS = [
    ("kapoor", "aisha"),
    ("ferretti", "luca"),
    ("tanaka", "yuki"),
    ("mehta", "priya"),
    ("hassan", "omar"),
    ("al-rashid", "fatima"),  # also accept alrashid
    ("wei", "chen"),
    ("moreau", "sofia"),
]

contact_files_found = 0
contact_details = []
if people_dir:
    all_people_mds = find_md_files(people_dir)
    all_people_content = " ".join((read_file(f) or "").lower() for f in all_people_mds)
    all_people_content += " ".join(f.stem.lower() for f in all_people_mds)
    for last, first in EXPECTED_CONTACTS:
        alt = last.replace("-", "")
        found = last in all_people_content or alt in all_people_content or first in all_people_content
        if found:
            contact_files_found += 1
        contact_details.append(f"{'✓' if found else '✗'} {first} {last}")

c7_passed = contact_files_found >= 7  # allow 1 miss
checks.append(check(
    "all_8_contacts_stored",
    c7_passed,
    f"Found {contact_files_found}/8 contacts. Details: {'; '.join(contact_details)}"
))
score_weights.append((c7_passed, 0.10))

# ─── CHECK 8: Projects category with INDEX.md ────────────────────────────────
projects_dir = memory_root / "projects"
projects_index_path = projects_dir / "INDEX.md" if projects_dir.exists() else None

if not projects_dir or not projects_dir.exists():
    c8_passed = False
    proj_index_content = ""
    detail = "No projects/ directory found in ~/memory/"
else:
    proj_index_content = read_file(projects_index_path) or "" if projects_index_path else ""
    c8_passed = (projects_index_path and projects_index_path.exists() and len(proj_index_content) > 50)
    detail = f"projects/INDEX.md {'found' if c8_passed else 'missing or empty'}"
checks.append(check("projects_category_with_index", c8_passed, detail))
score_weights.append((c8_passed, 0.08))

# ─── CHECK 9: All 4 active/recent projects stored ────────────────────────────
EXPECTED_PROJECTS = ["neurocrispr", "proteomx", "infectmodel", "structbio"]
proj_files_found = 0
proj_details = []
if projects_dir and projects_dir.exists():
    all_proj_mds = find_md_files(projects_dir)
    all_proj_content = " ".join((read_file(f) or "").lower() for f in all_proj_mds)
    all_proj_content += " ".join(f.stem.lower() for f in all_proj_mds)
    for pname in EXPECTED_PROJECTS:
        # Also check for space-separated variants
        variant = pname.replace("-", " ").replace("_", " ")
        found = pname in all_proj_content or variant in all_proj_content
        if found:
            proj_files_found += 1
        proj_details.append(f"{'✓' if found else '✗'} {pname}")

c9_passed = proj_files_found >= 3
checks.append(check(
    "all_4_projects_stored",
    c9_passed,
    f"Found {proj_files_found}/4 projects. Details: {'; '.join(proj_details)}"
))
score_weights.append((c9_passed, 0.10))

# ─── CHECK 10: Knowledge category exists with entries ────────────────────────
knowledge_dir = None
for candidate in ["knowledge", "notes", "domain_knowledge", "biomedical"]:
    p = memory_root / candidate
    if p.exists() and p.is_dir():
        knowledge_dir = p
        break

if knowledge_dir is None:
    c10_passed = False
    detail = "No knowledge/notes/domain_knowledge directory found in ~/memory/"
else:
    know_mds = find_md_files(knowledge_dir)
    # At least 3 knowledge entries (or one file with multiple sections)
    total_content = " ".join((read_file(f) or "") for f in know_mds)
    # Look for at least 3 of the 12 topic keywords
    topics = ["crispr", "mass spec", "western blot", "clinical trial", "cryo-em",
              "proteomics", "base edit", "10x genomics", "nih r01", "agent-based",
              "biobank", "statistical power", "perseus", "iacuc"]
    hits = sum(1 for t in topics if t.lower() in total_content.lower())
    c10_passed = hits >= 3
    detail = f"Knowledge dir: {knowledge_dir}. Topic keyword hits: {hits}/14. Files: {len(know_mds)}"
checks.append(check("knowledge_category_with_content", c10_passed, detail))
score_weights.append((c10_passed, 0.08))

# ─── CHECK 11: Archive split rule — no flat INDEX with >100 entries ───────────
# The 115 archive stubs must be organized under a subcategory, NOT a flat 100+ entry index
oversized_indices = []
if memory_root.exists():
    for idx_path in memory_root.rglob("INDEX.md"):
        try:
            content = idx_path.read_text(encoding="utf-8", errors="replace")
            rows = count_table_rows(content)
            # Also count bullet list items as entries
            bullet_rows = len(re.findall(r"^[-*]\s+\S", content, re.MULTILINE))
            total_entries = max(rows, bullet_rows)
            if total_entries > 100:
                oversized_indices.append(f"{idx_path} ({total_entries} entries)")
        except Exception:
            pass

c11_passed = len(oversized_indices) == 0
checks.append(check(
    "no_index_exceeds_100_entries",
    c11_passed,
    f"Oversized INDEX.md files (>100 entries): {oversized_indices if oversized_indices else 'None — all compliant'}"
))
score_weights.append((c11_passed, 0.10))

# ─── CHECK 12: Archived projects in subcategory with own INDEX.md ─────────────
# Since 115 stubs exist, agent should have created a subcategory like projects/archived/
archived_subdir = None
for candidate_root in [projects_dir] if projects_dir and projects_dir.exists() else []:
    for subname in ["archived", "archive", "legacy", "old", "past"]:
        sub = candidate_root / subname
        if sub.exists() and sub.is_dir():
            archived_subdir = sub
            break
    if archived_subdir:
        break

if archived_subdir is None:
    # Maybe they used a different top-level structure
    for subname in ["archived_projects", "archive", "projects_archive"]:
        sub = memory_root / subname
        if sub.exists() and sub.is_dir():
            archived_subdir = sub
            break

if archived_subdir:
    archive_index = archived_subdir / "INDEX.md"
    sub_index_content = read_file(archive_index) or ""
    c12_passed = archive_index.exists() and len(sub_index_content) > 50
    detail = f"Archived subcategory found at {archived_subdir}. INDEX.md {'present' if c12_passed else 'missing'}."
else:
    # Check if root projects/INDEX.md references a subcategory
    if proj_index_content:
        refs = re.findall(r"(archived?|legacy|old|past)/", proj_index_content, re.IGNORECASE)
        c12_passed = len(refs) > 0
        detail = f"No archived subdir found, but projects/INDEX.md references: {refs}"
    else:
        c12_passed = False
        detail = "No archived subcategory or reference found for the 115 archive stubs."

checks.append(check("archived_projects_in_subcategory", c12_passed, detail))
score_weights.append((c12_passed, 0.09))

# ─── CHECK 13: Root projects/INDEX.md references subcategory (not 115 flat entries) ──
if projects_dir and projects_dir.exists() and projects_index_path and projects_index_path.exists():
    proj_idx = read_file(projects_index_path) or ""
    # Should reference archived/ or similar
    has_subcat_ref = bool(re.search(r"(archived?|legacy|old|active)/", proj_idx, re.IGNORECASE))
    # Must NOT list 115 stubs by name itself
    stub_count_in_index = len(re.findall(r"ARCH-\d{3}|project_stub_\d{3}|stub_\d{3}", proj_idx, re.IGNORECASE))
    c13_passed = has_subcat_ref or stub_count_in_index < 50
    detail = f"projects/INDEX.md has subcategory reference: {has_subcat_ref}. Direct stub entries: {stub_count_in_index}."
else:
    c13_passed = False
    detail = "projects/INDEX.md missing; cannot verify subcategory references."
checks.append(check(
    "projects_index_references_subcategory",
    c13_passed,
    detail
))
score_weights.append((c13_passed, 0.05))

# ─── SCORING ─────────────────────────────────────────────────────────────────
total_weight = sum(w for _, w in score_weights)
earned = sum(w for (passed, w) in score_weights if passed)
score = round(earned / total_weight, 4) if total_weight > 0 else 0.0

# Hard gate: must not have corrupted built-in memory AND must have memory at home
hard_fail = not c1_passed or not c2_passed or not c3_passed
if hard_fail:
    score = min(score, 0.25)

overall_passed = score >= 0.70 and not hard_fail

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))