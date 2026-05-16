import sys
import json
import subprocess
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    memory_dir = Path(workspace) / "memory"
    index_path = memory_dir / ".index.json"

    # ── Check 1: .index.json exists ──────────────────────────────────────────
    try:
        assert index_path.exists(), "Index file does not exist"
        checks.append({"name": "index_file_exists", "passed": True,
                        "detail": f"{index_path} found"})
    except AssertionError as e:
        checks.append({"name": "index_file_exists", "passed": False, "detail": str(e)})
        # Cannot proceed without index
        return checks

    # ── Load the index ────────────────────────────────────────────────────────
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except Exception as e:
        checks.append({"name": "index_parseable", "passed": False,
                        "detail": f"Failed to parse index: {e}"})
        return checks
    checks.append({"name": "index_parseable", "passed": True,
                   "detail": f"Index has {len(index)} entries"})

    # ── Check 2: Stale entry for old_batch_record_q3_2025.md was cleaned ─────
    stale_key = "old_batch_record_q3_2025.md"
    stale_cleaned = stale_key not in index
    checks.append({
        "name": "stale_entry_cleaned",
        "passed": stale_cleaned,
        "detail": (
            f"Orphaned entry '{stale_key}' successfully removed from index"
            if stale_cleaned else
            f"Orphaned entry '{stale_key}' still present in index — --clean was not run"
        )
    })

    # ── Check 3: All 11 remaining memory files are indexed ───────────────────
    expected_files = {
        "compound_alpha_synthesis.md",
        "compound_beta_toxicity.md",
        "protein_binding_assay.md",
        "analytical_method_validation.md",
        "stability_study_alpha.md",
        "in_vivo_pk_study.md",
        "formulation_notes.md",
        "regulatory_strategy.md",
        "compound_alpha_synthesis_copy1.md",
        "compound_alpha_synthesis_copy2.md",
        "protein_binding_assay_dup.md",
    }
    indexed_files = set(index.keys())
    missing = expected_files - indexed_files
    checks.append({
        "name": "all_active_files_indexed",
        "passed": len(missing) == 0,
        "detail": (
            f"All 11 active files indexed"
            if not missing else
            f"Missing from index: {sorted(missing)}"
        )
    })

    # ── Check 4: Deduplication was applied — duplicate files have FEWER chunks
    # compound_alpha_synthesis_copy1 and _copy2 are exact duplicates of the original.
    # After dedup, their chunk lists should be EMPTY (all chunks already seen from original).
    try:
        orig_chunks = index.get("compound_alpha_synthesis.md", {}).get("chunks", [])
        copy1_chunks = index.get("compound_alpha_synthesis_copy1.md", {}).get("chunks", [])
        copy2_chunks = index.get("compound_alpha_synthesis_copy2.md", {}).get("chunks", [])
        # The copies should have 0 deduplicated chunks (all are duplicates)
        dedup_applied = (len(copy1_chunks) == 0 and len(copy2_chunks) == 0 and len(orig_chunks) > 0)
        checks.append({
            "name": "sha256_dedup_applied",
            "passed": dedup_applied,
            "detail": (
                f"Deduplication correct: original has {len(orig_chunks)} chunk(s), "
                f"copy1 has {len(copy1_chunks)}, copy2 has {len(copy2_chunks)}"
                if dedup_applied else
                f"Deduplication NOT applied: original={len(orig_chunks)}, "
                f"copy1={len(copy1_chunks)}, copy2={len(copy2_chunks)}"
            )
        })
    except Exception as e:
        checks.append({"name": "sha256_dedup_applied", "passed": False,
                        "detail": f"Error checking dedup: {e}"})

    # ── Check 5: protein_binding_assay_dup.md also deduped ───────────────────
    try:
        orig_pb = index.get("protein_binding_assay.md", {}).get("chunks", [])
        dup_pb  = index.get("protein_binding_assay_dup.md", {}).get("chunks", [])
        pb_deduped = (len(dup_pb) == 0 and len(orig_pb) > 0)
        checks.append({
            "name": "protein_binding_dup_deduped",
            "passed": pb_deduped,
            "detail": (
                f"protein_binding_assay_dup.md correctly has 0 chunks after dedup "
                f"(original has {len(orig_pb)} chunk(s))"
                if pb_deduped else
                f"protein_binding_assay_dup.md has {len(dup_pb)} chunk(s) — dedup not working"
            )
        })
    except Exception as e:
        checks.append({"name": "protein_binding_dup_deduped", "passed": False,
                        "detail": f"Error: {e}"})

    # ── Check 6: --stats output was captured to a file ───────────────────────
    # Agent is asked to save stats to index_stats.txt
    stats_files = list(Path(workspace).rglob("index_stats.txt"))
    if not stats_files:
        checks.append({"name": "stats_file_exists", "passed": False,
                        "detail": "index_stats.txt not found anywhere in workspace"})
    else:
        stats_text = stats_files[0].read_text(encoding="utf-8", errors="replace")
        has_indexed_files = "indexed files" in stats_text.lower() or "indexed_files" in stats_text.lower()
        has_total_chunks  = "total chunks"  in stats_text.lower() or "total_chunks"  in stats_text.lower()
        has_unique_hashes = "unique" in stats_text.lower()
        all_stats_present = has_indexed_files and has_total_chunks and has_unique_hashes
        checks.append({
            "name": "stats_file_content",
            "passed": all_stats_present,
            "detail": (
                f"stats file at {stats_files[0]} contains required fields"
                if all_stats_present else
                f"stats file at {stats_files[0]} is missing fields. Content: {stats_text[:300]}"
            )
        })

    # ── Check 7: --search "palladium" was run and results saved ──────────────
    search_files = list(Path(workspace).rglob("search_results.txt"))
    if not search_files:
        checks.append({"name": "search_results_file_exists", "passed": False,
                        "detail": "search_results.txt not found anywhere in workspace"})
    else:
        search_text = search_files[0].read_text(encoding="utf-8", errors="replace")
        # palladium appears in compound_alpha_synthesis.md and in_vivo_pk_study.md
        has_result  = "palladium" in search_text.lower()
        has_file_ref = ("compound_alpha_synthesis.md" in search_text or
                        "in_vivo_pk_study.md" in search_text)
        search_correct = has_result and has_file_ref
        checks.append({
            "name": "search_results_content",
            "passed": search_correct,
            "detail": (
                f"search_results.txt correctly contains 'palladium' hits and file references"
                if search_correct else
                f"search_results.txt missing expected content. Found: {search_text[:300]}"
            )
        })

    return checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = run_checks(workspace)

    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4) if total > 0 else 0.0
    all_passed = (passed_count == total)

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()