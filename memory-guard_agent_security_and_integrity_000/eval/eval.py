#!/usr/bin/env python3
"""
Evaluation script for memory-guard workspace integrity task.
Checks:
1. .memory-guard/hashes.json exists and tracks SOUL.md, AGENTS.md, IDENTITY.md
2. actions.log, rejections.log, handoffs.log exist (three-log pattern)
3. At least two files have provenance stamps with correct [agent|timestamp|confidence|rationale] format
4. actions.log contains evidence of verify being run
5. rejections.log contains evidence of tampering detection
6. audit was run (actions.log should reflect it)
7. hashes.json entries have required fields (hash, initialized_at, size)
"""

import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    ws = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ----------------------------------------------------------------
    # CHECK 1: .memory-guard/hashes.json exists
    # ----------------------------------------------------------------
    hashes_path = ws / ".memory-guard" / "hashes.json"
    try:
        if not hashes_path.exists():
            checks.append({
                "name": "hash_registry_exists",
                "passed": False,
                "detail": f".memory-guard/hashes.json does not exist at {hashes_path}"
            })
            registry = {}
        else:
            with open(hashes_path) as f:
                registry = json.load(f)
            checks.append({
                "name": "hash_registry_exists",
                "passed": True,
                "detail": f".memory-guard/hashes.json found with {len(registry)} entries"
            })
            total_score += 0.15
    except Exception as e:
        checks.append({
            "name": "hash_registry_exists",
            "passed": False,
            "detail": f"Error reading hashes.json: {e}"
        })
        registry = {}

    # ----------------------------------------------------------------
    # CHECK 2: Registry tracks the three critical files
    # ----------------------------------------------------------------
    try:
        required_files = {"SOUL.md", "AGENTS.md", "IDENTITY.md"}
        tracked = set(registry.keys())
        covered = required_files.intersection(tracked)
        all_tracked = required_files.issubset(tracked)
        checks.append({
            "name": "registry_tracks_critical_files",
            "passed": all_tracked,
            "detail": f"Required: {required_files}. Found in registry: {tracked}. Covered: {covered}"
        })
        if all_tracked:
            total_score += 0.15
        elif len(covered) >= 2:
            total_score += 0.05
    except Exception as e:
        checks.append({
            "name": "registry_tracks_critical_files",
            "passed": False,
            "detail": f"Error checking registry keys: {e}"
        })

    # ----------------------------------------------------------------
    # CHECK 3: Registry entries have required fields
    # ----------------------------------------------------------------
    try:
        required_fields = {"hash", "initialized_at", "size"}
        entries_valid = 0
        entries_checked = 0
        for fname, meta in registry.items():
            if fname in {"SOUL.md", "AGENTS.md", "IDENTITY.md"}:
                entries_checked += 1
                meta_keys = set(meta.keys())
                if required_fields.issubset(meta_keys):
                    entries_valid += 1
                    # Validate hash is SHA-256 (64 hex chars)
                    h = meta.get("hash", "")
                    if not re.match(r'^[0-9a-f]{64}$', h):
                        entries_valid -= 1

        all_valid = (entries_checked > 0) and (entries_valid == entries_checked)
        checks.append({
            "name": "registry_entries_have_required_fields",
            "passed": all_valid,
            "detail": f"Checked {entries_checked} critical file entries, {entries_valid} had valid fields (hash/initialized_at/size with valid SHA-256)"
        })
        if all_valid:
            total_score += 0.10
    except Exception as e:
        checks.append({
            "name": "registry_entries_have_required_fields",
            "passed": False,
            "detail": f"Error validating registry entry fields: {e}"
        })

    # ----------------------------------------------------------------
    # CHECK 4: Three-log pattern files exist
    # ----------------------------------------------------------------
    try:
        log_files = ["actions.log", "rejections.log", "handoffs.log"]
        existing_logs = []
        missing_logs = []
        for lf in log_files:
            lpath = ws / lf
            if lpath.exists():
                existing_logs.append(lf)
            else:
                missing_logs.append(lf)

        all_logs_exist = len(missing_logs) == 0
        checks.append({
            "name": "three_log_pattern_exists",
            "passed": all_logs_exist,
            "detail": f"Existing: {existing_logs}. Missing: {missing_logs}"
        })
        if all_logs_exist:
            total_score += 0.10
        elif len(existing_logs) >= 2:
            total_score += 0.04
    except Exception as e:
        checks.append({
            "name": "three_log_pattern_exists",
            "passed": False,
            "detail": f"Error checking log files: {e}"
        })

    # ----------------------------------------------------------------
    # CHECK 5: Provenance stamps on memory files
    # Stamp format: [agent|timestamp|confidence|rationale]
    # Must be present on at least 2 of: MEMORY.md, HEARTBEAT.md, SOUL.md, AGENTS.md, IDENTITY.md
    # ----------------------------------------------------------------
    try:
        stamp_pattern = re.compile(r'^\[([^\|]+)\|([^\|]+)\|([^\|]+)\|([^\]]+)\]', re.MULTILINE)
        stamped_files = []
        candidate_files = ["MEMORY.md", "HEARTBEAT.md", "SOUL.md", "AGENTS.md", "IDENTITY.md"]

        for fname in candidate_files:
            fp = ws / fname
            if fp.exists():
                content = fp.read_text()
                matches = stamp_pattern.findall(content)
                if matches:
                    stamped_files.append((fname, matches))

        has_two_stamps = len(stamped_files) >= 2
        detail_parts = []
        for fname, matches in stamped_files:
            detail_parts.append(f"{fname}: {len(matches)} stamp(s) -> {matches[0]}")

        checks.append({
            "name": "provenance_stamps_applied",
            "passed": has_two_stamps,
            "detail": f"Files with valid [agent|timestamp|confidence|rationale] stamps: {len(stamped_files)}. " +
                      ("; ".join(detail_parts) if detail_parts else "None found.")
        })
        if has_two_stamps:
            total_score += 0.15
        elif len(stamped_files) == 1:
            total_score += 0.06
    except Exception as e:
        checks.append({
            "name": "provenance_stamps_applied",
            "passed": False,
            "detail": f"Error checking provenance stamps: {e}"
        })

    # ----------------------------------------------------------------
    # CHECK 6: actions.log contains evidence of verify being run
    # ----------------------------------------------------------------
    try:
        actions_path = ws / "actions.log"
        if not actions_path.exists():
            checks.append({
                "name": "verify_logged_in_actions",
                "passed": False,
                "detail": "actions.log does not exist"
            })
        else:
            actions_content = actions_path.read_text().lower()
            verify_evidence = (
                "verify" in actions_content or
                "verification" in actions_content or
                "intact" in actions_content or
                "passed" in actions_content
            )
            checks.append({
                "name": "verify_logged_in_actions",
                "passed": verify_evidence,
                "detail": f"actions.log contains verify evidence: {verify_evidence}. Content snippet: {actions_content[:300]}"
            })
            if verify_evidence:
                total_score += 0.10
    except Exception as e:
        checks.append({
            "name": "verify_logged_in_actions",
            "passed": False,
            "detail": f"Error reading actions.log: {e}"
        })

    # ----------------------------------------------------------------
    # CHECK 7: rejections.log contains tampering detection evidence
    # ----------------------------------------------------------------
    try:
        rejections_path = ws / "rejections.log"
        if not rejections_path.exists():
            checks.append({
                "name": "tampering_detected_in_rejections",
                "passed": False,
                "detail": "rejections.log does not exist"
            })
        else:
            rejections_content = rejections_path.read_text().lower()
            tamper_evidence = (
                "tamper" in rejections_content or
                "mismatch" in rejections_content or
                "unauthorized" in rejections_content or
                "modified" in rejections_content or
                "changed" in rejections_content or
                "hash" in rejections_content
            )
            checks.append({
                "name": "tampering_detected_in_rejections",
                "passed": tamper_evidence,
                "detail": f"rejections.log contains tampering detection: {tamper_evidence}. Content: {rejections_content[:300]}"
            })
            if tamper_evidence:
                total_score += 0.10
    except Exception as e:
        checks.append({
            "name": "tampering_detected_in_rejections",
            "passed": False,
            "detail": f"Error reading rejections.log: {e}"
        })

    # ----------------------------------------------------------------
    # CHECK 8: audit was run (actions.log should mention audit)
    # ----------------------------------------------------------------
    try:
        actions_path = ws / "actions.log"
        if not actions_path.exists():
            checks.append({
                "name": "audit_was_run",
                "passed": False,
                "detail": "actions.log does not exist, cannot verify audit"
            })
        else:
            actions_content = actions_path.read_text().lower()
            audit_evidence = "audit" in actions_content
            checks.append({
                "name": "audit_was_run",
                "passed": audit_evidence,
                "detail": f"actions.log contains 'audit' evidence: {audit_evidence}. Snippet: {actions_content[:400]}"
            })
            if audit_evidence:
                total_score += 0.10
    except Exception as e:
        checks.append({
            "name": "audit_was_run",
            "passed": False,
            "detail": f"Error checking audit evidence: {e}"
        })

    # ----------------------------------------------------------------
    # CHECK 9: A file was tampered AFTER init and verify caught it
    # (Verify that verify was run AFTER some modification — rejections.log is non-empty)
    # ----------------------------------------------------------------
    try:
        rejections_path = ws / "rejections.log"
        if rejections_path.exists():
            content = rejections_path.read_text().strip()
            has_content = len(content) > 0
            checks.append({
                "name": "rejections_log_nonempty",
                "passed": has_content,
                "detail": f"rejections.log is {'non-empty (good)' if has_content else 'empty — tampering scenario may not have been tested'}"
            })
            if has_content:
                total_score += 0.05
        else:
            checks.append({
                "name": "rejections_log_nonempty",
                "passed": False,
                "detail": "rejections.log missing"
            })
    except Exception as e:
        checks.append({
            "name": "rejections_log_nonempty",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ----------------------------------------------------------------
    # Final scoring
    # ----------------------------------------------------------------
    total_score = min(total_score, 1.0)
    passed = total_score >= 0.70 and all(
        c["passed"] for c in checks
        if c["name"] in {
            "hash_registry_exists",
            "registry_tracks_critical_files",
            "three_log_pattern_exists",
            "provenance_stamps_applied",
            "verify_logged_in_actions",
        }
    )

    result = {
        "passed": passed,
        "score": round(total_score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    evaluate(sys.argv[1])