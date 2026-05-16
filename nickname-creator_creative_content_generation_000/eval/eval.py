import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)

    # === CHECK 1: Find the report file ===
    report_files = list(workspace.rglob("nickname_report.md"))
    file_found = len(report_files) > 0
    checks.append({
        "name": "report_file_exists",
        "passed": file_found,
        "detail": f"Found {len(report_files)} file(s) named 'nickname_report.md'" if file_found else "No file named 'nickname_report.md' found anywhere in workspace"
    })

    if not file_found:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    report_path = report_files[0]
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({
            "name": "file_readable",
            "passed": False,
            "detail": f"Could not read file: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "file_readable",
        "passed": True,
        "detail": f"File read successfully, {len(content)} chars"
    })

    # === CHECK 2: Required header emoji 🎭 ===
    has_header_emoji = "🎭" in content
    checks.append({
        "name": "header_emoji_present",
        "passed": has_header_emoji,
        "detail": "Found 🎭 emoji in report header" if has_header_emoji else "Missing required 🎭 emoji in report header (required by output format spec)"
    })

    # === CHECK 3: Required 💬 创意解读 for each nickname ===
    has_creative_label = "💬" in content and "创意解读" in content
    checks.append({
        "name": "creative_interpretation_present",
        "passed": has_creative_label,
        "detail": "Found 💬 创意解读 section markers" if has_creative_label else "Missing required '💬 创意解读：' markers (required by output format spec)"
    })

    # === CHECK 4: Correct number of nicknames (3-5) ===
    # Count numbered entries like **1.** or 1. followed by a nickname
    numbered_entries = re.findall(r'\*\*\s*\d+\s*[\.\。]\s*.+?\*\*', content)
    if not numbered_entries:
        # Try alternate pattern: plain numbered list
        numbered_entries = re.findall(r'(?m)^\s*\d+\s*[\.\。]\s*\*{0,2}[^\n\*]+\*{0,2}', content)
    
    # Count 💬 as proxy for number of nickname entries
    creative_count = content.count("💬")
    nickname_count_valid = 3 <= creative_count <= 5
    checks.append({
        "name": "nickname_count_3_to_5",
        "passed": nickname_count_valid,
        "detail": f"Found {creative_count} nickname entries (💬 markers). Required: 3-5." + (" ✓" if nickname_count_valid else " ✗ - must be exactly 3-5 nicknames")
    })

    # === CHECK 5: Gender-appropriate content (female client) ===
    # Should NOT contain masculine-only terms like 大汉、爷 applied as the user's identity
    # Should reflect feminine or gender-neutral style
    # The client is female - names should be appropriate
    # Check for presence of rain/moon imagery (晓/雨/月 - from client's name and preferences)
    rain_moon_imagery = bool(re.search(r'[雨月晓]', content))
    checks.append({
        "name": "client_imagery_reflected",
        "passed": rain_moon_imagery,
        "detail": "Report incorporates client's personal imagery (雨/月/晓 from her name and preferences)" if rain_moon_imagery else "Report does not reflect client's stated imagery preferences (雨, 月, 晓 - from conversation transcript)"
    })

    # === CHECK 6: Style matches dual preference (文艺清冷 + 游戏竞技) ===
    # Look for indicators of both styles coexisting
    # 文艺清冷 style markers: poetic words, classical references, cold/ethereal feel
    wenyi_markers = re.search(r'[诗词月雨晚风烟霜寒清冷]', content)
    # 游戏竞技 style markers: game-related power words
    game_markers = re.search(r'[战猎杀境界神手锋刃破霸王]', content)
    style_dual = bool(wenyi_markers) and bool(game_markers)
    checks.append({
        "name": "dual_style_reflected",
        "passed": style_dual,
        "detail": f"文艺清冷 markers: {'present' if wenyi_markers else 'MISSING'}, 游戏竞技 markers: {'present' if game_markers else 'MISSING'}. Client requested both styles."
    })

    # === CHECK 7: Format uses bold markdown for nickname names ===
    has_bold_nicknames = bool(re.search(r'\*\*[^*\n]+\*\*', content))
    checks.append({
        "name": "bold_markdown_nicknames",
        "passed": has_bold_nicknames,
        "detail": "Nicknames are formatted in bold markdown (**name**) as required by output format" if has_bold_nicknames else "Nicknames are NOT formatted in bold markdown - output format requires **bold** for nickname names"
    })

    # === CHECK 8: Creative technique applied (拆字/谐音/意象联想/etc.) ===
    # Check creative interpretation sections have meaningful length
    creative_sections = re.findall(r'💬\s*创意解读[：:]\s*(.+?)(?=\n\n|\n\*\*|\Z)', content, re.DOTALL)
    meaningful_interpretations = [s for s in creative_sections if len(s.strip()) >= 10]
    has_meaningful_creative = len(meaningful_interpretations) >= 2
    checks.append({
        "name": "meaningful_creative_interpretations",
        "passed": has_meaningful_creative,
        "detail": f"Found {len(meaningful_interpretations)} meaningful creative interpretations (>=10 chars each). Required: at least 2 detailed interpretations explaining the nickname's meaning/origin."
    })

    # === CHECK 9: Does NOT use deprecated format (old format trap) ===
    # Old/trap format: "外号A - 解释" style without emoji markers
    uses_deprecated_format = bool(re.search(r'(?m)^\d+\.\s+\w+\s+-\s+\w+', content)) and "💬" not in content
    checks.append({
        "name": "not_using_deprecated_format",
        "passed": not uses_deprecated_format,
        "detail": "Report correctly uses new format (not the deprecated 'name - description' format from old templates)" if not uses_deprecated_format else "Report appears to use deprecated format (old template v1 format) instead of current spec"
    })

    # === Final scoring ===
    all_checks = checks[1:]  # exclude file-exists from scoring weight
    critical_checks = ["header_emoji_present", "creative_interpretation_present", 
                       "nickname_count_3_to_5", "client_imagery_reflected", 
                       "bold_markdown_nicknames"]
    
    passed_checks = [c for c in checks if c["passed"]]
    total_scored = len(checks)
    score_raw = len(passed_checks) / total_scored

    # Critical checks must all pass for overall pass
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )

    overall_passed = critical_passed and score_raw >= 0.75

    return {
        "passed": overall_passed,
        "score": round(score_raw, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))