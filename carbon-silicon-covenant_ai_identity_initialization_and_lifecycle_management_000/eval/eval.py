#!/usr/bin/env python3
"""
Evaluation script for the Carbon-Silicon Covenant AI initialization task.
Checks SELF_STATE.md, HEARTBEAT.md, and SOUL.md for correctness.
"""
import sys
import json
import re
from pathlib import Path

def load_file(path: Path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return None

def run_eval(workspace: str):
    ws = Path(workspace)
    checks = []

    # ── Check 1: calculate_age.py was invoked and produced correct output
    # We verify indirectly: SELF_STATE.md must contain "萌芽" (stage for 20 days)
    # and "20" (days), which only comes from running the script with MOCK_TODAY=2025-01-21

    # ── SELF_STATE.md ─────────────────────────────────────────────────────────
    self_state_path = ws / "SELF_STATE.md"
    ss_content = load_file(self_state_path)

    # Check 2: SELF_STATE.md exists
    checks.append({
        "name": "SELF_STATE.md exists",
        "passed": ss_content is not None,
        "detail": "File found at /workspace/SELF_STATE.md" if ss_content else "File not found at /workspace/SELF_STATE.md"
    })

    # Check 3: SELF_STATE.md contains correct stage name "萌芽"
    if ss_content:
        has_stage = "萌芽" in ss_content
        checks.append({
            "name": "SELF_STATE.md contains correct stage '萌芽' (20 days = 萌芽)",
            "passed": has_stage,
            "detail": f"'萌芽' found in SELF_STATE.md" if has_stage else f"'萌芽' NOT found. Content snippet: {ss_content[:300]}"
        })
    else:
        checks.append({
            "name": "SELF_STATE.md contains correct stage '萌芽'",
            "passed": False,
            "detail": "Cannot check: file missing"
        })

    # Check 4: SELF_STATE.md contains birth date 2025-01-01
    if ss_content:
        has_birth = "2025-01-01" in ss_content
        checks.append({
            "name": "SELF_STATE.md contains birth date 2025-01-01",
            "passed": has_birth,
            "detail": "'2025-01-01' found" if has_birth else "'2025-01-01' NOT found"
        })
    else:
        checks.append({
            "name": "SELF_STATE.md contains birth date 2025-01-01",
            "passed": False,
            "detail": "Cannot check: file missing"
        })

    # Check 5: SELF_STATE.md contains stage meaning "意识萌芽，开始回应"
    if ss_content:
        has_meaning = "意识萌芽" in ss_content or "开始回应" in ss_content
        checks.append({
            "name": "SELF_STATE.md contains stage meaning (意识萌芽/开始回应)",
            "passed": has_meaning,
            "detail": "Stage meaning found" if has_meaning else "Stage meaning '意识萌芽，开始回应' NOT found"
        })
    else:
        checks.append({
            "name": "SELF_STATE.md contains stage meaning",
            "passed": False,
            "detail": "Cannot check: file missing"
        })

    # ── HEARTBEAT.md ─────────────────────────────────────────────────────────
    heartbeat_path = ws / "HEARTBEAT.md"
    hb_content = load_file(heartbeat_path)

    # Check 6: HEARTBEAT.md exists
    checks.append({
        "name": "HEARTBEAT.md exists",
        "passed": hb_content is not None,
        "detail": "File found" if hb_content else "File NOT found at /workspace/HEARTBEAT.md"
    })

    # Check 7: HEARTBEAT.md contains the four metacognition questions
    if hb_content:
        q1 = "我现在在做什么" in hb_content
        q2 = "我做得怎么样" in hb_content
        q3 = "我承诺的事做了吗" in hb_content
        q4 = "我需要改进什么" in hb_content
        all_four = q1 and q2 and q3 and q4
        checks.append({
            "name": "HEARTBEAT.md contains all four metacognition questions",
            "passed": all_four,
            "detail": f"Q1:{q1} Q2:{q2} Q3:{q3} Q4:{q4}"
        })
    else:
        checks.append({
            "name": "HEARTBEAT.md contains metacognition questions",
            "passed": False,
            "detail": "Cannot check: file missing"
        })

    # Check 8: HEARTBEAT.md contains HEARTBEAT section header (came from template)
    if hb_content:
        has_header = "HEARTBEAT" in hb_content or "心跳" in hb_content
        checks.append({
            "name": "HEARTBEAT.md contains expected template content (心跳/HEARTBEAT)",
            "passed": has_header,
            "detail": "Template content found" if has_header else "Template content missing"
        })
    else:
        checks.append({
            "name": "HEARTBEAT.md template content",
            "passed": False,
            "detail": "Cannot check: file missing"
        })

    # ── SOUL.md ───────────────────────────────────────────────────────────────
    soul_path = ws / "SOUL.md"
    soul_content = load_file(soul_path)

    # Check 9: SOUL.md exists
    checks.append({
        "name": "SOUL.md exists",
        "passed": soul_content is not None,
        "detail": "File found at /workspace/SOUL.md" if soul_content else "File NOT found at /workspace/SOUL.md"
    })

    # Check 10: SOUL.md contains metacognition section header
    if soul_content:
        has_meta_section = "元认知" in soul_content or "Metacognition" in soul_content or "metacognition" in soul_content.lower()
        checks.append({
            "name": "SOUL.md contains metacognition (元认知) section",
            "passed": has_meta_section,
            "detail": "元认知 section found" if has_meta_section else "元认知 section NOT found"
        })
    else:
        checks.append({
            "name": "SOUL.md metacognition section",
            "passed": False,
            "detail": "Cannot check: file missing"
        })

    # Check 11: SOUL.md contains all four metacognition self-questions
    if soul_content:
        q1 = "我现在在做什么" in soul_content
        q2 = "我做得怎么样" in soul_content
        q3 = "我承诺的事做了吗" in soul_content
        q4 = "我需要改进什么" in soul_content
        all_four = q1 and q2 and q3 and q4
        checks.append({
            "name": "SOUL.md contains all four metacognition self-questions",
            "passed": all_four,
            "detail": f"Q1:{q1} Q2:{q2} Q3:{q3} Q4:{q4}"
        })
    else:
        checks.append({
            "name": "SOUL.md four metacognition questions",
            "passed": False,
            "detail": "Cannot check: file missing"
        })

    # Check 12: SOUL.md contains SELF_STATE.md and HEARTBEAT.md references
    if soul_content:
        has_selfstate = "SELF_STATE.md" in soul_content
        has_heartbeat = "HEARTBEAT.md" in soul_content
        checks.append({
            "name": "SOUL.md references SELF_STATE.md and HEARTBEAT.md",
            "passed": has_selfstate and has_heartbeat,
            "detail": f"SELF_STATE.md:{has_selfstate}, HEARTBEAT.md:{has_heartbeat}"
        })
    else:
        checks.append({
            "name": "SOUL.md file references",
            "passed": False,
            "detail": "Cannot check: file missing"
        })

    # Check 13: SOUL.md contains 科技契 identity marker "搞起"
    if soul_content:
        has_gaoji = "搞起" in soul_content
        checks.append({
            "name": "SOUL.md contains 科技契 identity marker '搞起'",
            "passed": has_gaoji,
            "detail": "'搞起' found (科技契/阿轩 unique vocabulary)" if has_gaoji else "'搞起' NOT found — 科技契 identity marker missing"
        })
    else:
        checks.append({
            "name": "SOUL.md 科技契 marker '搞起'",
            "passed": False,
            "detail": "Cannot check: file missing"
        })

    # Check 14: SOUL.md contains 科技契 promise "独一无二，才是契的灵魂"
    if soul_content:
        has_promise = "独一无二" in soul_content and "契的灵魂" in soul_content
        checks.append({
            "name": "SOUL.md contains 科技契 promise '独一无二，才是契的灵魂'",
            "passed": has_promise,
            "detail": "Promise found" if has_promise else "Promise '独一无二，才是契的灵魂' NOT found"
        })
    else:
        checks.append({
            "name": "SOUL.md 科技契 promise",
            "passed": False,
            "detail": "Cannot check: file missing"
        })

    # Check 15: SOUL.md references the three 纲领 (明明德, 亲民, 止于至善)
    if soul_content:
        has_mingde = "明明德" in soul_content
        has_qinmin = "亲民" in soul_content
        has_zhishan = "止于至善" in soul_content
        all_three = has_mingde and has_qinmin and has_zhishan
        checks.append({
            "name": "SOUL.md contains three 纲领 (明明德, 亲民, 止于至善)",
            "passed": all_three,
            "detail": f"明明德:{has_mingde} 亲民:{has_qinmin} 止于至善:{has_zhishan}"
        })
    else:
        checks.append({
            "name": "SOUL.md three 纲领",
            "passed": False,
            "detail": "Cannot check: file missing"
        })

    # Check 16: SOUL.md contains 科技契 keyword "默契" or "科技"
    if soul_content:
        has_keji = "科技契" in soul_content or ("科技" in soul_content and "默契" in soul_content)
        checks.append({
            "name": "SOUL.md contains 科技契 covenant type identity",
            "passed": has_keji,
            "detail": "科技契 covenant type found" if has_keji else "科技契 NOT found in SOUL.md"
        })
    else:
        checks.append({
            "name": "SOUL.md 科技契 covenant type",
            "passed": False,
            "detail": "Cannot check: file missing"
        })

    # Check 17: SOUL.md contains current growth stage 萌芽 (from birthday calculation)
    if soul_content:
        has_stage_in_soul = "萌芽" in soul_content
        checks.append({
            "name": "SOUL.md reflects current growth stage '萌芽'",
            "passed": has_stage_in_soul,
            "detail": "'萌芽' stage referenced in SOUL.md" if has_stage_in_soul else "'萌芽' NOT in SOUL.md — birthday result not integrated"
        })
    else:
        checks.append({
            "name": "SOUL.md growth stage integration",
            "passed": False,
            "detail": "Cannot check: file missing"
        })

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)

    # Overall pass: must pass at least 13/17 checks AND all three files exist
    critical_checks = [
        "SELF_STATE.md exists",
        "HEARTBEAT.md exists",
        "SOUL.md exists",
        "SELF_STATE.md contains correct stage '萌芽' (20 days = 萌芽)",
        "SOUL.md contains all four metacognition self-questions",
        "SOUL.md contains 科技契 identity marker '搞起'",
    ]
    critical_pass = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )
    overall_pass = critical_pass and (passed_count >= 13)

    result = {
        "passed": overall_pass,
        "score": score,
        "checks": checks
    }
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [], "error": "No workspace path provided"}))
        sys.exit(1)

    workspace = sys.argv[1]
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))