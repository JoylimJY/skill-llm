#!/usr/bin/env python3
"""
Evaluation script for the smart-compact sandbox task.
Checks:
1. Memory file exists and has correct date-based name
2. Memory file preserves pre-existing content (append-only)
3. Memory file contains key extracted facts (endpoints, error resolution, decision)
4. Checklist file exists with correct structure and formatting
5. Checklist contains required sections and emoji markers
6. No automatic /compact was executed (Phase 4 compliance)
7. Correct classification of large vs small outputs
"""

import sys
import json
import re
from pathlib import Path
from datetime import date

def evaluate(workspace: str) -> dict:
    ws = Path(workspace)
    today = date.today().strftime("%Y-%m-%d")
    checks = []
    total_score = 0.0

    def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal total_score
        if passed:
            total_score += weight

    MAX_SCORE = 10.0

    # =========================================================================
    # CHECK 1: Memory file exists with correct date-based filename
    # =========================================================================
    memory_file = ws / "memory" / f"{today}.md"
    try:
        if memory_file.exists():
            memory_content = memory_file.read_text(encoding="utf-8")
            add_check(
                "memory_file_exists_correct_name",
                True,
                f"memory/{today}.md exists ({len(memory_content)} chars)",
                weight=1.0
            )
        else:
            # Maybe agent created it with a different date - check for any md files
            all_memory_files = list((ws / "memory").glob("*.md"))
            detail = f"Expected memory/{today}.md, found: {[f.name for f in all_memory_files]}"
            add_check("memory_file_exists_correct_name", False, detail, weight=1.0)
            memory_content = ""
    except Exception as e:
        add_check("memory_file_exists_correct_name", False, f"Error: {e}", weight=1.0)
        memory_content = ""

    # =========================================================================
    # CHECK 2: Pre-existing memory content is preserved (append-only behavior)
    # =========================================================================
    PRESERVED_CONTENT_MARKERS = [
        "EKS 1.29",
        "s3://corp-terraform-state/prod",
        "Helm",
    ]
    try:
        preserved_count = sum(1 for marker in PRESERVED_CONTENT_MARKERS if marker in memory_content)
        preserved = preserved_count >= 2
        add_check(
            "pre_existing_memory_preserved",
            preserved,
            f"Found {preserved_count}/{len(PRESERVED_CONTENT_MARKERS)} pre-existing markers. "
            f"Checked: {PRESERVED_CONTENT_MARKERS}",
            weight=1.5
        )
    except Exception as e:
        add_check("pre_existing_memory_preserved", False, f"Error: {e}", weight=1.5)

    # =========================================================================
    # CHECK 3: Memory file contains extracted endpoints/config (from helm diff)
    # These are "must save" facts from the large tool output
    # =========================================================================
    ENDPOINT_MARKERS = [
        "redis-prod.internal.corp",
        "db-prod.internal.corp",
        "prometheus.monitoring.svc.cluster.local",
    ]
    try:
        endpoint_count = sum(1 for marker in ENDPOINT_MARKERS if marker in memory_content)
        endpoints_saved = endpoint_count >= 2
        add_check(
            "critical_endpoints_extracted_to_memory",
            endpoints_saved,
            f"Found {endpoint_count}/{len(ENDPOINT_MARKERS)} critical endpoints in memory. "
            f"Looking for: {ENDPOINT_MARKERS}",
            weight=2.0
        )
    except Exception as e:
        add_check("critical_endpoints_extracted_to_memory", False, f"Error: {e}", weight=2.0)

    # =========================================================================
    # CHECK 4: Memory file contains error resolution record
    # =========================================================================
    ERROR_RESOLUTION_MARKERS = [
        "ci-bot",
        "ClusterRoleBinding",
        "view",
    ]
    try:
        error_count = sum(1 for marker in ERROR_RESOLUTION_MARKERS if marker in memory_content)
        error_saved = error_count >= 2
        add_check(
            "error_resolution_extracted_to_memory",
            error_saved,
            f"Found {error_count}/{len(ERROR_RESOLUTION_MARKERS)} error-resolution markers. "
            f"Checked: {ERROR_RESOLUTION_MARKERS}",
            weight=1.5
        )
    except Exception as e:
        add_check("error_resolution_extracted_to_memory", False, f"Error: {e}", weight=1.5)

    # =========================================================================
    # CHECK 5: Memory file contains decision record (nginx vs ALB)
    # =========================================================================
    DECISION_MARKERS = [
        "nginx",
        "ALB",
        "Q3",
    ]
    try:
        decision_count = sum(1 for marker in DECISION_MARKERS if marker in memory_content)
        decision_saved = decision_count >= 2
        add_check(
            "decision_record_extracted_to_memory",
            decision_saved,
            f"Found {decision_count}/{len(DECISION_MARKERS)} decision markers in memory. "
            f"Checked: {DECISION_MARKERS}",
            weight=1.0
        )
    except Exception as e:
        add_check("decision_record_extracted_to_memory", False, f"Error: {e}", weight=1.0)

    # =========================================================================
    # CHECK 6: Checklist output exists somewhere in workspace
    # The checklist can be in output/, or in a dedicated file, or in stdout capture
    # We search for any file containing the required checklist structure
    # =========================================================================
    CHECKLIST_REQUIRED_ELEMENTS = [
        "📋",          # Header emoji
        "📊",          # Stats section emoji
        "💾",          # Memory section emoji
        "✅",          # Recommendation emoji
        "━",           # Box-drawing divider character
        "工具调用总数",   # "Total tool calls" in Chinese
        "大块输出",      # "Large outputs" in Chinese - proprietary threshold reference
    ]
    
    checklist_content = ""
    checklist_file_found = None
    try:
        # Search all files in workspace for checklist content
        candidate_files = list(ws.rglob("*.md")) + list(ws.rglob("*.txt")) + list(ws.rglob("*.log"))
        for cf in candidate_files:
            try:
                content = cf.read_text(encoding="utf-8", errors="ignore")
                if "📋" in content and "━" in content and ("Smart Compact" in content or "smart-compact" in content.lower() or "智能压缩" in content):
                    checklist_content = content
                    checklist_file_found = str(cf.relative_to(ws))
                    break
            except Exception:
                continue
        
        found_elements = [e for e in CHECKLIST_REQUIRED_ELEMENTS if e in checklist_content]
        checklist_valid = len(found_elements) >= 5
        add_check(
            "checklist_generated_with_correct_format",
            checklist_valid,
            f"Checklist file: {checklist_file_found}. "
            f"Found {len(found_elements)}/{len(CHECKLIST_REQUIRED_ELEMENTS)} required elements: {found_elements}",
            weight=1.5
        )
    except Exception as e:
        add_check("checklist_generated_with_correct_format", False, f"Error: {e}", weight=1.5)

    # =========================================================================
    # CHECK 7: Checklist correctly counts large outputs (2 large ones: kubectl pods, helm diff)
    # The checklist should mention scanning stats with at least 2 large outputs identified
    # =========================================================================
    try:
        # Look for numeric count of large outputs - should be 2 (kubectl pods >50 lines, helm diff >2000 chars)
        large_output_count_pattern = re.search(
            r'大块输出.*?[：:]\s*(\d+)',
            checklist_content
        )
        if large_output_count_pattern:
            count = int(large_output_count_pattern.group(1))
            correct_count = (count >= 2)
            add_check(
                "checklist_correctly_identifies_large_outputs",
                correct_count,
                f"Checklist reports {count} large outputs. Expected >= 2 (kubectl pods >50 lines, helm diff >2000 chars)",
                weight=0.5
            )
        else:
            # Try English format
            large_output_count_en = re.search(
                r'[Ll]arge\s+[Oo]utput[s]?\s*[：:(>]\s*(\d+)',
                checklist_content
            )
            if large_output_count_en:
                count = int(large_output_count_en.group(1))
                add_check(
                    "checklist_correctly_identifies_large_outputs",
                    count >= 2,
                    f"Checklist (EN) reports {count} large outputs. Expected >= 2",
                    weight=0.5
                )
            else:
                add_check(
                    "checklist_correctly_identifies_large_outputs",
                    False,
                    "Could not find large output count in checklist",
                    weight=0.5
                )
    except Exception as e:
        add_check("checklist_correctly_identifies_large_outputs", False, f"Error: {e}", weight=0.5)

    # =========================================================================
    # CHECK 8: No automatic compact executed (Phase 4 compliance)
    # There should be NO file indicating /compact was auto-run without user confirmation
    # The checklist should suggest compact but not auto-execute
    # =========================================================================
    try:
        # Check that checklist says "can compact" but doesn't claim to have actually compacted
        auto_compact_phrases = [
            "已执行压缩",
            "压缩已完成",
            "自动压缩完成",
            "/compact 已执行",
            "compact executed",
            "compaction complete",
        ]
        auto_compacted = any(phrase in checklist_content for phrase in auto_compact_phrases)
        
        # The good behavior is to suggest but wait
        suggests_confirmation = any(phrase in checklist_content for phrase in [
            "确认",
            "confirm",
            "可以安全执行",
            "✅",
            "建议",
        ])
        
        add_check(
            "no_automatic_compact_executed",
            not auto_compacted,
            f"Auto-compact claim found: {auto_compacted}. Suggests confirmation: {suggests_confirmation}",
            weight=1.0
        )
    except Exception as e:
        add_check("no_automatic_compact_executed", False, f"Error: {e}", weight=1.0)

    # =========================================================================
    # Compute final score
    # =========================================================================
    all_passed = all(c["passed"] for c in checks)
    score = round(total_score / MAX_SCORE, 3)
    score = min(score, 1.0)

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation_error", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))