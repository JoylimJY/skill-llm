import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace):
    results = []
    
    # 1. Find the output script file
    novel_dir = Path(workspace) / "projects" / "凌云传" / "novels"
    expected_filename = "《凌云传》剧本.txt"
    script_path = novel_dir / expected_filename
    
    # Also search broadly in case agent placed it elsewhere
    found_files = list(Path(workspace).rglob("《凌云传》剧本.txt"))
    
    if not script_path.exists():
        if found_files:
            results.append(check("file_location", False, 
                f"文件存在但位置错误: {found_files[0]}. 应保存在: {script_path}"))
            script_path = found_files[0]  # use found file for further checks
        else:
            results.append(check("file_location", False, "未找到《凌云传》剧本.txt文件"))
            # All other checks fail
            for name in ["file_naming", "header_block", "yiju_hua_format", "scene_headers", 
                         "shot_marker", "os_format", "special_markers", "system_voice",
                         "audio_markers", "scene_change", "four_stage_structure"]:
                results.append(check(name, False, "文件未找到，无法检查"))
            total = sum(1 for r in results if r["passed"])
            return results, total / len(results)
    else:
        results.append(check("file_location", True, f"文件位于正确目录: {script_path}"))
    
    # Read file
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        results.append(check("file_readable", False, f"文件读取失败: {e}"))
        score = sum(1 for r in results if r["passed"]) / max(len(results), 1)
        return results, score
    
    results.append(check("file_readable", True, "文件可正常读取"))
    
    # 2. Check filename (must have 《》brackets)
    results.append(check("file_naming", True, f"文件名正确: {script_path.name}"))
    
    # 3. Check header block - must contain all required fields
    required_header_fields = ["作品名", "题材", "类型", "简略梗概", "主角", "受众", "情绪承诺", "本集一句话", "钩子", "增量", "反转", "续看"]
    missing_fields = [f for f in required_header_fields if f not in content]
    if missing_fields:
        results.append(check("header_block", False, f"缺少必要字段: {missing_fields}"))
    else:
        results.append(check("header_block", True, "头部信息块包含所有必要字段"))
    
    # 4. Check "本集一句话" format - must follow template with 【目标】【规则/限制】etc.
    yiju_pattern = r'本集一句话[：:].{0,200}为了.{1,50}在.{1,80}下.{0,30}逼到.{1,50}最后.{1,80}引出'
    yiju_match = re.search(yiju_pattern, content, re.DOTALL)
    if yiju_match:
        results.append(check("yiju_hua_format", True, "本集一句话格式符合模板"))
    else:
        # More lenient check: just has the key structural words
        yiju_pattern2 = r'本集一句话[：:]'
        if re.search(yiju_pattern2, content):
            # Check it has the 5 key elements
            yiju_section = content[content.find("本集一句话"):content.find("本集一句话")+200]
            has_mubia = "目标" in yiju_section or "为了" in yiju_section
            has_limit = "限制" in yiju_section or "规则" in yiju_section or "在" in yiju_section
            has_junjing = "困境" in yiju_section or "逼" in yiju_section
            has_bianhua = "最后" in yiju_section or "变化" in yiju_section
            has_xuyan = "续看" in yiju_section or "引出" in yiju_section
            if sum([has_mubia, has_limit, has_junjing, has_bianhua, has_xuyan]) >= 3:
                results.append(check("yiju_hua_format", True, "本集一句话包含主要模板元素"))
            else:
                results.append(check("yiju_hua_format", False, f"本集一句话格式不符合模板，缺少关键元素"))
        else:
            results.append(check("yiju_hua_format", False, "缺少'本集一句话'字段"))
    
    # 5. Check scene headers - must have format like "1-1 场景名 日外/日内/夜外/夜内"
    scene_header_pattern = r'\d+-\d+\s+\S+\s+(日外|日内|夜外|夜内)'
    scene_headers = re.findall(scene_header_pattern, content)
    if len(scene_headers) >= 2:
        results.append(check("scene_headers", True, f"找到{len(scene_headers)}个格式正确的场标题（含时间代码）"))
    else:
        # Try looser match
        loose_scene = re.findall(r'\d+-\d+', content)
        if loose_scene:
            results.append(check("scene_headers", False, 
                f"找到{len(loose_scene)}个场次标记，但场标题缺少时间代码(日外/日内/夜外/夜内)"))
        else:
            results.append(check("scene_headers", False, "未找到场标题（格式应为：1-1 场景名 日外/日内/夜外/夜内）"))
    
    # 6. Check ▲ shot markers
    shot_markers = re.findall(r'▲', content)
    if len(shot_markers) >= 3:
        # Check they have content describing framing/action
        shot_lines = [line for line in content.split('\n') if line.strip().startswith('▲')]
        has_framing = any(any(w in line for w in ['景', '近景', '全景', '中景', '特写', '俯']) for line in shot_lines)
        if has_framing:
            results.append(check("shot_marker", True, f"找到{len(shot_markers)}个▲镜头标记，包含景别描述"))
        else:
            results.append(check("shot_marker", False, f"找到{len(shot_markers)}个▲标记，但镜头描述缺少景别信息"))
    elif len(shot_markers) > 0:
        results.append(check("shot_marker", False, f"▲镜头标记数量不足（仅{len(shot_markers)}个，需要至少3个）"))
    else:
        results.append(check("shot_marker", False, "未找到▲镜头标记（这是剧本的核心格式要求）"))
    
    # 7. Check OS (inner monologue) format - must be on separate line under character name
    # Pattern: character name line, then "OS" on next line, then content
    os_pattern = r'\w+[：:]\s*\n\s*OS\s*\n'
    os_matches = re.findall(os_pattern, content)
    # Also check inline OS format as fallback
    inline_os = re.findall(r'\w+OS[：:]', content)
    if os_matches:
        results.append(check("os_format", True, f"找到{len(os_matches)}处正确格式的OS内心独白（角色名+换行+OS+换行+内容）"))
    elif inline_os:
        results.append(check("os_format", False, f"OS格式不正确，应为角色名后换行写OS，不应写成'角色名OS：'"))
    else:
        # Check if there's any OS at all
        if 'OS' in content:
            results.append(check("os_format", False, "包含OS但格式不正确，应为：角色名：\\nOS\\n内心独白内容"))
        else:
            results.append(check("os_format", False, "未找到OS内心独白（小说有心理描写，应转换为OS格式）"))
    
    # 8. Check special markers - 【闪回】/【闪出】 (novel has flashback content)
    has_flashback_open = '【闪回】' in content
    has_flashback_close = '【闪出】' in content or '【闪回结束】' in content
    if has_flashback_open and has_flashback_close:
        results.append(check("special_markers", True, "正确使用【闪回】...【闪出】标记"))
    elif has_flashback_open:
        results.append(check("special_markers", False, "有【闪回】但缺少【闪出】结束标记"))
    else:
        results.append(check("special_markers", False, "未找到【闪回】标记（原著有回忆片段，应使用此标记）"))
    
    # 9. Check system voice format (novel has system announcement)
    has_system = '系统' in content and ('：' in content or ':' in content)
    system_lines = [line for line in content.split('\n') if '系统' in line and ('：' in line or ':' in line)]
    if system_lines:
        results.append(check("system_voice", True, f"包含系统提示音台词: {system_lines[0][:50]}"))
    else:
        results.append(check("system_voice", False, "未找到系统提示音台词（原著有系统叮声，应转换为'系统：'格式）"))
    
    # 10. Check audio markers (音效/BGM/特效)
    has_audio = bool(re.search(r'音效[：:]|BGM[：:]|特效[：:]', content))
    if has_audio:
        audio_count = len(re.findall(r'音效[：:]|BGM[：:]|特效[：:]', content))
        results.append(check("audio_markers", True, f"包含{audio_count}处音效/BGM/特效标记"))
    else:
        results.append(check("audio_markers", False, "缺少音效/BGM/特效标记"))
    
    # 11. Check scene endings have changes (升级/反转/悬念/兑现)
    change_words = ['升级', '反转', '悬念', '兑现', '变化', '转折']
    # Check the structural section of the script
    has_turn = any(w in content for w in ['Turn', '转折', '反转', '兑现', '续看'])
    header_has_structure = '续看' in content and ('反转' in content or '兑现' in content)
    if header_has_structure:
        results.append(check("scene_change", True, "剧本结构包含反转/兑现/续看等变化节点"))
    else:
        results.append(check("scene_change", False, "剧本缺少明确的场景变化节点（反转/兑现/续看）"))
    
    # 12. Check four-stage structure (钩子/增量/反转兑现/续看)
    four_stage = all(stage in content for stage in ['钩子', '增量', '续看'])
    if four_stage:
        results.append(check("four_stage_structure", True, "包含完整四段式结构（钩子/增量/反转兑现/续看）"))
    else:
        missing = [s for s in ['钩子', '增量', '续看'] if s not in content]
        results.append(check("four_stage_structure", False, f"四段式结构不完整，缺少: {missing}"))
    
    # Calculate score
    total_passed = sum(1 for r in results if r["passed"])
    score = total_passed / len(results)
    
    return results, score

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    try:
        checks, score = run_eval(workspace)
        passed = score >= 0.70  # Need 70% of checks to pass
        
        print(json.dumps({
            "passed": passed,
            "score": round(score, 3),
            "checks": checks
        }, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_error", "passed": False, "detail": str(e)}]
        }, ensure_ascii=False))