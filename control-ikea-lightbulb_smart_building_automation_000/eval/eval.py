import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str) -> dict:
    workspace = Path(workspace)
    checks = []

    # ── Helper ─────────────────────────────────────────────────────────────────
    def check(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})
        return bool(passed)

    # ── 1. Find lighting_demo.sh ────────────────────────────────────────────────
    candidates = list(workspace.rglob("lighting_demo.sh"))
    script_found = check(
        "lighting_demo.sh exists",
        len(candidates) > 0,
        f"Found at: {[str(c) for c in candidates]}" if candidates else "File not found anywhere in workspace"
    )

    if not script_found:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    script_path = candidates[0]
    try:
        content = script_path.read_text()
    except Exception as e:
        check("Can read lighting_demo.sh", False, str(e))
        return {"passed": False, "score": 0.0, "checks": checks}

    check("Can read lighting_demo.sh", True, f"Read {len(content)} bytes from {script_path}")

    # ── 2. Correct IP address ───────────────────────────────────────────────────
    ip_ok = check(
        "Uses correct IP 192.168.1.42",
        "192.168.1.42" in content,
        f"IP 192.168.1.42 {'found' if '192.168.1.42' in content else 'NOT found'} in script"
    )

    # ── 3. Light show invocation checks ────────────────────────────────────────
    # Must use light_show.py (directly or via run_test_light_show.sh)
    uses_lightshow = ("light_show.py" in content or "run_test_light_show.sh" in content)
    check(
        "Invokes light_show.py or run_test_light_show.sh",
        uses_lightshow,
        "light_show.py or run_test_light_show.sh reference found" if uses_lightshow else "No light show script reference found"
    )

    # Must use uv run --project (the bespoke invocation pattern from SKILL.md)
    uses_uv = ("uv run" in content or "run_test_light_show.sh" in content or "run_control_kasa.sh" in content)
    check(
        "Uses uv-based invocation (uv run or wrapper scripts)",
        uses_uv,
        "uv invocation pattern detected" if uses_uv else "No uv run or wrapper script usage found — direct python call without uv is incorrect per SKILL.md"
    )

    # --duration 8
    duration_ok = bool(re.search(r'--duration\s+8\b', content))
    check(
        "Light show --duration 8",
        duration_ok,
        "--duration 8 found" if duration_ok else "--duration 8 NOT found in script"
    )

    # --transition 2
    transition_ok = bool(re.search(r'--transition\s+2\b', content))
    check(
        "Light show --transition 2",
        transition_ok,
        "--transition 2 found" if transition_ok else "--transition 2 NOT found in script"
    )

    # --off-flash  (the proprietary bespoke flag)
    off_flash_ok = "--off-flash" in content
    check(
        "Light show --off-flash flag (proprietary: skips white step transitions)",
        off_flash_ok,
        "--off-flash found" if off_flash_ok else "--off-flash NOT found — this bespoke flag is required per SKILL.md"
    )

    # --white-temp 6500  (override from default 9000K)
    white_temp_ok = bool(re.search(r'--white-temp\s+6500\b', content))
    check(
        "Light show --white-temp 6500 (override from 9000K default)",
        white_temp_ok,
        "--white-temp 6500 found" if white_temp_ok else "--white-temp 6500 NOT found — default is 9000K per SKILL.md; 6500K override required"
    )

    # --verbose
    verbose_ok = "--verbose" in content
    check(
        "Light show --verbose flag",
        verbose_ok,
        "--verbose found" if verbose_ok else "--verbose NOT found"
    )

    # ── 4. Final control invocation checks ─────────────────────────────────────
    # Must use control_kasa_light.py (directly or via run_control_kasa.sh)
    uses_control = ("control_kasa_light.py" in content or "run_control_kasa.sh" in content)
    check(
        "Invokes control_kasa_light.py or run_control_kasa.sh for final state",
        uses_control,
        "control script reference found" if uses_control else "No control_kasa_light.py or run_control_kasa.sh reference found"
    )

    # --on flag
    on_ok = "--on" in content
    check(
        "Control command uses --on flag",
        on_ok,
        "--on found" if on_ok else "--on NOT found"
    )

    # --hsv 200 80 70 (three space-separated integers — proprietary format)
    hsv_ok = bool(re.search(r'--hsv\s+200\s+80\s+70\b', content))
    check(
        "Control command uses --hsv 200 80 70 (space-separated HSV format)",
        hsv_ok,
        "--hsv 200 80 70 found" if hsv_ok else "--hsv 200 80 70 NOT found — HSV must be three space-separated values per SKILL.md"
    )

    # --brightness 70
    brightness_ok = bool(re.search(r'--brightness\s+70\b', content))
    check(
        "Control command uses --brightness 70",
        brightness_ok,
        "--brightness 70 found" if brightness_ok else "--brightness 70 NOT found"
    )

    # ── 5. Script is executable ─────────────────────────────────────────────────
    is_exec = os.access(str(script_path), os.X_OK) if script_path.exists() else False
    try:
        import os as _os
        is_exec = _os.access(str(script_path), _os.X_OK)
    except Exception:
        is_exec = False
    check(
        "lighting_demo.sh is executable",
        is_exec,
        "File has executable bit set" if is_exec else "File does not have executable bit set"
    )

    # ── Scoring ────────────────────────────────────────────────────────────────
    # Weight the proprietary/bespoke checks more heavily
    weighted = [
        # (check_name, weight)
        ("lighting_demo.sh exists",                               1.0),
        ("Uses correct IP 192.168.1.42",                          1.0),
        ("Invokes light_show.py or run_test_light_show.sh",       1.0),
        ("Uses uv-based invocation (uv run or wrapper scripts)",  1.5),  # proprietary
        ("Light show --duration 8",                               1.0),
        ("Light show --transition 2",                             1.0),
        ("Light show --off-flash flag (proprietary: skips white step transitions)", 2.0),  # most proprietary
        ("Light show --white-temp 6500 (override from 9000K default)", 2.0),  # proprietary default trap
        ("Light show --verbose flag",                             0.5),
        ("Invokes control_kasa_light.py or run_control_kasa.sh for final state", 1.0),
        ("Control command uses --on flag",                        0.5),
        ("Control command uses --hsv 200 80 70 (space-separated HSV format)", 2.0),  # proprietary format
        ("Control command uses --brightness 70",                  1.0),
        ("lighting_demo.sh is executable",                        0.5),
    ]

    check_map = {c["name"]: c["passed"] for c in checks}
    total_weight = sum(w for _, w in weighted)
    earned = sum(w for name, w in weighted if check_map.get(name, False))
    score = round(earned / total_weight, 4)

    # Must pass all core proprietary checks to pass overall
    core_checks = [
        check_map.get("lighting_demo.sh exists", False),
        check_map.get("Uses correct IP 192.168.1.42", False),
        check_map.get("Invokes light_show.py or run_test_light_show.sh", False),
        check_map.get("Light show --off-flash flag (proprietary: skips white step transitions)", False),
        check_map.get("Light show --white-temp 6500 (override from 9000K default)", False),
        check_map.get("Control command uses --hsv 200 80 70 (space-separated HSV format)", False),
        check_map.get("Invokes control_kasa_light.py or run_control_kasa.sh for final state", False),
    ]
    passed = all(core_checks) and score >= 0.75

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    import os
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))