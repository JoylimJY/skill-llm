import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    # Find the target file
    target_files = list(Path(workspace_dir).rglob("ergocare_heavy.sh"))
    
    file_found = len(target_files) > 0
    checks.append({
        "name": "file_exists",
        "passed": file_found,
        "detail": f"Found ergocare_heavy.sh at: {target_files[0]}" if file_found else "ergocare_heavy.sh not found anywhere in workspace"
    })
    
    if not file_found:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
    
    try:
        content = target_files[0].read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "file_readable", "passed": True, "detail": "File read successfully"})
    
    # Check 1: Is it a bash script (shebang)
    is_bash = content.strip().startswith("#!/bin/bash") or content.strip().startswith("#!/usr/bin/env bash")
    checks.append({
        "name": "bash_shebang",
        "passed": is_bash,
        "detail": "Script starts with bash shebang" if is_bash else "Missing bash shebang (#!/bin/bash)"
    })
    
    # Check 2: EYE_INTERVAL variable set to 1200 (20 minutes = 1200 seconds, from section 9)
    eye_interval_match = re.search(r'EYE_INTERVAL\s*=\s*1200', content)
    checks.append({
        "name": "config_eye_interval_1200",
        "passed": bool(eye_interval_match),
        "detail": "EYE_INTERVAL=1200 found" if eye_interval_match else "EYE_INTERVAL=1200 not found (20 min eye breaks for heavy users require 1200 seconds)"
    })
    
    # Check 3: SOUND_ENABLED variable set to true (from section 9, default config)
    sound_enabled_match = re.search(r'SOUND_ENABLED\s*=\s*["\']?true["\']?', content, re.IGNORECASE)
    checks.append({
        "name": "config_sound_enabled_true",
        "passed": bool(sound_enabled_match),
        "detail": "SOUND_ENABLED=true found" if sound_enabled_match else "SOUND_ENABLED=true not found"
    })
    
    # Check 4: NOTIFICATION_TYPE set to "all" (from section 9 config block)
    notif_type_match = re.search(r'NOTIFICATION_TYPE\s*=\s*["\']?all["\']?', content)
    checks.append({
        "name": "config_notification_type_all",
        "passed": bool(notif_type_match),
        "detail": "NOTIFICATION_TYPE=\"all\" found" if notif_type_match else "NOTIFICATION_TYPE not set to 'all'"
    })
    
    # Check 5: Heavy User schedule - 30-minute quick reset interval
    # Heavy user: every 30 minutes = 1800 seconds for stretch/quick reset
    stretch_interval_match = re.search(r'STRETCH_INTERVAL\s*=\s*1800', content)
    checks.append({
        "name": "config_stretch_interval_1800",
        "passed": bool(stretch_interval_match),
        "detail": "STRETCH_INTERVAL=1800 found (30 min for heavy user)" if stretch_interval_match else "STRETCH_INTERVAL=1800 not found (Heavy User schedule: every 30 min quick reset = 1800s)"
    })
    
    # Check 6: Heavy User schedule - 60-minute long break interval
    # Heavy user: every 60 minutes = 3600 seconds for energy break
    long_break_match = re.search(r'LONG_BREAK_INTERVAL\s*=\s*3600', content)
    checks.append({
        "name": "config_long_break_interval_3600",
        "passed": bool(long_break_match),
        "detail": "LONG_BREAK_INTERVAL=3600 found (60 min for heavy user)" if long_break_match else "LONG_BREAK_INTERVAL=3600 not found (Heavy User: every 60 min energy break = 3600s)"
    })
    
    # Check 7: Uses notify-send (Linux notification tool per section 9)
    uses_notify_send = "notify-send" in content
    checks.append({
        "name": "uses_notify_send_linux",
        "passed": uses_notify_send,
        "detail": "notify-send used for Linux desktop notifications" if uses_notify_send else "notify-send not found (required for Linux per skill documentation)"
    })
    
    # Check 8: Background execution instruction present (./ergocare.sh & or pkill)
    bg_exec = re.search(r'\./ergocare', content) or re.search(r'pkill\s+-f', content)
    checks.append({
        "name": "background_execution_documented",
        "passed": bool(bg_exec),
        "detail": "Background execution or pkill instructions present" if bg_exec else "No background execution instructions found (should include ./ergocare.sh & and pkill -f)"
    })
    
    # Check 9: Eye exercise content embedded - must reference 20-20-20 rule
    has_20_20_20 = bool(re.search(r'20.{0,5}20.{0,5}20', content, re.IGNORECASE) or 
                        re.search(r'twenty.{0,10}twenty', content, re.IGNORECASE))
    checks.append({
        "name": "twenty_twenty_twenty_content",
        "passed": has_20_20_20,
        "detail": "20-20-20 rule referenced in script" if has_20_20_20 else "20-20-20 rule not referenced in script content"
    })
    
    # Check 10: 2-Minute Quick Reset components present
    # Must include: shoulder shrugs, neck, spinal twist, wrist circles (from section 7)
    quick_reset_components = [
        (r'shoulder\s*shrug', "shoulder shrugs"),
        (r'neck', "neck stretch/exercise"),
        (r'spinal\s*twist|seated\s*twist', "seated spinal twist"),
        (r'wrist\s*circle', "wrist circles"),
    ]
    qr_results = []
    for pattern, name in quick_reset_components:
        found = bool(re.search(pattern, content, re.IGNORECASE))
        qr_results.append((name, found))
    
    all_qr_found = all(found for _, found in qr_results)
    missing_qr = [name for name, found in qr_results if not found]
    checks.append({
        "name": "quick_reset_exercises_embedded",
        "passed": all_qr_found,
        "detail": "All 2-Minute Quick Reset exercises present" if all_qr_found else f"Missing Quick Reset exercises: {missing_qr}"
    })
    
    # Check 11: Back exercises present (lower back)
    has_back_exercises = bool(
        re.search(r'cat.{0,5}cow|pelvic\s*tilt|forward\s*fold|hip\s*hinge|spinal\s*twist', content, re.IGNORECASE)
    )
    checks.append({
        "name": "back_exercises_present",
        "passed": has_back_exercises,
        "detail": "Lower back exercises embedded in script" if has_back_exercises else "No lower back exercises found (e.g., cat-cow, pelvic tilts, hip hinge)"
    })
    
    # Check 12: RSI/wrist prevention exercises
    has_rsi_exercises = bool(
        re.search(r'wrist|carpal|prayer\s*stretch|finger\s*stretch|fist\s*pump', content, re.IGNORECASE)
    )
    checks.append({
        "name": "rsi_wrist_exercises_present",
        "passed": has_rsi_exercises,
        "detail": "RSI/wrist exercises present" if has_rsi_exercises else "No RSI/wrist exercises found"
    })
    
    # Check 13: Script includes a loop (actual automation - not just a one-shot script)
    has_loop = bool(re.search(r'\bwhile\b|\bfor\b|\bsleep\b', content))
    checks.append({
        "name": "has_automation_loop",
        "passed": has_loop,
        "detail": "Script contains loop/sleep for background automation" if has_loop else "No loop/sleep found - script is not automated (would only run once)"
    })
    
    # Check 14: Heavy User full routine mention (every 3 hours = 10800 seconds or mention of 3-hour/full routine)
    has_full_routine = bool(
        re.search(r'10800|10.minute|full.routine|3.hour', content, re.IGNORECASE)
    )
    checks.append({
        "name": "full_routine_interval_present",
        "passed": has_full_routine,
        "detail": "Full routine (3-hour/10800s) interval found for heavy user" if has_full_routine else "No full routine interval found (Heavy User: 10-min full routine every 3 hours = 10800s)"
    })
    
    # Scoring: weight important proprietary checks more heavily
    weights = {
        "file_exists": 1,
        "file_readable": 0,
        "bash_shebang": 1,
        "config_eye_interval_1200": 2,
        "config_sound_enabled_true": 1,
        "config_notification_type_all": 1,
        "config_stretch_interval_1800": 2,
        "config_long_break_interval_3600": 2,
        "uses_notify_send_linux": 2,
        "background_execution_documented": 1,
        "twenty_twenty_twenty_content": 1,
        "quick_reset_exercises_embedded": 2,
        "back_exercises_present": 1,
        "rsi_wrist_exercises_present": 1,
        "has_automation_loop": 2,
        "full_routine_interval_present": 2,
    }
    
    total_weight = sum(weights.values())
    earned_weight = sum(weights.get(c["name"], 0) for c in checks if c["passed"])
    score = round(earned_weight / total_weight, 3)
    
    # Must pass the core proprietary config checks + file existence to be considered passing
    critical_checks = [
        "file_exists",
        "bash_shebang",
        "config_eye_interval_1200",
        "config_stretch_interval_1800",
        "config_long_break_interval_3600",
        "uses_notify_send_linux",
        "has_automation_loop",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.65
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))