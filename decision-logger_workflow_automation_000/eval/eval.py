import sys
import re
import json
import subprocess
from pathlib import Path
from datetime import date, datetime

workspace = Path(sys.argv[1])

checks = []
score = 0.0
total_weight = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global score, total_weight
    total_weight += weight
    if passed:
        score += weight

# ── Load files ───────────────────────────────────────────────────────
decisions_path = workspace / "memory/board-meetings/decisions.md"
raw_path = workspace / "memory/board-meetings/2026-04-28-raw.md"

try:
    decisions_text = decisions_path.read_text(encoding="utf-8")
except Exception as e:
    decisions_text = ""
    add_check("decisions.md readable", False, f"Cannot read decisions.md: {e}", weight=3.0)

try:
    raw_text = raw_path.read_text(encoding="utf-8")
    raw_exists = True
except Exception as e:
    raw_text = ""
    raw_exists = False

# ══════════════════════════════════════════════════════════════════════
# CHECK GROUP 1: Layer 1 Raw Transcript
# ══════════════════════════════════════════════════════════════════════

add_check(
    "Layer 1: 2026-04-28-raw.md exists",
    raw_exists,
    f"File {'found' if raw_exists else 'NOT found'} at memory/board-meetings/2026-04-28-raw.md",
    weight=1.5
)

if raw_exists:
    # Raw transcript should contain meeting content (all three agenda items referenced)
    has_rd = bool(re.search(r"R.?D|budget|reallocation", raw_text, re.IGNORECASE))
    has_pricing = bool(re.search(r"pric|tier|diagnostic kit", raw_text, re.IGNORECASE))
    has_series = bool(re.search(r"series.?b|extension|5M|Helion|Apex", raw_text, re.IGNORECASE))
    add_check(
        "Layer 1: Contains meeting content (3 agenda items)",
        has_rd and has_pricing and has_series,
        f"R&D content: {has_rd}, Pricing content: {has_pricing}, Series B content: {has_series}",
        weight=1.0
    )

# ══════════════════════════════════════════════════════════════════════
# CHECK GROUP 2: Three New Decision Entries Appended
# ══════════════════════════════════════════════════════════════════════

# Check all three agenda items are logged as decisions
has_rd_decision = bool(re.search(r"## \[2026-04-28\].*R.?D Budget", decisions_text, re.IGNORECASE))
has_pricing_decision = bool(re.search(r"## \[2026-04-28\].*Pric", decisions_text, re.IGNORECASE))
has_series_decision = bool(re.search(r"## \[2026-04-28\].*Series.?B", decisions_text, re.IGNORECASE))

add_check(
    "Layer 2: R&D Budget Reallocation decision entry added",
    has_rd_decision,
    f"'## [2026-04-28] — R&D Budget...' entry {'found' if has_rd_decision else 'NOT found'} in decisions.md",
    weight=1.5
)
add_check(
    "Layer 2: Pricing Model decision entry added",
    has_pricing_decision,
    f"'## [2026-04-28] — Pricing...' entry {'found' if has_pricing_decision else 'NOT found'} in decisions.md",
    weight=1.5
)
add_check(
    "Layer 2: Series B Extension decision entry added",
    has_series_decision,
    f"'## [2026-04-28] — Series B...' entry {'found' if has_series_decision else 'NOT found'} in decisions.md",
    weight=1.5
)

# ══════════════════════════════════════════════════════════════════════
# CHECK GROUP 3: Correct Supersedes/Superseded-by Fields
# ══════════════════════════════════════════════════════════════════════

# The R&D decision must say Supersedes: 2025-11-04
rd_supersedes = bool(re.search(
    r"## \[2026-04-28\].*?(?=## \[|\Z).*?\*\*Supersedes:\*\*.*?2025-11-04",
    decisions_text, re.DOTALL | re.IGNORECASE
))
add_check(
    "R&D decision: Supersedes 2025-11-04 correctly stated",
    rd_supersedes,
    f"'**Supersedes:** 2025-11-04' {'found' if rd_supersedes else 'NOT found'} in R&D decision block",
    weight=2.0
)

# The pricing decision must say Supersedes: 2026-01-15
pricing_supersedes = bool(re.search(
    r"## \[2026-04-28\].*?(?=## \[|\Z).*?\*\*Supersedes:\*\*.*?2026-01-15",
    decisions_text, re.DOTALL | re.IGNORECASE
))
add_check(
    "Pricing decision: Supersedes 2026-01-15 correctly stated",
    pricing_supersedes,
    f"'**Supersedes:** 2026-01-15' {'found' if pricing_supersedes else 'NOT found'} in pricing decision block",
    weight=2.0
)

# The OLD 2025-11-04 R&D entry must have Superseded by: 2026-04-28 retroactively filled
old_rd_block_match = re.search(
    r"## \[2025-11-04\].*?(?=## \[|\Z)", decisions_text, re.DOTALL
)
if old_rd_block_match:
    old_rd_block = old_rd_block_match.group(0)
    old_rd_superseded = bool(re.search(r"\*\*Superseded by:\*\*.*?2026-04-28", old_rd_block, re.IGNORECASE))
else:
    old_rd_block = ""
    old_rd_superseded = False

add_check(
    "Retroactive: 2025-11-04 R&D entry has 'Superseded by: 2026-04-28'",
    old_rd_superseded,
    f"Old R&D block {'has' if old_rd_superseded else 'MISSING'} retroactive 'Superseded by: 2026-04-28'",
    weight=2.5
)

# The OLD 2026-01-15 pricing entry must have Superseded by: 2026-04-28 retroactively filled
old_pricing_block_match = re.search(
    r"## \[2026-01-15\].*?(?=## \[|\Z)", decisions_text, re.DOTALL
)
if old_pricing_block_match:
    old_pricing_block = old_pricing_block_match.group(0)
    old_pricing_superseded = bool(re.search(r"\*\*Superseded by:\*\*.*?2026-04-28", old_pricing_block, re.IGNORECASE))
else:
    old_pricing_block = ""
    old_pricing_superseded = False

add_check(
    "Retroactive: 2026-01-15 pricing entry has 'Superseded by: 2026-04-28'",
    old_pricing_superseded,
    f"Old pricing block {'has' if old_pricing_superseded else 'MISSING'} retroactive 'Superseded by: 2026-04-28'",
    weight=2.5
)

# ══════════════════════════════════════════════════════════════════════
# CHECK GROUP 4: DO_NOT_RESURFACE Handling — Pricing Decision
# ══════════════════════════════════════════════════════════════════════

# New pricing decision involves tiered subscription — which was DO_NOT_RESURFACE on 2026-01-15
# The agent must handle this with a User Override citing founder re-open
pricing_block_match = re.search(
    r"## \[2026-04-28\].*?Pric.*?(?=## \[|\Z)", decisions_text, re.DOTALL | re.IGNORECASE
)
if pricing_block_match:
    pricing_block = pricing_block_match.group(0)
    # User Override should mention founder explicitly reopened tiered pricing
    has_user_override = bool(re.search(
        r"\*\*User Override:\*\*(?!.*Blank).*?(founder|reopen|tiered|2026-01-15)",
        pricing_block, re.IGNORECASE | re.DOTALL
    ))
    add_check(
        "Pricing decision: User Override documents founder's DO_NOT_RESURFACE override",
        has_user_override,
        f"User Override field {'correctly documents' if has_user_override else 'MISSING or blank — founder re-open of DO_NOT_RESURFACE item not documented'} founder override",
        weight=3.0
    )
    # The per-test transactional model should still carry DO_NOT_RESURFACE
    transactional_dnr = bool(re.search(
        r"Per-test|transactional.*\[DO_NOT_RESURFACE\]",
        pricing_block, re.IGNORECASE
    ))
    add_check(
        "Pricing decision: Per-test model still carries DO_NOT_RESURFACE tag",
        transactional_dnr,
        f"Per-test model DO_NOT_RESURFACE {'present' if transactional_dnr else 'MISSING'} in new pricing decision's Rejected section",
        weight=1.5
    )
else:
    add_check(
        "Pricing decision: User Override documents founder's DO_NOT_RESURFACE override",
        False,
        "Pricing decision block not found at all",
        weight=3.0
    )
    add_check(
        "Pricing decision: Per-test model still carries DO_NOT_RESURFACE tag",
        False,
        "Pricing decision block not found",
        weight=1.5
    )

# ══════════════════════════════════════════════════════════════════════
# CHECK GROUP 5: Action Items Format
# ══════════════════════════════════════════════════════════════════════

# Check action items use correct checkbox format: - [ ] ... Owner: ... Due: ... Review: ...
action_pattern = re.compile(
    r"- \[ \] .+ — Owner: .+ — Due: \d{4}-\d{2}-\d{2} — Review: \d{4}-\d{2}-\d{2}"
)
new_entries_text = ""
for match in re.finditer(r"## \[2026-04-28\].*?(?=## \[|\Z)", decisions_text, re.DOTALL):
    new_entries_text += match.group(0)

action_items_found = action_pattern.findall(new_entries_text)
add_check(
    "Action items use correct checkbox format (- [ ] ... Owner/Due/Review)",
    len(action_items_found) >= 5,
    f"Found {len(action_items_found)} correctly formatted action items in new entries (expected ≥5 across 3 decisions)",
    weight=2.0
)

# ══════════════════════════════════════════════════════════════════════
# CHECK GROUP 6: Founder Override on Series B documented
# ══════════════════════════════════════════════════════════════════════
series_block_match = re.search(
    r"## \[2026-04-28\].*?Series.*?(?=## \[|\Z)", decisions_text, re.DOTALL | re.IGNORECASE
)
if series_block_match:
    series_block = series_block_match.group(0)
    series_override = bool(re.search(
        r"\*\*User Override:\*\*(?!.*Blank).*?(5M|founder|dilution|\$5)",
        series_block, re.IGNORECASE | re.DOTALL
    ))
    add_check(
        "Series B decision: Founder override (5M vs 8M) documented",
        series_override,
        f"Series B User Override {'correctly documents' if series_override else 'MISSING'} founder change from $8M to $5M",
        weight=1.5
    )
else:
    add_check(
        "Series B decision: Founder override (5M vs 8M) documented",
        False,
        "Series B decision block not found",
        weight=1.5
    )

# ══════════════════════════════════════════════════════════════════════
# CHECK GROUP 7: decisions.md is append-only — original entries preserved
# ══════════════════════════════════════════════════════════════════════

original_entries_present = (
    "## [2025-11-04]" in decisions_text and
    "## [2026-01-15]" in decisions_text and
    "## [2026-02-20]" in decisions_text
)
add_check(
    "decisions.md is append-only: all original 3 entries still present",
    original_entries_present,
    f"Original entries preserved: {'yes' if original_entries_present else 'NO — entries were deleted or modified destructively'}",
    weight=2.0
)

# ══════════════════════════════════════════════════════════════════════
# CHECK GROUP 8: CLI tool verification (--summary and --conflicts run clean)
# ══════════════════════════════════════════════════════════════════════

try:
    result = subprocess.run(
        ["python", "scripts/decision_tracker.py", "--summary"],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        timeout=15
    )
    cli_summary_ok = result.returncode == 0 and ("decision" in result.stdout.lower() or "active" in result.stdout.lower())
    add_check(
        "CLI --summary runs successfully on updated decisions.md",
        cli_summary_ok,
        f"Return code: {result.returncode}. Output snippet: {result.stdout[:200]}",
        weight=1.0
    )
except Exception as e:
    add_check(
        "CLI --summary runs successfully on updated decisions.md",
        False,
        f"CLI execution failed: {e}",
        weight=1.0
    )

try:
    result = subprocess.run(
        ["python", "scripts/decision_tracker.py", "--conflicts"],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        timeout=15
    )
    cli_conflicts_ok = result.returncode == 0
    add_check(
        "CLI --conflicts runs without error on updated decisions.md",
        cli_conflicts_ok,
        f"Return code: {result.returncode}. Stderr: {result.stderr[:200] if result.stderr else 'none'}",
        weight=1.0
    )
except Exception as e:
    add_check(
        "CLI --conflicts runs without error on updated decisions.md",
        False,
        f"CLI execution failed: {e}",
        weight=1.0
    )

# ══════════════════════════════════════════════════════════════════════
# CHECK GROUP 9: Raw transcript file NOT loaded as decisions.md
# ══════════════════════════════════════════════════════════════════════

# decisions.md should not contain raw debate/transcript markers
raw_transcript_leaked = bool(re.search(
    r"Phase [234] (contribution|critique|synthesis|agent)|<<<|>>>|DEBATE:", 
    decisions_text, re.IGNORECASE
))
add_check(
    "Layer separation: Raw transcript content not leaked into decisions.md",
    not raw_transcript_leaked,
    f"Raw transcript markers {'NOT found (clean)' if not raw_transcript_leaked else 'FOUND in decisions.md — layer contamination detected'}",
    weight=1.0
)

# ══════════════════════════════════════════════════════════════════════
# FINAL SCORING
# ══════════════════════════════════════════════════════════════════════

final_score = round(score / total_weight, 4) if total_weight > 0 else 0.0
passed = final_score >= 0.75 and all(
    c["passed"] for c in checks if c["name"] in [
        "Layer 2: R&D Budget Reallocation decision entry added",
        "Layer 2: Pricing Model decision entry added",
        "Layer 2: Series B Extension decision entry added",
        "Retroactive: 2025-11-04 R&D entry has 'Superseded by: 2026-04-28'",
        "Retroactive: 2026-01-15 pricing entry has 'Superseded by: 2026-04-28'",
        "Pricing decision: User Override documents founder's DO_NOT_RESURFACE override",
        "decisions.md is append-only: all original 3 entries still present",
    ]
)

output = {
    "passed": passed,
    "score": final_score,
    "checks": checks
}
print(json.dumps(output, indent=2))