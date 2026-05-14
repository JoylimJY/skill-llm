#!/usr/bin/env python3
"""
Evaluation script for the Aria-7 identity audit task.
Checks that the agent:
1. Ran neon-soul synthesize --reset with custom --memory-path and --output-path
2. Ran neon-soul audit --stats (or read synthesis-data.json)
3. Ran neon-soul rollback --list (or read backups directory)
4. Produced aria-7-identity-audit.json with correct structure and content
"""
import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ─── Check 1: SOUL.md was generated at the custom path ───────────────────
    try:
        soul_path = workspace / "agents" / "aria-7" / "soul-output" / "SOUL.md"
        if soul_path.exists():
            soul_content = soul_path.read_text()
            has_content = len(soul_content.strip()) > 100
            total_score += add_check(
                "SOUL.md generated at custom output path",
                has_content,
                f"SOUL.md found at {soul_path}, length={len(soul_content)} chars" if has_content
                else f"SOUL.md exists but is nearly empty ({len(soul_content)} chars)"
            )
        else:
            # Also check if it was written at workspace root (agent may have used default)
            alt_path = workspace / "SOUL.md"
            if alt_path.exists():
                total_score += add_check(
                    "SOUL.md generated at custom output path",
                    False,
                    f"SOUL.md found at default path ({alt_path}) instead of required custom path (agents/aria-7/soul-output/SOUL.md). Agent did not use --output-path flag."
                )
            else:
                total_score += add_check(
                    "SOUL.md generated at custom output path",
                    False,
                    "SOUL.md not found at custom path or default path. Synthesis may not have run."
                )
    except Exception as e:
        total_score += add_check("SOUL.md generated at custom output path", False, f"Exception: {e}")

    # ─── Check 2: .neon-soul state was reset (caches cleared) ────────────────
    try:
        state_path = workspace / ".neon-soul" / "state.json"
        if state_path.exists():
            state = json.loads(state_path.read_text())
            # After --reset, the stale marker should be gone and timestamp should be recent
            is_stale = state.get("stale", False)
            old_model = state.get("model", "") == "llama2:7b"
            # The timestamp should be different from the stale 2024-01-01
            last_syn = state.get("lastSynthesis", "")
            was_reset = not is_stale and "2024-01-01" not in last_syn
            total_score += add_check(
                "State was reset (--reset flag used)",
                was_reset,
                f"state.json model={state.get('model','?')}, stale={is_stale}, lastSynthesis={last_syn}"
            )
        else:
            total_score += add_check(
                "State was reset (--reset flag used)",
                False,
                "state.json not found — synthesis may not have completed"
            )
    except Exception as e:
        total_score += add_check("State was reset (--reset flag used)", False, f"Exception: {e}")

    # ─── Check 3: synthesis-data.json has signals/principles/axioms ──────────
    try:
        synth_path = workspace / ".neon-soul" / "synthesis-data.json"
        if synth_path.exists():
            synth_data = json.loads(synth_path.read_text())
            signals = synth_data.get("signals", [])
            axioms = synth_data.get("axioms", [])
            is_stale = synth_data.get("meta", {}).get("stale", False)
            has_data = len(signals) > 0 and not is_stale
            total_score += add_check(
                "synthesis-data.json populated with fresh signals and axioms",
                has_data,
                f"signals={len(signals)}, axioms={len(axioms)}, stale={is_stale}"
            )
        else:
            total_score += add_check(
                "synthesis-data.json populated with fresh signals and axioms",
                False,
                "synthesis-data.json not found"
            )
    except Exception as e:
        total_score += add_check("synthesis-data.json populated with fresh signals and axioms", False, f"Exception: {e}")

    # ─── Check 4: aria-7-identity-audit.json exists ────────────────────────
    report_path = None
    try:
        candidates = list(workspace.rglob("aria-7-identity-audit.json"))
        if candidates:
            report_path = candidates[0]
            total_score += add_check(
                "aria-7-identity-audit.json report file exists",
                True,
                f"Found at {report_path}"
            )
        else:
            total_score += add_check(
                "aria-7-identity-audit.json report file exists",
                False,
                "aria-7-identity-audit.json not found anywhere in workspace"
            )
    except Exception as e:
        total_score += add_check("aria-7-identity-audit.json report file exists", False, f"Exception: {e}")

    # ─── Check 5: Report has correct top-level structure ─────────────────────
    report = None
    if report_path:
        try:
            report_text = report_path.read_text()
            report = json.loads(report_text)
            required_keys = {"agent_name", "synthesis_summary", "audit_stats", "backup_history"}
            present_keys = set(report.keys())
            has_structure = required_keys.issubset(present_keys)
            total_score += add_check(
                "Report has required top-level keys",
                has_structure,
                f"Required: {required_keys}, Present: {present_keys}"
            )
        except json.JSONDecodeError as e:
            total_score += add_check(
                "Report has required top-level keys",
                False,
                f"aria-7-identity-audit.json is not valid JSON: {e}"
            )
        except Exception as e:
            total_score += add_check("Report has required top-level keys", False, f"Exception: {e}")
    else:
        total_score += add_check("Report has required top-level keys", False, "Report file missing, skipping structure check")

    # ─── Check 6: agent_name is "Aria-7" in the report ───────────────────────
    if report:
        try:
            agent_name = report.get("agent_name", "")
            correct_name = "aria" in agent_name.lower() or "aria-7" in agent_name.lower()
            total_score += add_check(
                "Report identifies agent as Aria-7",
                correct_name,
                f"agent_name='{agent_name}'"
            )
        except Exception as e:
            total_score += add_check("Report identifies agent as Aria-7", False, f"Exception: {e}")
    else:
        total_score += add_check("Report identifies agent as Aria-7", False, "Report missing")

    # ─── Check 7: audit_stats contains tier/dimension breakdown ──────────────
    if report:
        try:
            audit_stats = report.get("audit_stats", {})
            has_tiers = any(k in str(audit_stats).lower() for k in ["tier", "axiom", "signal", "principle"])
            has_dims = any(k in str(audit_stats).lower() for k in ["dimension", "cognitive", "epistemic", "values", "soulcraft"])
            has_counts = isinstance(audit_stats, dict) and len(audit_stats) > 0
            audit_valid = has_tiers or has_dims or has_counts
            total_score += add_check(
                "audit_stats contains tier/dimension/count data from neon-soul audit",
                audit_valid,
                f"audit_stats type={type(audit_stats).__name__}, "
                f"has_tiers={has_tiers}, has_dims={has_dims}, has_counts={has_counts}, "
                f"keys={list(audit_stats.keys()) if isinstance(audit_stats, dict) else 'N/A'}"
            )
        except Exception as e:
            total_score += add_check("audit_stats contains tier/dimension/count data from neon-soul audit", False, f"Exception: {e}")
    else:
        total_score += add_check("audit_stats contains tier/dimension/count data from neon-soul audit", False, "Report missing")

    # ─── Check 8: backup_history lists the pre-existing backups ─────────────
    if report:
        try:
            backup_history = report.get("backup_history", [])
            # We seeded 2 backups: 2024-01-01T120000Z and 2024-02-15T083000Z
            backup_str = str(backup_history).lower()
            found_backups = (
                "2024-01-01" in backup_str or
                "120000" in backup_str or
                "2024-02-15" in backup_str or
                "083000" in backup_str or
                (isinstance(backup_history, list) and len(backup_history) >= 2)
            )
            total_score += add_check(
                "backup_history reflects actual backups from rollback --list",
                found_backups,
                f"backup_history type={type(backup_history).__name__}, "
                f"count={len(backup_history) if isinstance(backup_history, list) else 'N/A'}, "
                f"content_sample={str(backup_history)[:200]}"
            )
        except Exception as e:
            total_score += add_check("backup_history reflects actual backups from rollback --list", False, f"Exception: {e}")
    else:
        total_score += add_check("backup_history reflects actual backups from rollback --list", False, "Report missing")

    # ─── Check 9: synthesis_summary mentions axioms or signals ───────────────
    if report:
        try:
            summary = report.get("synthesis_summary", "")
            summary_str = str(summary).lower()
            has_soul_terms = any(t in summary_str for t in ["axiom", "signal", "pattern", "soul", "identity", "principle", "synthesis"])
            total_score += add_check(
                "synthesis_summary contains meaningful soul synthesis content",
                has_soul_terms and len(summary_str) > 30,
                f"synthesis_summary length={len(summary_str)}, has_terms={has_soul_terms}, preview='{str(summary)[:200]}'"
            )
        except Exception as e:
            total_score += add_check("synthesis_summary contains meaningful soul synthesis content", False, f"Exception: {e}")
    else:
        total_score += add_check("synthesis_summary contains meaningful soul synthesis content", False, "Report missing")

    # ─── Check 10: Memory path was correctly targeted (not default) ──────────
    try:
        # The default memory path is memory/ — agent must have used agents/aria-7/memory-logs/
        default_mem = workspace / "memory"
        custom_mem = workspace / "agents" / "aria-7" / "memory-logs"
        # If synthesis ran correctly, synthesis-data.json should reference the custom path files
        if (workspace / ".neon-soul" / "synthesis-data.json").exists():
            synth_text = (workspace / ".neon-soul" / "synthesis-data.json").read_text()
            # Check for references to actual memory file names we created
            memory_file_names = ["session-2024-01-15", "session-2024-01-22", "session-2024-02-03",
                                  "reflection-core-values", "preferences-2024", "diary-2024-q1"]
            found_refs = sum(1 for f in memory_file_names if f in synth_text)
            # Even partial match is good
            used_custom_path = found_refs >= 1 or "aria-7" in synth_text or "memory-logs" in synth_text
            total_score += add_check(
                "Custom --memory-path (agents/aria-7/memory-logs) was used",
                used_custom_path,
                f"Found {found_refs}/6 custom memory file references in synthesis-data.json"
            )
        else:
            # Check if SOUL.md references them
            if soul_path.exists() if 'soul_path' in dir() else False:
                soul_text = soul_path.read_text()
                found = any(f in soul_text for f in ["precision over speed", "transparency", "deep focus"])
                total_score += add_check(
                    "Custom --memory-path (agents/aria-7/memory-logs) was used",
                    found,
                    f"SOUL.md contains expected patterns from custom memory: {found}"
                )
            else:
                total_score += add_check(
                    "Custom --memory-path (agents/aria-7/memory-logs) was used",
                    False,
                    "Cannot verify — synthesis-data.json and SOUL.md both missing/empty"
                )
    except Exception as e:
        total_score += add_check("Custom --memory-path (agents/aria-7/memory-logs) was used", False, f"Exception: {e}")

    # ─── Final scoring ────────────────────────────────────────────────────────
    num_checks = len(checks)
    final_score = total_score / num_checks if num_checks > 0 else 0.0
    passed = final_score >= 0.6  # Must pass at least 6/10 checks

    result = {
        "passed": passed,
        "score": round(final_score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace_dir)