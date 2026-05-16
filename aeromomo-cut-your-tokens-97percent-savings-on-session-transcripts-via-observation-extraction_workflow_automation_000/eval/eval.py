#!/usr/bin/env python3
"""
Evaluation script for claw-compactor pipeline task.
Checks:
1. claw-compactor-config.json exists at workspace root with correct chars_per_token=3.5
2. memory/.codebook.json exists and is valid JSON with at least some entries (dict step ran)
3. memory/observations/ directory contains at least one .md file (observe step ran)
4. memory/.observed-sessions.json exists (observe step tracking artifact)
5. memory/MEMORY-L0.md exists and is within the ~200 token limit (~800 chars at 4 chars/token, or ~700 chars at 3.5)
6. MEMORY.md has been compressed (smaller than original or codebook entries present)
"""

import sys
import json
import os
from pathlib import Path

def count_tokens_heuristic(text, chars_per_token=4.0):
    return len(text) / chars_per_token

def run_eval(workspace_str):
    workspace = Path(workspace_str)
    checks = []
    total_score = 0.0

    # ── CHECK 1: claw-compactor-config.json exists with chars_per_token=3.5 ──
    check_name = "claw-compactor-config.json exists with chars_per_token=3.5"
    try:
        config_path = workspace / "claw-compactor-config.json"
        if not config_path.exists():
            checks.append({"name": check_name, "passed": False,
                           "detail": "claw-compactor-config.json not found at workspace root"})
        else:
            config = json.loads(config_path.read_text())
            cpt = config.get("chars_per_token")
            if cpt is None:
                checks.append({"name": check_name, "passed": False,
                               "detail": f"chars_per_token key missing from config. Found keys: {list(config.keys())}"})
            elif abs(float(cpt) - 3.5) > 0.01:
                checks.append({"name": check_name, "passed": False,
                               "detail": f"chars_per_token is {cpt}, expected 3.5"})
            else:
                checks.append({"name": check_name, "passed": True,
                               "detail": f"chars_per_token correctly set to {cpt}"})
                total_score += 1.0
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 2: memory/.codebook.json exists and is valid with entries ──
    check_name = "memory/.codebook.json exists and contains dictionary entries"
    try:
        codebook_path = workspace / "memory" / ".codebook.json"
        if not codebook_path.exists():
            checks.append({"name": check_name, "passed": False,
                           "detail": "memory/.codebook.json not found — dict step was not run"})
        else:
            codebook = json.loads(codebook_path.read_text())
            if not isinstance(codebook, dict):
                checks.append({"name": check_name, "passed": False,
                               "detail": f"Codebook is not a dict, got {type(codebook)}"})
            elif len(codebook) == 0:
                checks.append({"name": check_name, "passed": False,
                               "detail": "Codebook is empty — no dictionary encoding was applied"})
            else:
                checks.append({"name": check_name, "passed": True,
                               "detail": f"Codebook has {len(codebook)} entries"})
                total_score += 1.0
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 3: memory/observations/ has at least one markdown file ──
    check_name = "memory/observations/ contains at least one observation .md file"
    try:
        obs_dir = workspace / "memory" / "observations"
        if not obs_dir.exists():
            checks.append({"name": check_name, "passed": False,
                           "detail": "memory/observations/ directory does not exist — observe step not run"})
        else:
            md_files = list(obs_dir.glob("*.md"))
            if len(md_files) == 0:
                # Also check for any files at all
                all_files = list(obs_dir.iterdir())
                checks.append({"name": check_name, "passed": False,
                               "detail": f"No .md files in observations/. Files present: {[f.name for f in all_files]}"})
            else:
                # Verify the files have actual content
                non_empty = [f for f in md_files if f.stat().st_size > 10]
                if not non_empty:
                    checks.append({"name": check_name, "passed": False,
                                   "detail": "Observation .md files exist but appear empty"})
                else:
                    checks.append({"name": check_name, "passed": True,
                                   "detail": f"Found {len(non_empty)} non-empty observation file(s): {[f.name for f in non_empty]}"})
                    total_score += 1.0
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 4: memory/.observed-sessions.json exists ──
    check_name = "memory/.observed-sessions.json tracking artifact exists"
    try:
        obs_sessions_path = workspace / "memory" / ".observed-sessions.json"
        if not obs_sessions_path.exists():
            checks.append({"name": check_name, "passed": False,
                           "detail": "memory/.observed-sessions.json not found — observe step incomplete or not run"})
        else:
            content = obs_sessions_path.read_text().strip()
            if not content:
                checks.append({"name": check_name, "passed": False,
                               "detail": ".observed-sessions.json is empty"})
            else:
                try:
                    data = json.loads(content)
                    checks.append({"name": check_name, "passed": True,
                                   "detail": f".observed-sessions.json exists and is valid JSON: {str(data)[:100]}"})
                    total_score += 1.0
                except json.JSONDecodeError:
                    checks.append({"name": check_name, "passed": False,
                                   "detail": ".observed-sessions.json is not valid JSON"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 5: memory/MEMORY-L0.md exists and is within token budget ──
    check_name = "memory/MEMORY-L0.md exists and is within ~200 token limit"
    try:
        l0_path = workspace / "memory" / "MEMORY-L0.md"
        if not l0_path.exists():
            checks.append({"name": check_name, "passed": False,
                           "detail": "memory/MEMORY-L0.md not found — tiers step was not run"})
        else:
            content = l0_path.read_text()
            char_count = len(content)
            # At 3.5 chars/token (our custom config), 200 tokens = 700 chars
            # At 4.0 chars/token (default), 200 tokens = 800 chars
            # Be lenient: accept up to 250 tokens equivalent = ~1000 chars
            estimated_tokens_35 = char_count / 3.5
            estimated_tokens_40 = char_count / 4.0
            if char_count == 0:
                checks.append({"name": check_name, "passed": False,
                               "detail": "MEMORY-L0.md is empty"})
            elif estimated_tokens_40 > 300:
                checks.append({"name": check_name, "passed": False,
                               "detail": f"MEMORY-L0.md too large: {char_count} chars, ~{estimated_tokens_40:.0f} tokens (limit ~200-250)"})
            else:
                checks.append({"name": check_name, "passed": True,
                               "detail": f"MEMORY-L0.md: {char_count} chars, ~{estimated_tokens_35:.0f} tokens (at 3.5 c/t), ~{estimated_tokens_40:.0f} tokens (at 4 c/t)"})
                total_score += 1.5
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 6: MEMORY.md has been modified (compressed) ──
    check_name = "memory/MEMORY.md was compressed (reduced from original)"
    try:
        memory_path = workspace / "memory" / "MEMORY.md"
        if not memory_path.exists():
            checks.append({"name": check_name, "passed": False,
                           "detail": "memory/MEMORY.md not found at all"})
        else:
            content = memory_path.read_text()
            original_size = 1724  # Approximate char count of original MEMORY_MD
            current_size = len(content)
            # Check for $XX dictionary codes OR reduced size
            has_dollar_codes = any(f"${chr(65+i)}" in content or f"${chr(65+i)}{chr(65+j)}" in content
                                   for i in range(26) for j in range(26))
            # Also look for generic $[A-Z]{2} pattern
            import re
            dollar_codes = re.findall(r'\$[A-Z]{2}', content)
            size_reduced = current_size < original_size * 0.95

            if dollar_codes:
                checks.append({"name": check_name, "passed": True,
                               "detail": f"MEMORY.md contains {len(set(dollar_codes))} unique dictionary codes: {list(set(dollar_codes))[:5]}. Size: {current_size} chars."})
                total_score += 0.5
            elif size_reduced:
                checks.append({"name": check_name, "passed": True,
                               "detail": f"MEMORY.md reduced from ~{original_size} to {current_size} chars ({100*(1-current_size/original_size):.1f}% reduction)"})
                total_score += 0.5
            else:
                checks.append({"name": check_name, "passed": False,
                               "detail": f"MEMORY.md does not appear compressed. Size: {current_size} chars (original ~{original_size}). No dictionary codes found."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── FINAL SCORE ───────────────────────────────────────────────────────────
    max_score = 6.0
    normalized_score = round(total_score / max_score, 3)
    passed = total_score >= 4.0  # Must pass at least 4 out of 6 weighted points

    result = {
        "passed": passed,
        "score": normalized_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "invocation", "passed": False,
                                      "detail": "No workspace path provided"}]}))
        sys.exit(1)
    run_eval(sys.argv[1])