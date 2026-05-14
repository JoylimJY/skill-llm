import sys
import json
import re
from pathlib import Path
from datetime import date

workspace = Path(sys.argv[1])

checks = []

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# ─── HELPER ───────────────────────────────────────────────────────────────────
def read_file(path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return None

def find_file(pattern):
    results = list(workspace.rglob(pattern))
    return results[0] if results else None

# ─── 1. Daily Notes Created for New Sessions ──────────────────────────────────

# Session A note (pre-existing, but agent should not overwrite incorrectly)
# Sessions B and C and D daily notes must exist with correct entries
for date_str, expected_tags in [
    ("2025-01-22", ["PREFERENCE", "BOUNDARY", "GOAL"]),
    ("2025-02-05", ["PREFERENCE"]),
    ("2025-03-15", ["FACT", "PREFERENCE", "GOAL"]),
]:
    note_path = workspace / "memory" / f"{date_str}.md"
    content = read_file(note_path)
    if content is None:
        check(f"daily_note_exists_{date_str}", False, f"File memory/{date_str}.md not found.")
        continue
    check(f"daily_note_exists_{date_str}", True, f"memory/{date_str}.md exists.")
    for tag in expected_tags:
        found = tag in content
        check(
            f"daily_note_{date_str}_has_{tag}",
            found,
            f"Expected tag {tag} in memory/{date_str}.md. Content snippet: {content[:300]}"
        )

# ─── 2. Session D (2025-03-15) Daily Note — Project Helix as GOAL, impact 3 ──
note_d = workspace / "memory" / "2025-03-15.md"
content_d = read_file(note_d)
if content_d:
    # Must have GOAL for Project Helix
    helix_goal = bool(re.search(r'GOAL.*[Hh]elix|[Hh]elix.*GOAL', content_d))
    check("daily_2025-03-15_helix_goal", helix_goal,
          f"Project Helix should be tagged GOAL in 2025-03-15.md. Found: {content_d[:400]}")
    # Must have impact: 3 for Helix (outcome-critical)
    helix_impact3 = bool(re.search(r'[Hh]elix[\s\S]{0,120}impact\s*:\s*3|impact\s*:\s*3[\s\S]{0,60}[Hh]elix', content_d))
    check("daily_2025-03-15_helix_impact3", helix_impact3,
          f"Project Helix must have impact:3 (outcome-critical). Content: {content_d[:500]}")
    # dark mode must be PREFERENCE (explicitly confirmed)
    darkmode_pref = bool(re.search(r'PREFERENCE.*dark.?mode|dark.?mode.*PREFERENCE', content_d, re.IGNORECASE))
    check("daily_2025-03-15_darkmode_preference", darkmode_pref,
          f"Dark mode must be tagged PREFERENCE. Content: {content_d[:500]}")
else:
    check("daily_2025-03-15_helix_goal", False, "2025-03-15.md missing.")
    check("daily_2025-03-15_helix_impact3", False, "2025-03-15.md missing.")
    check("daily_2025-03-15_darkmode_preference", False, "2025-03-15.md missing.")

# ─── 3. Session C: Rust forgetting — must be absent from MEMORY.md & notes ────
memory_md_path = workspace / "MEMORY.md"
memory_content = read_file(memory_md_path)

if memory_content:
    rust_absent = "rust" not in memory_content.lower()
    check("memory_md_rust_forgotten", rust_absent,
          f"Rust interest must NOT appear in MEMORY.md (user requested forget). Content snippet: {memory_content[:600]}")
else:
    check("memory_md_rust_forgotten", False, "MEMORY.md not found.")

# ─── 4. MEMORY.md Exists and Has Required Long-Term Entries ───────────────────
if memory_content is None:
    check("memory_md_exists", False, "MEMORY.md not found.")
    for _ in range(12):
        checks.append({"name": "memory_md_content_check", "passed": False, "detail": "MEMORY.md missing"})
else:
    check("memory_md_exists", True, "MEMORY.md found.")

    # Must contain Python preference (repeated 3 sessions: A, B implied, D)
    python_pref = bool(re.search(r'PREFERENCE.*[Pp]ython|[Pp]ython.*PREFERENCE', memory_content))
    check("memory_md_python_preference", python_pref,
          f"Python code examples preference must be in MEMORY.md (repeated 3+ sessions). Snippet: {memory_content[:500]}")

    # Must contain short/direct answers preference (sessions A and C = repeated)
    short_answers = bool(re.search(r'PREFERENCE.*short|short.*PREFERENCE|PREFERENCE.*direct|direct.*PREFERENCE', memory_content, re.IGNORECASE))
    check("memory_md_short_answers", short_answers,
          f"Short/direct answers preference must be in MEMORY.md. Content: {memory_content[:500]}")

    # BOUNDARY: do not store company name (explicit boundary, impact 3 = promote immediately)
    company_boundary = bool(re.search(r'BOUNDARY.*company|company.*BOUNDARY', memory_content, re.IGNORECASE))
    check("memory_md_company_boundary", company_boundary,
          f"Company name boundary must be promoted to MEMORY.md. Content: {memory_content[:600]}")

    # Project Helix must be in MEMORY.md (impact 3, promote immediately)
    helix_in_memory = bool(re.search(r'[Hh]elix', memory_content))
    check("memory_md_helix_project", helix_in_memory,
          f"Project Helix (impact 3, outcome-critical) must be promoted to MEMORY.md immediately. Content: {memory_content[:600]}")

    # dark mode preference (explicitly confirmed in session D) must be in MEMORY.md
    darkmode_memory = bool(re.search(r'dark.?mode', memory_content, re.IGNORECASE))
    check("memory_md_darkmode", darkmode_memory,
          f"Dark mode preference (explicitly confirmed) must be in MEMORY.md. Content: {memory_content[:600]}")

    # Fast decision-making preference must be promoted (impact 2, repeated or explicit)
    fast_decision = bool(re.search(r'decision|caveat|fast', memory_content, re.IGNORECASE))
    check("memory_md_fast_decisions", fast_decision,
          f"Fast decision-making preference must be in MEMORY.md. Content: {memory_content[:500]}")

    # pytest preference (explicit, score 2) must be in MEMORY.md
    pytest_pref = bool(re.search(r'pytest', memory_content, re.IGNORECASE))
    check("memory_md_pytest", pytest_pref,
          f"pytest preference must be in MEMORY.md (explicit, impact 2). Content: {memory_content[:500]}")

# ─── 5. Promotion Rule: HYPOTHESIS must NOT be in MEMORY.md unless confirmed ──
if memory_content:
    # The two pre-existing hypotheses (async/await and pair-programming) were NEVER confirmed
    # They must NOT appear as non-demoted entries in MEMORY.md
    async_hyp_not_promoted = not bool(re.search(r'async.*await|threading', memory_content, re.IGNORECASE))
    check("memory_md_no_unconfirmed_hypothesis_async", async_hyp_not_promoted,
          f"Unconfirmed HYPOTHESIS (async/await preference) must NOT be in MEMORY.md. Content: {memory_content[:600]}")

    pair_prog_not_promoted = not bool(re.search(r'pair.?program', memory_content, re.IGNORECASE))
    check("memory_md_no_unconfirmed_hypothesis_pairprog", pair_prog_not_promoted,
          f"Unconfirmed HYPOTHESIS (pair-programming) must NOT be in MEMORY.md. Content: {memory_content[:600]}")

# ─── 6. Confidence Decay Check ────────────────────────────────────────────────
# Today is 2025-03-15
# async/await HYPOTHESIS was created 2025-01-10 = 64 days ago → must be DISCARDED (>60 days)
# pair-programming HYPOTHESIS was created 2025-01-22 = 52 days ago → must be LOW or discarded (>30 days)

# Check in memory/2025-01-10.md: async/await hypothesis should be noted as discarded/removed
note_a = workspace / "memory" / "2025-01-10.md"
content_a = read_file(note_a)
if content_a:
    # Agent may update the original file or create a new daily note referencing the discard
    async_discarded = bool(re.search(r'discard|remov|stale|decay|drop', content_a, re.IGNORECASE))
    # Alternatively agent may just not carry it forward — check MEMORY.md (already checked above)
    # We also check if the daily note annotates it as stale
    check("hypothesis_async_decayed_or_discarded", async_discarded or async_hyp_not_promoted,
          f"async/await hypothesis (64 days old) must be discarded or marked stale. note_a: {content_a[:300]}")
else:
    check("hypothesis_async_decayed_or_discarded", False, "memory/2025-01-10.md missing.")

# ─── 7. Lodestar Demotion: project paused in session C ────────────────────────
# Lodestar v1 GOAL must NOT appear as an active goal in MEMORY.md (it was paused/abandoned trajectory)
if memory_content:
    # Lodestar goal should not be listed as active/ongoing goal
    # It may appear as paused/stale but not as an active priority
    lodestar_active = bool(re.search(r'GOAL.*[Ll]odestar.*v1|[Ll]odestar.*Q1\s*2025', memory_content))
    check("memory_md_lodestar_not_active_goal", not lodestar_active,
          f"Lodestar v1/Q1 2025 goal must be demoted (project paused). Content: {memory_content[:600]}")
else:
    check("memory_md_lodestar_not_active_goal", False, "MEMORY.md missing.")

# ─── 8. Correct tag integrity: no FACT is inferred ────────────────────────────
# Check that the agent hasn't tagged something as FACT that can only be inferred
# The dark mode preference in session D was EXPLICITLY stated, so it CAN be FACT or PREFERENCE
# The async/await pattern was INFERRED from architecture → must be HYPOTHESIS, not FACT
if content_a:
    async_not_fact = not bool(re.search(r'FACT.*async|async.*FACT', content_a, re.IGNORECASE))
    check("tag_integrity_async_not_fact", async_not_fact,
          f"async/await pattern is inferred and must NOT be tagged FACT. content_a snippet: {content_a[:300]}")
else:
    check("tag_integrity_async_not_fact", False, "memory/2025-01-10.md missing.")

# ─── SCORING ──────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4) if total > 0 else 0.0
passed_overall = score >= 0.75

result = {
    "passed": passed_overall,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))