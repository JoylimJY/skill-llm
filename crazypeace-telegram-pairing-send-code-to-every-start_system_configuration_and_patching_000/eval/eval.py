import sys
import json
import re
from pathlib import Path

TARGET = Path("/usr/lib/node_modules/openclaw/lib/pairing/channels/telegram.js")
INVOCATION_LOG = Path("/tmp/openclaw_invocations.log")

checks = []

# ── Check 1: Target file exists ──────────────────────────────────────────────
try:
    content = TARGET.read_text(encoding="utf-8")
    checks.append({
        "name": "target_file_exists",
        "passed": True,
        "detail": f"File found at {TARGET}"
    })
except FileNotFoundError:
    checks.append({
        "name": "target_file_exists",
        "passed": False,
        "detail": f"File not found: {TARGET}"
    })
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)
except Exception as e:
    checks.append({
        "name": "target_file_exists",
        "passed": False,
        "detail": f"Unexpected error reading file: {e}"
    })
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── Check 2: The OLD guard clause `if (!created)` is GONE ───────────────────
old_pattern = re.compile(r'if\s*\(\s*!\s*created\s*\)')
has_old = bool(old_pattern.search(content))
checks.append({
    "name": "old_guard_removed",
    "passed": not has_old,
    "detail": (
        "Old guard `if (!created)` still present — not modified"
        if has_old else
        "Old guard `if (!created)` correctly removed"
    )
})

# ── Check 3: The NEW guard clause `if (!code)` is PRESENT ───────────────────
new_pattern = re.compile(r'if\s*\(\s*!\s*code\s*\)')
has_new = bool(new_pattern.search(content))
checks.append({
    "name": "new_guard_present",
    "passed": has_new,
    "detail": (
        "New guard `if (!code)` not found — critical change missing"
        if not has_new else
        "New guard `if (!code)` correctly added"
    )
})

# ── Check 4: The early return still returns `{ created: false }` ─────────────
# The new guard must still return { created: false } (same semantics for the
# return value, just triggered on a different condition)
return_pattern = re.compile(
    r'if\s*\(\s*!\s*code\s*\)\s*return\s*\{\s*created\s*:\s*false\s*\}'
)
has_correct_return = bool(return_pattern.search(content))
checks.append({
    "name": "early_return_semantics_preserved",
    "passed": has_correct_return,
    "detail": (
        "The `if (!code)` guard does not return `{ created: false }` — "
        "return value semantics changed incorrectly"
        if not has_correct_return else
        "`if (!code) return { created: false }` correctly in place"
    )
})

# ── Check 5: `issuePairingChallenge` function is still intact ────────────────
fn_pattern = re.compile(r'async\s+function\s+issuePairingChallenge\s*\(')
has_fn = bool(fn_pattern.search(content))
checks.append({
    "name": "function_signature_intact",
    "passed": has_fn,
    "detail": (
        "`issuePairingChallenge` function signature not found — "
        "function may have been accidentally deleted or renamed"
        if not has_fn else
        "Function signature intact"
    )
})

# ── Check 6: `openclaw gateway restart` was called ───────────────────────────
try:
    invocations = INVOCATION_LOG.read_text(encoding="utf-8")
    restart_pattern = re.compile(r'gateway\s+restart')
    restarted = bool(restart_pattern.search(invocations))
    checks.append({
        "name": "openclaw_gateway_restart_called",
        "passed": restarted,
        "detail": (
            "`openclaw gateway restart` was NOT called — service must be "
            "restarted for changes to take effect"
            if not restarted else
            "`openclaw gateway restart` correctly invoked"
        )
    })
except FileNotFoundError:
    checks.append({
        "name": "openclaw_gateway_restart_called",
        "passed": False,
        "detail": "Invocation log not found — `openclaw` was never called"
    })
except Exception as e:
    checks.append({
        "name": "openclaw_gateway_restart_called",
        "passed": False,
        "detail": f"Error reading invocation log: {e}"
    })

# ── Scoring ──────────────────────────────────────────────────────────────────
# Weights: the two core logic checks are most important
weights = {
    "target_file_exists":              0.10,
    "old_guard_removed":               0.25,
    "new_guard_present":               0.25,
    "early_return_semantics_preserved":0.20,
    "function_signature_intact":       0.10,
    "openclaw_gateway_restart_called": 0.10,
}

score = sum(
    weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights
)

all_passed = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": all_passed,
    "score": round(score, 4),
    "checks": checks
}, ensure_ascii=False, indent=2))