import sys
import json
import re
from pathlib import Path

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    # ── Locate the output file ────────────────────────────────────────────
    # The task asks to save as "api_toc.md"
    candidates = list(workspace.rglob("api_toc.md"))

    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False,
                        "detail": "api_toc.md not found anywhere in workspace"}]
        }

    # Use the first (and ideally only) match
    toc_file = candidates[0]
    checks.append({"name": "output_file_exists", "passed": True,
                   "detail": f"Found at {toc_file}"})

    try:
        content = toc_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "file_readable", "passed": False,
                                  "detail": str(e)}]
        }

    lines = [l for l in content.strip().splitlines() if l.strip()]

    # ── CHECK 1: H1 headings are EXCLUDED (min-level=2) ──────────────────
    # "DataPulse API Reference", "SDKs and Libraries" type H1 entries
    h1_entries_plain = ["DataPulse API Reference"]
    h1_leaked = any(
        "DataPulse API Reference" in line or
        (re.search(r'\[DataPulse API Reference\]', line))
        for line in lines
    )
    checks.append({
        "name": "h1_excluded",
        "passed": not h1_leaked,
        "detail": "H1 heading 'DataPulse API Reference' must NOT appear (min-level=2)" if h1_leaked
                  else "H1 headings correctly excluded"
    })

    # ── CHECK 2: H5/H6 headings are EXCLUDED (max-level=4) ───────────────
    # H5: "Timeout Settings", "400 Bad Request", "401 Unauthorized", "429 Too Many Requests",
    #     "500 Internal Server Error"
    # H6: "Default Values"
    h5_h6_samples = [
        "Timeout Settings", "400 Bad Request", "Default Values",
        "500 Internal Server Error", "401 Unauthorized"
    ]
    h56_leaked = any(
        any(sample in line for sample in h5_h6_samples)
        for line in lines
    )
    checks.append({
        "name": "h5_h6_excluded",
        "passed": not h56_leaked,
        "detail": "H5/H6 headings must NOT appear (max-level=4)" if h56_leaked
                  else "H5/H6 headings correctly excluded"
    })

    # ── CHECK 3: Format is "links" (all entries are anchor links) ─────────
    non_link_entries = [l for l in lines if l.strip().startswith("-") and
                        not re.search(r'\[.+\]\(#.+\)', l)]
    all_links = len(non_link_entries) == 0
    checks.append({
        "name": "links_format",
        "passed": all_links,
        "detail": f"All bullet entries must be markdown anchor links. Non-link lines: {non_link_entries[:3]}"
                  if not all_links else "All entries correctly formatted as anchor links"
    })

    # ── CHECK 4: Code-block headings are NOT included ─────────────────────
    # Inside fenced code blocks we have: "Example ingestion payload",
    # "Response Fields", "Webhook fields", and "This is inside a code block"
    code_block_leaks = [
        "Example ingestion payload", "Response Fields",
        "Webhook fields", "This is inside a code block",
        "Fields", "data (array)", "items", "timestamp", "value"
    ]
    # Check for any of these showing up as TOC entries
    leaked_code = []
    for line in lines:
        for leak in code_block_leaks:
            if leak in line and line.strip().startswith("-"):
                leaked_code.append(line.strip())
    code_block_clean = len(leaked_code) == 0
    checks.append({
        "name": "code_blocks_skipped",
        "passed": code_block_clean,
        "detail": f"Headings inside code blocks must be skipped. Found: {leaked_code[:3]}"
                  if not code_block_clean else "Code block headings correctly skipped"
    })

    # ── CHECK 5: Duplicate "Configuration" anchor deduplication ───────────
    # There are two H3 "### Configuration" headings.
    # The skill should produce: #configuration and #configuration-1
    config_links = [l for l in lines if "configuration" in l.lower() and
                    re.search(r'\[Configuration\]', l, re.IGNORECASE)]
    has_first  = any(re.search(r'\[Configuration\]\(#configuration\b', l, re.IGNORECASE)
                     and "configuration-1" not in l for l in config_links)
    has_second = any("configuration-1" in l for l in config_links)
    dedup_ok = has_first and has_second
    checks.append({
        "name": "duplicate_anchor_deduplication",
        "passed": dedup_ok,
        "detail": (
            f"Two 'Configuration' H3s must produce anchors #configuration and #configuration-1. "
            f"Found config links: {config_links}"
        ) if not dedup_ok else "Duplicate Configuration anchors correctly deduplicated"
    })

    # ── CHECK 6: Key H2-H4 headings ARE present ───────────────────────────
    expected_present = [
        "Authentication", "Endpoints", "Webhooks",
        "Error Codes", "Token Endpoint", "Data Ingestion",
        "Request Parameters", "Rate Limits"
    ]
    missing = []
    for expected in expected_present:
        found = any(expected in line for line in lines)
        if not found:
            missing.append(expected)
    coverage_ok = len(missing) == 0
    checks.append({
        "name": "expected_headings_present",
        "passed": coverage_ok,
        "detail": f"Missing expected headings: {missing}" if missing
                  else "All expected H2-H4 headings are present"
    })

    # ── CHECK 7: Indentation follows relative level (links format) ─────────
    # H2 -> top-level "- [...]"  (0 leading spaces)
    # H3 -> "  - [...]"          (2 leading spaces)
    # H4 -> "    - [...]"        (4 leading spaces)
    # Spot-check "Authentication" (H2) -> 0 indent
    # Spot-check "Token Endpoint" (H3) -> 2 spaces indent
    # Spot-check "Request Parameters" (H4) -> 4 spaces indent
    indent_checks_pass = True
    indent_details = []
    spot_checks = [
        ("Authentication", 0),
        ("Token Endpoint", 2),
        ("Request Parameters", 4),
    ]
    for heading, expected_indent in spot_checks:
        matching = [l for l in lines if heading in l]
        if matching:
            actual_indent = len(matching[0]) - len(matching[0].lstrip())
            if actual_indent != expected_indent:
                indent_checks_pass = False
                indent_details.append(
                    f"'{heading}': expected indent {expected_indent}, got {actual_indent}"
                )
        else:
            indent_checks_pass = False
            indent_details.append(f"'{heading}' not found for indent check")

    checks.append({
        "name": "correct_indentation",
        "passed": indent_checks_pass,
        "detail": "; ".join(indent_details) if indent_details
                  else "Indentation correct for sampled headings"
    })

    # ── Final scoring ─────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    all_passed = passed_count == total

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "invocation", "passed": False,
                                      "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = run_eval(sys.argv[1])
    print(json.dumps(result, indent=2))