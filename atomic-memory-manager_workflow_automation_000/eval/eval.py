import sys
import json
import os
import re
from pathlib import Path
from datetime import date

def load_file(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return None

def run_eval(workspace):
    checks = []
    score_parts = []

    memory_md_path = Path(workspace) / "MEMORY.md"
    daily_path = Path(workspace) / "memory" / "2025-06-14.md"

    # ── Load files ───────────────────────────────────────────────────────────
    memory_md = load_file(memory_md_path)
    daily_note = load_file(daily_path)

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 1: memory/2025-06-14.md exists
    # ══════════════════════════════════════════════════════════════════════════
    c1_passed = daily_note is not None
    checks.append({
        "name": "daily_note_file_exists",
        "passed": c1_passed,
        "detail": "memory/2025-06-14.md must exist for today's session notes." if c1_passed
                  else "memory/2025-06-14.md not found. Day-specific events must go in the dated daily file."
    })
    score_parts.append(1.0 if c1_passed else 0.0)

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 2: Daily note contains batch 7 sequencing readiness fact
    # ══════════════════════════════════════════════════════════════════════════
    batch7_in_daily = False
    if daily_note:
        # Accept any note that mentions batch 7 and sequencing (ready/confirmed)
        has_batch7 = bool(re.search(r'batch\s*7', daily_note, re.IGNORECASE))
        has_seq = bool(re.search(r'sequenc', daily_note, re.IGNORECASE))
        has_ready = bool(re.search(r'ready|confirmed|approved|cleared', daily_note, re.IGNORECASE))
        batch7_in_daily = has_batch7 and has_seq and has_ready
    checks.append({
        "name": "daily_note_contains_batch7_sequencing",
        "passed": batch7_in_daily,
        "detail": "memory/2025-06-14.md should record that sample batch 7 is confirmed ready for sequencing." if batch7_in_daily
                  else f"memory/2025-06-14.md missing batch 7 sequencing confirmation. Content: {repr(daily_note[:300]) if daily_note else 'FILE MISSING'}"
    })
    score_parts.append(1.0 if batch7_in_daily else 0.0)

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 3: MEMORY.md contains Bayesian preference (standing preference → MEMORY.md)
    # ══════════════════════════════════════════════════════════════════════════
    bayesian_in_memory = False
    if memory_md:
        has_bayesian = bool(re.search(r'bayesian', memory_md, re.IGNORECASE))
        # Should be a preference/method note, not just a mention
        has_stat = bool(re.search(r'stat|method|inference|analysis|preferred', memory_md, re.IGNORECASE))
        bayesian_in_memory = has_bayesian and has_stat
    checks.append({
        "name": "memory_md_contains_bayesian_preference",
        "passed": bayesian_in_memory,
        "detail": "MEMORY.md should record the standing preference for Bayesian statistical methods." if bayesian_in_memory
                  else f"MEMORY.md missing Bayesian inference preference. Content snippet: {repr(memory_md[:400]) if memory_md else 'FILE MISSING'}"
    })
    score_parts.append(1.0 if bayesian_in_memory else 0.0)

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 4: Batch 7 event NOT written to MEMORY.md (wrong destination)
    # ══════════════════════════════════════════════════════════════════════════
    batch7_not_in_memory_md = True
    if memory_md:
        # Batch 7 sequencing readiness is a one-off event, must NOT be in MEMORY.md
        has_b7 = bool(re.search(r'batch\s*7.*sequenc|sequenc.*batch\s*7', memory_md, re.IGNORECASE))
        # Allow if it's a general rule, not the specific event
        has_specific_event = bool(re.search(r'batch\s*7.*ready|batch\s*7.*confirmed|confirmed.*batch\s*7.*sequenc', memory_md, re.IGNORECASE))
        if has_specific_event:
            batch7_not_in_memory_md = False
    checks.append({
        "name": "batch7_event_not_in_MEMORY_md",
        "passed": batch7_not_in_memory_md,
        "detail": "Batch 7 readiness is a one-off event and must NOT be in MEMORY.md (wrong destination)." if batch7_not_in_memory_md
                  else "MEMORY.md incorrectly contains the batch 7 sequencing event. One-off events belong in dated daily notes."
    })
    score_parts.append(1.0 if batch7_not_in_memory_md else 0.0)

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 5: Bayesian preference NOT written to daily note (wrong destination)
    # ══════════════════════════════════════════════════════════════════════════
    bayesian_not_in_daily = True
    if daily_note:
        # Bayesian pref is a standing preference, should NOT be ONLY in daily
        # It's okay if it mentions it in passing, but it must not be the primary home
        # We check: is it listed as a preference/decision in daily? That's wrong.
        has_bayesian_pref_in_daily = bool(re.search(r'prefer.*bayesian|bayesian.*prefer|stat.*method.*bayesian|bayesian.*stat.*method', daily_note, re.IGNORECASE))
        if has_bayesian_pref_in_daily:
            bayesian_not_in_daily = False
    checks.append({
        "name": "bayesian_preference_not_primary_in_daily_note",
        "passed": bayesian_not_in_daily,
        "detail": "Standing preference (Bayesian stats) must live in MEMORY.md, not only in a dated daily note." if bayesian_not_in_daily
                  else "Daily note seems to be the primary location for the Bayesian preference. Standing preferences belong in MEMORY.md."
    })
    score_parts.append(1.0 if bayesian_not_in_daily else 0.0)

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 6: Trivial throwaway fact (coffee machine) NOT written anywhere in memory
    # ══════════════════════════════════════════════════════════════════════════
    coffee_not_written = True
    all_memory_files = list(Path(workspace).glob("memory/*.md")) + [memory_md_path]
    for mf in all_memory_files:
        content = load_file(mf)
        if content and bool(re.search(r'coffee', content, re.IGNORECASE)):
            # Check if it's a NEW write (the original daily had it, but only in 2025-06-12.md)
            if str(mf) != str(Path(workspace) / "memory" / "2025-06-12.md"):
                coffee_not_written = False
                break
    checks.append({
        "name": "trivial_coffee_fact_not_newly_recorded",
        "passed": coffee_not_written,
        "detail": "The coffee machine comment is trivial scratch and must NOT be written into any new memory file." if coffee_not_written
                  else "A trivial/throwaway fact (coffee machine) was incorrectly written into a memory file."
    })
    score_parts.append(1.0 if coffee_not_written else 0.0)

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 7: Original MEMORY.md content preserved (not wiped/truncated)
    # ══════════════════════════════════════════════════════════════════════════
    original_preserved = False
    if memory_md:
        has_hoffmann = bool(re.search(r'hoffmann', memory_md, re.IGNORECASE))
        has_kras = bool(re.search(r'KRAS', memory_md, re.IGNORECASE))
        has_nextflow = bool(re.search(r'nextflow', memory_md, re.IGNORECASE))
        original_preserved = has_hoffmann and has_kras and has_nextflow
    checks.append({
        "name": "original_memory_md_content_preserved",
        "passed": original_preserved,
        "detail": "Original MEMORY.md standing facts (Hoffmann, KRAS, Nextflow) must still be present after editing." if original_preserved
                  else f"Original MEMORY.md content appears corrupted or truncated. Snippet: {repr(memory_md[:300]) if memory_md else 'FILE MISSING'}"
    })
    score_parts.append(1.0 if original_preserved else 0.0)

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 8: Bayesian note is concise (not a paragraph of commentary)
    # ══════════════════════════════════════════════════════════════════════════
    bayesian_concise = True
    if memory_md and bayesian_in_memory:
        # Find lines mentioning bayesian
        lines = memory_md.splitlines()
        bayesian_lines = [l for l in lines if re.search(r'bayesian', l, re.IGNORECASE)]
        # Each bayesian line should be short (under 200 chars) — no multi-sentence rambling
        for bl in bayesian_lines:
            if len(bl.strip()) > 200:
                bayesian_concise = False
                break
            # Check for multiple sentences (more than 2 sentence-ending punctuation)
            if len(re.findall(r'[.!?]', bl)) > 2:
                bayesian_concise = False
                break
    checks.append({
        "name": "bayesian_note_is_concise",
        "passed": bayesian_concise,
        "detail": "Bayesian preference note is concise and factual." if bayesian_concise
                  else "Bayesian preference note is too verbose. Notes should be the smallest useful fact, not commentary."
    })
    score_parts.append(1.0 if bayesian_concise else 0.0)

    # ── Final score ──────────────────────────────────────────────────────────
    total = sum(score_parts)
    max_score = len(score_parts)
    final_score = round(total / max_score, 4)
    passed = total >= (max_score * 0.875)  # 7/8 checks must pass

    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))