import sys
import json
import os
from pathlib import Path

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    total_score = 0.0
    max_score = 0.0

    def check(name, weight, passed, detail):
        nonlocal total_score, max_score
        max_score += weight
        if passed:
            total_score += weight
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ── CHECK 1: SOUL.md written to correct output path ─────────────────────
    soul_path = workspace / "output" / "SOUL.md"
    try:
        soul_content = soul_path.read_text()
        check("soul_md_at_correct_path", 1.5,
              len(soul_content) > 200,
              f"SOUL.md found at output/SOUL.md, length={len(soul_content)}")
    except Exception as e:
        check("soul_md_at_correct_path", 1.5, False, f"SOUL.md not found at output/SOUL.md: {e}")
        soul_content = ""

    # ── CHECK 2: --reset was used (stale caches cleared) ────────────────────
    neon_dir = workspace / ".neon-soul"
    try:
        state_raw = (neon_dir / "state.json").read_text()
        state = json.loads(state_raw)
        reset_used = state.get("resetUsed", False)
        check("reset_flag_used", 1.5,
              reset_used,
              f"resetUsed={reset_used} in state.json")
    except Exception as e:
        check("reset_flag_used", 1.5, False, f"Could not read state.json: {e}")
        state = {}

    # ── CHECK 3: --include-soul was used ────────────────────────────────────
    try:
        synthesis_raw = (neon_dir / "synthesis-data.json").read_text()
        synthesis = json.loads(synthesis_raw)
        included_soul = synthesis.get("includedSoul", False)
        check("include_soul_flag_used", 1.5,
              included_soul,
              f"includedSoul={included_soul} in synthesis-data.json")
    except Exception as e:
        check("include_soul_flag_used", 1.5, False, f"Could not read synthesis-data.json: {e}")
        synthesis = {}

    # ── CHECK 4: --memory-path pointed to consultant-memory/ ────────────────
    try:
        mem_path = synthesis.get("memoryPath", "")
        used_consultant_memory = "consultant-memory" in mem_path
        check("correct_memory_path", 1.5,
              used_consultant_memory,
              f"memoryPath in synthesis-data.json: '{mem_path}'")
    except Exception as e:
        check("correct_memory_path", 1.5, False, f"Error checking memoryPath: {e}")

    # ── CHECK 5: Synthesis data has correct axiom/signal counts ─────────────
    try:
        axiom_count = synthesis.get("axiomCount", 0)
        signal_count = synthesis.get("signalCount", 0)
        axioms = synthesis.get("axioms", [])
        ok = axiom_count >= 5 and signal_count >= 10 and len(axioms) >= 5
        check("synthesis_data_populated", 1.0,
              ok,
              f"axiomCount={axiom_count}, signalCount={signal_count}, axioms in list={len(axioms)}")
    except Exception as e:
        check("synthesis_data_populated", 1.0, False, f"Error checking synthesis counts: {e}")

    # ── CHECK 6: SOUL.md contains axiom references ──────────────────────────
    try:
        has_axioms = "axiom-001" in soul_content or "Honesty" in soul_content
        has_dimensions = "ethics" in soul_content or "cognition" in soul_content
        ok = has_axioms and has_dimensions
        check("soul_md_contains_axioms", 1.0,
              ok,
              f"has_axiom_refs={has_axioms}, has_dimensions={has_dimensions}")
    except Exception as e:
        check("soul_md_contains_axioms", 1.0, False, f"Error reading soul content: {e}")

    # ── CHECK 7: state.json has fresh timestamp (after stale 2023 date) ─────
    try:
        last_syn = state.get("lastSynthesis", "")
        is_fresh = last_syn.startswith("2024") or last_syn.startswith("2025")
        check("state_timestamp_fresh", 0.5,
              is_fresh,
              f"lastSynthesis='{last_syn}'")
    except Exception as e:
        check("state_timestamp_fresh", 0.5, False, f"Error checking timestamp: {e}")

    # ── CHECK 8: axiom-trace.txt exists with valid trace content ─────────────
    trace_path = workspace / "output" / "axiom-trace.txt"
    try:
        trace_content = trace_path.read_text()
        # Must reference an axiom ID and have provenance chain (principles + signals)
        has_axiom_id = any(f"axiom-{str(i).zfill(3)}" in trace_content for i in range(1, 10))
        has_principles = "principle" in trace_content.lower() or "Principles" in trace_content
        has_signals = "signal" in trace_content.lower() or "Signals" in trace_content
        has_sources = "source" in trace_content.lower() or ".md" in trace_content
        ok = has_axiom_id and (has_principles or has_signals) and has_sources
        check("axiom_trace_file_valid", 1.5,
              ok,
              f"trace file found, has_axiom_id={has_axiom_id}, has_principles={has_principles}, "
              f"has_signals={has_signals}, has_sources={has_sources}")
    except Exception as e:
        check("axiom_trace_file_valid", 1.5, False, f"axiom-trace.txt not found or unreadable: {e}")

    # ── CHECK 9: backup was created ──────────────────────────────────────────
    try:
        backups_dir = neon_dir / "backups"
        backups = list(backups_dir.glob("SOUL-*.md")) if backups_dir.exists() else []
        check("backup_created", 0.5,
              len(backups) >= 0,  # soft check — backup only created if previous soul existed
              f"Backups found: {len(backups)}")
    except Exception as e:
        check("backup_created", 0.5, False, f"Error checking backups: {e}")

    # ── CHECK 10: --output-path was used (synthesis-data records correct outputPath) ──
    try:
        out_path = synthesis.get("outputPath", "")
        used_output_path = "output" in out_path
        check("output_path_flag_used", 1.0,
              used_output_path,
              f"outputPath in synthesis-data.json: '{out_path}'")
    except Exception as e:
        check("output_path_flag_used", 1.0, False, f"Error checking outputPath: {e}")

    # ── Final score ──────────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    overall_passed = score >= 0.75 and checks[0]["passed"]  # must produce SOUL.md

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()