FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    ripgrep \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    python-frontmatter \
    PyYAML \
    thefuzz \
    python-Levenshtein \
    pymorphy2 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create the vault directory structure
RUN mkdir -p /home/ruslan/webdav/data/ruslain/.obsidian
RUN mkdir -p /home/ruslan/.openclaw/workspace/skills/obsidian/scripts

# Create obsidian_cli.py - the main CLI tool
RUN cat > /home/ruslan/.openclaw/workspace/skills/obsidian/scripts/obsidian_cli.py << 'PYEOF'
#!/usr/bin/env python3
"""Obsidian CLI tool for vault management."""

import argparse
import json
import os
import sys
import re
from pathlib import Path
from datetime import datetime
import yaml

def get_vault_path():
    vault = os.environ.get('OBSIDIAN_VAULT', '')
    if not vault:
        print(json.dumps({"error": "OBSIDIAN_VAULT not set"}))
        sys.exit(1)
    return Path(vault)

def parse_frontmatter(content):
    """Parse YAML frontmatter from markdown content."""
    if content.startswith('---'):
        end = content.find('\n---', 3)
        if end != -1:
            fm_text = content[3:end].strip()
            try:
                fm = yaml.safe_load(fm_text)
                body = content[end+4:].strip()
                return fm or {}, body
            except:
                pass
    return {}, content

def render_frontmatter(fm, body):
    """Render frontmatter + body to markdown string."""
    if fm:
        fm_yaml = yaml.dump(fm, default_flow_style=False, allow_unicode=True).strip()
        return f"---\n{fm_yaml}\n---\n\n{body}"
    return body

def find_note(vault_path, name):
    """Find a note by name (case-insensitive, with or without .md)."""
    name_lower = name.lower().replace('.md', '')
    for md_file in vault_path.rglob('*.md'):
        if md_file.stem.lower() == name_lower:
            return md_file
    return None

def cmd_list(vault_path, folder=None, json_output=False):
    results = []
    search_path = vault_path / folder if folder else vault_path
    for md_file in sorted(search_path.rglob('*.md')):
        rel = md_file.relative_to(vault_path)
        results.append({
            "path": str(rel),
            "name": md_file.stem,
            "folder": str(rel.parent) if str(rel.parent) != '.' else ''
        })
    if json_output:
        print(json.dumps(results, ensure_ascii=False))
    else:
        for r in results:
            print(r['path'])

def cmd_folders(vault_path, json_output=False):
    folders = set()
    for md_file in vault_path.rglob('*.md'):
        rel = md_file.relative_to(vault_path)
        if str(rel.parent) != '.':
            folders.add(str(rel.parent))
    result = sorted(list(folders))
    if json_output:
        print(json.dumps(result, ensure_ascii=False))
    else:
        for f in result:
            print(f)

def cmd_read(vault_path, name, json_output=False):
    note_file = find_note(vault_path, name)
    if not note_file:
        err = {"error": f"Note not found: {name}"}
        print(json.dumps(err) if json_output else f"Error: {err['error']}")
        sys.exit(1)
    content = note_file.read_text(encoding='utf-8')
    fm, body = parse_frontmatter(content)
    result = {
        "path": str(note_file.relative_to(vault_path)),
        "name": note_file.stem,
        "frontmatter": fm,
        "content": content,
        "body": body
    }
    if json_output:
        print(json.dumps(result, ensure_ascii=False, default=str))
    else:
        print(content)

def cmd_create(vault_path, title, content='', folder=None, tags=None, auto_folder=False, json_output=False):
    if auto_folder and not folder:
        folder = _suggest_folder_logic(vault_path, content, title)
    
    now = datetime.now().isoformat(timespec='seconds')
    fm = {
        'created': now,
        'modified': now,
    }
    if tags:
        fm['tags'] = tags if isinstance(tags, list) else [tags]
    
    full_content = render_frontmatter(fm, f"# {title}\n\n{content}")
    
    if folder:
        note_dir = vault_path / folder
        note_dir.mkdir(parents=True, exist_ok=True)
    else:
        note_dir = vault_path
    
    note_path = note_dir / f"{title}.md"
    if note_path.exists():
        err = {"error": f"Note already exists: {title}"}
        print(json.dumps(err) if json_output else f"Error: {err['error']}")
        sys.exit(1)
    
    note_path.write_text(full_content, encoding='utf-8')
    result = {
        "success": True,
        "path": str(note_path.relative_to(vault_path)),
        "name": title
    }
    if json_output:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"Created: {result['path']}")

def _suggest_folder_logic(vault_path, content, title=''):
    """Suggest best folder based on content similarity."""
    folders = set()
    note_keywords = {}
    
    for md_file in vault_path.rglob('*.md'):
        rel = md_file.relative_to(vault_path)
        folder = str(rel.parent)
        if folder == '.':
            folder = ''
        if folder:
            folders.add(folder)
            if folder not in note_keywords:
                note_keywords[folder] = []
            try:
                text = md_file.read_text(encoding='utf-8').lower()
                note_keywords[folder].append(text)
            except:
                pass
    
    if not folders:
        return ''
    
    combined = (content + ' ' + title).lower()
    best_folder = ''
    best_score = -1
    
    for folder, texts in note_keywords.items():
        folder_words = set(re.findall(r'\w+', folder.lower()))
        combined_words = set(re.findall(r'\w+', combined))
        all_text = ' '.join(texts)
        text_words = set(re.findall(r'\w+', all_text))
        
        overlap_folder = len(folder_words & combined_words)
        overlap_text = len(text_words & combined_words)
        score = overlap_folder * 3 + overlap_text
        
        if score > best_score:
            best_score = score
            best_folder = folder
    
    return best_folder

def cmd_suggest_folder(vault_path, content, title='', json_output=False):
    folder = _suggest_folder_logic(vault_path, content, title)
    result = {"suggested_folder": folder}
    if json_output:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(folder)

def cmd_edit(vault_path, name, mode, content='', section=None, json_output=False):
    note_file = find_note(vault_path, name)
    if not note_file:
        err = {"error": f"Note not found: {name}"}
        print(json.dumps(err) if json_output else f"Error: {err['error']}")
        sys.exit(1)
    
    existing = note_file.read_text(encoding='utf-8')
    fm, body = parse_frontmatter(existing)
    
    # Update modified timestamp
    fm['modified'] = datetime.now().isoformat(timespec='seconds')
    
    if mode == 'append':
        new_body = body + '\n\n' + content
    elif mode == 'prepend':
        new_body = content + '\n\n' + body
    elif mode == 'replace':
        new_body = content
    elif mode == 'replace-section':
        if not section:
            err = {"error": "replace-section requires -s SECTION"}
            print(json.dumps(err) if json_output else f"Error: {err['error']}")
            sys.exit(1)
        # Find section header and replace until next same-level or higher header
        pattern = rf'(##{{1,6}}\s+{re.escape(section)}\s*\n)(.*?)(?=\n##{{1,6}}\s|\Z)'
        replacement_text = f'## {section}\n\n{content}\n'
        new_body, count = re.subn(pattern, replacement_text, body, flags=re.DOTALL)
        if count == 0:
            # Section not found, append it
            new_body = body + f'\n\n## {section}\n\n{content}'
    else:
        err = {"error": f"Unknown edit mode: {mode}"}
        print(json.dumps(err) if json_output else f"Error: {err['error']}")
        sys.exit(1)
    
    new_content = render_frontmatter(fm, new_body)
    note_file.write_text(new_content, encoding='utf-8')
    
    result = {"success": True, "path": str(note_file.relative_to(vault_path)), "mode": mode}
    if json_output:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"Edited ({mode}): {result['path']}")

def cmd_tags(vault_path, json_output=False):
    tag_counts = {}
    for md_file in vault_path.rglob('*.md'):
        content = md_file.read_text(encoding='utf-8')
        fm, body = parse_frontmatter(content)
        for tag in fm.get('tags', []):
            tag_counts[str(tag)] = tag_counts.get(str(tag), 0) + 1
        for inline_tag in re.findall(r'(?<!\[)#([a-zA-Z][a-zA-Z0-9_/-]*)', body):
            tag_counts[inline_tag] = tag_counts.get(inline_tag, 0) + 1
    result = [{"tag": k, "count": v} for k, v in sorted(tag_counts.items())]
    if json_output:
        print(json.dumps(result, ensure_ascii=False))
    else:
        for item in result:
            print(f"{item['tag']}: {item['count']}")

def cmd_links(vault_path, name, json_output=False):
    note_file = find_note(vault_path, name)
    if not note_file:
        err = {"error": f"Note not found: {name}"}
        print(json.dumps(err) if json_output else f"Error: {err['error']}")
        sys.exit(1)
    
    content = note_file.read_text(encoding='utf-8')
    outgoing = re.findall(r'\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]', content)
    
    incoming = []
    note_stem = note_file.stem
    for md_file in vault_path.rglob('*.md'):
        if md_file == note_file:
            continue
        other_content = md_file.read_text(encoding='utf-8')
        if f'[[{note_stem}' in other_content or f'[[{note_stem}|' in other_content:
            incoming.append(md_file.stem)
    
    result = {"outgoing": list(set(outgoing)), "incoming": list(set(incoming))}
    if json_output:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"Outgoing: {result['outgoing']}")
        print(f"Incoming: {result['incoming']}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vault', default=None)
    parser.add_argument('--json', action='store_true', dest='json_output')
    
    subparsers = parser.add_subparsers(dest='command')
    
    # list
    list_parser = subparsers.add_parser('list')
    list_parser.add_argument('folder', nargs='?', default=None)
    
    # folders
    subparsers.add_parser('folders')
    
    # read
    read_parser = subparsers.add_parser('read')
    read_parser.add_argument('name')
    
    # create
    create_parser = subparsers.add_parser('create')
    create_parser.add_argument('title')
    create_parser.add_argument('-c', '--content', default='')
    create_parser.add_argument('-f', '--folder', default=None)
    create_parser.add_argument('-t', '--tags', nargs='+', default=None)
    create_parser.add_argument('--auto-folder', action='store_true')
    
    # edit
    edit_parser = subparsers.add_parser('edit')
    edit_parser.add_argument('name')
    edit_parser.add_argument('mode', choices=['append', 'prepend', 'replace', 'replace-section'])
    edit_parser.add_argument('-c', '--content', default='')
    edit_parser.add_argument('-s', '--section', default=None)
    
    # tags
    subparsers.add_parser('tags')
    
    # links
    links_parser = subparsers.add_parser('links')
    links_parser.add_argument('name')
    
    # suggest-folder
    sf_parser = subparsers.add_parser('suggest-folder')
    sf_parser.add_argument('content')
    sf_parser.add_argument('--title', default='')
    
    args = parser.parse_args()
    
    vault_path = Path(args.vault) if args.vault else get_vault_path()
    
    if args.command == 'list':
        cmd_list(vault_path, args.folder, args.json_output)
    elif args.command == 'folders':
        cmd_folders(vault_path, args.json_output)
    elif args.command == 'read':
        cmd_read(vault_path, args.name, args.json_output)
    elif args.command == 'create':
        cmd_create(vault_path, args.title, args.content, args.folder, args.tags, args.auto_folder, args.json_output)
    elif args.command == 'edit':
        cmd_edit(vault_path, args.name, args.mode, args.content, args.section, args.json_output)
    elif args.command == 'tags':
        cmd_tags(vault_path, args.json_output)
    elif args.command == 'links':
        cmd_links(vault_path, args.name, args.json_output)
    elif args.command == 'suggest-folder':
        cmd_suggest_folder(vault_path, args.content, args.title, args.json_output)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
PYEOF

# Create obsidian_search.py
RUN cat > /home/ruslan/.openclaw/workspace/skills/obsidian/scripts/obsidian_search.py << 'PYEOF'
#!/usr/bin/env python3
"""Obsidian fuzzy/phonetic search tool."""

import sys
import os
import json
import re
import subprocess
from pathlib import Path
import argparse

def transliterate_ru_en(text):
    """Basic RU->EN phonetic transliteration."""
    mapping = {
        'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo',
        'ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m',
        'н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u',
        'ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'sch',
        'ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya'
    }
    result = ''
    for ch in text.lower():
        result += mapping.get(ch, ch)
    return result

def score_note(path, title, content, query):
    """Score a note against a query."""
    query_lower = query.lower()
    query_translit = transliterate_ru_en(query_lower)
    title_lower = title.lower()
    title_translit = transliterate_ru_en(title_lower)
    content_lower = content.lower()
    
    score = 0
    matched_context = []
    
    # Title match (highest weight)
    if query_lower in title_lower or query_translit in title_translit:
        score += 100
    
    # Partial title match
    query_words = query_lower.split()
    for word in query_words:
        if word in title_lower or transliterate_ru_en(word) in title_translit:
            score += 20
    
    # Content match
    for line in content.split('\n'):
        line_lower = line.lower()
        if query_lower in line_lower:
            score += 10
            matched_context.append(line.strip()[:100])
        else:
            for word in query_words:
                if word in line_lower:
                    score += 2
                    if line.strip():
                        matched_context.append(line.strip()[:100])
                    break
    
    return score, matched_context[:3]

def search(vault_path, query, limit=10):
    results = []
    vault = Path(vault_path)
    
    for md_file in vault.rglob('*.md'):
        try:
            content = md_file.read_text(encoding='utf-8')
        except:
            continue
        
        title = md_file.stem
        score, context = score_note(str(md_file), title, content, query)
        
        if score > 0:
            results.append({
                "path": str(md_file.relative_to(vault)),
                "title": title,
                "score": score,
                "context": context
            })
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('vault', help='Vault path')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--json', action='store_true', dest='json_output')
    args = parser.parse_args()
    
    results = search(args.vault, args.query, args.limit)
    
    if args.json_output:
        print(json.dumps(results, ensure_ascii=False))
    else:
        for r in results:
            print(f"[{r['score']}] {r['path']}")
            for ctx in r['context']:
                print(f"  > {ctx}")

if __name__ == '__main__':
    main()
PYEOF

RUN chmod +x /home/ruslan/.openclaw/workspace/skills/obsidian/scripts/obsidian_cli.py
RUN chmod +x /home/ruslan/.openclaw/workspace/skills/obsidian/scripts/obsidian_search.py

RUN useradd -m -s /bin/bash agent 2>/dev/null || true

WORKDIR /workspace
ENV OBSIDIAN_VAULT=/home/ruslan/webdav/data/ruslain