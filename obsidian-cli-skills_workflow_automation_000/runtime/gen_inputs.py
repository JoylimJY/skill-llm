#!/usr/bin/env python3
"""
Generate the sandbox workspace for the obsidian-cli task.
Creates:
1. A realistic research vault directory structure with distractor files
2. A mock obsidian-cli executable that simulates real behavior
3. A config directory mimicking the real obsidian-cli config location
"""

import os
import json
import stat
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")
VAULT_DIR = WORKSPACE / "research_vault"
DISTRACTOR_VAULT = WORKSPACE / "old_vault_backup"
CONFIG_DIR = Path("/root/.openclaw")

# Create vault directories
VAULT_DIR.mkdir(parents=True, exist_ok=True)
DISTRACTOR_VAULT.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# ── Distractor files in research_vault ──────────────────────────────────────
distractor_notes = {
    "protein-folding-notes.md": "---\nstatus: published\ntags: biology,proteins\n---\n# Protein Folding\n\nAlphaFold changed everything.\n",
    "crispr-ethics.md": "---\nstatus: review\ntags: ethics,crispr\nauthor: dr.jones\n---\n# CRISPR Ethics\n\nOff-target effects remain a concern.\n",
    "lab-budget-2026.md": "# Lab Budget 2026\n\n- Equipment: $50,000\n- Personnel: $120,000\n- Reagents: $30,000\n",
    "meeting-notes-2026-01-15.md": "# Team Meeting Jan 15\n\nDiscussed Q1 publication goals.\nNext meeting: Feb 5.\n",
    "references.md": "# Key References\n\n1. Einstein 1935 EPR paper\n2. Bell 1964 inequalities\n3. Aspect 1982 experiment\n",
    "TODO.md": "# TODO\n\n- [ ] Submit grant application\n- [ ] Review student thesis\n- [ ] Update lab website\n",
}

subdir_notes = {
    "archive/old-quantum-draft.md": "---\nstatus: abandoned\ntags: quantum\n---\n# Old Draft\n\nThis was superseded by newer work.\n",
    "archive/photon-entanglement-2024.md": "---\nstatus: published\ntags: photon,quantum\nauthor: dr.chen\n---\n# Photon Entanglement 2024\n\nKey results from the 2024 experiment.\n",
    "templates/research-template.md": "---\nstatus: template\ntags: \nauthor: \n---\n# {{title}}\n\n## Abstract\n\n## Methods\n\n## Results\n\n## Conclusions\n",
    "templates/review-template.md": "---\nstatus: draft\ntags: \n---\n# Literature Review: {{topic}}\n\n## Overview\n\n## Key Papers\n",
}

for fname, content in distractor_notes.items():
    (VAULT_DIR / fname).write_text(content)

for fpath, content in subdir_notes.items():
    full_path = VAULT_DIR / fpath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# Distractor vault with some old notes
(DISTRACTOR_VAULT / "legacy-note-1.md").write_text("# Legacy Note\n\nThis is from the old vault.\n")
(DISTRACTOR_VAULT / "legacy-note-2.md").write_text("# Another Legacy\n\nArchived content.\n")

# ── obsidian-cli config (mimics real tool's config location) ─────────────────
# Start with NO default vault set (agent must set it)
config_data = {
    "default_vault": "",
    "vaults": {
        "research_vault": str(VAULT_DIR),
        "old_vault_backup": str(DISTRACTOR_VAULT),
    }
}
(CONFIG_DIR / "config.json").write_text(json.dumps(config_data, indent=2))

# ── Mock obsidian-cli script ─────────────────────────────────────────────────
mock_cli = r'''#!/usr/bin/env python3
"""
Mock obsidian-cli that mimics the real tool's behavior.
State is stored in /root/.openclaw/config.json and vault markdown files.
"""
import sys
import os
import json
import re
import argparse
from pathlib import Path

CONFIG_PATH = Path("/root/.openclaw/config.json")

def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {"default_vault": "", "vaults": {}}

def save_config(cfg):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))

def get_vault_path(cfg, vault_name=None):
    if vault_name:
        if vault_name in cfg.get("vaults", {}):
            return Path(cfg["vaults"][vault_name])
        p = Path(vault_name)
        if p.exists():
            return p
        print(f"Error: vault '{vault_name}' not found", file=sys.stderr)
        sys.exit(1)
    default = cfg.get("default_vault", "")
    if not default:
        print("Error: no default vault set. Use set-default first.", file=sys.stderr)
        sys.exit(1)
    if default in cfg.get("vaults", {}):
        return Path(cfg["vaults"][default])
    p = Path(default)
    if p.exists():
        return p
    print(f"Error: default vault path '{default}' not found", file=sys.stderr)
    sys.exit(1)

def note_path(vault, name):
    if not name.endswith(".md"):
        name = name + ".md"
    return vault / name

def parse_frontmatter(content):
    """Returns (frontmatter_dict, body_str) or ({}, content)"""
    if content.startswith("---\n"):
        end = content.find("\n---\n", 4)
        if end != -1:
            import yaml
            fm_text = content[4:end]
            try:
                fm = yaml.safe_load(fm_text) or {}
            except:
                fm = {}
            body = content[end+5:]
            return fm, body
    return {}, content

def render_frontmatter(fm, body):
    import yaml
    if not fm:
        return body
    fm_text = yaml.dump(fm, default_flow_style=False, allow_unicode=True).rstrip()
    return f"---\n{fm_text}\n---\n{body}"

def cmd_set_default(args):
    cfg = load_config()
    target = args.vault_name
    # Check if it's a known vault name
    if target in cfg.get("vaults", {}):
        cfg["default_vault"] = target
        save_config(cfg)
        print(f"Default vault set to: {target}")
        return
    # Check if it's a path
    p = Path(target)
    if p.exists() and p.is_dir():
        # Register it
        vname = p.name
        cfg["vaults"][vname] = str(p)
        cfg["default_vault"] = vname
        save_config(cfg)
        print(f"Default vault set to: {vname} ({p})")
        return
    # Try treating as absolute path string
    print(f"Error: '{target}' is not a known vault name or existing directory", file=sys.stderr)
    sys.exit(1)

def cmd_print_default(args):
    cfg = load_config()
    default = cfg.get("default_vault", "")
    if not default:
        print("No default vault set.", file=sys.stderr)
        sys.exit(1)
    vault_path = cfg.get("vaults", {}).get(default, default)
    if hasattr(args, 'path_only') and args.path_only:
        print(vault_path)
    else:
        print(f"Default vault name:  {default}")
        print(f"Default vault path:  {vault_path}")

def cmd_create(args):
    cfg = load_config()
    vault = get_vault_path(cfg, getattr(args, 'vault', None))
    np = note_path(vault, args.name)
    content = args.content or ""
    if np.exists():
        if getattr(args, 'append', False):
            existing = np.read_text()
            np.write_text(existing + content)
            print(f"Appended to note: {np}")
            return
        if getattr(args, 'overwrite', False):
            np.write_text(content)
            print(f"Overwritten note: {np}")
            return
        print(f"Error: note '{args.name}' already exists. Use --append or --overwrite.", file=sys.stderr)
        sys.exit(1)
    np.parent.mkdir(parents=True, exist_ok=True)
    np.write_text(content)
    print(f"Created note: {np}")

def cmd_print(args):
    cfg = load_config()
    vault = get_vault_path(cfg, getattr(args, 'vault', None))
    np = note_path(vault, args.name)
    if not np.exists():
        print(f"Error: note '{args.name}' not found", file=sys.stderr)
        sys.exit(1)
    print(np.read_text(), end="")

def cmd_move(args):
    cfg = load_config()
    vault = get_vault_path(cfg, getattr(args, 'vault', None))
    src = note_path(vault, args.old_name)
    dst = note_path(vault, args.new_name)
    if not src.exists():
        print(f"Error: note '{args.old_name}' not found", file=sys.stderr)
        sys.exit(1)
    if dst.exists():
        print(f"Error: destination '{args.new_name}' already exists", file=sys.stderr)
        sys.exit(1)
    # Update wiki links in all notes
    old_stem = src.stem
    new_stem = dst.stem
    for md_file in vault.rglob("*.md"):
        if md_file == src:
            continue
        try:
            text = md_file.read_text()
            updated = text.replace(f"[[{old_stem}]]", f"[[{new_stem}]]")
            if updated != text:
                md_file.write_text(updated)
        except:
            pass
    # Move the file itself (preserving content)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text())
    src.unlink()
    print(f"Moved note from {src} to {dst}")

def cmd_delete(args):
    cfg = load_config()
    vault = get_vault_path(cfg, getattr(args, 'vault', None))
    np = note_path(vault, args.name)
    if not np.exists():
        print(f"Error: note '{args.name}' not found", file=sys.stderr)
        sys.exit(1)
    np.unlink()
    print(f"Deleted note: {np}")

def cmd_frontmatter(args):
    cfg = load_config()
    vault = get_vault_path(cfg, getattr(args, 'vault', None))
    np = note_path(vault, args.name)
    if not np.exists():
        print(f"Error: note '{args.name}' not found", file=sys.stderr)
        sys.exit(1)
    content = np.read_text()
    fm, body = parse_frontmatter(content)
    
    if getattr(args, 'print_fm', False):
        import yaml
        if fm:
            print(yaml.dump(fm, default_flow_style=False, allow_unicode=True), end="")
        else:
            print("(no frontmatter)")
        return
    
    if getattr(args, 'edit', False):
        key = args.key
        value = args.value
        fm[key] = value
        np.write_text(render_frontmatter(fm, body))
        print(f"Updated frontmatter: {key} = {value}")
        return
    
    if getattr(args, 'delete_key', False):
        key = args.key
        if key in fm:
            del fm[key]
            np.write_text(render_frontmatter(fm, body))
            print(f"Deleted frontmatter key: {key}")
        else:
            print(f"Key '{key}' not found in frontmatter")
        return
    
    print("Error: specify --print, --edit, or --delete", file=sys.stderr)
    sys.exit(1)

def cmd_search_content(args):
    cfg = load_config()
    vault = get_vault_path(cfg, getattr(args, 'vault', None))
    keyword = args.keyword
    for md_file in vault.rglob("*.md"):
        try:
            if keyword.lower() in md_file.read_text().lower():
                print(md_file)
        except:
            pass

def main():
    if len(sys.argv) < 2:
        print("Usage: obsidian-cli <command> [options]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    rest = sys.argv[2:]
    
    if cmd == "set-default":
        p = argparse.ArgumentParser()
        p.add_argument("vault_name")
        cmd_set_default(p.parse_args(rest))
    
    elif cmd == "print-default":
        p = argparse.ArgumentParser()
        p.add_argument("--path-only", dest="path_only", action="store_true")
        cmd_print_default(p.parse_args(rest))
    
    elif cmd == "create":
        p = argparse.ArgumentParser()
        p.add_argument("name")
        p.add_argument("--content", "-c", default="")
        p.add_argument("--overwrite", action="store_true")
        p.add_argument("--append", "-a", action="store_true")
        p.add_argument("--vault", "-v", default=None)
        cmd_create(p.parse_args(rest))
    
    elif cmd == "print":
        p = argparse.ArgumentParser()
        p.add_argument("name")
        p.add_argument("--vault", "-v", default=None)
        cmd_print(p.parse_args(rest))
    
    elif cmd == "move":
        p = argparse.ArgumentParser()
        p.add_argument("old_name")
        p.add_argument("new_name")
        p.add_argument("--vault", "-v", default=None)
        cmd_move(p.parse_args(rest))
    
    elif cmd == "delete":
        p = argparse.ArgumentParser()
        p.add_argument("name")
        p.add_argument("--vault", "-v", default=None)
        cmd_delete(p.parse_args(rest))
    
    elif cmd == "frontmatter":
        p = argparse.ArgumentParser()
        p.add_argument("name")
        p.add_argument("--print", dest="print_fm", action="store_true")
        p.add_argument("--edit", dest="edit", action="store_true")
        p.add_argument("--delete", dest="delete_key", action="store_true")
        p.add_argument("--key", default=None)
        p.add_argument("--value", default=None)
        p.add_argument("--vault", "-v", default=None)
        cmd_frontmatter(p.parse_args(rest))
    
    elif cmd == "search-content":
        p = argparse.ArgumentParser()
        p.add_argument("keyword")
        p.add_argument("--vault", "-v", default=None)
        cmd_search_content(p.parse_args(rest))
    
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

cli_path = WORKSPACE / "obsidian-cli"
cli_path.write_text(mock_cli)
cli_path.chmod(cli_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# Also place in /usr/local/bin so it's on PATH
import shutil
shutil.copy(str(cli_path), "/usr/local/bin/obsidian-cli")
os.chmod("/usr/local/bin/obsidian-cli", 0o755)

print("Workspace generated successfully.")
print(f"  Vault: {VAULT_DIR}")
print(f"  Distractor vault: {DISTRACTOR_VAULT}")
print(f"  Config: {CONFIG_DIR / 'config.json'}")
print(f"  CLI: {cli_path}")