#!/usr/bin/env python3
"""
Generate the Obsidian vault structure, distractor notes, and the actual scripts.
This script creates a realistic biotech research vault plus the CLI tool scripts.
"""
import os
import random
import json
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

VAULT = Path("/home/ruslan/webdav/data/ruslain")
SCRIPTS_DIR = Path("/home/ruslan/.openclaw/workspace/skills/obsidian/scripts")

# Create directories
for d in [
    VAULT / ".obsidian",
    VAULT / "Projects",
    VAULT / "Research",
    VAULT / "Research" / "Proteins",
    VAULT / "Research" / "Assays",
    VAULT / "Lab" / "Protocols",
    VAULT / "Lab" / "Equipment",
    VAULT / "Meetings",
    VAULT / "Literature",
    VAULT / "Admin",
    SCRIPTS_DIR,
]:
    d.mkdir(parents=True, exist_ok=True)

def make_note(path: Path, title: str, tags: list, content: str, created: str = None, modified: str = None):
    if created is None:
        created = "2024-03-10T09:00:00"
    if modified is None:
        modified = "2024-03-15T14:30:00"
    frontmatter = f"""---
created: {created}
modified: {modified}
tags:
{chr(10).join(f'  - {t}' for t in tags)}
---

# {title}

{content}
"""
    path.write_text(frontmatter, encoding="utf-8")

# ---- DISTRACTOR NOTES ----
make_note(
    VAULT / "Admin" / "Onboarding.md",
    "Onboarding Checklist",
    ["admin", "hr"],
    "Welcome to the lab. Complete the following:\n\n- [ ] Badge access\n- [ ] Safety training\n- [ ] IT setup\n\n[[Lab Safety Protocol]]"
)

make_note(
    VAULT / "Lab" / "Protocols" / "Cell Culture Protocol.md",
    "Cell Culture Protocol",
    ["protocol", "lab", "cell-culture"],
    "## Materials\n\n- DMEM medium\n- FBS 10%\n- Trypsin\n\n## Steps\n\n1. Warm media to 37°C\n2. Aspirate old media\n3. Add trypsin, incubate 5 min\n\nSee also [[EGFR Binding Assay Notes]]"
)

make_note(
    VAULT / "Lab" / "Equipment" / "Mass Spectrometer Maintenance.md",
    "Mass Spectrometer Maintenance Log",
    ["equipment", "maintenance"],
    "Last calibrated: 2024-02-20\n\nNext service: 2024-08-20\n\nNotes: Detector voltage adjusted to 1.8kV"
)

make_note(
    VAULT / "Meetings" / "Q1 Review.md",
    "Q1 2024 Review Meeting",
    ["meeting", "review"],
    "Attendees: Dr. Smith, Dr. Chen, Ruslan\n\n## Action Items\n\n- Complete EGFR inhibitor series by April\n- Submit IND application draft\n- Review [[KRAS G12C Mutation Study]]"
)

make_note(
    VAULT / "Literature" / "Smith2023 EGFR Review.md",
    "Smith 2023 EGFR Review",
    ["literature", "EGFR", "review"],
    "Citation: Smith et al. 2023, J. Med. Chem.\n\nKey finding: Third-generation EGFR inhibitors show improved selectivity over T790M mutant.\n\nRelevant to our [[EGFR Inhibitor Project]]"
)

make_note(
    VAULT / "Literature" / "Jones2022 KRAS Inhibitors.md",
    "Jones 2022 KRAS Inhibitors",
    ["literature", "KRAS", "inhibitors"],
    "Citation: Jones et al. 2022, Nature Chemical Biology\n\nSotorasib mechanism: Covalent binding to C12 in KRAS G12C\n\nSee [[KRAS G12C Mutation Study]] for our internal data"
)

make_note(
    VAULT / "Admin" / "Budget 2024.md",
    "Budget 2024",
    ["admin", "finance"],
    "Total allocated: $2.4M\n\nBreakdown:\n- Consumables: $800k\n- Equipment: $400k\n- Personnel: $1.2M"
)

make_note(
    VAULT / "Lab" / "Protocols" / "Western Blot Protocol.md",
    "Western Blot Protocol",
    ["protocol", "lab", "western-blot"],
    "## Gel Preparation\n\n10% polyacrylamide gel\n\n## Transfer\n\n100V for 1h at 4°C\n\n## Blocking\n\n5% milk in TBST, 1h RT"
)

make_note(
    VAULT / "Meetings" / "Weekly Sync 2024-03-18.md",
    "Weekly Sync 2024-03-18",
    ["meeting", "weekly"],
    "Discussed progress on EGFR project.\n\nDr. Chen presented IC50 data for compound series.\n\nNext steps: dose-response curves for top 3 compounds."
)

make_note(
    VAULT / "Lab" / "Equipment" / "HPLC Log.md",
    "HPLC Log",
    ["equipment", "hplc"],
    "Column: C18 reverse phase, 4.6x150mm\n\nLast run: 2024-03-14\n\nColumn pressure nominal."
)

# ---- KEY RESEARCH NOTES (the agent must find and reference these) ----
make_note(
    VAULT / "Research" / "Proteins" / "EGFR Structure and Function.md",
    "EGFR Structure and Function",
    ["research", "EGFR", "protein", "target"],
    """## Overview

Epidermal Growth Factor Receptor (EGFR) is a receptor tyrosine kinase encoded by the ERBB1 gene.
Molecular weight: ~134 kDa (unglycosylated).

## Domain Architecture

- **Extracellular domain**: Ligand binding (domains I-IV)
- **Transmembrane domain**: Single-pass alpha helix
- **Intracellular kinase domain**: ATP-binding cleft, activation loop

## Key Mutations in Cancer

| Mutation | Type | Drug Sensitivity |
|----------|------|-----------------|
| L858R    | Activating | Sensitive to gefitinib |
| T790M    | Resistance | Resistant to 1st/2nd gen |
| C797S    | Resistance | Resistant to osimertinib |

## Signaling Pathways

Activates: RAS/MAPK, PI3K/AKT, STAT3

[[EGFR Inhibitor Project]] [[Smith2023 EGFR Review]]
""",
    created="2024-01-05T08:00:00",
    modified="2024-03-01T11:00:00"
)

make_note(
    VAULT / "Research" / "Assays" / "EGFR Binding Assay Notes.md",
    "EGFR Binding Assay Notes",
    ["research", "EGFR", "assay", "binding"],
    """## Assay Format

TR-FRET competitive binding assay using purified EGFR kinase domain (aa 696-1022).

## Conditions

- Protein concentration: 5 nM
- Tracer: Kinase Tracer 236, 10 nM
- Buffer: 50mM HEPES pH 7.5, 10mM MgCl2, 1mM EGTA, 0.01% Brij-35

## Positive Controls

- Erlotinib: IC50 = 2.1 nM (n=8, CV=12%)
- Gefitinib: IC50 = 6.8 nM (n=6, CV=9%)

## Data Analysis

4-parameter logistic curve fit. Report IC50 ± 95% CI.

See protocol: [[Cell Culture Protocol]]
Related: [[EGFR Structure and Function]]
""",
    created="2024-02-01T10:00:00",
    modified="2024-03-10T09:30:00"
)

make_note(
    VAULT / "Research" / "Proteins" / "KRAS G12C Mutation Study.md",
    "KRAS G12C Mutation Study",
    ["research", "KRAS", "mutation", "oncology"],
    """## Background

KRAS G12C is a point mutation (Gly→Cys at codon 12) found in ~13% of NSCLC.
The cysteine residue creates a unique covalent binding opportunity.

## Internal Compound Data

| Compound | IC50 (nM) | Selectivity vs WT |
|----------|-----------|-------------------|
| INT-001  | 45        | >500x             |
| INT-002  | 12        | >1000x            |
| INT-003  | 8.3       | >800x             |

## Structural Insights

Compounds bind in the switch II pocket (S-IIP).
Critical H-bonds: His95, Tyr96, Gln99.

[[Jones2022 KRAS Inhibitors]]
""",
    created="2024-01-20T13:00:00",
    modified="2024-03-12T16:00:00"
)

# ---- THE NOTE THE AGENT MUST EDIT (add a section to this) ----
make_note(
    VAULT / "Projects" / "EGFR Inhibitor Project.md",
    "EGFR Inhibitor Project",
    ["project", "EGFR", "drug-discovery"],
    """## Objective

Develop next-generation covalent EGFR inhibitors targeting C797S resistance mutation.

## Current Status

Phase: Lead optimization
Active series: Compound series A (pyrimidine scaffold)

## Team

- Dr. Sarah Chen (Med Chem lead)
- Dr. Marcus Webb (Biology)
- Ruslan (Computational)

## Timeline

- Q1 2024: Scaffold exploration (COMPLETE)
- Q2 2024: Lead optimization
- Q3 2024: Preclinical candidate nomination

## Key Results

IC50 data for top compounds:
- Cpd-A01: 3.4 nM (EGFR WT), 28 nM (C797S)
- Cpd-A07: 1.8 nM (EGFR WT), 11 nM (C797S)
- Cpd-A12: 2.1 nM (EGFR WT), 8.7 nM (C797S)

## Next Steps

- Complete selectivity panel (kinome-wide)
- ADMET profiling for Cpd-A12
- Structural biology: crystallography request submitted
""",
    created="2024-01-15T10:30:00",
    modified="2024-03-18T09:00:00"
)

# ---- obsidian_search.py ----
(SCRIPTS_DIR / "obsidian_search.py").write_text(r'''#!/usr/bin/env python3
"""obsidian_search.py - search Obsidian vault"""
import sys
import os
import json
import argparse
import subprocess
import re
from pathlib import Path

def phonetic_transliterate(text):
    """Simple RU<->EN phonetic mapping"""
    ru_to_en = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ж':'zh','з':'z',
                'и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p',
                'р':'r','с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch',
                'ш':'sh','щ':'shch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya'}
    result = text.lower()
    for ru, en in ru_to_en.items():
        result = result.replace(ru, en)
    return result

def search_vault(vault_path, query, limit=10):
    vault = Path(vault_path)
    results = []
    
    # Use ripgrep for fast search
    try:
        rg_result = subprocess.run(
            ['rg', '-l', '-i', query, str(vault), '--glob', '*.md'],
            capture_output=True, text=True, timeout=10
        )
        matched_files = set(rg_result.stdout.strip().split('\n')) if rg_result.stdout.strip() else set()
    except Exception:
        matched_files = set()
    
    # Also try phonetic variant
    phonetic_query = phonetic_transliterate(query)
    if phonetic_query != query.lower():
        try:
            rg_result2 = subprocess.run(
                ['rg', '-l', '-i', phonetic_query, str(vault), '--glob', '*.md'],
                capture_output=True, text=True, timeout=10
            )
            if rg_result2.stdout.strip():
                matched_files.update(rg_result2.stdout.strip().split('\n'))
        except Exception:
            pass
    
    # Score all .md files
    all_md = list(vault.rglob('*.md'))
    
    for md_file in all_md:
        if str(md_file).startswith(str(vault / '.obsidian')):
            continue
        try:
            content = md_file.read_text(encoding='utf-8', errors='ignore')
            title = md_file.stem
            score = 0
            context_snippets = []
            
            # Title match (high weight)
            if query.lower() in title.lower():
                score += 10
            if phonetic_transliterate(query) in phonetic_transliterate(title):
                score += 5
            
            # Content match from ripgrep
            if str(md_file) in matched_files:
                score += 3
                # Extract context
                for line in content.split('\n'):
                    if query.lower() in line.lower():
                        context_snippets.append(line.strip()[:100])
                        if len(context_snippets) >= 3:
                            break
            
            # Tag match
            tag_match = re.search(r'^tags:\s*\n((?:\s+-\s+.+\n)*)', content, re.MULTILINE)
            if tag_match:
                tags_text = tag_match.group(0)
                if query.lower() in tags_text.lower():
                    score += 4
            
            if score > 0:
                rel_path = md_file.relative_to(vault)
                results.append({
                    'path': str(rel_path),
                    'title': title,
                    'score': score,
                    'context': context_snippets[:2]
                })
        except Exception:
            continue
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('vault', help='Vault path')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    
    results = search_vault(args.vault, args.query, args.limit)
    
    if args.json:
        print(json.dumps({'results': results}, indent=2))
    else:
        for r in results:
            print(f"[{r['score']}] {r['title']} ({r['path']})")
            for ctx in r['context']:
                print(f"  > {ctx}")

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# ---- obsidian_cli.py ----
(SCRIPTS_DIR / "obsidian_cli.py").write_text(r'''#!/usr/bin/env python3
"""obsidian_cli.py - Obsidian vault management CLI"""
import sys
import os
import json
import argparse
import re
from pathlib import Path
from datetime import datetime

def get_vault():
    vault = os.environ.get('OBSIDIAN_VAULT', '')
    if not vault:
        sys.stderr.write("Error: OBSIDIAN_VAULT not set\n")
        sys.exit(1)
    return Path(vault)

def parse_frontmatter(content):
    """Parse YAML frontmatter from markdown content"""
    if not content.startswith('---'):
        return {}, content
    end = content.find('\n---', 3)
    if end == -1:
        return {}, content
    fm_text = content[4:end]
    body = content[end+4:].lstrip('\n')
    
    fm = {}
    current_key = None
    current_list = None
    for line in fm_text.split('\n'):
        if not line.strip():
            continue
        if line.startswith('  - ') or line.startswith('- '):
            item = line.strip().lstrip('- ')
            if current_list is not None:
                current_list.append(item)
        elif ':' in line:
            key, _, val = line.partition(':')
            key = key.strip()
            val = val.strip()
            if val == '':
                current_list = []
                fm[key] = current_list
                current_key = key
            else:
                fm[key] = val
                current_key = key
                current_list = None
    return fm, body

def serialize_frontmatter(fm):
    lines = ['---']
    for k, v in fm.items():
        if isinstance(v, list):
            lines.append(f'{k}:')
            for item in v:
                lines.append(f'  - {item}')
        else:
            lines.append(f'{k}: {v}')
    lines.append('---')
    return '\n'.join(lines) + '\n'

def find_note(vault, name):
    """Find a note by name (case-insensitive, with or without .md)"""
    if name.endswith('.md'):
        name = name[:-3]
    for md in vault.rglob('*.md'):
        if md.stem.lower() == name.lower():
            return md
    return None

def cmd_list(vault, folder=None, use_json=False):
    base = vault / folder if folder else vault
    notes = []
    for md in base.rglob('*.md'):
        if '.obsidian' in str(md):
            continue
        rel = md.relative_to(vault)
        notes.append({'path': str(rel), 'title': md.stem})
    if use_json:
        print(json.dumps({'notes': notes}, indent=2))
    else:
        for n in notes:
            print(f"{n['path']}")

def cmd_folders(vault, use_json=False):
    folders = set()
    for md in vault.rglob('*.md'):
        if '.obsidian' in str(md):
            continue
        parent = md.parent.relative_to(vault)
        if str(parent) != '.':
            folders.add(str(parent))
    folders = sorted(folders)
    if use_json:
        print(json.dumps({'folders': folders}, indent=2))
    else:
        for f in folders:
            print(f)

def cmd_read(vault, name, use_json=False):
    note = find_note(vault, name)
    if not note:
        result = {'error': f'Note not found: {name}'}
        if use_json:
            print(json.dumps(result))
        else:
            print(f"Error: {result['error']}")
        sys.exit(1)
    content = note.read_text(encoding='utf-8')
    fm, body = parse_frontmatter(content)
    rel = note.relative_to(vault)
    result = {
        'path': str(rel),
        'title': note.stem,
        'frontmatter': fm,
        'content': content,
        'body': body
    }
    if use_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(content)

def suggest_folder_logic(vault, content_text, title=''):
    """Suggest best folder based on content similarity"""
    folders = {}
    for md in vault.rglob('*.md'):
        if '.obsidian' in str(md):
            continue
        parent = str(md.parent.relative_to(vault))
        if parent == '.':
            parent = ''
        folders[parent] = folders.get(parent, 0) + 1
    
    # Score folders based on keywords in content and title
    text_lower = (content_text + ' ' + title).lower()
    folder_scores = {}
    
    keyword_map = {
        'Research': ['research', 'study', 'analysis', 'protein', 'assay', 'egfr', 'kras', 'binding', 'mutation', 'inhibitor', 'structure', 'function', 'summary'],
        'Research/Proteins': ['protein', 'egfr', 'kras', 'structure', 'function', 'receptor', 'kinase', 'mutation'],
        'Research/Assays': ['assay', 'binding', 'ic50', 'tr-fret', 'protocol', 'dose-response'],
        'Projects': ['project', 'timeline', 'objective', 'status', 'milestone', 'team'],
        'Literature': ['citation', 'paper', 'review', 'journal', 'published', 'et al'],
        'Lab/Protocols': ['protocol', 'procedure', 'steps', 'materials', 'buffer'],
        'Meetings': ['meeting', 'attendees', 'action items', 'agenda'],
        'Admin': ['budget', 'hr', 'admin', 'onboarding'],
    }
    
    for folder, keywords in keyword_map.items():
        score = sum(3 if kw in text_lower else 0 for kw in keywords)
        if score > 0:
            folder_scores[folder] = score
    
    if not folder_scores:
        return 'Research'
    
    return max(folder_scores, key=folder_scores.get)

def cmd_suggest_folder(vault, content_text, title='', use_json=False):
    folder = suggest_folder_logic(vault, content_text, title)
    if use_json:
        print(json.dumps({'suggested_folder': folder}, indent=2))
    else:
        print(folder)

def cmd_create(vault, title, content='', folder=None, tags=None, auto_folder=False, use_json=False):
    if auto_folder and not folder:
        folder = suggest_folder_logic(vault, content, title)
    
    if folder:
        note_dir = vault / folder
    else:
        note_dir = vault
    
    note_dir.mkdir(parents=True, exist_ok=True)
    note_path = note_dir / f"{title}.md"
    
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    fm = {
        'created': now,
        'modified': now,
        'tags': tags or []
    }
    
    fm_text = serialize_frontmatter(fm)
    full_content = fm_text + '\n# ' + title + '\n\n' + content
    
    note_path.write_text(full_content, encoding='utf-8')
    
    rel = note_path.relative_to(vault)
    result = {
        'created': True,
        'path': str(rel),
        'title': title,
        'folder': folder or ''
    }
    if use_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Created: {rel}")

def cmd_edit(vault, name, mode, content='', section=None, use_json=False):
    note = find_note(vault, name)
    if not note:
        result = {'error': f'Note not found: {name}'}
        if use_json:
            print(json.dumps(result))
        sys.exit(1)
    
    existing = note.read_text(encoding='utf-8')
    fm, body = parse_frontmatter(existing)
    
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    fm['modified'] = now
    fm_text = serialize_frontmatter(fm)
    
    if mode == 'append':
        new_body = body.rstrip('\n') + '\n\n' + content
    elif mode == 'prepend':
        new_body = content + '\n\n' + body.lstrip('\n')
    elif mode == 'replace':
        new_body = content
    elif mode == 'replace-section':
        if not section:
            sys.stderr.write("Error: --section/-s required for replace-section\n")
            sys.exit(1)
        # Find section in body and replace its content
        section_pattern = re.compile(
            r'(^#{1,6}\s+' + re.escape(section) + r'\s*$)(.*?)(?=^#{1,6}\s|\Z)',
            re.MULTILINE | re.DOTALL
        )
        if section_pattern.search(body):
            new_body = section_pattern.sub(
                lambda m: m.group(1) + '\n\n' + content + '\n\n',
                body
            )
        else:
            # Section not found, append it
            new_body = body.rstrip('\n') + '\n\n## ' + section + '\n\n' + content + '\n'
    else:
        sys.stderr.write(f"Error: Unknown mode: {mode}\n")
        sys.exit(1)
    
    note.write_text(fm_text + '\n' + new_body, encoding='utf-8')
    
    rel = note.relative_to(vault)
    result = {'edited': True, 'path': str(rel), 'mode': mode}
    if use_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Edited ({mode}): {rel}")

def cmd_tags(vault, use_json=False):
    tags = {}
    for md in vault.rglob('*.md'):
        if '.obsidian' in str(md):
            continue
        try:
            content = md.read_text(encoding='utf-8')
            fm, _ = parse_frontmatter(content)
            for tag in (fm.get('tags') or []):
                tags[tag] = tags.get(tag, 0) + 1
        except Exception:
            pass
    if use_json:
        print(json.dumps({'tags': tags}, indent=2))
    else:
        for tag, count in sorted(tags.items()):
            print(f"{tag}: {count}")

def cmd_links(vault, name, use_json=False):
    note = find_note(vault, name)
    if not note:
        result = {'error': f'Note not found: {name}'}
        if use_json:
            print(json.dumps(result))
        sys.exit(1)
    
    content = note.read_text(encoding='utf-8')
    # Outgoing links
    outgoing = re.findall(r'\[\[([^\]|#]+)(?:[|#][^\]]*)?]]', content)
    
    # Incoming links
    incoming = []
    for md in vault.rglob('*.md'):
        if md == note or '.obsidian' in str(md):
            continue
        try:
            other_content = md.read_text(encoding='utf-8')
            if note.stem.lower() in [l.lower() for l in re.findall(r'\[\[([^\]|#]+)(?:[|#][^\]]*)?]]', other_content)]:
                incoming.append(md.stem)
        except Exception:
            pass
    
    result = {
        'note': note.stem,
        'outgoing': outgoing,
        'incoming': incoming
    }
    if use_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Outgoing: {', '.join(outgoing)}")
        print(f"Incoming: {', '.join(incoming)}")

def main():
    parser = argparse.ArgumentParser(prog='obsidian_cli.py')
    parser.add_argument('--vault', default=os.environ.get('OBSIDIAN_VAULT', ''))
    parser.add_argument('--json', action='store_true', dest='use_json')
    
    subparsers = parser.add_subparsers(dest='command')
    
    # list
    list_p = subparsers.add_parser('list')
    list_p.add_argument('folder', nargs='?', default=None)
    
    # folders
    subparsers.add_parser('folders')
    
    # read
    read_p = subparsers.add_parser('read')
    read_p.add_argument('name')
    
    # create
    create_p = subparsers.add_parser('create')
    create_p.add_argument('title')
    create_p.add_argument('-c', '--content', default='')
    create_p.add_argument('-f', '--folder', default=None)
    create_p.add_argument('-t', '--tags', nargs='+', default=[])
    create_p.add_argument('--auto-folder', action='store_true')
    
    # edit
    edit_p = subparsers.add_parser('edit')
    edit_p.add_argument('name')
    edit_p.add_argument('mode', choices=['append', 'prepend', 'replace', 'replace-section'])
    edit_p.add_argument('-c', '--content', default='')
    edit_p.add_argument('-s', '--section', default=None)
    
    # tags
    subparsers.add_parser('tags')
    
    # links
    links_p = subparsers.add_parser('links')
    links_p.add_argument('name')
    
    # suggest-folder
    sf_p = subparsers.add_parser('suggest-folder')
    sf_p.add_argument('content')
    sf_p.add_argument('--title', default='')
    
    args = parser.parse_args()
    
    vault = Path(args.vault) if args.vault else get_vault()
    
    if args.command == 'list':
        cmd_list(vault, args.folder, args.use_json)
    elif args.command == 'folders':
        cmd_folders(vault, args.use_json)
    elif args.command == 'read':
        cmd_read(vault, args.name, args.use_json)
    elif args.command == 'create':
        cmd_create(vault, args.title, args.content, args.folder, args.tags, args.auto_folder, args.use_json)
    elif args.command == 'edit':
        cmd_edit(vault, args.name, args.mode, args.content, args.section, args.use_json)
    elif args.command == 'tags':
        cmd_tags(vault, args.use_json)
    elif args.command == 'links':
        cmd_links(vault, args.name, args.use_json)
    elif args.command == 'suggest-folder':
        cmd_suggest_folder(vault, args.content, args.title, args.use_json)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# ---- Write workspace marker ----
Path("/workspace/task_ready.txt").write_text("Vault and scripts initialized.\n")
print("Setup complete.")
print(f"Vault: {VAULT}")
print(f"Scripts: {SCRIPTS_DIR}")
print(f"Notes created: {len(list(VAULT.rglob('*.md')))}")