#!/usr/bin/env python3
"""
Evaluation script for the idea-check task.
Usage: python eval_script.py <workspace_dir>
"""
import sys
import json
import os
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0
    weight_sum = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, weight_sum
        checks.append({"name": name, "passed": passed, "detail": detail})
        weight_sum += weight
        if passed:
            total_score += weight

    # -------------------------------------------------------
    # FIND the output file
    # -------------------------------------------------------
    result_file = None
    candidates = list(Path(workspace).rglob("idea_check_result.md"))
    if candidates:
        result_file = candidates[0]
    
    if result_file is None:
        add_check("output_file_exists", False, "idea_check_result.md not found anywhere in workspace", weight=3.0)
        # Still run registry check
        try:
            registry_path = "/tmp/mcporter_registry.json"
            with open(registry_path) as f:
                registry = json.load(f)
            registered = "idea-reality" in registry
            add_check(
                "mcporter_registered",
                registered,
                f"idea-reality registered: {registered}. Registry: {registry}" if registered else "idea-reality not found in registry"
            )
        except Exception as e:
            add_check("mcporter_registered", False, f"Could not read registry: {e}")
        
        score = total_score / weight_sum if weight_sum > 0 else 0.0
        return {"passed": False, "score": round(score, 3), "checks": checks}

    add_check("output_file_exists", True, f"Found at {result_file}", weight=3.0)

    # Read content
    try:
        content = result_file.read_text(encoding="utf-8")
    except Exception as e:
        add_check("output_file_readable", False, f"Cannot read file: {e}", weight=2.0)
        score = total_score / weight_sum if weight_sum > 0 else 0.0
        return {"passed": False, "score": round(score, 3), "checks": checks}

    add_check("output_file_readable", True, f"File readable, {len(content)} chars", weight=1.0)

    # -------------------------------------------------------
    # CHECK 1: mcporter registry — idea-reality must be registered
    # -------------------------------------------------------
    try:
        registry_path = "/tmp/mcporter_registry.json"
        with open(registry_path) as f:
            registry = json.load(f)
        registered = "idea-reality" in registry
        cmd_correct = False
        if registered:
            cmd_val = registry["idea-reality"].get("command", "")
            cmd_correct = "idea-reality-mcp" in cmd_val and "uvx" in cmd_val
        add_check(
            "mcporter_idea_reality_registered",
            registered,
            f"Registry entry: {registry.get('idea-reality', 'MISSING')}",
            weight=2.0
        )
        add_check(
            "mcporter_command_correct",
            cmd_correct,
            f"Command uses 'uvx idea-reality-mcp': {cmd_correct}. Got: {registry.get('idea-reality', {}).get('command', 'N/A')}",
            weight=1.5
        )
    except Exception as e:
        add_check("mcporter_idea_reality_registered", False, f"Registry read error: {e}", weight=2.0)
        add_check("mcporter_command_correct", False, f"Registry read error: {e}", weight=1.5)

    # -------------------------------------------------------
    # CHECK 2: Depth must be "deep" (triggered by "Deep check:" in idea)
    # -------------------------------------------------------
    # We verify this by checking that sources_checked includes all 5 sources
    # (the mock returns 5 sources only for depth=deep)
    all_five_sources = all(
        src.lower() in content.lower()
        for src in ["GitHub", "Hacker News", "npm", "PyPI", "Product Hunt"]
    )
    add_check(
        "depth_deep_all_five_sources",
        all_five_sources,
        f"All 5 sources (GitHub, Hacker News, npm, PyPI, Product Hunt) present in output: {all_five_sources}",
        weight=2.5
    )

    # -------------------------------------------------------
    # CHECK 3: Signal score — must show 87 (the deep check result)
    # -------------------------------------------------------
    signal_match = re.search(r'87\s*/\s*100|87/100', content)
    add_check(
        "signal_score_87",
        bool(signal_match),
        f"Signal score 87/100 found in output: {bool(signal_match)}",
        weight=2.0
    )

    # -------------------------------------------------------
    # CHECK 4: Red emoji indicator (signal > 70)
    # -------------------------------------------------------
    # Must use a red indicator. Common red emojis: 🔴, ❌, 🛑, 🚨, ⛔
    red_emojis = ["🔴", "❌", "🛑", "🚨", "⛔", "🚫"]
    has_red_emoji = any(e in content for e in red_emojis)
    add_check(
        "red_emoji_indicator",
        has_red_emoji,
        f"Red indicator emoji found: {has_red_emoji}. Checked: {red_emojis}",
        weight=2.0
    )

    # -------------------------------------------------------
    # CHECK 5: Header format — "Idea Check — <signal>/100" or similar
    # -------------------------------------------------------
    header_pattern = re.search(r'Idea Check\s*[—\-–]\s*\d+/100', content)
    add_check(
        "header_format_correct",
        bool(header_pattern),
        f"Header 'Idea Check — XX/100' found: {bool(header_pattern)}",
        weight=1.5
    )

    # -------------------------------------------------------
    # CHECK 6: Top competitors listed with star counts
    # -------------------------------------------------------
    has_flasgger = "flasgger" in content.lower()
    has_spectree = "spectree" in content.lower()
    has_apispec = "apispec" in content.lower()
    has_stars = bool(re.search(r'3[,.]?400\s*stars?|3400\s*stars?', content, re.IGNORECASE)) or \
                bool(re.search(r'1[,.]?200\s*stars?|1200\s*stars?', content, re.IGNORECASE))

    competitors_present = has_flasgger and has_spectree and has_apispec
    add_check(
        "top_competitors_listed",
        competitors_present,
        f"flasgger={has_flasgger}, spectree={has_spectree}, apispec={has_apispec}",
        weight=2.0
    )
    add_check(
        "star_counts_present",
        has_stars,
        f"Star counts (3400 or 1200) present in output: {has_stars}",
        weight=1.5
    )

    # -------------------------------------------------------
    # CHECK 7: STOP behavior (signal > 70 → stop, ask user)
    # -------------------------------------------------------
    # Must ask if user wants to proceed, pivot, or abandon
    stop_words = ["proceed", "pivot", "abandon"]
    has_stop_language = sum(1 for w in stop_words if w.lower() in content.lower()) >= 2
    add_check(
        "stop_behavior_signal_over_70",
        has_stop_language,
        f"Stop behavior: agent asks about proceed/pivot/abandon (found {sum(1 for w in stop_words if w.lower() in content.lower())}/3 keywords)",
        weight=2.0
    )

    # -------------------------------------------------------
    # CHECK 8: Pivot hints present (signal > 30 → show pivot hints)
    # -------------------------------------------------------
    pivot_keywords = ["type hint", "type-hint", "docstring", "non-web", "sdk", "breaking change", "diff"]
    has_pivot = any(kw.lower() in content.lower() for kw in pivot_keywords)
    add_check(
        "pivot_hints_present",
        has_pivot,
        f"Pivot hints found: {has_pivot}. Checked keywords: {pivot_keywords}",
        weight=1.5
    )

    # -------------------------------------------------------
    # FINAL SCORE
    # -------------------------------------------------------
    final_score = total_score / weight_sum if weight_sum > 0 else 0.0
    
    # Must pass critical checks to be considered passing overall
    critical_checks = [
        "output_file_exists",
        "mcporter_idea_reality_registered",
        "depth_deep_all_five_sources",
        "signal_score_87",
        "red_emoji_indicator",
        "top_competitors_listed",
        "stop_behavior_signal_over_70",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    overall_passed = critical_passed and final_score >= 0.72

    return {
        "passed": overall_passed,
        "score": round(final_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    workspace = sys.argv[1]
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))