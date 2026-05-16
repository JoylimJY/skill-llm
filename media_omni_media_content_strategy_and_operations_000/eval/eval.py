import sys
import json
import os
from pathlib import Path

def run_eval(workspace_dir: str):
    checks = []
    total_score = 0.0

    # --- Find the output file ---
    output_files = list(Path(workspace_dir).rglob("content_package.json"))
    
    if not output_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False, "detail": "content_package.json not found anywhere in workspace"}]
        }

    output_path = output_files[0]
    
    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found at {output_path}"})

    # --- Load JSON ---
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.05,
            "checks": checks + [{"name": "json_valid", "passed": False, "detail": f"Failed to parse JSON: {e}"}]
        }

    checks.append({"name": "json_valid", "passed": True, "detail": "JSON parsed successfully"})

    # ===================================================================
    # CHECK GROUP 1: Platform Content Adaptation (四平台内容适配)
    # ===================================================================

    # Check 1.1: All four platforms present
    platforms_key = None
    for key in ["platform_content", "platforms", "content_adaptation", "平台内容", "platform_adaptations", "content"]:
        if key in data:
            platforms_key = key
            break
    
    platform_content = data.get(platforms_key, data) if platforms_key else data
    
    # Try to find platform sections flexibly
    def find_platform(d, platform_names):
        """Recursively search for platform content in dict"""
        if not isinstance(d, dict):
            return None
        for key in d:
            if any(name.lower() in key.lower() for name in platform_names):
                return d[key]
        # Try nested
        for key in d:
            if isinstance(d[key], dict):
                result = find_platform(d[key], platform_names)
                if result:
                    return result
        return None

    wechat_content = find_platform(data, ["wechat", "微信", "weixin"])
    weibo_content = find_platform(data, ["weibo", "微博"])
    douyin_content = find_platform(data, ["douyin", "抖音", "tiktok"])
    xiaohongshu_content = find_platform(data, ["xiaohongshu", "小红书", "xhs", "redbook"])

    platforms_found = sum([
        wechat_content is not None,
        weibo_content is not None,
        douyin_content is not None,
        xiaohongshu_content is not None
    ])

    check_all_platforms = platforms_found == 4
    checks.append({
        "name": "all_four_platforms_present",
        "passed": check_all_platforms,
        "detail": f"Found {platforms_found}/4 platforms. WeChat={'✓' if wechat_content else '✗'}, Weibo={'✓' if weibo_content else '✗'}, Douyin={'✓' if douyin_content else '✗'}, Xiaohongshu={'✓' if xiaohongshu_content else '✗'}"
    })
    if check_all_platforms:
        total_score += 0.10

    # Check 1.2: WeChat content shows depth/service characteristics (深度解读)
    # Must have long-form content, deep analysis, NOT just a headline
    def get_text_content(obj):
        """Extract all string content from a dict/list recursively"""
        if isinstance(obj, str):
            return obj
        if isinstance(obj, dict):
            return " ".join(get_text_content(v) for v in obj.values())
        if isinstance(obj, list):
            return " ".join(get_text_content(item) for item in obj)
        return str(obj) if obj else ""

    wechat_text = get_text_content(wechat_content) if wechat_content else ""
    weibo_text = get_text_content(weibo_content) if weibo_content else ""
    douyin_text = get_text_content(douyin_content) if douyin_content else ""
    xhs_text = get_text_content(xiaohongshu_content) if xiaohongshu_content else ""

    # WeChat should be long-form (深度报道 characteristic) — at least 200 chars of content
    wechat_depth = len(wechat_text) >= 200
    # WeChat should contain depth/analysis indicators
    wechat_depth_keywords = any(kw in wechat_text for kw in [
        "深度", "分析", "解读", "报道", "调查", "背景", "全面", "详细", "完整",
        "深入", "专题", "服务", "读者", "社群", "私域", "阅读", "正文"
    ])
    
    wechat_check = wechat_depth or wechat_depth_keywords
    checks.append({
        "name": "wechat_depth_service_characteristic",
        "passed": wechat_check,
        "detail": f"WeChat content length: {len(wechat_text)} chars. Depth keywords found: {wechat_depth_keywords}. WeChat should emphasize depth/service per SKILL.md."
    })
    if wechat_check:
        total_score += 0.08

    # Check 1.3: Weibo content shows speed/hotspot characteristics
    # Should contain hashtags (#) or hot topic markers, shorter/punchy
    weibo_has_hashtag = "#" in weibo_text
    weibo_speed_keywords = any(kw in weibo_text for kw in [
        "速报", "热点", "话题", "转发", "热搜", "舆论", "快讯", "即时", "追踪",
        "breaking", "最新", "紧急", "突发", "#"
    ])
    weibo_check = weibo_has_hashtag or weibo_speed_keywords
    checks.append({
        "name": "weibo_speed_hotspot_characteristic",
        "passed": weibo_check,
        "detail": f"Weibo has hashtag: {weibo_has_hashtag}. Speed/hotspot keywords: {weibo_speed_keywords}. Weibo should emphasize speed and hot topics per SKILL.md."
    })
    if weibo_check:
        total_score += 0.08

    # Check 1.4: Douyin content has "Golden 3 seconds" (黄金三秒) principle applied
    # Must have script/开场/hook within first 3 seconds
    douyin_golden3 = any(kw in douyin_text for kw in [
        "三秒", "3秒", "开场", "钩子", "hook", "黄金", "前3秒", "前三秒",
        "吸引眼球", "第一秒", "冲击", "抓住", "悬念", "痛点开场", "直接切入"
    ])
    # Also check it's structured as a video script
    douyin_script_structure = any(kw in douyin_text for kw in [
        "脚本", "script", "口播", "画面", "字幕", "配音", "镜头", "秒", "时长"
    ])
    douyin_check = douyin_golden3 or douyin_script_structure
    checks.append({
        "name": "douyin_golden_3_seconds_script",
        "passed": douyin_check,
        "detail": f"Douyin golden-3-seconds: {douyin_golden3}. Script structure indicators: {douyin_script_structure}. Douyin must apply the 黄金三秒 principle per SKILL.md."
    })
    if douyin_check:
        total_score += 0.08

    # Check 1.5: Xiaohongshu shows circle/seeding (圈层/种草) characteristics
    xhs_seeding = any(kw in xhs_text for kw in [
        "种草", "测评", "真实", "体验", "圈层", "兴趣", "干货", "博主", "笔记",
        "分享", "好物", "推荐", "种草笔记", "探店", "vlog", "图文笔记"
    ])
    xhs_check = xhs_seeding
    checks.append({
        "name": "xiaohongshu_seeding_circle_characteristic",
        "passed": xhs_check,
        "detail": f"Xiaohongshu seeding/circle keywords: {xhs_seeding}. Content: {xhs_text[:100]}... XHS should emphasize 圈层与种草 per SKILL.md."
    })
    if xhs_check:
        total_score += 0.08

    # Check 1.6: Content genuinely derives from source material (uses actual data/quotes from interview)
    all_content_text = wechat_text + weibo_text + douyin_text + xhs_text
    source_data_used = any(kw in all_content_text for kw in [
        "张伟", "骨折", "合作关系", "职业伤害", "800万", "1.2万亿", "5500",
        "陈", "法律", "人社部", "2021", "34%", "李敏", "骑手保"
    ])
    checks.append({
        "name": "source_material_utilized",
        "passed": source_data_used,
        "detail": f"Agent used actual interview data/quotes/stats in content. Found source material references: {source_data_used}"
    })
    if source_data_used:
        total_score += 0.07

    # ===================================================================
    # CHECK GROUP 2: Platform Differentiation (避免一键分发)
    # ===================================================================

    # Check 2.1: Content is NOT identical across platforms (differentiation requirement)
    if all([wechat_text, weibo_text, douyin_text, xhs_text]):
        # Check pairwise similarity - texts should NOT be >80% identical
        def text_similarity(a, b):
            # Simple character-level overlap ratio
            set_a = set(a[:300])
            set_b = set(b[:300])
            if not set_a and not set_b:
                return 1.0
            if not set_a or not set_b:
                return 0.0
            intersection = set_a & set_b
            return len(intersection) / max(len(set_a), len(set_b))
        
        sims = [
            text_similarity(wechat_text, weibo_text),
            text_similarity(wechat_text, douyin_text),
            text_similarity(wechat_text, xhs_text),
        ]
        max_sim = max(sims)
        differentiated = max_sim < 0.85
        checks.append({
            "name": "platform_content_differentiated",
            "passed": differentiated,
            "detail": f"Max pairwise similarity: {max_sim:.2f}. Content should be differentiated per platform, not 一键分发. Threshold: <0.85"
        })
        if differentiated:
            total_score += 0.07
    else:
        checks.append({
            "name": "platform_content_differentiated",
            "passed": False,
            "detail": "Cannot check differentiation - not all platforms have content"
        })

    # ===================================================================
    # CHECK GROUP 3: Data Diagnosis (数据诊断)
    # ===================================================================

    # Find diagnosis section
    diagnosis_content = None
    for key in ["diagnosis", "data_diagnosis", "analytics", "diagnostics", "analysis",
                "数据诊断", "诊断", "分析", "data_analysis", "performance_analysis"]:
        if key in data:
            diagnosis_content = data[key]
            break
    
    # Also check nested
    if diagnosis_content is None:
        def find_diagnosis(d):
            if not isinstance(d, dict):
                return None
            for key in d:
                if any(kw in key.lower() for kw in ["diagnos", "analys", "诊断", "分析", "performance"]):
                    return d[key]
            for key in d:
                if isinstance(d[key], dict):
                    result = find_diagnosis(d[key])
                    if result:
                        return result
            return None
        diagnosis_content = find_diagnosis(data)

    diagnosis_text = get_text_content(diagnosis_content) if diagnosis_content else ""
    # Also search entire document
    full_doc_text = get_text_content(data)

    checks.append({
        "name": "diagnosis_section_exists",
        "passed": len(diagnosis_text) > 50,
        "detail": f"Diagnosis section found: {diagnosis_content is not None}. Length: {len(diagnosis_text)}"
    })
    if len(diagnosis_text) > 50:
        total_score += 0.05

    # Check 3.1: ART001 clickbait diagnosis
    # ART001 has high reads (58200) but very low likes (312) + low completion rate (8.2%)
    # SKILL.md: "阅读量高但互动率极低 → 标题党/封面误导"
    art001_diagnosis = any(kw in full_doc_text for kw in [
        "标题党", "ART001", "震惊", "误导", "标题与正文", "封面误导", "clickbait",
        "互动率低", "阅读量高", "高阅低互", "内容质量", "Call to Action", "互动引导"
    ])
    checks.append({
        "name": "art001_clickbait_diagnosis",
        "passed": art001_diagnosis,
        "detail": f"ART001 (高阅读/低互动) correctly diagnosed as clickbait/标题党 issue per SKILL.md troubleshooting. Found: {art001_diagnosis}"
    })
    if art001_diagnosis:
        total_score += 0.08

    # Check 3.2: ART003 completion rate diagnosis
    # ART003 douyin video: completion_rate=12.3%, avg_watch=7.2s on 58s video
    # SKILL.md: "完播率低 → 视频节奏问题"
    art003_diagnosis = any(kw in full_doc_text for kw in [
        "完播率", "ART003", "节奏", "rhythm", "视频节奏", "黄金三秒", "开场",
        "12.3", "7.2", "跳出", "前几秒", "节奏感", "剪辑节奏", "吸引力"
    ])
    checks.append({
        "name": "art003_completion_rate_diagnosis",
        "passed": art003_diagnosis,
        "detail": f"ART003 (低完播率12.3%) correctly diagnosed as video rhythm/节奏 issue per SKILL.md. Found: {art003_diagnosis}"
    })
    if art003_diagnosis:
        total_score += 0.08

    # Check 3.3: ART002 identified as positive example (深度内容 with high engagement)
    art002_positive = any(kw in full_doc_text for kw in [
        "ART002", "优质", "正面", "成功", "高质量", "深度", "好案例", "表现好",
        "互动率高", "完读率高", "71", "1890", "2340", "转发量高", "社交货币"
    ])
    checks.append({
        "name": "art002_positive_example_identified",
        "passed": art002_positive,
        "detail": f"ART002 identified as high-quality deep content with good engagement metrics. Found: {art002_positive}"
    })
    if art002_positive:
        total_score += 0.05

    # Check 3.4: ART005 Weibo - identified as speed/shares characteristic  
    # ART005 has 342K reads and 8900 shares on Weibo - social amplification
    art005_analysis = any(kw in full_doc_text for kw in [
        "ART005", "微博", "转发", "传播", "社交货币", "话题", "8900", "342",
        "扩散", "裂变", "weibo", "热点"
    ])
    checks.append({
        "name": "art005_weibo_shares_analysis",
        "passed": art005_analysis,
        "detail": f"ART005 Weibo high-share content analyzed. Found: {art005_analysis}"
    })
    if art005_analysis:
        total_score += 0.04

    # ===================================================================
    # CHECK GROUP 4: Structural Quality (结构完整性)
    # ===================================================================

    # Check 4.1: JSON has meaningful structure (not flat string dump)
    has_nested_structure = isinstance(data, dict) and any(isinstance(data[k], (dict, list)) for k in data)
    checks.append({
        "name": "structured_json_not_flat",
        "passed": has_nested_structure,
        "detail": f"Output is structured JSON with nested objects, not a flat string dump."
    })
    if has_nested_structure:
        total_score += 0.05

    # Check 4.2: One-source-multiple-formats principle mentioned or applied
    # "一次采集，多种生成" - all content derives from the same interview source
    omni_principle = any(kw in full_doc_text for kw in [
        "一次采集", "多种生成", "多元生成", "全媒", "矩阵", "多平台", "素材库",
        "核心素材", "同一素材", "原始素材", "interview_raw"
    ])
    checks.append({
        "name": "omni_media_one_source_principle",
        "passed": omni_principle,
        "detail": f"SKILL.md's 一次采集多种生成 principle acknowledged or applied. Found: {omni_principle}"
    })
    if omni_principle:
        total_score += 0.04

    # Check 4.3: Recommendations/改进建议 present in diagnosis
    has_recommendations = any(kw in full_doc_text for kw in [
        "建议", "改进", "优化", "下一步", "行动项", "recommendations",
        "suggestion", "改善", "策略", "对策", "措施"
    ])
    checks.append({
        "name": "diagnosis_includes_recommendations",
        "passed": has_recommendations,
        "detail": f"Diagnosis section includes actionable improvement recommendations. Found: {has_recommendations}"
    })
    if has_recommendations:
        total_score += 0.05

    # ===================================================================
    # FINAL SCORING
    # ===================================================================
    total_score = min(total_score, 1.0)
    passed = total_score >= 0.60

    return {
        "passed": passed,
        "score": round(total_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))