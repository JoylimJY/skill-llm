#!/usr/bin/env python3
"""
Evaluation script for the obsidian-cli research note management task.
Checks:
1. Default vault is set to research_vault (or its path)
2. Note "qe-review-final.md" exists in the vault
3. Note "quantum-entanglement-review.md" does NOT exist in the vault
4. The final note content contains the original body text AND the appended section
5. Frontmatter has 'status' = 'draft'
6. Frontmatter has 'tags' containing 'quantum' and 'physics'
7. Frontmatter does NOT have 'author' key
"""

import sys
import json
import subprocess
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def load_config():
    config_path = Path("/root/.openclaw/config.json")
    if not config_path.exists():
        return None
    return json.loads(config_path.read_text())

def parse_frontmatter(content):
    """Returns (frontmatter_dict, body_str) or ({}, content)"""
    if not yaml:
        return {}, content
    if content.startswith("---\n"):
        end = content.find("\n---\n", 4)
        if end != -1:
            fm_text = content[4:end]
            try:
                fm = yaml.safe_load(fm_text) or {}
            except Exception:
                fm = {}
            body = content[end+5:]
            return fm, body
    return {}, content

VAULT_PATH = Path("/workspace/research_vault")
FINAL_NOTE = VAULT_PATH / "qe-review-final.md"
ORIGINAL_NOTE = VAULT_PATH / "quantum-entanglement-review.md"

checks = []

# CHECK 1: Default vault is set to research_vault
def check_default_vault():
    cfg = load_config()
    if cfg is None:
        return False, "Config file not found at /root/.openclaw/config.json"
    default = cfg.get("default_vault", "")
    if not default:
        return False, "default_vault is empty in config"
    # Accept either vault name or path resolution
    vaults = cfg.get("vaults", {})
    resolved_path = vaults.get(default, default)
    rp = Path(resolved_path)
    expected = VAULT_PATH.resolve()
    if rp.resolve() == expected or default == "research_vault":
        return True, f"Default vault correctly set to '{default}' -> {resolved_path}"
    return False, f"Default vault is '{default}' -> {resolved_path}, expected research_vault at {VAULT_PATH}"

checks.append(run_check("default_vault_set", check_default_vault))

# CHECK 2: Final note exists
def check_final_note_exists():
    if FINAL_NOTE.exists():
        return True, f"Found: {FINAL_NOTE}"
    # Search recursively just in case it was placed in a subdirectory
    found = list(VAULT_PATH.rglob("qe-review-final.md"))
    if found:
        return True, f"Found at non-standard path: {found[0]}"
    return False, f"Note 'qe-review-final.md' not found in vault"

checks.append(run_check("final_note_exists", check_final_note_exists))

# CHECK 3: Original note does NOT exist (was moved/renamed)
def check_original_note_gone():
    if ORIGINAL_NOTE.exists():
        return False, f"Original note 'quantum-entanglement-review.md' still exists — should have been renamed"
    found = list(VAULT_PATH.rglob("quantum-entanglement-review.md"))
    if found:
        return False, f"Original note still exists at: {found[0]}"
    return True, "Original note 'quantum-entanglement-review.md' correctly removed (renamed)"

checks.append(run_check("original_note_removed", check_original_note_gone))

# CHECK 4: Final note has original content AND appended content
def check_note_content():
    found = list(VAULT_PATH.rglob("qe-review-final.md"))
    if not found:
        return False, "Note not found, cannot check content"
    content = found[0].read_text()
    _, body = parse_frontmatter(content)
    body_lower = body.lower()
    
    # The note should have some initial research content
    has_initial = any(kw in body_lower for kw in [
        "quantum", "entanglement", "review", "introduction", "abstract", "overview"
    ])
    # The note should have an appended conclusions/summary section
    has_appended = any(kw in body_lower for kw in [
        "conclusion", "summary", "result", "finding", "final"
    ])
    
    if has_initial and has_appended:
        return True, f"Note contains both original content and appended section (body length: {len(body)} chars)"
    elif not has_initial:
        return False, f"Note seems to be missing initial research content. Body snippet: {body[:200]!r}"
    else:
        return False, f"Note seems to be missing appended conclusions/summary. Body snippet: {body[:400]!r}"

checks.append(run_check("note_content_complete", check_note_content))

# CHECK 5: Frontmatter has status=draft
def check_fm_status():
    found = list(VAULT_PATH.rglob("qe-review-final.md"))
    if not found:
        return False, "Note not found"
    content = found[0].read_text()
    fm, _ = parse_frontmatter(content)
    if not fm:
        return False, "No frontmatter found in note"
    status = fm.get("status", None)
    if status == "draft":
        return True, f"status='draft' correctly set"
    return False, f"Expected status='draft', got status={status!r}. Full frontmatter: {fm}"

checks.append(run_check("frontmatter_status_draft", check_fm_status))

# CHECK 6: Frontmatter has tags containing quantum and physics
def check_fm_tags():
    found = list(VAULT_PATH.rglob("qe-review-final.md"))
    if not found:
        return False, "Note not found"
    content = found[0].read_text()
    fm, _ = parse_frontmatter(content)
    if not fm:
        return False, "No frontmatter found in note"
    tags = fm.get("tags", None)
    if tags is None:
        return False, f"'tags' key not found in frontmatter. Full FM: {fm}"
    tags_str = str(tags).lower()
    has_quantum = "quantum" in tags_str
    has_physics = "physics" in tags_str
    if has_quantum and has_physics:
        return True, f"tags correctly contain 'quantum' and 'physics': {tags!r}"
    missing = []
    if not has_quantum:
        missing.append("quantum")
    if not has_physics:
        missing.append("physics")
    return False, f"tags missing: {missing}. Got: {tags!r}"

checks.append(run_check("frontmatter_tags_correct", check_fm_tags))

# CHECK 7: Frontmatter does NOT have 'author' key
def check_fm_no_author():
    found = list(VAULT_PATH.rglob("qe-review-final.md"))
    if not found:
        return False, "Note not found"
    content = found[0].read_text()
    fm, _ = parse_frontmatter(content)
    if not fm:
        # If there's no frontmatter at all, author is certainly absent
        return True, "No frontmatter (author key absent by default)"
    if "author" in fm:
        return False, f"'author' key still present in frontmatter with value: {fm['author']!r}"
    return True, "'author' key correctly absent from frontmatter"

checks.append(run_check("frontmatter_author_deleted", check_fm_no_author))

# ── Scoring ──────────────────────────────────────────────────────────────────
passed_checks = sum(1 for c in checks if c["passed"])
total_checks = len(checks)
score = passed_checks / total_checks
all_passed = passed_checks == total_checks

result = {
    "passed": all_passed,
    "score": round(score, 4),
    "checks": checks
}

print(json.dumps(result, indent=2))
sys.exit(0 if all_passed else 1)