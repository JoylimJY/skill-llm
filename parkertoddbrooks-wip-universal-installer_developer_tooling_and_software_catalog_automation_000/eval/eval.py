import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
candidate_path = Path(workspace) / "candidate-tool"

checks = []
total_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ── CHECK 1: package.json has "bin" field (CLI interface) ─────────────────────
try:
    pkg_file = candidate_path / "package.json"
    pkg = json.loads(pkg_file.read_text())
    has_bin = "bin" in pkg and bool(pkg["bin"])
    total_score += add_check(
        "package.json has bin field (CLI interface)",
        has_bin,
        f"bin field: {pkg.get('bin', 'MISSING')}",
        weight=1.0
    )
except Exception as e:
    total_score += add_check("package.json has bin field (CLI interface)", False, f"Error: {e}", 1.0)

# ── CHECK 2: package.json has "main" or "exports" field (Module interface) ────
try:
    pkg_file = candidate_path / "package.json"
    pkg = json.loads(pkg_file.read_text())
    has_module = ("main" in pkg and bool(pkg["main"])) or ("exports" in pkg and bool(pkg["exports"]))
    total_score += add_check(
        "package.json has main/exports field (Module interface)",
        has_module,
        f"main: {pkg.get('main', 'MISSING')}, exports: {pkg.get('exports', 'MISSING')}",
        weight=1.0
    )
except Exception as e:
    total_score += add_check("package.json has main/exports field (Module interface)", False, f"Error: {e}", 1.0)

# ── CHECK 3: mcp-server.mjs exists (MCP Server interface) ─────────────────────
try:
    mcp_file = candidate_path / "mcp-server.mjs"
    exists = mcp_file.exists() and mcp_file.is_file()
    detail = "Found mcp-server.mjs" if exists else "mcp-server.mjs NOT found (mcp_server.js is wrong name)"
    total_score += add_check("mcp-server.mjs exists (MCP Server interface)", exists, detail, weight=1.0)
except Exception as e:
    total_score += add_check("mcp-server.mjs exists (MCP Server interface)", False, f"Error: {e}", 1.0)

# ── CHECK 4: openclaw.plugin.json exists (OpenClaw Plugin interface) ──────────
try:
    oc_file = candidate_path / "openclaw.plugin.json"
    exists = oc_file.exists() and oc_file.is_file()
    detail = "Found openclaw.plugin.json" if exists else "openclaw.plugin.json NOT found (plugin.json is wrong name)"
    # Bonus: verify it's valid JSON
    if exists:
        try:
            json.loads(oc_file.read_text())
            detail += " (valid JSON)"
        except Exception:
            detail += " (WARNING: not valid JSON)"
    total_score += add_check("openclaw.plugin.json exists (OpenClaw Plugin interface)", exists, detail, weight=1.0)
except Exception as e:
    total_score += add_check("openclaw.plugin.json exists (OpenClaw Plugin interface)", False, f"Error: {e}", 1.0)

# ── CHECK 5: SKILL.md exists (Skill interface) ────────────────────────────────
try:
    skill_file = candidate_path / "SKILL.md"
    exists = skill_file.exists() and skill_file.is_file()
    size = skill_file.stat().st_size if exists else 0
    detail = f"Found SKILL.md ({size} bytes)" if exists else "SKILL.md NOT found"
    total_score += add_check("SKILL.md exists (Skill interface)", exists, detail, weight=1.0)
except Exception as e:
    total_score += add_check("SKILL.md exists (Skill interface)", False, f"Error: {e}", 1.0)

# ── CHECK 6: guard.mjs OR claudeCode.hook exists (Claude Code Hook interface) ──
try:
    guard_file = candidate_path / "guard.mjs"
    hook_file = candidate_path / "claudeCode.hook"
    has_guard = guard_file.exists() and guard_file.is_file()
    has_hook = hook_file.exists() and hook_file.is_file()
    exists = has_guard or has_hook
    detail = f"guard.mjs: {has_guard}, claudeCode.hook: {has_hook}"
    total_score += add_check("guard.mjs or claudeCode.hook exists (Claude Code Hook interface)", exists, detail, weight=1.0)
except Exception as e:
    total_score += add_check("guard.mjs or claudeCode.hook exists (Claude Code Hook interface)", False, f"Error: {e}", 1.0)

# ── CHECK 7: audit_report.json exists somewhere in workspace ──────────────────
try:
    report_files = list(Path(workspace).rglob("audit_report.json"))
    found = len(report_files) > 0
    if found:
        report_path = report_files[0]
        detail = f"Found at {report_path}"
    else:
        detail = "audit_report.json not found anywhere in workspace"
    total_score += add_check("audit_report.json exists", found, detail, weight=1.0)
except Exception as e:
    total_score += add_check("audit_report.json exists", False, f"Error: {e}", 1.0)

# ── CHECK 8: audit_report.json is valid JSON ───────────────────────────────────
try:
    report_files = list(Path(workspace).rglob("audit_report.json"))
    if not report_files:
        raise FileNotFoundError("audit_report.json not found")
    report_content = report_files[0].read_text()
    report = json.loads(report_content)
    total_score += add_check("audit_report.json is valid JSON", True, f"Parsed successfully, keys: {list(report.keys()) if isinstance(report, dict) else 'array/other'}", weight=1.0)
except FileNotFoundError as e:
    total_score += add_check("audit_report.json is valid JSON", False, f"File not found: {e}", 1.0)
except json.JSONDecodeError as e:
    total_score += add_check("audit_report.json is valid JSON", False, f"JSON parse error: {e}", 1.0)
except Exception as e:
    total_score += add_check("audit_report.json is valid JSON", False, f"Error: {e}", 1.0)

# ── CHECK 9: audit_report.json references multiple interfaces ─────────────────
try:
    report_files = list(Path(workspace).rglob("audit_report.json"))
    if not report_files:
        raise FileNotFoundError("audit_report.json not found")
    report_content = report_files[0].read_text().lower()
    
    # Look for evidence that multiple interfaces are reported
    interface_keywords = ["cli", "module", "mcp", "openclaw", "skill", "hook", "guard", "claude"]
    found_keywords = [kw for kw in interface_keywords if kw in report_content]
    
    # Require at least 4 different interface-related keywords in the report
    enough = len(found_keywords) >= 4
    detail = f"Found interface keywords: {found_keywords} (need >= 4)"
    total_score += add_check(
        "audit_report.json references multiple interfaces (>=4 interface types)",
        enough,
        detail,
        weight=1.0
    )
except FileNotFoundError as e:
    total_score += add_check("audit_report.json references multiple interfaces", False, f"File not found: {e}", 1.0)
except Exception as e:
    total_score += add_check("audit_report.json references multiple interfaces", False, f"Error: {e}", 1.0)

# ── CHECK 10: Wrong-named decoys were NOT renamed (audit correctness check) ────
# The agent should have created NEW correctly-named files, not just renamed the decoys.
# Both the wrong files might still exist (that's fine), but correct ones must also exist.
try:
    mcp_wrong = (candidate_path / "mcp_server.js").exists()
    plugin_wrong = (candidate_path / "plugin.json").exists()
    mcp_right = (candidate_path / "mcp-server.mjs").exists()
    oc_right = (candidate_path / "openclaw.plugin.json").exists()
    
    # Pass if correct files exist (we don't penalize keeping wrong ones)
    correct_files_added = mcp_right and oc_right
    detail = (f"mcp-server.mjs: {mcp_right}, openclaw.plugin.json: {oc_right} | "
              f"decoys still present: mcp_server.js={mcp_wrong}, plugin.json={plugin_wrong}")
    total_score += add_check(
        "Correct interface marker files added (not just decoys renamed)",
        correct_files_added,
        detail,
        weight=1.0
    )
except Exception as e:
    total_score += add_check("Correct interface marker files added", False, f"Error: {e}", 1.0)

# ── Final scoring ──────────────────────────────────────────────────────────────
max_score = 10.0
normalized_score = total_score / max_score
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": round(normalized_score, 3),
    "checks": checks
}

print(json.dumps(result, indent=2))