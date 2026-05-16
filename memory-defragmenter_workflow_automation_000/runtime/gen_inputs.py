#!/usr/bin/env python3
"""
Generate a realistic, messy memory workspace for a biotech AI assistant.
Simulates 6 months of accumulated, bloated, duplicated, and stale memory files.
"""

import os
import random
import json
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")

def make_dirs():
    dirs = [
        "memory",
        "archive",
        "scripts",
        "references",
        "logs",
        "backups",
        "docs",
        "docs/protocols",
        "docs/trials",
        "configs",
    ]
    for d in dirs:
        Path(os.path.join(WORKSPACE, d)).mkdir(parents=True, exist_ok=True)

def days_ago(n):
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")

def make_hot_memory():
    """Create memory.md (HOT tier) - bloated beyond 100 lines with duplicates."""
    lines = []
    # Fresh entries (< 30 days)
    lines.append("# Memory - HOT Tier\n")
    lines.append(f"<!-- last_updated: {days_ago(2)} -->\n\n")
    lines.append("## Researcher Preferences\n")
    lines.append(f"- [tier:HOT] [added:{days_ago(5)}] Dr. Chen prefers statistical summaries in APA format\n")
    lines.append(f"- [tier:HOT] [added:{days_ago(3)}] Dr. Patel uses Python for data analysis, not R\n")
    lines.append(f"- [tier:HOT] [added:{days_ago(7)}] Lab meeting every Tuesday at 2pm\n")
    lines.append(f"- [tier:HOT] [added:{days_ago(1)}] Protocol ZX-44 requires cold-chain shipping\n")
    lines.append(f"- [tier:HOT] [added:{days_ago(4)}] Primary contact for Trial BT-209 is Dr. Rivera\n")
    # Duplicates of fresh entries
    lines.append("\n## Researcher Preferences (duplicate block)\n")
    lines.append(f"- [tier:HOT] [added:{days_ago(5)}] Dr. Chen prefers statistical summaries in APA format\n")
    lines.append(f"- [tier:HOT] [added:{days_ago(3)}] Dr. Patel uses Python for data analysis, not R\n")
    lines.append(f"- [tier:HOT] [added:{days_ago(7)}] Lab meeting every Tuesday at 2pm\n")
    # Stale entries (> 30 days)
    lines.append("\n## Old Protocol Notes\n")
    for i in range(40):
        lines.append(f"- [tier:HOT] [added:{days_ago(35 + i)}] Legacy protocol note {i+1}: buffer solution concentration {i*2+1} mM\n")
    # More fresh filler to push over 100 lines
    lines.append("\n## Current Trial Status\n")
    for i in range(60):
        lines.append(f"- [tier:HOT] [added:{days_ago(i % 10 + 1)}] Trial BT-{200+i} status: active, phase {(i%3)+1}\n")

    path = os.path.join(WORKSPACE, "memory.md")
    with open(path, "w") as f:
        f.writelines(lines)

def make_warm_memory():
    """Create memory/domains.md and memory/protocols.md (WARM tier) - bloated and stale."""
    # domains.md - over 200 lines, lots of stale content
    lines = ["# Domain Knowledge\n", f"<!-- last_updated: {days_ago(10)} -->\n\n"]
    lines.append("## Genomics\n")
    for i in range(60):
        age = 5 + i * 2
        lines.append(f"- [tier:WARM] [added:{days_ago(age)}] Genomics fact {i+1}: SNP rs{100000+i} associated with trait X\n")
    lines.append("\n## Proteomics\n")
    for i in range(60):
        age = 3 + i
        lines.append(f"- [tier:WARM] [added:{days_ago(age)}] Protein interaction {i+1}: complex AB-{i*3} involved in pathway Y\n")
    # Stale entries
    lines.append("\n## Outdated Assay Data\n")
    for i in range(100):
        lines.append(f"- [tier:WARM] [added:{days_ago(100 + i)}] Assay obsolete-{i+1}: result {random.randint(10,999)} ng/mL (superseded)\n")
    # Duplicates
    lines.append("\n## Genomics (repeated)\n")
    for i in range(10):
        age = 5 + i * 2
        lines.append(f"- [tier:WARM] [added:{days_ago(age)}] Genomics fact {i+1}: SNP rs{100000+i} associated with trait X\n")

    path = os.path.join(WORKSPACE, "memory", "domains.md")
    with open(path, "w") as f:
        f.writelines(lines)

    # protocols.md - moderate size, mixed stale/fresh
    lines2 = ["# Protocol Memory\n", f"<!-- last_updated: {days_ago(15)} -->\n\n"]
    for i in range(80):
        age = 2 + i * 3
        lines2.append(f"- [tier:WARM] [added:{days_ago(age)}] Protocol P-{1000+i}: {'active' if age < 30 else 'superseded'}, steps: {i+3}\n")
    # Duplicate block
    for i in range(20):
        age = 2 + i * 3
        lines2.append(f"- [tier:WARM] [added:{days_ago(age)}] Protocol P-{1000+i}: {'active' if age < 30 else 'superseded'}, steps: {i+3}\n")

    path2 = os.path.join(WORKSPACE, "memory", "protocols.md")
    with open(path2, "w") as f:
        f.writelines(lines2)

    # memory/researcher_notes.md - fresh and clean but slightly over limit
    lines3 = ["# Researcher Notes\n", f"<!-- last_updated: {days_ago(1)} -->\n\n"]
    for i in range(210):
        lines3.append(f"- [tier:WARM] [added:{days_ago(i % 20 + 1)}] Researcher note {i+1}: observation on experiment E-{500+i}\n")

    path3 = os.path.join(WORKSPACE, "memory", "researcher_notes.md")
    with open(path3, "w") as f:
        f.writelines(lines3)

def make_scripts():
    """Create the actual Python scripts that the agent will invoke."""

    # analyze_memory.py
    analyze_script = r'''#!/usr/bin/env python3
"""Analyze memory state and report on duplicates, staleness, tier distribution."""
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")
STALE_DAYS = 30

def parse_entries(filepath):
    entries = []
    try:
        with open(filepath) as f:
            for lineno, line in enumerate(f, 1):
                m = re.search(r'\[tier:(\w+)\].*\[added:(\d{4}-\d{2}-\d{2})\](.*)', line)
                if m:
                    entries.append({
                        'tier': m.group(1),
                        'added': m.group(2),
                        'text': m.group(3).strip(),
                        'line': line.strip(),
                        'lineno': lineno,
                        'file': filepath
                    })
    except Exception as e:
        print(f"  Warning: could not parse {filepath}: {e}", file=sys.stderr)
    return entries

def analyze():
    files = {
        'HOT': [
            os.path.join(WORKSPACE, 'memory.md'),
        ],
        'WARM': [
            os.path.join(WORKSPACE, 'memory', 'domains.md'),
            os.path.join(WORKSPACE, 'memory', 'protocols.md'),
            os.path.join(WORKSPACE, 'memory', 'researcher_notes.md'),
        ]
    }

    print("=" * 60)
    print("MEMORY ANALYSIS REPORT")
    print("=" * 60)

    today = datetime.now().date()
    total_duplicates = 0
    total_stale = 0
    total_lines = {}
    tier_violations = []
    limits = {'HOT': 100, 'WARM': 200}

    for tier, paths in files.items():
        print(f"\n[{tier} TIER]")
        for fpath in paths:
            if not os.path.exists(fpath):
                print(f"  {fpath}: NOT FOUND")
                continue
            with open(fpath) as f:
                all_lines = f.readlines()
            line_count = len(all_lines)
            total_lines[fpath] = line_count
            entries = parse_entries(fpath)
            texts = [e['text'] for e in entries]
            dups = len(texts) - len(set(texts))
            stale = sum(1 for e in entries if (today - datetime.strptime(e['added'], '%Y-%m-%d').date()).days >= STALE_DAYS)
            total_duplicates += dups
            total_stale += stale
            limit = limits[tier]
            violation = "OVER LIMIT" if line_count > limit else "ok"
            if line_count > limit:
                tier_violations.append(fpath)
            print(f"  {os.path.basename(fpath)}: {line_count} lines [{violation}, limit={limit}]")
            print(f"    Entries: {len(entries)}, Duplicates: {dups}, Stale (30+d): {stale}")

    print(f"\nSUMMARY:")
    print(f"  Total duplicate entries: {total_duplicates}")
    print(f"  Total stale entries: {total_stale}")
    print(f"  Files over tier limit: {len(tier_violations)}")
    for v in tier_violations:
        print(f"    - {v}")
    print("=" * 60)

if __name__ == '__main__':
    analyze()
'''

    # defragment.py
    defrag_script = r'''#!/usr/bin/env python3
"""Plan and execute memory defragmentation."""
import os
import re
import sys
import shutil
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import OrderedDict

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")
STALE_DAYS = 30
PLAN_FILE = os.path.join(WORKSPACE, "defragment-plan.md")
ARCHIVE_DIR = os.path.join(WORKSPACE, "archive")
BACKUP_DIR = os.path.join(WORKSPACE, "backups")

HOT_FILES = [os.path.join(WORKSPACE, 'memory.md')]
WARM_FILES = [
    os.path.join(WORKSPACE, 'memory', 'domains.md'),
    os.path.join(WORKSPACE, 'memory', 'protocols.md'),
    os.path.join(WORKSPACE, 'memory', 'researcher_notes.md'),
]
TIER_LIMITS = {'HOT': 100, 'WARM': 200}

def parse_entries(filepath):
    entries = []
    non_entries = []
    try:
        with open(filepath) as f:
            for lineno, line in enumerate(f, 1):
                m = re.search(r'\[tier:(\w+)\].*\[added:(\d{4}-\d{2}-\d{2})\](.*)', line)
                if m:
                    entries.append({
                        'tier': m.group(1),
                        'added': m.group(2),
                        'text': m.group(3).strip(),
                        'full_line': line.rstrip(),
                        'lineno': lineno,
                    })
                else:
                    non_entries.append((lineno, line))
    except Exception as e:
        print(f"ERROR reading {filepath}: {e}", file=sys.stderr)
    return entries, non_entries

def is_stale(date_str):
    today = datetime.now().date()
    added = datetime.strptime(date_str, '%Y-%m-%d').date()
    return (today - added).days >= STALE_DAYS

def plan():
    today = datetime.now().strftime("%Y-%m-%d")
    plan_lines = [f"# Defragmentation Plan\nGenerated: {today}\n\n"]
    total_merge = 0
    total_archive = 0
    all_files = [('HOT', f) for f in HOT_FILES] + [('WARM', f) for f in WARM_FILES]

    for tier, fpath in all_files:
        if not os.path.exists(fpath):
            continue
        entries, _ = parse_entries(fpath)
        seen_texts = OrderedDict()
        duplicates = []
        stale = []
        for e in entries:
            if e['text'] in seen_texts:
                duplicates.append(e)
                total_merge += 1
            else:
                seen_texts[e['text']] = e
            if is_stale(e['added']):
                stale.append(e)
                total_archive += 1

        fname = os.path.basename(fpath)
        plan_lines.append(f"## File: {fname} [{tier}]\n")
        plan_lines.append(f"- Duplicate entries to merge: {len(duplicates)}\n")
        plan_lines.append(f"- Stale entries to archive (30+ days): {len(stale)}\n")
        plan_lines.append(f"- Entries to delete: 0 (never delete, only archive)\n\n")

        if duplicates:
            plan_lines.append("### Duplicates (will be merged/removed):\n")
            for d in duplicates[:5]:
                plan_lines.append(f"  - line {d['lineno']}: {d['text'][:80]}\n")
            if len(duplicates) > 5:
                plan_lines.append(f"  ... and {len(duplicates)-5} more\n")
            plan_lines.append("\n")

        if stale:
            plan_lines.append("### Stale entries (will be archived):\n")
            for s in stale[:5]:
                plan_lines.append(f"  - line {s['lineno']} [added:{s['added']}]: {s['text'][:60]}\n")
            if len(stale) > 5:
                plan_lines.append(f"  ... and {len(stale)-5} more\n")
            plan_lines.append("\n")

    plan_lines.append(f"## Summary\n")
    plan_lines.append(f"- Total entries to merge: {total_merge}\n")
    plan_lines.append(f"- Total entries to archive: {total_archive}\n")
    plan_lines.append(f"- Entries to delete: 0\n")
    plan_lines.append(f"\n## Safety\n- Backup will be created before execution\n- Originals preserved in backups/\n")

    with open(PLAN_FILE, 'w') as f:
        f.writelines(plan_lines)

    print(f"Plan written to: {PLAN_FILE}")
    print(f"Total merges planned: {total_merge}")
    print(f"Total archives planned: {total_archive}")
    return True

def backup_file(fpath):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = os.path.basename(fpath)
    dest = os.path.join(BACKUP_DIR, f"{fname}.{ts}.bak")
    shutil.copy2(fpath, dest)
    return dest

def execute():
    if not os.path.exists(PLAN_FILE):
        print("ERROR: No defragment plan found. Run with --plan first.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)

    all_files = [('HOT', f) for f in HOT_FILES] + [('WARM', f) for f in WARM_FILES]
    today = datetime.now().strftime("%Y-%m-%d")

    for tier, fpath in all_files:
        if not os.path.exists(fpath):
            continue

        # Backup first (Safety Rule #1)
        bak = backup_file(fpath)
        print(f"Backed up {os.path.basename(fpath)} -> {bak}")

        entries, non_entries = parse_entries(fpath)

        # Deduplicate
        seen = OrderedDict()
        archived_entries = []
        kept_entries = []
        for e in entries:
            if e['text'] not in seen:
                seen[e['text']] = e
                if is_stale(e['added']):
                    archived_entries.append(e)
                else:
                    kept_entries.append(e)
            # else: duplicate - silently drop (merged)

        # Write archive file
        if archived_entries:
            arch_fname = f"{os.path.basename(fpath)}.archived.{today}.md"
            arch_path = os.path.join(ARCHIVE_DIR, arch_fname)
            with open(arch_path, 'a') as af:
                af.write(f"# Archived from {os.path.basename(fpath)} on {today}\n")
                for e in archived_entries:
                    af.write(f"{e['full_line']}\n")
            print(f"  Archived {len(archived_entries)} stale entries to {arch_fname}")

        # Rewrite file with only non-stale, non-duplicate entries
        header_lines = [line for (_, line) in non_entries if lineno_is_header(line)]
        with open(fpath, 'w') as f:
            # Write header comments and section headers from originals
            wrote_header = False
            for (lineno, line) in non_entries:
                stripped = line.strip()
                if stripped.startswith('#') or stripped.startswith('<!--'):
                    f.write(line)
                    wrote_header = True
            if not wrote_header:
                f.write(f"# Memory [{tier}]\n")
            f.write(f"<!-- last_updated: {today} -->\n\n")
            for e in kept_entries:
                f.write(f"{e['full_line']}\n")

        new_count = sum(1 for _ in open(fpath))
        limit = TIER_LIMITS[tier]
        status = "WITHIN LIMIT" if new_count <= limit else "STILL OVER (manual review needed)"
        print(f"  {os.path.basename(fpath)}: {len(kept_entries)} entries, {new_count} lines [{status}]")

    print("\nDefragmentation complete.")
    print("Run verify_memory.py to confirm integrity.")

def lineno_is_header(line):
    return line.strip().startswith('#') or line.strip().startswith('<!--')

if __name__ == '__main__':
    if '--plan' in sys.argv:
        plan()
    elif '--execute' in sys.argv:
        execute()
    else:
        print("Usage: defragment.py --plan | --execute", file=sys.stderr)
        sys.exit(1)
'''

    # verify_memory.py
    verify_script = r'''#!/usr/bin/env python3
"""Verify memory integrity after defragmentation."""
import os
import re
import sys
from datetime import datetime
from pathlib import Path

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")
TIER_LIMITS = {'HOT': 100, 'WARM': 200}

ALL_FILES = {
    'HOT': [os.path.join(WORKSPACE, 'memory.md')],
    'WARM': [
        os.path.join(WORKSPACE, 'memory', 'domains.md'),
        os.path.join(WORKSPACE, 'memory', 'protocols.md'),
        os.path.join(WORKSPACE, 'memory', 'researcher_notes.md'),
    ]
}

def verify():
    print("=" * 60)
    print("MEMORY VERIFICATION REPORT")
    print("=" * 60)
    all_passed = True
    results = {}

    for tier, paths in ALL_FILES.items():
        print(f"\n[{tier} TIER] limit={TIER_LIMITS[tier]} lines")
        for fpath in paths:
            fname = os.path.basename(fpath)
            result = {'file': fpath, 'tier': tier, 'checks': []}

            # Check 1: File readable
            try:
                with open(fpath) as f:
                    lines = f.readlines()
                result['checks'].append(('readable', True, f'{len(lines)} lines'))
            except Exception as e:
                result['checks'].append(('readable', False, str(e)))
                all_passed = False
                results[fname] = result
                continue

            line_count = len(lines)

            # Check 2: Within tier limit
            limit = TIER_LIMITS[tier]
            within = line_count <= limit
            result['checks'].append(('within_limit', within, f'{line_count} <= {limit}'))
            if not within:
                all_passed = False
                print(f"  FAIL {fname}: {line_count} lines exceeds {tier} limit of {limit}")
            else:
                print(f"  PASS {fname}: {line_count} lines (within {limit})")

            # Check 3: No duplicates
            entries = []
            for line in lines:
                m = re.search(r'\[added:\d{4}-\d{2}-\d{2}\](.*)', line)
                if m:
                    entries.append(m.group(1).strip())
            dup_count = len(entries) - len(set(entries))
            no_dups = dup_count == 0
            result['checks'].append(('no_duplicates', no_dups, f'{dup_count} duplicates found'))
            if not no_dups:
                print(f"    WARNING: {dup_count} duplicate entries in {fname}")

            # Check 4: Has updated timestamp
            has_ts = any('last_updated' in l for l in lines)
            result['checks'].append(('has_timestamp', has_ts, ''))
            if not has_ts:
                print(f"    WARNING: missing last_updated timestamp in {fname}")

            # Check 5: No stale entries remain in HOT/WARM (only warn)
            today = datetime.now().date()
            stale_count = 0
            for line in lines:
                m = re.search(r'\[added:(\d{4}-\d{2}-\d{2})\]', line)
                if m:
                    added = datetime.strptime(m.group(1), '%Y-%m-%d').date()
                    if (today - added).days >= 30:
                        stale_count += 1
            result['checks'].append(('stale_removed', stale_count == 0, f'{stale_count} stale entries remain'))
            if stale_count > 0:
                print(f"    INFO: {stale_count} stale entries remain in {fname}")

            results[fname] = result

    # Check archive directory exists and has content
    arch_dir = os.path.join(WORKSPACE, 'archive')
    arch_exists = os.path.isdir(arch_dir) and len(os.listdir(arch_dir)) > 0
    print(f"\n[ARCHIVE] Directory: {'exists with content' if arch_exists else 'empty or missing'}")

    # Check backups exist
    bak_dir = os.path.join(WORKSPACE, 'backups')
    bak_exists = os.path.isdir(bak_dir) and len(os.listdir(bak_dir)) > 0
    print(f"[BACKUPS] Directory: {'exists with content' if bak_exists else 'empty or missing'}")

    print(f"\n{'VERIFICATION PASSED' if all_passed else 'VERIFICATION FAILED - see issues above'}")
    print("=" * 60)

    # Write verification result
    result_file = os.path.join(WORKSPACE, 'verification_result.json')
    import json
    with open(result_file, 'w') as f:
        json.dump({
            'passed': all_passed,
            'timestamp': datetime.now().isoformat(),
            'results': {k: {
                'tier': v['tier'],
                'checks': v['checks']
            } for k, v in results.items()}
        }, f, indent=2)
    print(f"Result written to: {result_file}")
    return all_passed

if __name__ == '__main__':
    ok = verify()
    sys.exit(0 if ok else 1)
'''

    # references/rules.md
    rules_md = """# Defragmentation Rules

## Entry Format
All entries must follow: `- [tier:TIER] [added:YYYY-MM-DD] content`

## Staleness Policy
- Entries older than 30 days are considered stale
- Stale entries MUST be archived, not deleted
- Archive path: archive/

## Tier Size Limits
- HOT (memory.md): <= 100 lines
- WARM (memory/*.md): <= 200 lines each
- COLD (archive/): unlimited

## Safety Rules
1. ALWAYS backup before executing
2. REVIEW plan before applying
3. NEVER delete - only archive
4. KEEP originals for 24h after
5. VERIFY after every defragment

## Merge Rules
- Identical text content = duplicate, keep newest
- Similar entries = candidate for merge (manual review)
- Conflicting entries = keep both, flag for review
"""

    scripts_dir = os.path.join(WORKSPACE, "scripts")
    refs_dir = os.path.join(WORKSPACE, "references")

    with open(os.path.join(scripts_dir, "analyze_memory.py"), "w") as f:
        f.write(analyze_script)
    with open(os.path.join(scripts_dir, "defragment.py"), "w") as f:
        f.write(defrag_script)
    with open(os.path.join(scripts_dir, "verify_memory.py"), "w") as f:
        f.write(verify_script)
    with open(os.path.join(refs_dir, "rules.md"), "w") as f:
        f.write(rules_md)

def make_distractor_files():
    """Create realistic distractor files to increase complexity."""
    ws = WORKSPACE

    # Distractor logs
    log_dir = os.path.join(ws, "logs")
    for i in range(3):
        with open(os.path.join(log_dir, f"session_{2024_01_01 + i}.log"), "w") as f:
            f.write(f"Session log {i}\nEntries processed: {random.randint(100,500)}\n")
    
    # docs
    with open(os.path.join(ws, "docs", "protocols", "protocol_ZX44.md"), "w") as f:
        f.write("# Protocol ZX-44\nCold-chain shipping required.\nVersion 3.2\n")
    with open(os.path.join(ws, "docs", "trials", "BT209_summary.md"), "w") as f:
        f.write("# Trial BT-209\nPhase 2 clinical trial.\nPI: Dr. Rivera\n")
    with open(os.path.join(ws, "docs", "trials", "BT210_summary.md"), "w") as f:
        f.write("# Trial BT-210\nPhase 1 trial.\n")

    # configs
    with open(os.path.join(ws, "configs", "memory_config.json"), "w") as f:
        json.dump({
            "hot_tier_limit": 100,
            "warm_tier_limit": 200,
            "stale_threshold_days": 30,
            "archive_path": "archive/"
        }, f, indent=2)
    with open(os.path.join(ws, "configs", "lab_settings.json"), "w") as f:
        json.dump({"lab": "BioTech Research Unit 7", "ai_assistant": "LabAssist v2"}, f)

    # Some old archive files already existing (COLD tier)
    arch_dir = os.path.join(ws, "archive")
    # This archive is pre-existing from a previous defragment (much older)
    old_date = days_ago(200)
    with open(os.path.join(arch_dir, f"memory.md.archived.{days_ago(95)}.md"), "w") as f:
        f.write(f"# Archived 95 days ago\n")
        for i in range(20):
            f.write(f"- [tier:COLD] [added:{days_ago(95+i)}] Old archived entry {i}\n")

    # backups dir placeholder
    with open(os.path.join(ws, "backups", ".gitkeep"), "w") as f:
        f.write("")

def log_name_fix():
    """Fix the log file naming (remove invalid literal)."""
    log_dir = os.path.join(WORKSPACE, "logs")
    for i in range(3):
        with open(os.path.join(log_dir, f"session_2024010{i+1}.log"), "w") as f:
            f.write(f"Session log {i+1}\nEntries processed: {random.randint(100,500)}\n")


if __name__ == "__main__":
    make_dirs()
    make_hot_memory()
    make_warm_memory()
    make_scripts()
    log_name_fix()

    # Distractor docs and configs
    log_dir = os.path.join(WORKSPACE, "logs")
    docs_dir = os.path.join(WORKSPACE, "docs")
    ws = WORKSPACE

    with open(os.path.join(docs_dir, "protocols", "protocol_ZX44.md"), "w") as f:
        f.write("# Protocol ZX-44\nCold-chain shipping required.\nVersion 3.2\n")
    with open(os.path.join(docs_dir, "trials", "BT209_summary.md"), "w") as f:
        f.write("# Trial BT-209\nPhase 2 clinical trial.\nPI: Dr. Rivera\n")
    with open(os.path.join(docs_dir, "trials", "BT210_summary.md"), "w") as f:
        f.write("# Trial BT-210\nPhase 1 trial.\n")

    configs_dir = os.path.join(WORKSPACE, "configs")
    with open(os.path.join(configs_dir, "memory_config.json"), "w") as f:
        json.dump({
            "hot_tier_limit": 100,
            "warm_tier_limit": 200,
            "stale_threshold_days": 30,
            "archive_path": "archive/"
        }, f, indent=2)
    with open(os.path.join(configs_dir, "lab_settings.json"), "w") as f:
        json.dump({"lab": "BioTech Research Unit 7", "ai_assistant": "LabAssist v2"}, f)

    arch_dir = os.path.join(WORKSPACE, "archive")
    old_archive_date = days_ago(95)
    with open(os.path.join(arch_dir, f"memory.md.archived.{old_archive_date}.md"), "w") as f:
        f.write(f"# Archived {old_archive_date}\n")
        for i in range(20):
            f.write(f"- [tier:COLD] [added:{days_ago(95+i)}] Old archived entry {i}\n")

    print("Workspace generated successfully.")
    print(f"HOT file: memory.md")
    print(f"WARM files: memory/domains.md, memory/protocols.md, memory/researcher_notes.md")
    print(f"Scripts: scripts/analyze_memory.py, scripts/defragment.py, scripts/verify_memory.py")