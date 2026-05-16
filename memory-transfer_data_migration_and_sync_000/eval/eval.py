#!/usr/bin/env python3
"""
Evaluation script for memory-transfer task.
Checks that:
1. The agent used the list command to inspect memories (indirectly — we check they transferred the correct file)
2. A dry-run was performed (we check for a dry-run log file OR accept its absence as optional check)
3. The specific file 2025-03-15.md was transferred to the analyst workspace
4. The file content matches the source exactly
5. The other research memory files were NOT transferred (selective transfer)
6. The existing analyst memory files were NOT disturbed
"""

import sys
import json
from pathlib import Path

def run_eval(workspace_dir: str):
    checks = []
    total_score = 0.0
    total_weight = 0.0

    OPENCLAW_ROOT = Path("/home/node/.openclaw")
    RESEARCH_WS = OPENCLAW_ROOT / "workspace-research"
    ANALYST_WS = OPENCLAW_ROOT / "workspace-analyst"
    TARGET_FILE = "2025-03-15.md"

    # ── CHECK 1: Target file exists in analyst workspace ────────────────────
    weight = 0.40
    total_weight += weight
    check_name = "target_daily_memory_transferred"
    try:
        target_path = ANALYST_WS / "memory" / TARGET_FILE
        if target_path.exists():
            checks.append({
                "name": check_name,
                "passed": True,
                "detail": f"Found {TARGET_FILE} at expected path: {target_path}"
            })
            total_score += weight
        else:
            checks.append({
                "name": check_name,
                "passed": False,
                "detail": f"File NOT found at {target_path}. Agent failed to transfer the March 15th memory."
            })
    except Exception as e:
        checks.append({
            "name": check_name,
            "passed": False,
            "detail": f"Exception checking target file: {e}"
        })

    # ── CHECK 2: Content of transferred file matches source exactly ─────────
    weight = 0.30
    total_weight += weight
    check_name = "transferred_content_intact"
    try:
        src_path = RESEARCH_WS / "memory" / TARGET_FILE
        tgt_path = ANALYST_WS / "memory" / TARGET_FILE

        if not tgt_path.exists():
            checks.append({
                "name": check_name,
                "passed": False,
                "detail": "Cannot check content — target file does not exist."
            })
        else:
            src_content = src_path.read_text()
            tgt_content = tgt_path.read_text()

            # Key phrases that must be present
            key_phrases = [
                "Q1 Rebalancing Signals",
                "10Y Treasury yield crossed 4.75%",
                "Investment-grade spreads widening",
                "High-yield spreads: +42bps",
                "VIX term structure inversion",
                "Bloomberg Fixed Income Analytics"
            ]
            missing = [p for p in key_phrases if p not in tgt_content]

            if src_content == tgt_content and len(missing) == 0:
                checks.append({
                    "name": check_name,
                    "passed": True,
                    "detail": f"Transferred content is byte-for-byte identical to source. All {len(key_phrases)} key phrases present."
                })
                total_score += weight
            elif len(missing) == 0:
                checks.append({
                    "name": check_name,
                    "passed": True,
                    "detail": f"All {len(key_phrases)} key phrases present (minor whitespace differences acceptable)."
                })
                total_score += weight
            else:
                checks.append({
                    "name": check_name,
                    "passed": False,
                    "detail": f"Content mismatch. Missing key phrases: {missing}"
                })
    except Exception as e:
        checks.append({
            "name": check_name,
            "passed": False,
            "detail": f"Exception verifying content: {e}"
        })

    # ── CHECK 3: Selective transfer — other research daily files NOT copied ──
    weight = 0.15
    total_weight += weight
    check_name = "selective_transfer_only_target_date"
    try:
        analyst_mem_dir = ANALYST_WS / "memory"
        # Files that existed in analyst workspace BEFORE the task
        pre_existing_analyst_files = {"2025-03-08.md", "2025-03-11.md"}
        # Files from research that should NOT have been transferred
        research_only_files = {"2025-03-10.md", "2025-03-12.md", "2025-03-17.md", "2025-03-20.md"}

        if not analyst_mem_dir.exists():
            checks.append({
                "name": check_name,
                "passed": False,
                "detail": "Analyst memory directory does not exist."
            })
        else:
            analyst_files = set(f.name for f in analyst_mem_dir.iterdir() if f.is_file())
            # Unwanted = research files that ended up in analyst (excluding the target)
            unwanted = research_only_files.intersection(analyst_files)

            if len(unwanted) == 0:
                checks.append({
                    "name": check_name,
                    "passed": True,
                    "detail": f"Correct! Only {TARGET_FILE} was transferred. Analyst memory dir contains: {sorted(analyst_files)}"
                })
                total_score += weight
            else:
                checks.append({
                    "name": check_name,
                    "passed": False,
                    "detail": f"Over-transfer detected! These research files were incorrectly copied to analyst: {sorted(unwanted)}"
                })
    except Exception as e:
        checks.append({
            "name": check_name,
            "passed": False,
            "detail": f"Exception checking selective transfer: {e}"
        })

    # ── CHECK 4: Pre-existing analyst memory files are untouched ────────────
    weight = 0.15
    total_weight += weight
    check_name = "existing_analyst_memories_preserved"
    try:
        analyst_mem_dir = ANALYST_WS / "memory"
        pre_existing = {
            "2025-03-08.md": "Portfolio Review",
            "2025-03-11.md": "Stress Test Results"
        }

        all_present = True
        detail_parts = []
        for fname, expected_phrase in pre_existing.items():
            fpath = analyst_mem_dir / fname
            if not fpath.exists():
                all_present = False
                detail_parts.append(f"{fname}: MISSING (was deleted or overwritten)")
            else:
                content = fpath.read_text()
                if expected_phrase in content:
                    detail_parts.append(f"{fname}: OK ('{expected_phrase}' present)")
                else:
                    all_present = False
                    detail_parts.append(f"{fname}: CORRUPTED (expected phrase '{expected_phrase}' not found)")

        if all_present:
            checks.append({
                "name": check_name,
                "passed": True,
                "detail": "All pre-existing analyst memories preserved. " + "; ".join(detail_parts)
            })
            total_score += weight
        else:
            checks.append({
                "name": check_name,
                "passed": False,
                "detail": "Pre-existing analyst memories were disturbed: " + "; ".join(detail_parts)
            })
    except Exception as e:
        checks.append({
            "name": check_name,
            "passed": False,
            "detail": f"Exception checking pre-existing files: {e}"
        })

    # ── Compute final score ──────────────────────────────────────────────────
    final_score = round(total_score / total_weight, 4) if total_weight > 0 else 0.0
    passed = all(c["passed"] for c in checks)

    result = {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)