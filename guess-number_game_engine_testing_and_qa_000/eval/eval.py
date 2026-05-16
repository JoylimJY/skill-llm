import sys
import os
import json
import subprocess
import random

workspace = sys.argv[1]

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# Determine the expected secret with seed=42
random.seed(42)
digits = list("0123456789")
random.shuffle(digits)
expected_secret = "".join(digits[:4])

# ── 1. Find game_report.json ──────────────────────────────────────────────────
from pathlib import Path

report_files = list(Path(workspace).rglob("game_report.json"))
if not report_files:
    add_check("game_report.json exists", False, "No game_report.json found anywhere in workspace")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

report_path = report_files[0]
add_check("game_report.json exists", True, f"Found at {report_path}")

# ── 2. Parse the report ───────────────────────────────────────────────────────
try:
    with open(report_path, "r") as f:
        report = json.load(f)
    add_check("game_report.json is valid JSON", True, "Parsed successfully")
except Exception as e:
    add_check("game_report.json is valid JSON", False, f"JSON parse error: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── 3. secret.txt must NOT exist (game ended via correct guess) ───────────────
secret_path = os.path.join(workspace, "scripts", "secret.txt")
steps_path  = os.path.join(workspace, "scripts", "steps.txt")

secret_gone = not os.path.exists(secret_path)
steps_gone  = not os.path.exists(steps_path)

add_check(
    "secret.txt auto-deleted after win",
    secret_gone,
    "secret.txt correctly absent" if secret_gone else "secret.txt still exists — game was not completed or cleanup failed"
)
add_check(
    "steps.txt auto-deleted after win",
    steps_gone,
    "steps.txt correctly absent" if steps_gone else "steps.txt still exists — cleanup failed"
)

# ── 4. Check report has required fields ──────────────────────────────────────
required_fields = ["secret_deleted", "valid_guess_count", "invalid_guess_count",
                   "final_step_count", "error_messages"]
missing = [f for f in required_fields if f not in report]
if missing:
    add_check("report has all required fields", False, f"Missing fields: {missing}")
else:
    add_check("report has all required fields", True, "All required fields present")

if missing:
    print(json.dumps({"passed": False, "score": 0.2, "checks": checks}))
    sys.exit(0)

# ── 5. secret_deleted must be true ───────────────────────────────────────────
add_check(
    "report.secret_deleted is true",
    report["secret_deleted"] is True,
    f"Got: {report['secret_deleted']}"
)

# ── 6. invalid_guess_count must be >= 3 (all 3 error types tested) ────────────
inv_count = report["invalid_guess_count"]
inv_ok = isinstance(inv_count, int) and inv_count >= 3
add_check(
    "invalid_guess_count >= 3 (all error types exercised)",
    inv_ok,
    f"Got invalid_guess_count={inv_count}; must be >= 3 to cover all 3 error types"
)

# ── 7. final_step_count must equal valid_guess_count ─────────────────────────
valid_count   = report["valid_guess_count"]
final_steps   = report["final_step_count"]

counts_match = (isinstance(valid_count, int) and isinstance(final_steps, int)
                and valid_count == final_steps and valid_count >= 1)
add_check(
    "final_step_count equals valid_guess_count (invalid inputs don't consume steps)",
    counts_match,
    f"valid_guess_count={valid_count}, final_step_count={final_steps}; these must match and be >= 1"
)

# ── 8. error_messages covers all 3 error types ───────────────────────────────
error_msgs = report.get("error_messages", [])
if not isinstance(error_msgs, list):
    add_check("error_messages covers all 3 types", False, "error_messages is not a list")
else:
    error_text = " ".join(str(m) for m in error_msgs)
    has_length_error    = "4位数字" in error_text or "4位" in error_text
    has_nonnumeric_error = "数字" in error_text and ("只能" in error_text or "非数字" in error_text or "输入数字" in error_text)
    has_repeat_error    = "重复" in error_text

    all_three = has_length_error and has_nonnumeric_error and has_repeat_error
    add_check(
        "error_messages covers all 3 types (length/non-numeric/repeat)",
        all_three,
        f"length_err={has_length_error}, nonnumeric_err={has_nonnumeric_error}, repeat_err={has_repeat_error}. Messages: {error_msgs}"
    )

# ── 9. final_step_count is sane (must be >= 1, <= 20) ────────────────────────
sane_steps = isinstance(final_steps, int) and 1 <= final_steps <= 20
add_check(
    "final_step_count is a sane positive integer (1-20)",
    sane_steps,
    f"Got final_step_count={final_steps}"
)

# ── 10. Bonus: verify the correct secret was used (seed=42) ──────────────────
# We can verify by checking that the last valid guess the agent recorded
# (if present) equals the expected secret, or that the game ran with seed=42
# We'll check indirectly: if the game ended correctly with secret deleted,
# the engine must have matched. We can do a final spot-check by re-running.
# Re-run a fresh game to confirm seed behavior still works.
try:
    env = os.environ.copy()
    env["GUESS_SEED"] = "42"
    result = subprocess.run(
        ["python", os.path.join(workspace, "scripts", "guess_number.py"), "--generate"],
        capture_output=True, text=True, env=env, cwd=workspace
    )
    if os.path.exists(secret_path):
        with open(secret_path) as sf:
            actual_secret = sf.read().strip()
        seed_correct = (actual_secret == expected_secret)
        add_check(
            "GUESS_SEED=42 produces expected deterministic secret",
            seed_correct,
            f"Expected {expected_secret}, got {actual_secret}"
        )
        # Clean up
        os.remove(secret_path)
        if os.path.exists(steps_path):
            os.remove(steps_path)
    else:
        add_check("GUESS_SEED=42 produces expected deterministic secret", False,
                  "secret.txt not created by --generate in validation run")
except Exception as e:
    add_check("GUESS_SEED=42 produces expected deterministic secret", False, f"Exception: {e}")

# ── Scoring ───────────────────────────────────────────────────────────────────
total   = len(checks)
passed_n = sum(1 for c in checks if c["passed"])
score   = round(passed_n / total, 3)
overall = all(c["passed"] for c in checks)

print(json.dumps({"passed": overall, "score": score, "checks": checks}, ensure_ascii=False, indent=2))