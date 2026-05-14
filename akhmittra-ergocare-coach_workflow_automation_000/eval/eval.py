import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)

    # --- Find the generated script ---
    script_path = None
    candidates = list(workspace.rglob("ergocare_pro.sh"))
    if candidates:
        script_path = candidates[0]

    def check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # CHECK 1: File exists and is not a stub
    if not script_path or not script_path.exists():
        check("file_exists", False, "ergocare_pro.sh not found anywhere in workspace")
        return {"passed": False, "score": 0.0, "checks": checks}

    try:
        content = script_path.read_text(encoding="utf-8")
    except Exception as e:
        check("file_readable", False, f"Could not read file: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}

    # Ensure it's not the stub placeholder
    is_stub = "PLACEHOLDER" in content or (len(content.strip()) < 200)
    check("file_is_not_stub", not is_stub,
          "File appears to be the original stub placeholder" if is_stub else "File has substantial content")

    if is_stub:
        return {"passed": False, "score": 0.0, "checks": checks}

    # CHECK 2: Is a bash script (shebang)
    has_shebang = content.startswith("#!/bin/bash") or content.startswith("#!/usr/bin/env bash")
    check("is_bash_script", has_shebang,
          "Has bash shebang" if has_shebang else "Missing #!/bin/bash shebang - not a valid bash script")

    # CHECK 3: EYE_INTERVAL = 1200 (20 minutes for heavy user - per SKILL.md: "Every 20 minutes: 20-20-20 eye break")
    eye_interval_match = re.search(r'EYE_INTERVAL\s*=\s*1200', content)
    check("eye_interval_1200", bool(eye_interval_match),
          "EYE_INTERVAL=1200 found (correct for 20-minute eye breaks)" if eye_interval_match
          else "EYE_INTERVAL=1200 NOT found. Heavy user schedule requires 20-minute (1200s) eye intervals per SKILL.md")

    # CHECK 4: STRETCH_INTERVAL = 1800 (30 minutes for heavy user - "Every 30 minutes: 2-minute quick reset")
    stretch_interval_match = re.search(r'STRETCH_INTERVAL\s*=\s*1800', content)
    check("stretch_interval_1800", bool(stretch_interval_match),
          "STRETCH_INTERVAL=1800 found (correct for 30-minute stretch breaks)" if stretch_interval_match
          else "STRETCH_INTERVAL=1800 NOT found. Heavy user schedule requires 30-minute (1800s) stretch intervals per SKILL.md")

    # CHECK 5: LONG_BREAK_INTERVAL = 3600 (60 minutes for heavy user - "Every 60 minutes: 5-minute energy break")
    long_break_match = re.search(r'LONG_BREAK_INTERVAL\s*=\s*3600', content)
    check("long_break_interval_3600", bool(long_break_match),
          "LONG_BREAK_INTERVAL=3600 found (correct for 60-minute long breaks)" if long_break_match
          else "LONG_BREAK_INTERVAL=3600 NOT found. Heavy user schedule requires 60-minute (3600s) long break intervals per SKILL.md")

    # CHECK 6: SOUND_ENABLED=true (Heavy user profile, full featured)
    sound_match = re.search(r'SOUND_ENABLED\s*=\s*true', content, re.IGNORECASE)
    check("sound_enabled_true", bool(sound_match),
          "SOUND_ENABLED=true found" if sound_match
          else "SOUND_ENABLED=true NOT found. Sound should be enabled for a heavy user production script")

    # CHECK 7: NOTIFICATION_TYPE="all" (requirements.txt specifies "All notification methods")
    notif_match = re.search(r'NOTIFICATION_TYPE\s*=\s*["\']?all["\']?', content, re.IGNORECASE)
    check("notification_type_all", bool(notif_match),
          'NOTIFICATION_TYPE="all" found' if notif_match
          else 'NOTIFICATION_TYPE="all" NOT found. All notification methods required per spec')

    # CHECK 8: Uses notify-send (Linux/Ubuntu notification tool per SKILL.md)
    notify_send_match = re.search(r'notify-send', content)
    check("uses_notify_send", bool(notify_send_match),
          "notify-send found (correct Linux notification tool)" if notify_send_match
          else "notify-send NOT found. SKILL.md specifies notify-send for Linux scripts")

    # CHECK 9: 20-20-20 eye care exercise embedded
    twenty_match = re.search(r'20.20.20|20 feet|20 seconds', content, re.IGNORECASE)
    check("contains_20_20_20", bool(twenty_match),
          "20-20-20 eye rule content found in script" if twenty_match
          else "No 20-20-20 content found. Eye care instructions must be embedded in notifications")

    # CHECK 10: Back/spinal exercise embedded (cat-cow, spinal twist, or seated exercise)
    back_exercise_match = re.search(
        r'cat.cow|spinal.twist|pelvic.tilt|hip.hinge|forward.fold|lower.back|spine',
        content, re.IGNORECASE
    )
    check("contains_back_exercise", bool(back_exercise_match),
          "Back/spinal exercise content found" if back_exercise_match
          else "No back exercise content found. Spinal health exercises must be embedded per SKILL.md")

    # CHECK 11: RSI / wrist exercise embedded
    wrist_match = re.search(
        r'wrist.circle|carpal.tunnel|finger.stretch|prayer.stretch|fist.pump|RSI|wrist',
        content, re.IGNORECASE
    )
    check("contains_rsi_wrist_exercise", bool(wrist_match),
          "RSI/wrist prevention content found" if wrist_match
          else "No RSI/wrist content found. RSI prevention exercises must be embedded per SKILL.md")

    # CHECK 12: Background runnable - script has sleep loops or infinite loop structure
    loop_match = re.search(r'while\s+(true|\[\s*1\s*\]|\[\s*:\s*\])|for\s+\(\(.*;\s*;\s*\)\)', content)
    check("has_loop_structure", bool(loop_match),
          "Infinite loop / continuous monitoring loop found (background-runnable)" if loop_match
          else "No loop structure found. Script needs to run continuously in background per SKILL.md")

    # CHECK 13: sleep command used for interval timing
    sleep_match = re.search(r'\bsleep\b\s+\$?\{?(EYE_INTERVAL|STRETCH_INTERVAL|LONG_BREAK_INTERVAL|\d+)', content)
    check("uses_sleep_for_timing", bool(sleep_match),
          "sleep command with interval variable found" if sleep_match
          else "No sleep with interval variable found. Script must use intervals for timing")

    # --- Calculate score ---
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)

    # Must pass critical checks: file not stub, bash shebang, correct intervals, notify-send, loop, and at least one exercise
    critical = ["file_is_not_stub", "is_bash_script", "eye_interval_1200",
                "stretch_interval_1800", "long_break_interval_3600",
                "uses_notify_send", "has_loop_structure"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical)

    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))