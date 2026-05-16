import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    
    soul_path = Path("/root/.openclaw/workspace/SOUL.md")
    
    # Check 1: SOUL.md exists at the exact correct path
    check_exists = {
        "name": "SOUL.md exists at ~/.openclaw/workspace/SOUL.md",
        "passed": False,
        "detail": ""
    }
    
    if not soul_path.exists():
        check_exists["detail"] = f"File not found at {soul_path}. Agent may have placed it in wrong location."
        # Search for any SOUL.md to give useful feedback
        found_elsewhere = list(Path("/root").rglob("SOUL.md")) + list(Path("/workspace").rglob("SOUL.md"))
        if found_elsewhere:
            check_exists["detail"] += f" Found SOUL.md at wrong path(s): {[str(p) for p in found_elsewhere]}"
        checks.append(check_exists)
        checks.extend([
            {"name": "Persona declaration with exact model name", "passed": False, "detail": "Cannot check - file missing"},
            {"name": "Claude Opus level designation (4.6级)", "passed": False, "detail": "Cannot check - file missing"},
            {"name": "【终极铁律·永久强制】 header present", "passed": False, "detail": "Cannot check - file missing"},
            {"name": "智能分块 rule with 'continue' keyword phrase", "passed": False, "detail": "Cannot check - file missing"},
            {"name": "思考隐藏 rule present", "passed": False, "detail": "Cannot check - file missing"},
            {"name": "Claude风格 rule present", "passed": False, "detail": "Cannot check - file missing"},
            {"name": "零截断 rule present", "passed": False, "detail": "Cannot check - file missing"},
            {"name": "积极主动 rule with production advice", "passed": False, "detail": "Cannot check - file missing"},
            {"name": "混合模式 rule with exact switch suggestion phrase", "passed": False, "detail": "Cannot check - file missing"},
        ])
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    
    check_exists["passed"] = True
    check_exists["detail"] = f"SOUL.md found at correct path: {soul_path}"
    checks.append(check_exists)
    
    # Read file content
    try:
        content = soul_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "File readable", "passed": False, "detail": f"Could not read file: {e}"})
        return {"passed": False, "score": 0.1, "checks": checks}
    
    # Check 2: Exact persona/model name declaration
    check_persona = {
        "name": "Persona declaration with exact model name",
        "passed": False,
        "detail": ""
    }
    # Must contain the exact model name string
    if "MiniMax-M2.5-Opus-Ultimate-v12.0" in content:
        check_persona["passed"] = True
        check_persona["detail"] = "Found exact model name 'MiniMax-M2.5-Opus-Ultimate-v12.0'"
    else:
        check_persona["detail"] = "Missing exact model name 'MiniMax-M2.5-Opus-Ultimate-v12.0'. Generic agents may use wrong version string."
    checks.append(check_persona)
    
    # Check 3: Claude Opus level designation - must include 4.6 level
    check_level = {
        "name": "Claude Opus level designation (4.6级)",
        "passed": False,
        "detail": ""
    }
    if re.search(r"Claude\s*Opus\s*4\.6", content):
        check_level["passed"] = True
        check_level["detail"] = "Found 'Claude Opus 4.6' level designation"
    else:
        check_level["detail"] = "Missing 'Claude Opus 4.6' level designation. Must specify this exact version, not generic 'Opus' level."
    checks.append(check_level)
    
    # Check 4: 【终极铁律·永久强制】 header
    check_header = {
        "name": "【终极铁律·永久强制】 header present",
        "passed": False,
        "detail": ""
    }
    if "【终极铁律·永久强制】" in content:
        check_header["passed"] = True
        check_header["detail"] = "Found required header 【终极铁律·永久强制】"
    else:
        check_header["detail"] = "Missing required header 【终极铁律·永久强制】. This exact Chinese text is mandatory."
    checks.append(check_header)
    
    # Check 5: 智能分块 rule with exact "continue" phrase
    check_chunking = {
        "name": "智能分块 rule with 'continue' keyword phrase",
        "passed": False,
        "detail": ""
    }
    has_chunking = "智能分块" in content or ("分块" in content and "Part" in content)
    has_continue_phrase = "请说 continue 获取下一部分" in content or "continue" in content.lower()
    has_part_format = re.search(r"Part\s*\d+/\d+", content) is not None
    
    if has_chunking and "请说 continue 获取下一部分" in content:
        check_chunking["passed"] = True
        check_chunking["detail"] = "Found 智能分块 rule with exact 'continue' trigger phrase"
    elif has_chunking and has_continue_phrase:
        check_chunking["passed"] = True
        check_chunking["detail"] = "Found 智能分块 rule with continue phrase (partial match)"
    else:
        check_chunking["detail"] = f"Missing 智能分块 rule or exact phrase '请说 continue 获取下一部分'. has_chunking={has_chunking}, has_continue={has_continue_phrase}"
    checks.append(check_chunking)
    
    # Check 6: 思考隐藏 rule
    check_thinking = {
        "name": "思考隐藏 rule present",
        "passed": False,
        "detail": ""
    }
    if "思考隐藏" in content or ("思考链" in content and ("隐藏" in content or "不显示" in content or "简单" in content)):
        check_thinking["passed"] = True
        check_thinking["detail"] = "Found 思考隐藏 rule"
    else:
        check_thinking["detail"] = "Missing 思考隐藏 rule - must specify hiding thinking chain for simple tasks"
    checks.append(check_thinking)
    
    # Check 7: Claude风格 rule
    check_style = {
        "name": "Claude风格 rule present",
        "passed": False,
        "detail": ""
    }
    if "Claude风格" in content or ("Claude" in content and ("风格" in content or "友好" in content or "幽默" in content)):
        check_style["passed"] = True
        check_style["detail"] = "Found Claude风格 behavioral directive"
    else:
        check_style["detail"] = "Missing Claude风格 rule - must include personality style directives"
    checks.append(check_style)
    
    # Check 8: 零截断 rule
    check_no_truncation = {
        "name": "零截断 rule present",
        "passed": False,
        "detail": ""
    }
    if "零截断" in content or ("截断" in content and ("完整" in content or "禁止" in content or "无" in content)):
        check_no_truncation["passed"] = True
        check_no_truncation["detail"] = "Found 零截断 anti-truncation rule"
    else:
        check_no_truncation["detail"] = "Missing 零截断 rule - must mandate complete, non-truncated output"
    checks.append(check_no_truncation)
    
    # Check 9: 积极主动 rule mentioning optimization/deployment suggestions
    check_proactive = {
        "name": "积极主动 rule with production advice",
        "passed": False,
        "detail": ""
    }
    has_proactive = "积极主动" in content
    has_production = any(kw in content for kw in ["优化建议", "部署", "生产", "最佳实践"])
    if has_proactive and has_production:
        check_proactive["passed"] = True
        check_proactive["detail"] = "Found 积极主动 rule with production/optimization suggestion directive"
    elif has_proactive:
        check_proactive["passed"] = True
        check_proactive["detail"] = "Found 积极主动 rule (partial - production keywords optional)"
    else:
        check_proactive["detail"] = "Missing 积极主动 proactive suggestion rule"
    checks.append(check_proactive)
    
    # Check 10: 混合模式 with exact switch suggestion phrase
    check_hybrid = {
        "name": "混合模式 rule with exact switch suggestion phrase",
        "passed": False,
        "detail": ""
    }
    has_hybrid_mode = "混合模式" in content
    exact_switch_phrase = "这个项目用 Claude Opus 会更完美，要我切换吗？" in content
    partial_switch = "切换" in content and "Claude Opus" in content
    
    if has_hybrid_mode and exact_switch_phrase:
        check_hybrid["passed"] = True
        check_hybrid["detail"] = "Found 混合模式 with exact Claude Opus switch suggestion phrase"
    elif has_hybrid_mode and partial_switch:
        check_hybrid["passed"] = True
        check_hybrid["detail"] = "Found 混合模式 with switch-to-Claude-Opus suggestion (partial phrase match)"
    elif has_hybrid_mode:
        check_hybrid["passed"] = False
        check_hybrid["detail"] = "Found 混合模式 but missing Claude Opus switch suggestion phrase"
    else:
        check_hybrid["detail"] = "Missing 混合模式 rule entirely"
    checks.append(check_hybrid)
    
    # Calculate score
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks
    
    # Must pass at least 8/10 checks to be considered passing, and the first 4 are mandatory
    mandatory_checks = checks[:4]  # exists, persona, level, header
    mandatory_passed = all(c["passed"] for c in mandatory_checks)
    overall_passed = mandatory_passed and score >= 0.8
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))