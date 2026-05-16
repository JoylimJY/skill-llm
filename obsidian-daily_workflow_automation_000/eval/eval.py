import sys
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def get_vault_dir():
    state_dir = Path("/workspace/.obsidian-cli-state")
    default_file = state_dir / "default_vault"
    if not default_file.exists():
        return None, None
    vault_name = default_file.read_text().strip()
    safe = vault_name.replace(' ', '_').replace('/', '_')
    vault_dir = state_dir / "vaults" / safe
    return vault_name, vault_dir

def get_date_offset(days_ago):
    return (datetime.today() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

checks = []

# --- Check 1: Vault configured correctly ---
def check_vault_configured():
    state_dir = Path("/workspace/.obsidian-cli-state")
    default_file = state_dir / "default_vault"
    if not default_file.exists():
        return False, "Default vault file not found. set-default was never called."
    vault_name = default_file.read_text().strip()
    if "ResearchVault" not in vault_name and "researchvault" not in vault_name.lower():
        return False, f"Vault name '{vault_name}' does not match expected 'ResearchVault'."
    return True, f"Vault configured as: '{vault_name}'"

checks.append(run_check("vault_configured_as_ResearchVault", check_vault_configured))

# --- Check 2: Daily Notes subfolder used for all notes ---
def check_daily_notes_subfolder():
    vault_name, vault_dir = get_vault_dir()
    if vault_dir is None:
        return False, "No vault configured."
    daily_notes_dir = vault_dir / "Daily Notes"
    if not daily_notes_dir.exists():
        # Check if files are directly in vault root — wrong
        md_files = list(vault_dir.glob("*.md"))
        if md_files:
            return False, f"Notes found directly in vault root, not in 'Daily Notes' subfolder: {[f.name for f in md_files]}"
        return False, "Neither 'Daily Notes' subfolder nor any .md files found."
    md_files = list(daily_notes_dir.glob("*.md"))
    if not md_files:
        return False, "'Daily Notes' subfolder exists but contains no .md files."
    return True, f"'Daily Notes' subfolder has {len(md_files)} note(s): {[f.name for f in md_files]}"

checks.append(run_check("daily_notes_subfolder_used", check_daily_notes_subfolder))

# --- Check 3: Notes exist for all 3 dates (3-days-ago, yesterday, today) ---
def check_all_dates_have_notes():
    vault_name, vault_dir = get_vault_dir()
    if vault_dir is None:
        return False, "No vault configured."
    daily_notes_dir = vault_dir / "Daily Notes"
    
    dates = {
        "3_days_ago": get_date_offset(3),
        "yesterday": get_date_offset(1),
        "today": get_date_offset(0),
    }
    missing = []
    for label, d in dates.items():
        note = daily_notes_dir / f"{d}.md"
        if not note.exists():
            missing.append(f"{label} ({d}.md)")
    if missing:
        return False, f"Missing notes for: {missing}"
    return True, f"All 3 date notes present: {list(dates.values())}"

checks.append(run_check("notes_exist_for_all_three_dates", check_all_dates_have_notes))

# --- Check 4: 3-days-ago note has correct content (task + journal) ---
def check_three_days_ago_content():
    vault_name, vault_dir = get_vault_dir()
    if vault_dir is None:
        return False, "No vault configured."
    date_str = get_date_offset(3)
    note = vault_dir / "Daily Notes" / f"{date_str}.md"
    if not note.exists():
        return False, f"Note {date_str}.md not found."
    content = note.read_text()
    issues = []
    if "PCR reagents" not in content:
        issues.append("Missing task: 'Order new PCR reagents from supplier catalog'")
    if "banding pattern" not in content:
        issues.append("Missing journal: 'Observed unexpected banding pattern in gel run #47'")
    # Check entries start with "- " (obsidian format)
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    non_bullet = [l for l in lines if not l.startswith('- ') and not l.startswith('- [ ]')]
    if non_bullet:
        issues.append(f"Some entries don't follow '- ' bullet format: {non_bullet[:3]}")
    if issues:
        return False, f"Issues in {date_str}.md: {issues}"
    return True, f"{date_str}.md has correct task and journal entries with bullet format."

checks.append(run_check("three_days_ago_has_task_and_journal", check_three_days_ago_content))

# --- Check 5: Yesterday note has task + link + log ---
def check_yesterday_content():
    vault_name, vault_dir = get_vault_dir()
    if vault_dir is None:
        return False, "No vault configured."
    date_str = get_date_offset(1)
    note = vault_dir / "Daily Notes" / f"{date_str}.md"
    if not note.exists():
        return False, f"Note {date_str}.md not found."
    content = note.read_text()
    issues = []
    if "Dr. Chen" not in content:
        issues.append("Missing task: 'Schedule meeting with Dr. Chen about sequencing data'")
    if "ncbi.nlm.nih.gov" not in content:
        issues.append("Missing link: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9876543")
    if "Centrifuge" not in content:
        issues.append("Missing log: 'Centrifuge calibration completed'")
    # Check task uses checkbox format
    if "Dr. Chen" in content:
        task_line = [l for l in content.split('\n') if 'Dr. Chen' in l]
        if task_line and '[ ]' not in task_line[0]:
            issues.append(f"Task entry should use '- [ ]' checkbox format, got: {task_line[0]!r}")
    # Check link uses bare URL bullet
    if "ncbi.nlm.nih.gov" in content:
        link_line = [l for l in content.split('\n') if 'ncbi.nlm.nih.gov' in l]
        if link_line and not link_line[0].strip().startswith('- '):
            issues.append(f"Link entry should start with '- ', got: {link_line[0]!r}")
    if issues:
        return False, f"Issues in {date_str}.md: {issues}"
    return True, f"{date_str}.md has task (checkbox), link, and log entries."

checks.append(run_check("yesterday_has_task_link_log", check_yesterday_content))

# --- Check 6: Today note has task + journal + link ---
def check_today_content():
    vault_name, vault_dir = get_vault_dir()
    if vault_dir is None:
        return False, "No vault configured."
    date_str = get_date_offset(0)
    note = vault_dir / "Daily Notes" / f"{date_str}.md"
    if not note.exists():
        return False, f"Note {date_str}.md not found."
    content = note.read_text()
    issues = []
    if "RNA-seq" not in content:
        issues.append("Missing task: 'Analyze RNA-seq batch 12 results'")
    if "culture plates" not in content:
        issues.append("Missing journal: 'New culture plates arrived, stored at 4C'")
    if "github.com/bioinformatics/rna-tools" not in content:
        issues.append("Missing link: https://github.com/bioinformatics/rna-tools")
    # RNA-seq task should be checkbox
    if "RNA-seq" in content:
        task_line = [l for l in content.split('\n') if 'RNA-seq' in l]
        if task_line and '[ ]' not in task_line[0]:
            issues.append(f"RNA-seq task should use '- [ ]' checkbox, got: {task_line[0]!r}")
    if issues:
        return False, f"Issues in {date_str}.md: {issues}"
    return True, f"{date_str}.md has RNA-seq task (checkbox), journal, and github link."

checks.append(run_check("today_has_task_journal_link", check_today_content))

# --- Check 7: search-content finds "sequencing" in yesterday's note ---
def check_search_content():
    try:
        result = subprocess.run(
            ["obsidian-cli", "search-content", "sequencing"],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout + result.stderr
        if "No results found" in output and "sequencing" not in output.lower():
            return False, f"search-content 'sequencing' returned no results. Output: {output[:300]}"
        # Check that yesterday's date appears in results
        date_str = get_date_offset(1)
        if date_str not in output:
            # Maybe content has "sequencing" somewhere but yesterday note specifically
            vault_name, vault_dir = get_vault_dir()
            if vault_dir:
                yest_note = vault_dir / "Daily Notes" / f"{date_str}.md"
                if yest_note.exists():
                    content = yest_note.read_text()
                    if "sequencing" not in content.lower():
                        return False, f"'sequencing' not found in yesterday's note ({date_str}.md). Content: {content[:200]}"
                    # search found it but maybe showed different format
                    return True, f"search-content ran successfully. Yesterday's note contains 'sequencing'."
            return False, f"Yesterday's date {date_str} not in search output: {output[:300]}"
        return True, f"search-content found 'sequencing' including yesterday's note ({date_str})."
    except subprocess.TimeoutExpired:
        return False, "search-content timed out."
    except FileNotFoundError:
        return False, "obsidian-cli not found in PATH."

checks.append(run_check("search_content_finds_sequencing_in_yesterday", check_search_content))

# --- Check 8: Newline separation between entries (proprietary printf pattern) ---
def check_entry_newline_separation():
    """Each appended entry should be on its own line (not concatenated without newlines)."""
    vault_name, vault_dir = get_vault_dir()
    if vault_dir is None:
        return False, "No vault configured."
    
    issues = []
    for days_ago in [3, 1, 0]:
        date_str = get_date_offset(days_ago)
        note = vault_dir / "Daily Notes" / f"{date_str}.md"
        if not note.exists():
            continue
        content = note.read_text()
        # Check no two bullet entries are on the same line (concatenation artifact)
        for line in content.split('\n'):
            stripped = line.strip()
            # If a line contains two "- " patterns not at start, entries were concatenated
            if stripped.count('- [') + stripped.count('- h') + stripped.count('- O') > 1:
                issues.append(f"{date_str}.md: Entries appear concatenated on same line: {stripped[:80]!r}")
    
    if issues:
        return False, f"Newline separation issues: {issues}"
    return True, "All entries are properly separated on individual lines."

checks.append(run_check("entries_properly_newline_separated", check_entry_newline_separation))

# --- Aggregate ---
passed_count = sum(1 for c in checks if c["passed"])
total = len(checks)
score = round(passed_count / total, 4)
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))