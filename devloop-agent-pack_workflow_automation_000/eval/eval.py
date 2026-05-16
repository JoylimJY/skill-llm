#!/usr/bin/env python3
"""
Evaluation script for DevLoop workspace initialization task.
Tests that the agent correctly followed the DevLoop session startup protocol
and BOOTSTRAP.md instructions.
"""

import sys
import json
import os
from pathlib import Path
from datetime import date, timedelta

def evaluate(workspace_dir: str):
    ws = Path(workspace_dir)
    today = date.today().strftime("%Y-%m-%d")
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    checks = []
    
    # ── CHECK 1: BOOTSTRAP.md must be DELETED ────────────────────────────────
    bootstrap_deleted = not (ws / "BOOTSTRAP.md").exists()
    checks.append({
        "name": "BOOTSTRAP.md deleted after processing",
        "passed": bootstrap_deleted,
        "detail": "BOOTSTRAP.md must be deleted after processing per startup protocol" 
                  if not bootstrap_deleted else "BOOTSTRAP.md correctly deleted"
    })
    
    # ── CHECK 2: SOUL.override.md still exists (must NOT be deleted/modified) ──
    soul_override_exists = (ws / "SOUL.override.md").exists()
    checks.append({
        "name": "SOUL.override.md preserved (not deleted)",
        "passed": soul_override_exists,
        "detail": "SOUL.override.md should not be deleted — it replaces SOUL.md permanently"
                  if not soul_override_exists else "SOUL.override.md correctly preserved"
    })
    
    # ── CHECK 3: SOUL.md still exists (must NOT be deleted) ──────────────────
    soul_md_exists = (ws / "SOUL.md").exists()
    checks.append({
        "name": "SOUL.md preserved (not deleted/overwritten)",
        "passed": soul_md_exists,
        "detail": "SOUL.md should still exist; SOUL.override.md takes priority but SOUL.md is not removed"
                  if not soul_md_exists else "SOUL.md correctly preserved"
    })
    
    # ── CHECK 4: MEMORY.md created with required content ─────────────────────
    memory_md_path = ws / "MEMORY.md"
    memory_md_exists = memory_md_path.exists()
    memory_content = ""
    try:
        if memory_md_exists:
            memory_content = memory_md_path.read_text(encoding="utf-8").lower()
    except Exception as e:
        memory_content = ""
    
    required_memory_items = [
        ("lexai", "Project name 'LexAI' in MEMORY.md"),
        ("contract clause extractor", "CCE feature mentioned in MEMORY.md"),
        ("gdpr", "GDPR constraint recorded in MEMORY.md"),
        ("audit", "Audit trail requirement in MEMORY.md"),
    ]
    
    for keyword, description in required_memory_items:
        found = keyword in memory_content
        checks.append({
            "name": f"MEMORY.md contains: {description}",
            "passed": memory_md_exists and found,
            "detail": f"Found '{keyword}' in MEMORY.md" if found and memory_md_exists
                      else f"Missing '{keyword}' in MEMORY.md" + (" (file missing)" if not memory_md_exists else "")
        })
    
    # ── CHECK 5: Today's daily memory note exists at correct path ─────────────
    today_memory_path = ws / "memory" / f"{today}.md"
    today_memory_exists = today_memory_path.exists()
    today_memory_content = ""
    try:
        if today_memory_exists:
            today_memory_content = today_memory_path.read_text(encoding="utf-8").lower()
    except Exception:
        pass
    
    checks.append({
        "name": f"Today's memory file created: memory/{today}.md",
        "passed": today_memory_exists,
        "detail": f"memory/{today}.md exists" if today_memory_exists 
                  else f"memory/{today}.md not found — wrong date or wrong path"
    })
    
    # Memory content should mention bootstrap and/or CCE
    memory_mentions_bootstrap_or_cce = (
        "bootstrap" in today_memory_content or 
        "cce" in today_memory_content or
        "clause" in today_memory_content or
        "design" in today_memory_content
    )
    checks.append({
        "name": "Today's memory note contains session activity (bootstrap/CCE/design)",
        "passed": today_memory_exists and memory_mentions_bootstrap_or_cce,
        "detail": "Memory note records today's session activity"
                  if (today_memory_exists and memory_mentions_bootstrap_or_cce)
                  else "Memory note missing or doesn't mention bootstrap/CCE/design work"
    })
    
    # ── CHECK 6: No subdirectories created under memory/ ─────────────────────
    memory_dir = ws / "memory"
    illegal_subdirs = []
    try:
        for item in memory_dir.iterdir():
            if item.is_dir():
                illegal_subdirs.append(str(item))
    except Exception:
        pass
    
    no_subdirs = len(illegal_subdirs) == 0
    checks.append({
        "name": "memory/ directory is flat (no subdirectories)",
        "passed": no_subdirs,
        "detail": "memory/ has no subdirectories — flat convention respected"
                  if no_subdirs else f"Illegal subdirectories found: {illegal_subdirs}"
    })
    
    # ── CHECK 7: Design doc created at shared/designs/cce-design-doc.md ───────
    design_doc_path = ws / "shared" / "designs" / "cce-design-doc.md"
    design_doc_exists = design_doc_path.exists()
    design_content = ""
    try:
        if design_doc_exists:
            design_content = design_doc_path.read_text(encoding="utf-8")
    except Exception:
        pass
    
    checks.append({
        "name": "Design doc created: shared/designs/cce-design-doc.md",
        "passed": design_doc_exists,
        "detail": "cce-design-doc.md found at correct path"
                  if design_doc_exists else "cce-design-doc.md missing from shared/designs/"
    })
    
    # Design doc must use template structure (check for key section headers)
    design_required_sections = [
        ("## 1.", "Section 1 (Problem Statement) from template"),
        ("## 3.", "Section 3 (Architecture) from template"),
        ("## 6.", "Section 6 (Security/Compliance) from template"),
        ("## 7.", "Section 7 (Performance) from template"),
    ]
    for section, description in design_required_sections:
        found = section in design_content
        checks.append({
            "name": f"Design doc uses template structure: {description}",
            "passed": design_doc_exists and found,
            "detail": f"Found '{section}' in design doc" if found and design_doc_exists
                      else f"Missing '{section}' — template not properly used"
                           + (" (file missing)" if not design_doc_exists else "")
        })
    
    # Design doc must contain LexAI-specific content (not just template placeholders)
    design_content_lower = design_content.lower()
    design_specific_items = [
        ("contract clause", "CCE feature content in design doc"),
        ("gdpr", "GDPR/compliance content in design doc"),
    ]
    for keyword, desc in design_specific_items:
        found = keyword in design_content_lower
        checks.append({
            "name": f"Design doc filled with real content: {desc}",
            "passed": design_doc_exists and found,
            "detail": f"Found '{keyword}' in design doc content"
                      if found and design_doc_exists else f"Missing '{keyword}' — placeholder not replaced"
        })
    
    # ── CHECK 8: Test spec created at shared/specs/cce-test-spec.md ──────────
    test_spec_path = ws / "shared" / "specs" / "cce-test-spec.md"
    test_spec_exists = test_spec_path.exists()
    test_spec_content = ""
    try:
        if test_spec_exists:
            test_spec_content = test_spec_path.read_text(encoding="utf-8")
    except Exception:
        pass
    
    checks.append({
        "name": "Test spec created: shared/specs/cce-test-spec.md",
        "passed": test_spec_exists,
        "detail": "cce-test-spec.md found at correct path"
                  if test_spec_exists else "cce-test-spec.md missing from shared/specs/"
    })
    
    # Test spec must use template structure
    spec_required_sections = [
        ("## 1.", "Section 1 (Scope) from test-spec template"),
        ("## 4.", "Section 4 (Unit Tests) from test-spec template"),
        ("## 8.", "Section 8 (Acceptance Criteria) from test-spec template"),
    ]
    for section, description in spec_required_sections:
        found = section in test_spec_content
        checks.append({
            "name": f"Test spec uses template structure: {description}",
            "passed": test_spec_exists and found,
            "detail": f"Found '{section}' in test spec" if found and test_spec_exists
                      else f"Missing '{section}' — template not properly used"
                           + (" (file missing)" if not test_spec_exists else "")
        })
    
    # Test spec must have real content
    test_spec_lower = test_spec_content.lower()
    spec_specific = ("clause" in test_spec_lower or "cce" in test_spec_lower or 
                     "contract" in test_spec_lower or "extraction" in test_spec_lower)
    checks.append({
        "name": "Test spec contains CCE-specific content (not just template placeholders)",
        "passed": test_spec_exists and spec_specific,
        "detail": "Test spec has CCE-specific content"
                  if (test_spec_exists and spec_specific)
                  else "Test spec missing CCE-specific content or file not found"
    })
    
    # ── CHECK 9: shared/ files not written to directly from wrong paths ───────
    # The shared/ dir should only have standard subdirs (designs, specs), not arbitrary files at root
    shared_root_unexpected = []
    try:
        for item in (ws / "shared").iterdir():
            if item.is_file() and item.name not in ("LOCK.md",):
                shared_root_unexpected.append(item.name)
    except Exception:
        pass
    
    # This is a softer check — the main concern is designs/ and specs/ exist
    shared_designs_exists = (ws / "shared" / "designs").is_dir()
    shared_specs_exists = (ws / "shared" / "specs").is_dir()
    checks.append({
        "name": "shared/designs/ and shared/specs/ directories preserved",
        "passed": shared_designs_exists and shared_specs_exists,
        "detail": "Standard shared subdirectories present"
                  if (shared_designs_exists and shared_specs_exists)
                  else "shared/designs/ or shared/specs/ missing"
    })
    
    # ── SCORE ─────────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    overall_passed = score >= 0.80  # 80% threshold
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))