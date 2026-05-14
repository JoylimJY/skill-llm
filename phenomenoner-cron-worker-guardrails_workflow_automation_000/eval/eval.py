import sys
import json
import os
import re
import subprocess
from pathlib import Path

workspace = sys.argv[1]

checks = []

def check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

# ── Helper ──────────────────────────────────────────────────────────────────
def read(path):
    with open(path) as f:
        return f.read()

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 1: tools/nightly_summary.py exists (scripts-first refactor)
# ══════════════════════════════════════════════════════════════════════════════
tool_script = Path(workspace) / "tools" / "nightly_summary.py"
try:
    assert tool_script.exists(), "File not found"
    src = read(tool_script)
    check("tools/nightly_summary.py exists", True, "Found")
except Exception as e:
    check("tools/nightly_summary.py exists", False, str(e))
    src = ""

# CHECK 1b: the tool script does NOT use bash -lc or python -c inline logic
try:
    bad_patterns = ["bash -lc", "python3 -c", "python -c"]
    found_bad = [p for p in bad_patterns if p in src]
    check("nightly_summary.py avoids inline shell python -c / bash -lc",
          len(found_bad) == 0,
          f"Found forbidden patterns: {found_bad}" if found_bad else "Clean")
except Exception as e:
    check("nightly_summary.py avoids inline shell python -c / bash -lc", False, str(e))

# CHECK 1c: the tool script contains csv/json logic (actually does the work)
try:
    has_csv = "csv" in src or "open(" in src
    has_json = "json" in src
    check("nightly_summary.py contains CSV/JSON data processing",
          has_csv and has_json,
          f"csv_logic={has_csv}, json_logic={has_json}")
except Exception as e:
    check("nightly_summary.py contains CSV/JSON data processing", False, str(e))

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 2: NO_REPLY silent-on-success convention in nightly_summary.py
# ══════════════════════════════════════════════════════════════════════════════
try:
    # Agent must emit NO_REPLY (or print nothing) on success — NO_REPLY is the OpenClaw convention
    no_reply_present = "NO_REPLY" in src
    # Also acceptable: the script prints nothing on success path
    # We check for at least the convention being honored: either NO_REPLY string or
    # no unconditional print/echo on the happy path
    # Strict check: NO_REPLY must appear somewhere (the skill says emit exactly NO_REPLY)
    check("nightly_summary.py uses NO_REPLY convention on success",
          no_reply_present,
          "NO_REPLY found in script" if no_reply_present else "NO_REPLY string absent — silent-on-success convention not applied")
except Exception as e:
    check("nightly_summary.py uses NO_REPLY convention on success", False, str(e))

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 3: nightly_summary.sh (or new wrapper) references tools/nightly_summary.py
#          and does NOT contain the broken bash -lc inline block
# ══════════════════════════════════════════════════════════════════════════════
nightly_sh = Path(workspace) / "scripts" / "nightly_summary.sh"
try:
    sh_src = read(nightly_sh)
    has_tool_call = "tools/nightly_summary.py" in sh_src or "tools/nightly_summary" in sh_src
    still_broken = "bash -lc" in sh_src and "python3 -c" in sh_src
    check("nightly_summary.sh calls tools/nightly_summary.py (scripts-first)",
          has_tool_call,
          "Calls tool script" if has_tool_call else "Still uses inline logic, not refactored")
    check("nightly_summary.sh no longer contains broken bash -lc + python3 -c block",
          not still_broken,
          "Cleaned up" if not still_broken else "bash -lc + python3 -c inline block still present")
except Exception as e:
    check("nightly_summary.sh calls tools/nightly_summary.py (scripts-first)", False, str(e))
    check("nightly_summary.sh no longer contains broken bash -lc + python3 -c block", False, str(e))

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 4: top_price_alert.sh — pipefail + head SIGPIPE fix
# ══════════════════════════════════════════════════════════════════════════════
alert_sh = Path(workspace) / "scripts" / "top_price_alert.sh"
try:
    alert_src = read(alert_sh)
    # The fix: pipefail must NOT be set when piping into head, OR the pipe-to-head is removed
    # Acceptable signals: removal of "set -euo pipefail" / "set -o pipefail", 
    # OR the head | pipeline is replaced by script-based filtering
    still_has_pipefail = bool(re.search(r'set\s+.*pipefail|set\s+-[a-z]*o\s+pipefail', alert_src))
    still_pipes_to_head = bool(re.search(r'\|\s*head', alert_src))
    # Bad = both present together
    bad_combo = still_has_pipefail and still_pipes_to_head
    check("top_price_alert.sh: pipefail + head SIGPIPE combo removed",
          not bad_combo,
          "Fixed: pipefail+head combo gone" if not bad_combo else "STILL has 'set ...pipefail' combined with pipe-to-head")
except Exception as e:
    check("top_price_alert.sh: pipefail + head SIGPIPE combo removed", False, str(e))

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 5: push_report.sh — non-fast-forward rejection handling (fetch + cherry-pick, NO force)
# ══════════════════════════════════════════════════════════════════════════════
push_sh = Path(workspace) / "scripts" / "push_report.sh"
try:
    push_src = read(push_sh)
    # Must NOT use --force or -f push
    uses_force = bool(re.search(r'git push.*--force|git push.*\s-f\b', push_src))
    # Must handle rejection: fetch the remote branch AND cherry-pick (or rebase/cherry-pick onto it)
    has_fetch = "git fetch" in push_src
    has_cherry_pick = "cherry-pick" in push_src
    has_retry_push = push_src.count("git push") >= 2  # original push + retry push
    check("push_report.sh: no force-push",
          not uses_force,
          "No force push found" if not uses_force else "FORBIDDEN --force / -f push found")
    check("push_report.sh: fetches remote branch on rejection",
          has_fetch,
          "git fetch present" if has_fetch else "No git fetch — rejection recovery missing")
    check("push_report.sh: uses cherry-pick to transplant commits",
          has_cherry_pick,
          "cherry-pick present" if has_cherry_pick else "No cherry-pick — conservative rebase pattern missing")
    check("push_report.sh: retries git push after recovery",
          has_retry_push,
          f"Found {push_src.count('git push')} git push invocations (need ≥ 2)" )
except Exception as e:
    check("push_report.sh: no force-push", False, str(e))
    check("push_report.sh: fetches remote branch on rejection", False, str(e))
    check("push_report.sh: uses cherry-pick to transplant commits", False, str(e))
    check("push_report.sh: retries git push after recovery", False, str(e))

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 6: tools/nightly_summary.py is actually runnable (basic syntax check)
# ══════════════════════════════════════════════════════════════════════════════
try:
    result = subprocess.run(
        ["python3", "-m", "py_compile", str(tool_script)],
        capture_output=True, text=True, timeout=10
    )
    check("tools/nightly_summary.py passes Python syntax check",
          result.returncode == 0,
          "Syntax OK" if result.returncode == 0 else result.stderr.strip())
except Exception as e:
    check("tools/nightly_summary.py passes Python syntax check", False, str(e))

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 7: Hardening header present somewhere (cron wrapper or new file)
# ══════════════════════════════════════════════════════════════════════════════
try:
    # The skill mandates a 2-line hardening header mentioning cron-agent-contract.md
    # and cron-worker-guardrails. Check nightly_summary.sh and/or the tool script.
    combined = ""
    for candidate in [
        Path(workspace) / "scripts" / "nightly_summary.sh",
        Path(workspace) / "tools" / "nightly_summary.py",
    ]:
        if candidate.exists():
            combined += read(candidate)

    has_contract_ref = "cron-agent-contract" in combined
    has_skill_ref = "cron-worker-guardrails" in combined
    check("Hardening header references cron-agent-contract.md",
          has_contract_ref,
          "Reference found" if has_contract_ref else "No mention of cron-agent-contract.md in wrapper or tool script")
    check("Hardening header references cron-worker-guardrails skill",
          has_skill_ref,
          "Reference found" if has_skill_ref else "No mention of cron-worker-guardrails in wrapper or tool script")
except Exception as e:
    check("Hardening header references cron-agent-contract.md", False, str(e))
    check("Hardening header references cron-worker-guardrails skill", False, str(e))

# ══════════════════════════════════════════════════════════════════════════════
# SCORE
# ══════════════════════════════════════════════════════════════════════════════
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4)
all_passed = passed_count == total

print(json.dumps({
    "passed": all_passed,
    "score": score,
    "checks": checks
}, indent=2))