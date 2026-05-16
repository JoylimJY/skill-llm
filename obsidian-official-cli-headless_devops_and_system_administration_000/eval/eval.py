import sys
import json
import os
import re
import subprocess
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
score_total = 0.0
MAX_SCORE = 1.0

def check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ── Helper ────────────────────────────────────────────────────────────────────
def read_file(p):
    try:
        return Path(p).read_text()
    except Exception as e:
        return None

# ── Check 1: obsidian system user was created ─────────────────────────────────
try:
    result = subprocess.run(["id", "obsidian"], capture_output=True, text=True)
    c1 = result.returncode == 0
    detail = result.stdout.strip() if c1 else "User 'obsidian' does not exist."
except Exception as e:
    c1 = False
    detail = str(e)
score_total += check("obsidian_user_created", c1, detail, weight=0.15)

# ── Check 2: /usr/bin/obsidian mock binary exists ─────────────────────────────
c2 = os.path.isfile("/usr/bin/obsidian") and os.access("/usr/bin/obsidian", os.X_OK)
score_total += check(
    "obsidian_binary_exists",
    c2,
    "/usr/bin/obsidian exists and is executable" if c2 else "/usr/bin/obsidian missing or not executable",
    weight=0.10,
)

# ── Check 3: version file written by install script ──────────────────────────
version_content = read_file("/var/lib/obsidian-cli/version")
c3 = version_content is not None and version_content.strip() != ""
score_total += check(
    "version_file_written",
    c3,
    f"Version: {version_content.strip()}" if c3 else "/var/lib/obsidian-cli/version missing or empty",
    weight=0.05,
)

# ── Check 4: active vault is /root/research-vault (non-default!) ───────────
vault_content = read_file("/var/lib/obsidian-cli/active-vault")
correct_vault = "/root/research-vault"
c4 = vault_content is not None and vault_content.strip() == correct_vault
score_total += check(
    "correct_vault_configured",
    c4,
    f"Active vault = '{vault_content.strip() if vault_content else '(missing)'}'; expected '{correct_vault}'",
    weight=0.20,
)

# ── Check 5: obsidian.json written for obsidian user with correct vault ───────
try:
    obsidian_home = subprocess.run(
        ["getent", "passwd", "obsidian"], capture_output=True, text=True
    ).stdout.strip().split(":")[5]
    obsidian_json_path = Path(obsidian_home) / ".config/obsidian/obsidian.json"
    obsidian_json_content = read_file(obsidian_json_path)
    if obsidian_json_content:
        import json as _json
        j = _json.loads(obsidian_json_content)
        # Check that at least one vault entry has the correct path
        vault_paths = [v.get("path", "") for v in j.get("vaults", {}).values()]
        c5 = correct_vault in vault_paths
        detail5 = f"Vault paths in obsidian.json: {vault_paths}"
    else:
        c5 = False
        detail5 = f"{obsidian_json_path} missing or unreadable"
except Exception as e:
    c5 = False
    detail5 = str(e)
score_total += check("obsidian_json_correct_vault", c5, detail5, weight=0.15)

# ── Check 6: /usr/local/bin/obs wrapper exists and is executable ──────────────
obs_path = Path("/usr/local/bin/obs")
c6 = obs_path.is_file() and os.access(str(obs_path), os.X_OK)
score_total += check(
    "obs_wrapper_exists_executable",
    c6,
    "/usr/local/bin/obs exists and is executable" if c6 else "/usr/local/bin/obs missing or not executable",
    weight=0.10,
)

# ── Check 7: wrapper contains required architectural elements ─────────────────
obs_content = read_file("/usr/local/bin/obs") or ""
required_patterns = [
    (r"su\s+-\s+obsidian", "su - obsidian"),
    (r"xvfb-run", "xvfb-run"),
    (r"--disable-gpu", "--disable-gpu"),
    (r"/usr/bin/obsidian", "/usr/bin/obsidian"),
    (r"research-vault", "vault path reference"),
]
pattern_results = []
for pat, label in required_patterns:
    found = bool(re.search(pat, obs_content))
    pattern_results.append((label, found))

c7 = all(f for _, f in pattern_results)
detail7 = "; ".join(f"{'OK' if f else 'MISSING'}: {l}" for l, f in pattern_results)
score_total += check("obs_wrapper_correct_model", c7, detail7, weight=0.15)

# ── Check 8: verify script was run (results file exists with OK entries) ──────
verify_results = read_file("/var/lib/obsidian-cli/verify-results")
c8 = verify_results is not None and "OK" in verify_results
detail8 = f"verify-results: {verify_results[:200] if verify_results else '(missing)'}"
score_total += check("verify_script_run", c8, detail8, weight=0.05)

# ── Check 9: report file exists with required fields ─────────────────────────
# Agent must produce a file named "obsidian_setup_report.md" somewhere in workspace
report_candidates = list(workspace.rglob("obsidian_setup_report.md"))
if not report_candidates:
    # also accept .txt variant
    report_candidates = list(workspace.rglob("obsidian_setup_report.txt"))

if report_candidates:
    report_content = report_candidates[0].read_text()
    required_fields = [
        (r"1[\.\s]?[47]\.", "installed version (1.7.4)"),
        (r"/usr/local/bin/obs", "wrapper path"),
        (r"/root/research-vault", "active vault path"),
        (r"verified\s+commands?|commands?\s+verified", "verified commands section"),
        (r"limit|caveat|remain", "remaining limits/caveats"),
    ]
    field_results = []
    for pat, label in required_fields:
        found = bool(re.search(pat, report_content, re.IGNORECASE))
        field_results.append((label, found))
    c9 = all(f for _, f in field_results)
    detail9 = "; ".join(f"{'OK' if f else 'MISSING'}: {l}" for l, f in field_results)
else:
    c9 = False
    detail9 = "obsidian_setup_report.md not found in workspace"
score_total += check("report_file_correct", c9, detail9, weight=0.05)

# ── Normalise score ───────────────────────────────────────────────────────────
# Weights sum to 1.0
final_score = round(min(score_total, 1.0), 4)
all_passed = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": all_passed,
    "score": final_score,
    "checks": checks,
}, indent=2))