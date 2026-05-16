import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    obsidian_base = workspace / "Obsidian" / "Docs" / "OpenClaw"
    tips_dir = obsidian_base / "tips"

    # ---- CHECK 1: Correct knowledge base directory structure exists ----
    required_dirs = [
        obsidian_base / "docs",
        obsidian_base / "tips",
    ]
    required_files_base = [
        obsidian_base / "daily-tips.json",
        obsidian_base / "tips-log.md",
        obsidian_base / "latest-version.txt",
    ]
    missing_structure = []
    for p in required_dirs + required_files_base:
        if not p.exists():
            missing_structure.append(str(p.relative_to(workspace)))
    
    struct_ok = len(missing_structure) == 0
    checks.append({
        "name": "knowledge_base_structure_complete",
        "passed": struct_ok,
        "detail": "All required dirs and base files exist" if struct_ok else f"Missing: {missing_structure}"
    })
    if struct_ok:
        total_score += 1.0

    # ---- CHECK 2: latest-version.txt exists and is non-empty ----
    try:
        version_file = obsidian_base / "latest-version.txt"
        version_content = version_file.read_text(encoding="utf-8").strip()
        version_ok = len(version_content) > 0
        checks.append({
            "name": "latest_version_txt_populated",
            "passed": version_ok,
            "detail": f"Content: '{version_content}'" if version_ok else "File exists but is empty"
        })
        if version_ok:
            total_score += 0.5
    except Exception as e:
        checks.append({"name": "latest_version_txt_populated", "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 3: Tip articles exist in tips/ with correct naming convention ----
    # Expected: files like "{topic}-{chinese-description}.md"
    # From raw-tip-topics: gateway-使用指南.md, message-发送消息.md, channel-管理频道.md
    try:
        tip_files = [f for f in tips_dir.glob("*.md") if f.name != "BROKEN-stub.md"]
        
        # Check at least 3 valid tip files exist
        valid_count = len(tip_files)
        count_ok = valid_count >= 3
        checks.append({
            "name": "minimum_three_tip_articles",
            "passed": count_ok,
            "detail": f"Found {valid_count} tip files (excluding BROKEN-stub.md): {[f.name for f in tip_files]}"
        })
        if count_ok:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "minimum_three_tip_articles", "passed": False, "detail": f"Error: {e}"})
        tip_files = []

    # ---- CHECK 4: Tip articles follow the EXACT proprietary template structure ----
    # Required sections (in Chinese): 简介, 使用场景, 详细步骤, 示例, 注意事项
    REQUIRED_SECTIONS = ["## 简介", "## 使用场景", "## 详细步骤", "## 示例", "## 注意事项"]
    
    try:
        tip_files_real = [f for f in tips_dir.glob("*.md") if f.name != "BROKEN-stub.md"]
        
        template_violations = []
        template_compliant_count = 0
        
        for tip_file in tip_files_real:
            content = tip_file.read_text(encoding="utf-8")
            missing_sections = [sec for sec in REQUIRED_SECTIONS if sec not in content]
            if missing_sections:
                template_violations.append(f"{tip_file.name}: missing {missing_sections}")
            else:
                template_compliant_count += 1
        
        all_compliant = len(template_violations) == 0 and template_compliant_count >= 3
        checks.append({
            "name": "tip_articles_follow_exact_template_with_chinese_sections",
            "passed": all_compliant,
            "detail": (
                f"All {template_compliant_count} tips have correct Chinese section headers"
                if all_compliant
                else f"Violations: {template_violations}"
            )
        })
        if all_compliant:
            total_score += 2.0
    except Exception as e:
        checks.append({
            "name": "tip_articles_follow_exact_template_with_chinese_sections",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ---- CHECK 5: Tip articles have a top-level H1 title ----
    try:
        tip_files_real = [f for f in tips_dir.glob("*.md") if f.name != "BROKEN-stub.md"]
        h1_violations = []
        for tip_file in tip_files_real:
            content = tip_file.read_text(encoding="utf-8")
            if not re.search(r'^#\s+\S', content, re.MULTILINE):
                h1_violations.append(tip_file.name)
        
        h1_ok = len(h1_violations) == 0 and len(tip_files_real) >= 3
        checks.append({
            "name": "tip_articles_have_h1_title",
            "passed": h1_ok,
            "detail": "All tips have H1 titles" if h1_ok else f"Missing H1 in: {h1_violations}"
        })
        if h1_ok:
            total_score += 0.5
    except Exception as e:
        checks.append({"name": "tip_articles_have_h1_title", "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 6: Tip articles contain bash code blocks ----
    try:
        tip_files_real = [f for f in tips_dir.glob("*.md") if f.name != "BROKEN-stub.md"]
        bash_violations = []
        for tip_file in tip_files_real:
            content = tip_file.read_text(encoding="utf-8")
            if "```bash" not in content and "```\nopenclaw" not in content:
                bash_violations.append(tip_file.name)
        
        bash_ok = len(bash_violations) == 0 and len(tip_files_real) >= 3
        checks.append({
            "name": "tip_articles_contain_bash_code_blocks",
            "passed": bash_ok,
            "detail": "All tips contain bash code examples" if bash_ok else f"Missing bash blocks in: {bash_violations}"
        })
        if bash_ok:
            total_score += 0.5
    except Exception as e:
        checks.append({"name": "tip_articles_contain_bash_code_blocks", "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 7: daily-tips.json is valid JSON and non-empty/structured ----
    try:
        daily_tips_path = obsidian_base / "daily-tips.json"
        raw = daily_tips_path.read_text(encoding="utf-8").strip()
        data = json.loads(raw)
        
        # Must not be empty dict {} - must have some structure indicating tip selection
        is_non_trivial = isinstance(data, dict) and len(data) > 0
        
        checks.append({
            "name": "daily_tips_json_has_content",
            "passed": is_non_trivial,
            "detail": f"daily-tips.json content: {json.dumps(data)[:200]}" if is_non_trivial else "daily-tips.json is empty or trivial"
        })
        if is_non_trivial:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "daily_tips_json_has_content", "passed": False, "detail": f"Error reading/parsing daily-tips.json: {e}"})

    # ---- CHECK 8: tips-log.md exists and contains some logging structure ----
    try:
        tips_log = (obsidian_base / "tips-log.md").read_text(encoding="utf-8").strip()
        log_ok = len(tips_log) > 0
        checks.append({
            "name": "tips_log_md_initialized",
            "passed": log_ok,
            "detail": f"tips-log.md content (first 100 chars): {tips_log[:100]}" if log_ok else "tips-log.md is empty"
        })
        if log_ok:
            total_score += 0.5
    except Exception as e:
        checks.append({"name": "tips_log_md_initialized", "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 9: Tip filenames follow expected naming convention (kebab-chinese pattern) ----
    try:
        tip_files_real = [f for f in tips_dir.glob("*.md") if f.name != "BROKEN-stub.md"]
        convention_ok_count = 0
        convention_failures = []
        
        # Pattern: word(s)-chinese_chars.md
        pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9-]+-[\u4e00-\u9fff]+.*\.md$')
        
        for tf in tip_files_real:
            if pattern.match(tf.name):
                convention_ok_count += 1
            else:
                convention_failures.append(tf.name)
        
        convention_ok = convention_ok_count >= 3
        checks.append({
            "name": "tip_filenames_follow_kebab_chinese_convention",
            "passed": convention_ok,
            "detail": (
                f"{convention_ok_count} files follow naming convention"
                if convention_ok
                else f"Non-conforming names: {convention_failures}, conforming: {convention_ok_count}"
            )
        })
        if convention_ok:
            total_score += 1.0
    except Exception as e:
        checks.append({
            "name": "tip_filenames_follow_kebab_chinese_convention",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ---- CHECK 10: 使用场景 section has bullet list items ----
    try:
        tip_files_real = [f for f in tips_dir.glob("*.md") if f.name != "BROKEN-stub.md"]
        bullet_violations = []
        for tf in tip_files_real:
            content = tf.read_text(encoding="utf-8")
            # Find content between 使用场景 and next ## section
            match = re.search(r'## 使用场景\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
            if match:
                section_body = match.group(1)
                if not re.search(r'^- .+', section_body, re.MULTILINE):
                    bullet_violations.append(tf.name)
            else:
                bullet_violations.append(tf.name)
        
        bullets_ok = len(bullet_violations) == 0 and len(tip_files_real) >= 3
        checks.append({
            "name": "usage_scenarios_section_has_bullet_list",
            "passed": bullets_ok,
            "detail": "All 使用场景 sections have bullet items" if bullets_ok else f"Missing bullets in: {bullet_violations}"
        })
        if bullets_ok:
            total_score += 0.5
    except Exception as e:
        checks.append({"name": "usage_scenarios_section_has_bullet_list", "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 11: 详细步骤 section has numbered list items ----
    try:
        tip_files_real = [f for f in tips_dir.glob("*.md") if f.name != "BROKEN-stub.md"]
        numbered_violations = []
        for tf in tip_files_real:
            content = tf.read_text(encoding="utf-8")
            match = re.search(r'## 详细步骤\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
            if match:
                section_body = match.group(1)
                if not re.search(r'^\d+\. .+', section_body, re.MULTILINE):
                    numbered_violations.append(tf.name)
            else:
                numbered_violations.append(tf.name)
        
        numbered_ok = len(numbered_violations) == 0 and len(tip_files_real) >= 3
        checks.append({
            "name": "detailed_steps_section_has_numbered_list",
            "passed": numbered_ok,
            "detail": "All 详细步骤 sections have numbered items" if numbered_ok else f"Missing numbered steps in: {numbered_violations}"
        })
        if numbered_ok:
            total_score += 0.5
    except Exception as e:
        checks.append({"name": "detailed_steps_section_has_numbered_list", "passed": False, "detail": f"Error: {e}"})

    # Normalize score to 0-1
    max_score = 9.5
    normalized_score = round(min(total_score / max_score, 1.0), 4)

    passed = (
        checks[0]["passed"] and  # structure
        checks[3]["passed"] and  # template compliance (most critical)
        checks[8]["passed"]      # naming convention
    )

    result = {
        "passed": passed,
        "score": normalized_score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace_dir)