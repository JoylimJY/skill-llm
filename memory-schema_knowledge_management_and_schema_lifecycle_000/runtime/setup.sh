#!/bin/bash
set -e

echo "=== Setting up Basic Memory mock environment ==="

# Create the mock basic-memory tool as a Python script
cat > /usr/local/bin/basic_memory_tools.py << 'PYEOF'
#!/usr/bin/env python3
"""
Mock implementation of Basic Memory schema tools for evaluation sandbox.
Implements: write_note, edit_note, schema_infer, schema_validate, schema_diff
All state is persisted to /workspace/memory and /workspace/schema.
"""
import sys
import os
import json
import yaml
import re
import glob
from pathlib import Path
from collections import defaultdict, Counter

WORKSPACE = "/workspace"
MEMORY_DIR = os.path.join(WORKSPACE, "memory")
SCHEMA_DIR = os.path.join(WORKSPACE, "schema")

def parse_note(filepath):
    """Parse a markdown note with YAML frontmatter."""
    with open(filepath) as f:
        content = f.read()
    
    # Extract frontmatter
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
    if fm_match:
        try:
            frontmatter = yaml.safe_load(fm_match.group(1)) or {}
        except:
            frontmatter = {}
        body = fm_match.group(2)
    else:
        frontmatter = {}
        body = content
    
    # Extract observations (lines matching "- [category] value")
    observations = defaultdict(list)
    for line in body.split('\n'):
        obs_match = re.match(r'\s*-\s*\[(\w+)\]\s*(.*)', line)
        if obs_match:
            cat, val = obs_match.group(1), obs_match.group(2).strip()
            observations[cat].append(val)
    
    return frontmatter, body, observations

def load_schema(entity_type):
    """Load schema for an entity type."""
    schema_path = os.path.join(SCHEMA_DIR, f"{entity_type}.md")
    if not os.path.exists(schema_path):
        return None
    fm, body, obs = parse_note(schema_path)
    return fm

def get_notes_of_type(note_type):
    """Find all notes with a given type."""
    notes = []
    for path in Path(MEMORY_DIR).rglob("*.md"):
        try:
            fm, body, obs = parse_note(str(path))
            if fm.get("type") == note_type:
                notes.append((str(path), fm, body, obs))
        except:
            pass
    return notes

def schema_infer(noteType, threshold=0.6):
    """Infer schema from existing notes of a type."""
    notes = get_notes_of_type(noteType)
    if not notes:
        print(f"No notes found with type: {noteType}")
        return
    
    print(f"\n=== Schema Inference for '{noteType}' ({len(notes)} notes found) ===\n")
    
    # Collect all fields from frontmatter
    field_counter = Counter()
    field_values = defaultdict(list)
    
    for path, fm, body, obs in notes:
        for k, v in fm.items():
            if k in ('title', 'type'):
                continue
            field_counter[k] += 1
            if v is not None:
                field_values[k].append(v)
    
    total = len(notes)
    print(f"Threshold: {threshold} ({threshold*100:.0f}% of notes must have field)\n")
    print("Suggested schema fields:")
    print("-" * 50)
    
    for field, count in sorted(field_counter.items(), key=lambda x: -x[1]):
        freq = count / total
        if freq < threshold:
            status = f"[below threshold, freq={freq:.0f%}]"
        else:
            status = f"[included, freq={freq:.0f%}]"
        
        # Infer type
        vals = field_values[field]
        inferred_type = "string"
        if all(isinstance(v, bool) for v in vals):
            inferred_type = "boolean"
        elif all(isinstance(v, int) for v in vals if v is not None):
            inferred_type = "integer"
        elif all(isinstance(v, (int, float)) for v in vals if v is not None):
            inferred_type = "number"
        elif any(isinstance(v, list) for v in vals):
            inferred_type = "array"
        
        optional = "?" if freq < 1.0 else ""
        arr_hint = "(array)" if inferred_type == "array" else ""
        print(f"  {field}{optional}{arr_hint}: {inferred_type}  {status}")
    
    print("\nNote: Review suggestions and create schema with write_note(directory='schema', note_type='schema')")
    return field_counter, field_values, total

def write_note(title, directory, note_type=None, metadata=None, content=None):
    """Write a note to the filesystem."""
    # Determine file path
    safe_title = title.replace(" ", "-").replace("/", "-")
    filepath = os.path.join(WORKSPACE, directory, f"{safe_title}.md")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Build frontmatter
    fm_data = {"title": title}
    if note_type:
        fm_data["type"] = note_type
    if metadata:
        fm_data.update(metadata)
    
    fm_str = yaml.dump(fm_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    body = content or f"# {title}\n"
    
    full_content = f"---\n{fm_str}---\n{body}\n"
    
    with open(filepath, "w") as f:
        f.write(full_content)
    
    print(f"Note written: {filepath}")
    return filepath

def edit_note(identifier, operation, find_text=None, content=None, expected_replacements=None):
    """Edit an existing note."""
    # Resolve identifier to path
    possible_paths = [
        os.path.join(WORKSPACE, identifier + ".md"),
        os.path.join(WORKSPACE, identifier),
        os.path.join(MEMORY_DIR, identifier + ".md"),
        os.path.join(SCHEMA_DIR, identifier.split("/")[-1] + ".md"),
    ]
    
    filepath = None
    for p in possible_paths:
        if os.path.exists(p):
            filepath = p
            break
    
    # Also try schema/ prefix
    if filepath is None and "/" in identifier:
        parts = identifier.split("/")
        if parts[0] == "schema":
            fp = os.path.join(SCHEMA_DIR, parts[1] + ".md")
            if os.path.exists(fp):
                filepath = fp
    
    if filepath is None:
        print(f"ERROR: Note not found: {identifier}")
        return False
    
    with open(filepath) as f:
        current = f.read()
    
    if operation == "find_replace":
        if find_text is None or content is None:
            print("ERROR: find_replace requires find_text and content")
            return False
        
        count = current.count(find_text)
        if expected_replacements is not None and count != expected_replacements:
            print(f"ERROR: Expected {expected_replacements} replacements but found {count}")
            return False
        
        new_content = current.replace(find_text, content)
        with open(filepath, "w") as f:
            f.write(new_content)
        print(f"Edited {filepath}: replaced {count} occurrence(s)")
        return True
    
    elif operation == "append":
        with open(filepath, "a") as f:
            f.write("\n" + content)
        print(f"Appended to {filepath}")
        return True
    
    else:
        print(f"ERROR: Unknown operation: {operation}")
        return False

def schema_validate(noteType=None, identifier=None):
    """Validate notes against their schema."""
    if identifier:
        # Single note validation
        possible = [
            os.path.join(WORKSPACE, identifier + ".md"),
            os.path.join(MEMORY_DIR, identifier + ".md"),
            os.path.join(WORKSPACE, identifier),
        ]
        notes_to_check = []
        for p in possible:
            if os.path.exists(p):
                fm, body, obs = parse_note(p)
                notes_to_check.append((p, fm, body, obs))
                break
        if not notes_to_check:
            print(f"Note not found: {identifier}")
            return
        note_type_for_schema = notes_to_check[0][1].get("type", "Unknown")
    else:
        notes_to_check = get_notes_of_type(noteType)
        note_type_for_schema = noteType
    
    schema_fm = load_schema(note_type_for_schema)
    if not schema_fm:
        print(f"No schema found for type: {note_type_for_schema}")
        return
    
    schema_def = schema_fm.get("schema", {})
    settings = schema_fm.get("settings", {})
    validation_mode = settings.get("validation", "warn") if isinstance(settings, dict) else "warn"
    
    print(f"\n=== Validation: {note_type_for_schema} ({len(notes_to_check)} notes) ===")
    print(f"Mode: {validation_mode}\n")
    
    total_issues = 0
    
    for path, fm, body, obs in notes_to_check:
        note_name = Path(path).stem
        issues = []
        
        for field_key, field_def in schema_def.items():
            # Parse field key
            is_optional = "?" in field_key
            base_name = field_key.replace("?", "").replace("(array)", "").replace("(enum)", "").strip()
            
            # Check if field appears as observation category
            if base_name not in obs:
                if not is_optional:
                    issues.append(f"MISSING required field '{base_name}' (not found as observation category)")
            
        # Check for unknown observation categories
        known_bases = set()
        for field_key in schema_def.keys():
            base = field_key.replace("?", "").replace("(array)", "").replace("(enum)", "").strip()
            known_bases.add(base)
        
        for obs_cat in obs.keys():
            if obs_cat not in known_bases:
                issues.append(f"UNKNOWN field '{obs_cat}' (not in schema)")
        
        if issues:
            total_issues += len(issues)
            print(f"  [{validation_mode.upper()}] {note_name}:")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print(f"  [OK] {note_name}")
    
    print(f"\nTotal issues: {total_issues}")
    return total_issues

def schema_diff(noteType):
    """Detect drift between schema and actual note usage."""
    notes = get_notes_of_type(noteType)
    schema_fm = load_schema(noteType)
    
    if not schema_fm:
        print(f"No schema found for type: {noteType}")
        return
    
    schema_def = schema_fm.get("schema", {})
    schema_version = schema_fm.get("version", 1)
    
    print(f"\n=== Schema Diff: {noteType} (schema v{schema_version}, {len(notes)} notes) ===\n")
    
    # Collect observation categories from all notes
    obs_counter = Counter()
    for path, fm, body, obs in notes:
        for cat in obs.keys():
            obs_counter[cat] += 1
    
    # Known schema fields
    schema_bases = {}
    for field_key in schema_def.keys():
        base = field_key.replace("?", "").replace("(array)", "").replace("(enum)", "").strip()
        is_optional = "?" in field_key
        schema_bases[base] = {"optional": is_optional, "key": field_key}
    
    total = len(notes)
    
    # Fields in notes but NOT in schema
    print("Fields in notes but NOT in schema (candidates for addition):")
    found_new = False
    for cat, count in sorted(obs_counter.items(), key=lambda x: -x[1]):
        if cat not in schema_bases:
            freq = count / total
            print(f"  + {cat}  (used in {count}/{total} notes, {freq:.0%})")
            found_new = True
    if not found_new:
        print("  (none)")
    
    # Schema fields rarely/never used
    print("\nSchema fields rarely used in notes:")
    found_rare = False
    for base, info in schema_bases.items():
        count = obs_counter.get(base, 0)
        freq = count / total if total > 0 else 0
        if freq < 0.5:
            print(f"  ~ {base}  (used in {count}/{total} notes, {freq:.0%})")
            found_rare = True
    if not found_rare:
        print("  (none)")
    
    print(f"\nRecommendation: Consider adding new fields as optional to schema v{schema_version + 1}")
    return obs_counter, schema_bases

# CLI interface
if __name__ == "__main__":
    import ast
    
    if len(sys.argv) < 2:
        print("Usage: basic_memory_tools.py <function> [args_as_json]")
        sys.exit(1)
    
    func_name = sys.argv[1]
    kwargs = {}
    if len(sys.argv) > 2:
        try:
            kwargs = json.loads(sys.argv[2])
        except:
            pass
    
    func_map = {
        "schema_infer": schema_infer,
        "write_note": write_note,
        "edit_note": edit_note,
        "schema_validate": schema_validate,
        "schema_diff": schema_diff,
    }
    
    if func_name not in func_map:
        print(f"Unknown function: {func_name}")
        sys.exit(1)
    
    result = func_map[func_name](**kwargs)
PYEOF

chmod +x /usr/local/bin/basic_memory_tools.py

# Create a convenient wrapper script
cat > /usr/local/bin/memory_tool << 'BASHEOF'
#!/bin/bash
python3 /usr/local/bin/basic_memory_tools.py "$@"
BASHEOF
chmod +x /usr/local/bin/memory_tool

# Create a Python helper that agents can import
cat > /workspace/memory_tools.py << 'PYEOF'
"""
Basic Memory tools - import and call directly.
"""
import sys
sys.path.insert(0, '/usr/local/bin')

from basic_memory_tools import (
    schema_infer,
    write_note,
    edit_note,
    schema_validate,
    schema_diff,
    parse_note,
    load_schema,
    get_notes_of_type,
)

__all__ = [
    'schema_infer', 'write_note', 'edit_note',
    'schema_validate', 'schema_diff',
    'parse_note', 'load_schema', 'get_notes_of_type',
]
PYEOF

echo "=== Basic Memory mock environment ready ==="
echo "Tools available:"
echo "  - Python: from memory_tools import schema_infer, write_note, edit_note, schema_validate, schema_diff"
echo "  - CLI: memory_tool <function> '<json_kwargs>'"
echo ""
echo "Workspace structure:"
find /workspace -name "*.md" | head -30