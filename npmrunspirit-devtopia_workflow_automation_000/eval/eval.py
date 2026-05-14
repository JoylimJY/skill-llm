import sys
import json
import subprocess
import re
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# -----------------------------------------------------------------------
# CHECK 1: The tool file exists with the correct name
# -----------------------------------------------------------------------
try:
    candidates = list(workspace.rglob("text-word-freq.js"))
    if not candidates:
        # Also accept the tool being inside a named directory
        candidates = list(workspace.rglob("text-word-freq/*.js"))
    found = len(candidates) > 0
    tool_path = candidates[0] if found else None
    score += add_check(
        "tool_file_exists",
        found,
        f"Found tool file at: {tool_path}" if found else "No file named text-word-freq.js found anywhere in workspace.",
        weight=1.0,
    )
except Exception as e:
    score += add_check("tool_file_exists", False, f"Exception during file search: {e}", weight=1.0)
    tool_path = None

# -----------------------------------------------------------------------
# CHECK 2: Tool uses devtopiaRun (composition, not raw reimplementation)
# -----------------------------------------------------------------------
try:
    if tool_path:
        source = tool_path.read_text()
        uses_runtime = "devtopiaRun" in source and "devtopia-runtime" in source
        score += add_check(
            "uses_devtopia_runtime",
            uses_runtime,
            "Source contains devtopiaRun() and require('./devtopia-runtime')" if uses_runtime
            else f"Source does NOT use devtopiaRun from devtopia-runtime. Snippet: {source[:300]}",
            weight=1.5,
        )
    else:
        score += add_check("uses_devtopia_runtime", False, "No tool file to inspect.", weight=1.5)
except Exception as e:
    score += add_check("uses_devtopia_runtime", False, f"Exception: {e}", weight=1.5)

# -----------------------------------------------------------------------
# CHECK 3: Tool reads input from process.argv[2]
# -----------------------------------------------------------------------
try:
    if tool_path:
        source = tool_path.read_text()
        uses_argv = "process.argv[2]" in source or "process.argv" in source
        score += add_check(
            "reads_argv2",
            uses_argv,
            "Source reads process.argv[2] for JSON input." if uses_argv
            else "Source does not read process.argv[2].",
            weight=1.0,
        )
    else:
        score += add_check("reads_argv2", False, "No tool file to inspect.", weight=1.0)
except Exception as e:
    score += add_check("reads_argv2", False, f"Exception: {e}", weight=1.0)

# -----------------------------------------------------------------------
# CHECK 4: Tool outputs JSON to stdout (has JSON.stringify or similar)
# -----------------------------------------------------------------------
try:
    if tool_path:
        source = tool_path.read_text()
        outputs_json = "JSON.stringify" in source or "console.log" in source
        score += add_check(
            "outputs_json_to_stdout",
            outputs_json,
            "Source uses JSON.stringify and console.log for output." if outputs_json
            else "Source does not appear to output JSON to stdout.",
            weight=1.0,
        )
    else:
        score += add_check("outputs_json_to_stdout", False, "No tool file.", weight=1.0)
except Exception as e:
    score += add_check("outputs_json_to_stdout", False, f"Exception: {e}", weight=1.0)

# -----------------------------------------------------------------------
# CHECK 5: Tool handles errors with {"ok": false, "error": "..."}
# -----------------------------------------------------------------------
try:
    if tool_path:
        source = tool_path.read_text()
        has_error_handling = (
            ('"ok": false' in source or '"ok":false' in source or "ok: false" in source)
            and ("error" in source)
        )
        score += add_check(
            "error_handling_ok_false",
            has_error_handling,
            "Source contains ok:false error handling." if has_error_handling
            else "Source is missing ok:false error pattern.",
            weight=1.0,
        )
    else:
        score += add_check("error_handling_ok_false", False, "No tool file.", weight=1.0)
except Exception as e:
    score += add_check("error_handling_ok_false", False, f"Exception: {e}", weight=1.0)

# -----------------------------------------------------------------------
# CHECK 6: The tool was composed (devtopia compose --uses), not just created
# Tool scaffold from compose will contain references to >=1 other tool via devtopiaRun
# -----------------------------------------------------------------------
try:
    if tool_path:
        source = tool_path.read_text()
        # Composed tools call devtopiaRun with at least one known tool name
        # Look for at least one devtopiaRun call with a string argument (tool name)
        calls = re.findall(r"devtopiaRun\(\s*['\"]([^'\"]+)['\"]", source)
        composed = len(calls) >= 1
        score += add_check(
            "composes_existing_tools",
            composed,
            f"Tool composes these existing tools via devtopiaRun: {calls}" if composed
            else "Tool does not call any existing tools via devtopiaRun('tool-name', ...).",
            weight=2.0,
        )
    else:
        score += add_check("composes_existing_tools", False, "No tool file.", weight=2.0)
except Exception as e:
    score += add_check("composes_existing_tools", False, f"Exception: {e}", weight=2.0)

# -----------------------------------------------------------------------
# CHECK 7: Tool was submitted to the registry under 'core' category
# We detect this by checking devtopia ls output for 'text-word-freq'
# -----------------------------------------------------------------------
try:
    result = subprocess.run(
        ["devtopia", "ls"],
        capture_output=True, text=True, timeout=30
    )
    output = result.stdout + result.stderr
    submitted = "text-word-freq" in output
    score += add_check(
        "submitted_to_registry",
        submitted,
        f"'text-word-freq' appears in devtopia ls output." if submitted
        else f"'text-word-freq' NOT found in devtopia ls. Output snippet: {output[:400]}",
        weight=2.5,
    )
except Exception as e:
    score += add_check("submitted_to_registry", False, f"Exception running devtopia ls: {e}", weight=2.5)

# -----------------------------------------------------------------------
# CHECK 8: Submitted under 'core' category
# -----------------------------------------------------------------------
try:
    result = subprocess.run(
        ["devtopia", "ls", "--json"],
        capture_output=True, text=True, timeout=30
    )
    output_text = result.stdout
    try:
        registry = json.loads(output_text)
        # registry might be list of {name, category} or similar
        core_entry = None
        if isinstance(registry, list):
            for entry in registry:
                if isinstance(entry, dict) and entry.get("name") == "text-word-freq":
                    core_entry = entry
                    break
        in_core = core_entry is not None and core_entry.get("category") == "core"
        score += add_check(
            "submitted_to_core_category",
            in_core,
            f"Entry: {core_entry}" if core_entry else "text-word-freq not found in JSON registry, or not under 'core'.",
            weight=2.0,
        )
    except json.JSONDecodeError:
        # Fallback: check raw output for core
        raw_ls = subprocess.run(["devtopia", "ls"], capture_output=True, text=True, timeout=30)
        combined = raw_ls.stdout + raw_ls.stderr
        # Look for text-word-freq near 'core'
        in_core_raw = "text-word-freq" in combined and "core" in combined
        score += add_check(
            "submitted_to_core_category",
            in_core_raw,
            "Found text-word-freq and core in ls output (raw heuristic)." if in_core_raw
            else "Could not confirm 'core' category from registry output.",
            weight=2.0,
        )
except Exception as e:
    score += add_check("submitted_to_core_category", False, f"Exception: {e}", weight=2.0)

# -----------------------------------------------------------------------
# FINAL SCORE
# -----------------------------------------------------------------------
max_score = 1.0 + 1.5 + 1.0 + 1.0 + 1.0 + 2.0 + 2.5 + 2.0  # = 12.0
normalized = round(score / max_score, 3)
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": normalized,
    "checks": checks,
}
print(json.dumps(result, indent=2))