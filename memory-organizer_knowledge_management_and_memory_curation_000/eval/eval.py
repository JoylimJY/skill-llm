import sys
import json
import re
from pathlib import Path

def load_file(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None

def run_eval(workspace):
    checks = []
    workspace = Path(workspace)

    memory_md_path = workspace / "MEMORY.md"
    memory_md = load_file(memory_md_path)

    # =========================================================================
    # CHECK 1: MEMORY.md must exist and not be empty
    # =========================================================================
    if memory_md is None:
        checks.append({"name": "MEMORY.md exists", "passed": False, "detail": "MEMORY.md is missing."})
        return checks
    checks.append({"name": "MEMORY.md exists", "passed": True, "detail": "MEMORY.md found."})

    # =========================================================================
    # CHECK 2: MEMORY.md must NOT contain duplicate lines/bullets
    # =========================================================================
    lines = [l.strip() for l in memory_md.splitlines() if l.strip() and not l.strip().startswith("#")]
    unique_lines = set(lines)
    has_duplicates = len(lines) != len(unique_lines)
    checks.append({
        "name": "MEMORY.md has no duplicate bullets",
        "passed": not has_duplicates,
        "detail": f"{'Duplicate entries found.' if has_duplicates else 'No duplicates found.'} Total lines: {len(lines)}, unique: {len(unique_lines)}"
    })

    # =========================================================================
    # CHECK 3: MEMORY.md must NOT contain date-based session log sections
    # (No 'Session Log', 'Session 20XX', or date-headed blocks)
    # =========================================================================
    date_section_pattern = re.compile(r'(session log|session\s+20\d{2}-\d{2}-\d{2})', re.IGNORECASE)
    has_date_sections = bool(date_section_pattern.search(memory_md))
    checks.append({
        "name": "MEMORY.md has no date-based session log sections",
        "passed": not has_date_sections,
        "detail": "Date-based session log sections found in MEMORY.md." if has_date_sections else "No date-based sections found."
    })

    # =========================================================================
    # CHECK 4: MEMORY.md must NOT contain noisy/temporary items
    # (debugging transcripts, random ideas, old completed tasks)
    # =========================================================================
    noise_patterns = [
        r'debugging transcript',
        r'tried import sys',
        r'coffee machine',
        r'weather was nice',
        r'new monitor',
        r'keyboard layout',
        r'random idea',
        r'maybe switch to ruff',
        r'published v1\.0\.0',
        r'fixed login bug',
        r'deployed hotfix',
        r'status check',
        r'build: green',
        r'coverage: \d+%',
    ]
    noise_found = []
    for pat in noise_patterns:
        if re.search(pat, memory_md, re.IGNORECASE):
            noise_found.append(pat)
    checks.append({
        "name": "MEMORY.md free from noisy/temporary content",
        "passed": len(noise_found) == 0,
        "detail": f"Noisy patterns found: {noise_found}" if noise_found else "No noisy content found."
    })

    # =========================================================================
    # CHECK 5: MEMORY.md must retain stable user preferences (deduplicated)
    # e.g., short paragraphs / punchy style — but only ONCE
    # =========================================================================
    pref_count = len(re.findall(r'short paragraphs', memory_md, re.IGNORECASE))
    pref_present = pref_count >= 1
    pref_not_duplicated = pref_count == 1
    checks.append({
        "name": "MEMORY.md retains user style preference (deduplicated, exactly once)",
        "passed": pref_present and pref_not_duplicated,
        "detail": f"'short paragraphs' preference found {pref_count} time(s). Expected exactly 1."
    })

    # =========================================================================
    # CHECK 6: MEMORY.md must retain core workspace rules (deduplicated)
    # e.g., "never modify files outside /workspace" — but only ONCE
    # =========================================================================
    ws_rule_count = len(re.findall(r'never modify files outside', memory_md, re.IGNORECASE))
    ws_rule_present = ws_rule_count >= 1
    ws_rule_not_dup = ws_rule_count == 1
    checks.append({
        "name": "MEMORY.md retains workspace rule (deduplicated, exactly once)",
        "passed": ws_rule_present and ws_rule_not_dup,
        "detail": f"Workspace rule found {ws_rule_count} time(s). Expected exactly 1."
    })

    # =========================================================================
    # CHECK 7: MEMORY.md must retain active todos (authentication refactor and/or CI migration)
    # but NOT completed/resolved tasks
    # =========================================================================
    has_active_todo_auth = bool(re.search(r'refactor.*auth|auth.*refactor', memory_md, re.IGNORECASE))
    has_active_todo_ci = bool(re.search(r'ci pipeline|self.hosted runner|migrate.*ci|ci.*migrat', memory_md, re.IGNORECASE))
    has_active_todos = has_active_todo_auth or has_active_todo_ci
    checks.append({
        "name": "MEMORY.md retains at least one active cross-session todo",
        "passed": has_active_todos,
        "detail": f"Auth refactor todo: {has_active_todo_auth}, CI migration todo: {has_active_todo_ci}"
    })

    # =========================================================================
    # CHECK 8: MEMORY.md must promote the durable SSL rule from 2024-03-10
    # "All HTTP clients must use certifi" — this is a permanent team policy
    # =========================================================================
    has_certifi_rule = bool(re.search(r'certifi', memory_md, re.IGNORECASE))
    checks.append({
        "name": "MEMORY.md promotes durable SSL/certifi policy from daily file",
        "passed": has_certifi_rule,
        "detail": "certifi SSL policy found in MEMORY.md." if has_certifi_rule else "Missing: permanent certifi SSL policy not promoted from 2024-03-10."
    })

    # =========================================================================
    # CHECK 9: MEMORY.md must promote the durable .env requirement from 2024-03-12
    # "DATABASE_URL and SECRET_KEY needed in .env" — permanent dev requirement
    # =========================================================================
    has_env_rule = bool(re.search(r'DATABASE_URL|SECRET_KEY|\.env', memory_md, re.IGNORECASE))
    checks.append({
        "name": "MEMORY.md promotes durable .env/environment variable rule from daily file",
        "passed": has_env_rule,
        "detail": ".env requirement found in MEMORY.md." if has_env_rule else "Missing: .env requirement not promoted from 2024-03-12."
    })

    # =========================================================================
    # CHECK 10: MEMORY.md must NOT contain verbose daily summaries from dated files
    # (bulk content like "Debugging Journal", "Step 1:", "Step 2:", etc.)
    # =========================================================================
    verbose_patterns = [
        r'step \d+:',
        r'debugging journal',
        r'morning standup',
        r'afternoon\b',
        r'end of day summary',
        r'sprint velocity',
        r'PR #\d+',
        r'coverage increased',
        r'linter output',
    ]
    verbose_found = []
    for pat in verbose_patterns:
        if re.search(pat, memory_md, re.IGNORECASE):
            verbose_found.append(pat)
    checks.append({
        "name": "MEMORY.md does not contain verbose daily log content",
        "passed": len(verbose_found) == 0,
        "detail": f"Verbose log patterns found in MEMORY.md: {verbose_found}" if verbose_found else "No verbose log content found."
    })

    # =========================================================================
    # CHECK 11: MEMORY.md must be structured by durable topic, not by date
    # Should NOT have headers like "## 2024-03-10" or "## March 10"
    # =========================================================================
    date_header_pattern = re.compile(r'^#{1,3}\s*(20\d{2}-\d{2}-\d{2}|march|january|february|april)\b', re.IGNORECASE | re.MULTILINE)
    has_date_headers = bool(date_header_pattern.search(memory_md))
    checks.append({
        "name": "MEMORY.md is structured by topic, not by date",
        "passed": not has_date_headers,
        "detail": "Date-based headers found in MEMORY.md." if has_date_headers else "No date-based headers found."
    })

    # =========================================================================
    # CHECK 12: Dated memory files must still EXIST (preserved, not deleted)
    # =========================================================================
    expected_dated = [
        "memory/2024-03-10.md",
        "memory/2024-03-11.md",
        "memory/2024-03-12.md",
        "memory/2024-03-13.md",
        "memory/2024-03-14.md",
    ]
    missing_dated = []
    for rel in expected_dated:
        if not (workspace / rel).exists():
            missing_dated.append(rel)
    checks.append({
        "name": "All dated memory files are preserved (not deleted)",
        "passed": len(missing_dated) == 0,
        "detail": f"Missing dated files: {missing_dated}" if missing_dated else "All dated files preserved."
    })

    # =========================================================================
    # CHECK 13: Dated files must be compressed (shorter than original) but non-empty
    # We check that 2024-03-10 and 2024-03-11 are NOT byte-for-byte identical to originals
    # (indicating no compression was done at all)
    # =========================================================================
    original_lengths = {
        "memory/2024-03-10.md": 855,  # approximate char count of original
        "memory/2024-03-11.md": 680,
    }
    compressed_correctly = []
    for rel, orig_len in original_lengths.items():
        fpath = workspace / rel
        if fpath.exists():
            content = fpath.read_text(encoding="utf-8")
            cur_len = len(content)
            compressed = cur_len < orig_len and cur_len > 10
            compressed_correctly.append((rel, compressed, cur_len, orig_len))
        else:
            compressed_correctly.append((rel, False, 0, orig_len))

    all_compressed = all(c[1] for c in compressed_correctly)
    detail_parts = [f"{r}: {cur}/{orig} chars ({'compressed' if ok else 'NOT compressed or empty'})" for r, ok, cur, orig in compressed_correctly]
    checks.append({
        "name": "Verbose dated files are compressed in-place (shorter than original)",
        "passed": all_compressed,
        "detail": "; ".join(detail_parts)
    })

    # =========================================================================
    # CHECK 14: 2024-03-10 dated file must still contain reference to SSL/certifi fix
    # (historical detail preserved locally)
    # =========================================================================
    dated_10 = load_file(workspace / "memory/2024-03-10.md")
    has_ssl_history = bool(re.search(r'certifi|ssl|payments', dated_10 or "", re.IGNORECASE))
    checks.append({
        "name": "2024-03-10.md retains SSL/certifi historical detail after compression",
        "passed": has_ssl_history,
        "detail": "SSL/certifi context preserved in dated file." if has_ssl_history else "SSL/certifi context lost from dated file."
    })

    # =========================================================================
    # CHECK 15: MEMORY.md must not be excessively long
    # Should be under 80 non-empty lines (short enough for startup loading)
    # =========================================================================
    non_empty_lines = [l for l in memory_md.splitlines() if l.strip()]
    line_count = len(non_empty_lines)
    is_short_enough = line_count <= 80
    checks.append({
        "name": "MEMORY.md is short enough for startup loading (<=80 non-empty lines)",
        "passed": is_short_enough,
        "detail": f"MEMORY.md has {line_count} non-empty lines. Limit: 80."
    })

    return checks

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = run_eval(workspace)
    passed_checks = [c for c in checks if c["passed"]]
    score = round(len(passed_checks) / len(checks), 4) if checks else 0.0
    overall = score >= 0.80  # must pass at least 80% of checks

    result = {
        "passed": overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()