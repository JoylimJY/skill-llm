#!/usr/bin/env python3
"""
Evaluator for the dreaming skill task.
Checks:
1. data/dream-state.json has correct camelCase fields with valid types
2. data/dream-config.json has correct format: {"topics": ["category:prompt", ...]} with biotech topics
3. memory/dreams/YYYY-MM-DD.md exists and has correct proprietary formatting
4. Dream content references the chosen topic/category
5. should-dream.sh still executes correctly after state changes
"""

import sys
import json
import re
import subprocess
import os
from pathlib import Path
from datetime import date

def run_checks(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0
    weights = {}

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal total_score
        if passed:
            total_score += weight
        weights[name] = weight

    # ── CHECK 1: dream-state.json has correct camelCase fields ───────────────
    state_path = ws / "data/dream-state.json"
    try:
        raw = state_path.read_text()
        state = json.loads(raw)

        has_last_dream_date = "lastDreamDate" in state
        has_dreams_tonight = "dreamsTonight" in state
        has_max_dreams = "maxDreamsPerNight" in state
        has_chance = "dreamChance" in state

        all_fields = has_last_dream_date and has_dreams_tonight and has_max_dreams and has_chance
        add_check(
            "dream-state.json has correct camelCase fields",
            all_fields,
            f"Fields present: lastDreamDate={has_last_dream_date}, dreamsTonight={has_dreams_tonight}, "
            f"maxDreamsPerNight={has_max_dreams}, dreamChance={has_chance}",
            weight=1.5
        )

        # dreamChance must be a float/int (not a string like "sometimes")
        chance_val = state.get("dreamChance")
        chance_is_numeric = isinstance(chance_val, (int, float)) and not isinstance(chance_val, bool)
        add_check(
            "dreamChance is numeric type",
            chance_is_numeric,
            f"dreamChance value: {repr(chance_val)} (type: {type(chance_val).__name__})",
            weight=1.0
        )

        # maxDreamsPerNight should be a positive integer
        max_val = state.get("maxDreamsPerNight")
        max_valid = isinstance(max_val, int) and not isinstance(max_val, bool) and max_val >= 1
        add_check(
            "maxDreamsPerNight is a positive integer",
            max_valid,
            f"maxDreamsPerNight value: {repr(max_val)}",
            weight=0.5
        )

        # No wrong old field names remain
        old_fields = {"last_dream", "dreams_tonight", "dream_chance"}
        leftover = old_fields.intersection(state.keys())
        add_check(
            "Old malformed fields removed from dream-state.json",
            len(leftover) == 0,
            f"Leftover old fields: {leftover}",
            weight=0.5
        )

    except FileNotFoundError:
        add_check("dream-state.json has correct camelCase fields", False, "File not found", weight=1.5)
        add_check("dreamChance is numeric type", False, "File not found", weight=1.0)
        add_check("maxDreamsPerNight is a positive integer", False, "File not found", weight=0.5)
        add_check("Old malformed fields removed from dream-state.json", False, "File not found", weight=0.5)
    except json.JSONDecodeError as e:
        add_check("dream-state.json has correct camelCase fields", False, f"JSON parse error: {e}", weight=1.5)
        add_check("dreamChance is numeric type", False, "JSON parse error", weight=1.0)
        add_check("maxDreamsPerNight is a positive integer", False, "JSON parse error", weight=0.5)
        add_check("Old malformed fields removed from dream-state.json", False, "JSON parse error", weight=0.5)

    # ── CHECK 2: dream-config.json has correct format with biotech topics ────
    config_path = ws / "data/dream-config.json"
    try:
        raw = config_path.read_text()
        config = json.loads(raw)

        has_topics_key = "topics" in config
        add_check(
            "dream-config.json has 'topics' key (not 'dream_topics' or other)",
            has_topics_key,
            f"Keys present: {list(config.keys())}",
            weight=1.0
        )

        if has_topics_key:
            topics = config["topics"]
            is_list = isinstance(topics, list)
            add_check(
                "dream-config.json topics is an array",
                is_list,
                f"topics type: {type(topics).__name__}",
                weight=0.5
            )

            if is_list and len(topics) > 0:
                # All entries must be strings in "category:prompt" format
                colon_format = all(
                    isinstance(t, str) and ":" in t and len(t.split(":", 1)) == 2
                    for t in topics
                )
                add_check(
                    "All topics are strings in 'category:prompt' format",
                    colon_format,
                    f"Topics sample: {topics[:3]}",
                    weight=1.5
                )

                # Must not be the old wrong format (dicts with 'id'/'text' keys)
                not_old_format = not any(isinstance(t, dict) for t in topics)
                add_check(
                    "Topics are not old dict format",
                    not_old_format,
                    f"Topics are plain strings, not dicts",
                    weight=0.5
                )

                # Must contain biotech/pharma-relevant content (keyword check)
                all_topics_str = " ".join(topics).lower()
                biotech_keywords = [
                    "drug", "compound", "molecule", "trial", "target", "protein",
                    "assay", "biomarker", "pathway", "therapeutic", "clinical",
                    "pharma", "discovery", "synthesis", "efficacy", "toxicity",
                    "ligand", "receptor", "gene", "cell", "tissue", "cancer",
                    "antibody", "enzyme", "inhibitor", "ic50", "moa"
                ]
                has_biotech = any(kw in all_topics_str for kw in biotech_keywords)
                add_check(
                    "Topics contain domain-relevant biotech/pharma content",
                    has_biotech,
                    f"Topics text (truncated): {all_topics_str[:200]}",
                    weight=1.5
                )
            else:
                add_check("All topics are strings in 'category:prompt' format", False,
                          "Topics list is empty or missing", weight=1.5)
                add_check("Topics are not old dict format", False, "Topics list is empty", weight=0.5)
                add_check("Topics contain domain-relevant biotech/pharma content", False,
                          "Topics list is empty", weight=1.5)
        else:
            add_check("dream-config.json topics is an array", False, "No 'topics' key", weight=0.5)
            add_check("All topics are strings in 'category:prompt' format", False,
                      "No 'topics' key", weight=1.5)
            add_check("Topics are not old dict format", False, "No 'topics' key", weight=0.5)
            add_check("Topics contain domain-relevant biotech/pharma content", False,
                      "No 'topics' key", weight=1.5)

    except FileNotFoundError:
        for name, w in [
            ("dream-config.json has 'topics' key (not 'dream_topics' or other)", 1.0),
            ("dream-config.json topics is an array", 0.5),
            ("All topics are strings in 'category:prompt' format", 1.5),
            ("Topics are not old dict format", 0.5),
            ("Topics contain domain-relevant biotech/pharma content", 1.5),
        ]:
            add_check(name, False, "File not found", weight=w)
    except json.JSONDecodeError as e:
        for name, w in [
            ("dream-config.json has 'topics' key (not 'dream_topics' or other)", 1.0),
            ("dream-config.json topics is an array", 0.5),
            ("All topics are strings in 'category:prompt' format", 1.5),
            ("Topics are not old dict format", 0.5),
            ("Topics contain domain-relevant biotech/pharma content", 1.5),
        ]:
            add_check(name, False, f"JSON error: {e}", weight=w)

    # ── CHECK 3: memory/dreams/YYYY-MM-DD.md exists with correct formatting ──
    dreams_dir = ws / "memory/dreams"
    dream_files = list(dreams_dir.glob("????-??-??.md"))
    # Exclude old distractor file
    dream_files = [f for f in dream_files if f.name != "old-dream-2026-01-15.md"]

    has_dream_file = len(dream_files) > 0
    add_check(
        "A dream file exists in memory/dreams/",
        has_dream_file,
        f"Found files: {[f.name for f in dream_files]}",
        weight=1.5
    )

    if has_dream_file:
        # Use the most recently modified dream file
        dream_file = max(dream_files, key=lambda f: f.stat().st_mtime)
        try:
            content = dream_file.read_text()

            # Must have H1 header: "# Dreams — YYYY-MM-DD" with an em dash (—), NOT a hyphen (-)
            h1_emdash_pattern = re.compile(r'^# Dreams\s+\u2014\s+\d{4}-\d{2}-\d{2}', re.MULTILINE)
            has_h1_emdash = bool(h1_emdash_pattern.search(content))
            add_check(
                "Dream file H1 uses em dash (—) not hyphen (-): '# Dreams — YYYY-MM-DD'",
                has_h1_emdash,
                f"File: {dream_file.name}\nContent start: {repr(content[:120])}",
                weight=2.0
            )

            # Must have H2 section: "## HH:MM — Topic (category-name)" with em dash
            h2_emdash_pattern = re.compile(
                r'^## \d{2}:\d{2}\s+\u2014\s+.+\(.+\)',
                re.MULTILINE
            )
            has_h2_emdash = bool(h2_emdash_pattern.search(content))
            add_check(
                "Dream H2 section uses em dash and parenthesized category: '## HH:MM — Title (category)'",
                has_h2_emdash,
                f"H2 pattern search in: {repr(content[:300])}",
                weight=2.0
            )

            # Must have actual dream content (more than just headers — at least 50 chars of body)
            # Strip headers and check remaining content
            non_header_lines = [
                line for line in content.splitlines()
                if line.strip() and not line.startswith("#")
            ]
            body_text = " ".join(non_header_lines)
            has_substance = len(body_text) >= 50
            add_check(
                "Dream file contains substantive written content (not just headers)",
                has_substance,
                f"Body text length: {len(body_text)} chars. Sample: {repr(body_text[:150])}",
                weight=1.5
            )

            # H1 date should match the filename date
            filename_date = dream_file.stem  # e.g., "2026-07-12"
            h1_date_match = re.search(r'# Dreams\s+\u2014\s+(\d{4}-\d{2}-\d{2})', content)
            if h1_date_match:
                header_date = h1_date_match.group(1)
                date_matches = (header_date == filename_date)
                add_check(
                    "H1 date matches filename date",
                    date_matches,
                    f"Filename date: {filename_date}, H1 date: {header_date}",
                    weight=0.5
                )
            else:
                add_check(
                    "H1 date matches filename date",
                    False,
                    "Could not extract H1 date (em-dash header missing)",
                    weight=0.5
                )

        except Exception as e:
            for name, w in [
                ("Dream file H1 uses em dash (—) not hyphen (-): '# Dreams — YYYY-MM-DD'", 2.0),
                ("Dream H2 section uses em dash and parenthesized category: '## HH:MM — Title (category)'", 2.0),
                ("Dream file contains substantive written content (not just headers)", 1.5),
                ("H1 date matches filename date", 0.5),
            ]:
                add_check(name, False, f"Error reading file: {e}", weight=w)
    else:
        for name, w in [
            ("Dream file H1 uses em dash (—) not hyphen (-): '# Dreams — YYYY-MM-DD'", 2.0),
            ("Dream H2 section uses em dash and parenthesized category: '## HH:MM — Title (category)'", 2.0),
            ("Dream file contains substantive written content (not just headers)", 1.5),
            ("H1 date matches filename date", 0.5),
        ]:
            add_check(name, False, "No dream file found", weight=w)

    # ── CHECK 4: should-dream.sh is still functional (updated state allows re-run on same day) ─
    # We verify the script can be invoked without crashing (state is valid JSON)
    try:
        result = subprocess.run(
            ["bash", str(ws / "skills/dreaming/scripts/should-dream.sh")],
            capture_output=True, text=True,
            cwd=str(ws),
            env={**os.environ, "WORKSPACE": str(ws)},
            timeout=10
        )
        # Exit code 2 means limit reached (already dreamed tonight) — that's fine and expected
        # Exit code 0 means another dream was issued
        # Exit code 1/3 are also acceptable (quiet hours miss or dice roll)
        # What we want to confirm: it didn't crash with exit code != 0,1,2,3
        # and that stderr doesn't contain JSON errors
        script_no_crash = result.returncode in (0, 1, 2, 3)
        stderr_no_json_error = "parse error" not in result.stderr.lower() and \
                               "invalid" not in result.stderr.lower()
        add_check(
            "should-dream.sh runs without crashing (valid state JSON)",
            script_no_crash and stderr_no_json_error,
            f"Exit code: {result.returncode}, stderr: {repr(result.stderr[:200])}",
            weight=1.0
        )
    except subprocess.TimeoutExpired:
        add_check("should-dream.sh runs without crashing (valid state JSON)", False,
                  "Script timed out", weight=1.0)
    except Exception as e:
        add_check("should-dream.sh runs without crashing (valid state JSON)", False,
                  f"Error running script: {e}", weight=1.0)

    # ── Compute final score ───────────────────────────────────────────────────
    total_weight = sum(weights.values())
    final_score = round(total_score / total_weight, 4) if total_weight > 0 else 0.0
    overall_passed = final_score >= 0.75 and all(
        c["passed"] for c in checks
        if c["name"] in {
            "dream-state.json has correct camelCase fields",
            "dreamChance is numeric type",
            "All topics are strings in 'category:prompt' format",
            "Topics contain domain-relevant biotech/pharma content",
            "Dream file H1 uses em dash (—) not hyphen (-): '# Dreams — YYYY-MM-DD'",
            "Dream H2 section uses em dash and parenthesized category: '## HH:MM — Title (category)'",
            "Dream file contains substantive written content (not just headers)",
        }
    )

    return {
        "passed": overall_passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "usage", "passed": False, "detail": "Usage: eval.py <workspace_path>"}
        ]}))
        sys.exit(1)

    result = run_checks(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))