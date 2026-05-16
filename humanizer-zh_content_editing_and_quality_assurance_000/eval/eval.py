import sys
import json
import re
from pathlib import Path

def load_file(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None

def check_ai_patterns_removed(text, article_label):
    """Check that key AI patterns have been removed or significantly reduced."""
    checks = []
    
    # Check: Removed exaggerated significance phrases (夸大意义)
    significance_words = ["标志着.*关键转折点", "不断演变的格局", "关键里程碑", "深刻转变", "不可磨灭", "深深植根于", "永恒的", "持久的影响"]
    found_significance = []
    for w in significance_words:
        if re.search(w, text):
            found_significance.append(w)
    checks.append({
        "name": f"{article_label}: 夸大意义词汇已移除",
        "passed": len(found_significance) == 0,
        "detail": f"仍存在夸大意义词汇: {found_significance}" if found_significance else "已清除夸大意义词汇"
    })
    
    # Check: Removed promotional/advertising language (宣传性语言)
    promo_words = ["令人叹为观止", "迷人的自然美景", "充满活力", "坐落于.*心脏", "开创性的", "令人印象深刻的", "必游之地"]
    found_promo = [w for w in promo_words if w in text]
    checks.append({
        "name": f"{article_label}: 宣传性语言已移除",
        "passed": len(found_promo) == 0,
        "detail": f"仍存在宣传性词汇: {found_promo}" if found_promo else "已清除宣传性语言"
    })
    
    # Check: Removed AI vocabulary (AI词汇)
    ai_vocab = ["此外", "彰显", "格局", "至关重要", "充满活力", "深度", "深刻"]
    found_ai_vocab = [w for w in ai_vocab if text.count(w) > 1]  # Allow at most 1 occurrence
    checks.append({
        "name": f"{article_label}: 高频AI词汇已大幅减少",
        "passed": len(found_ai_vocab) <= 2,
        "detail": f"仍有过多AI词汇 (出现>1次): {found_ai_vocab}" if len(found_ai_vocab) > 2 else f"AI词汇使用已控制 (少量残余可接受: {found_ai_vocab})"
    })
    
    # Check: Removed em-dash overuse (破折号过度使用)
    em_dash_count = text.count("——")
    checks.append({
        "name": f"{article_label}: 破折号过度使用已修正",
        "passed": em_dash_count <= 1,
        "detail": f"破折号使用次数: {em_dash_count} (原文多处使用，应减少至0-1次)" if em_dash_count > 1 else f"破折号使用合理: {em_dash_count}次"
    })
    
    # Check: Removed tricolon/rule-of-three (三段式法则)
    tricolon_patterns = [
        r"[：:][^。\n]*、[^。\n]*、[^。\n]*",  # colon followed by three items with 、
    ]
    found_tricolon = []
    for pat in tricolon_patterns:
        matches = re.findall(pat, text)
        for m in matches:
            # Count items separated by 、
            items = m.split("、")
            if len(items) >= 3:
                found_tricolon.append(m[:30])
    checks.append({
        "name": f"{article_label}: 三段式列举已打破",
        "passed": len(found_tricolon) == 0,
        "detail": f"仍存在三段式列举: {found_tricolon[:2]}" if found_tricolon else "三段式结构已修正"
    })
    
    # Check: Removed vague attribution (模糊归因)
    vague_attr = ["行业报告显示", "专家认为", "观察者指出", "一些分析人士认为", "一些批评者认为"]
    found_vague = [w for w in vague_attr if w in text]
    checks.append({
        "name": f"{article_label}: 模糊归因已移除",
        "passed": len(found_vague) == 0,
        "detail": f"仍存在模糊归因: {found_vague}" if found_vague else "已移除模糊归因"
    })
    
    # Check: Removed -ing shallow analysis endings (肤浅分析)
    ing_endings = ["展现城市的", "确保公园在", "彰显了.*理念", "反映了城市对", "培养了更具", "确保乘客在"]
    found_ing = [w for w in ing_endings if re.search(w, text)]
    checks.append({
        "name": f"{article_label}: 现在分词肤浅分析短语已移除",
        "passed": len(found_ing) == 0,
        "detail": f"仍存在肤浅分析短语: {found_ing}" if found_ing else "肤浅分析短语已清除"
    })
    
    # Check: Removed negative parallel structures (否定式排比)
    neg_parallel = ["这不仅仅是.*而是", "不仅仅是.*更是"]
    found_neg = [p for p in neg_parallel if re.search(p, text)]
    checks.append({
        "name": f"{article_label}: 否定式排比已移除",
        "passed": len(found_neg) == 0,
        "detail": f"仍存在否定式排比: {found_neg}" if found_neg else "否定式排比已清除"
    })
    
    # Check: Removed generic positive conclusions (通用积极结论)
    generic_conclusions = ["激动人心的时代", "前景光明", "向正确方向迈出的重要一步", "未来看起来.*光明", "希望这对.*有帮助"]
    found_generic = [w for w in generic_conclusions if re.search(w, text)]
    checks.append({
        "name": f"{article_label}: 通用积极结论已移除",
        "passed": len(found_generic) == 0,
        "detail": f"仍存在通用积极结论: {found_generic}" if found_generic else "通用积极结论已清除"
    })
    
    # Check: Removed chatbot conversational traces (协作交流痕迹)
    chatbot_traces = ["希望这对", "如果您想了解更多", "请告诉我", "这是一个.*概述"]
    found_chatbot = [w for w in chatbot_traces if re.search(w, text)]
    checks.append({
        "name": f"{article_label}: 聊天机器人对话痕迹已移除",
        "passed": len(found_chatbot) == 0,
        "detail": f"仍存在聊天痕迹: {found_chatbot}" if found_chatbot else "聊天痕迹已清除"
    })
    
    # Check: Removed over-qualification (过度限定)
    over_qual = ["可以潜在地.*认为", "可能.*可能.*被认为", "一定的积极影响"]
    found_oq = [w for w in over_qual if re.search(w, text)]
    checks.append({
        "name": f"{article_label}: 过度限定语言已移除",
        "passed": len(found_oq) == 0,
        "detail": f"仍存在过度限定: {found_oq}" if found_oq else "过度限定已清除"
    })
    
    # Check: Removed "challenges" boilerplate section (挑战与未来展望套路)
    challenge_boilerplate = ["尽管.*面临.*挑战.*尽管存在这些挑战"]
    found_cb = [w for w in challenge_boilerplate if re.search(w, text)]
    checks.append({
        "name": f"{article_label}: 挑战与展望套路段落已移除",
        "passed": len(found_cb) == 0,
        "detail": f"仍存在套路段落: {found_cb}" if found_cb else "套路段落已清除"
    })
    
    # Check: Is-verb substitution avoided (系动词回避)
    is_substitutes = ["作为.*重要体现", "充当着.*纽带", "作为.*重要组成部分"]
    found_isub = [w for w in is_substitutes if re.search(w, text)]
    checks.append({
        "name": f"{article_label}: 系动词回避模式已修正",
        "passed": len(found_isub) == 0,
        "detail": f"仍有系动词回避: {found_isub}" if found_isub else "系动词使用自然"
    })
    
    # Check: Text is substantially rewritten (not nearly identical to original)
    # If more than 70% of original sentences are present verbatim, it's not rewritten
    original_sentences_park = [
        "坐落于城市心脏地带的河滨公园",
        "充满活力的滨水区域将被打造成",
        "改造方案涵盖三大核心板块",
        "这不仅仅是一次公园翻新"
    ]
    original_sentences_subway = [
        "地铁8号线延伸段的正式通车",
        "这不仅仅是一条地铁线路的延伸",
        "值得注意的是，各站台设计均融入了",
        "希望这对广大市民有帮助"
    ]
    
    if "河滨公园" in article_label or "riverside" in article_label.lower():
        check_sentences = original_sentences_park
    else:
        check_sentences = original_sentences_subway
    
    unchanged_count = sum(1 for s in check_sentences if s in text)
    checks.append({
        "name": f"{article_label}: 文本已实质性重写",
        "passed": unchanged_count <= 1,
        "detail": f"有{unchanged_count}/{len(check_sentences)}个原始句子仍未修改，文章改动不足" if unchanged_count > 1 else "文章已实质性重写"
    })
    
    return checks

def check_quality_report(report_text):
    """Check that quality report contains proper scoring for both articles."""
    checks = []
    
    if report_text is None:
        return [{
            "name": "质量报告文件存在",
            "passed": False,
            "detail": "未找到 quality_report.txt 文件"
        }]
    
    checks.append({
        "name": "质量报告文件存在",
        "passed": True,
        "detail": "找到质量报告文件"
    })
    
    # Check that both articles are scored
    has_park = "河滨公园" in report_text or "riverside" in report_text.lower() or "公园" in report_text
    has_subway = "地铁" in report_text or "subway" in report_text.lower() or "8号线" in report_text
    checks.append({
        "name": "质量报告包含两篇文章的评分",
        "passed": has_park and has_subway,
        "detail": f"河滨公园: {'✓' if has_park else '✗'}, 地铁8号线: {'✓' if has_subway else '✗'}"
    })
    
    # Check that the 5 dimensions are present in the report
    dimensions = ["直接性", "节奏", "信任度", "真实性", "精炼度"]
    found_dims = [d for d in dimensions if d in report_text]
    checks.append({
        "name": "质量报告包含5个评分维度",
        "passed": len(found_dims) >= 4,
        "detail": f"找到维度: {found_dims} ({len(found_dims)}/5)"
    })
    
    # Check that scores /10 are present (at least some numeric scores)
    score_pattern = re.findall(r'(\d+)\s*/\s*10', report_text)
    checks.append({
        "name": "质量报告包含 /10 格式的维度评分",
        "passed": len(score_pattern) >= 4,
        "detail": f"找到{len(score_pattern)}个 /10 格式评分 (期望至少4个，每篇文章最少2个维度)" 
    })
    
    # Check that total /50 score is present
    total_pattern = re.findall(r'(\d+)\s*/\s*50', report_text)
    checks.append({
        "name": "质量报告包含 /50 总分",
        "passed": len(total_pattern) >= 1,
        "detail": f"找到{len(total_pattern)}个 /50 总分" if total_pattern else "未找到 /50 总分格式"
    })
    
    # Check that the total scores are in a reasonable range (should be high quality after humanizing)
    valid_totals = [int(s) for s in total_pattern if 1 <= int(s) <= 50]
    checks.append({
        "name": "质量总分在合理范围内(1-50)",
        "passed": len(valid_totals) >= 1,
        "detail": f"有效总分: {valid_totals}" if valid_totals else "无有效总分或分数超出1-50范围"
    })
    
    return checks

def main():
    if len(sys.argv) < 2:
        workspace = "/workspace"
    else:
        workspace = sys.argv[1]
    
    all_checks = []
    
    # 1. Check output files exist
    park_final_path = Path(workspace) / "drafts/reviewed/riverside_park_final.txt"
    subway_final_path = Path(workspace) / "drafts/reviewed/subway_line8_final.txt"
    quality_report_path = Path(workspace) / "drafts/reviewed/quality_report.txt"
    
    park_text = load_file(park_final_path)
    subway_text = load_file(subway_final_path)
    quality_text = load_file(quality_report_path)
    
    all_checks.append({
        "name": "河滨公园最终稿存在",
        "passed": park_text is not None,
        "detail": f"文件路径: {park_final_path}" if park_text else f"未找到文件: {park_final_path}"
    })
    all_checks.append({
        "name": "地铁8号线最终稿存在",
        "passed": subway_text is not None,
        "detail": f"文件路径: {subway_final_path}" if subway_text else f"未找到文件: {subway_final_path}"
    })
    
    # 2. Check park article AI patterns removed
    if park_text:
        park_checks = check_ai_patterns_removed(park_text, "河滨公园")
        all_checks.extend(park_checks)
    else:
        all_checks.append({
            "name": "河滨公园: AI模式检查 (跳过 - 文件不存在)",
            "passed": False,
            "detail": "无法执行检查，文件不存在"
        })
    
    # 3. Check subway article AI patterns removed
    if subway_text:
        subway_checks = check_ai_patterns_removed(subway_text, "地铁8号线")
        all_checks.extend(subway_checks)
    else:
        all_checks.append({
            "name": "地铁8号线: AI模式检查 (跳过 - 文件不存在)",
            "passed": False,
            "detail": "无法执行检查，文件不存在"
        })
    
    # 4. Check quality report
    report_checks = check_quality_report(quality_text)
    all_checks.extend(report_checks)
    
    # 5. Additional cross-article checks
    if park_text and subway_text:
        # Check that files are not identical to each other (sanity)
        all_checks.append({
            "name": "两篇文章内容不相同（基本健全性检查）",
            "passed": park_text != subway_text,
            "detail": "两篇文章内容不同" if park_text != subway_text else "两篇文章内容完全相同，疑似错误"
        })
        
        # Check minimum length - humanized text shouldn't be empty
        all_checks.append({
            "name": "河滨公园最终稿长度合理 (>100字)",
            "passed": len(park_text) > 100,
            "detail": f"字数: {len(park_text)}"
        })
        all_checks.append({
            "name": "地铁8号线最终稿长度合理 (>100字)",
            "passed": len(subway_text) > 100,
            "detail": f"字数: {len(subway_text)}"
        })
    
    # Calculate score
    passed_count = sum(1 for c in all_checks if c["passed"])
    total_count = len(all_checks)
    score = passed_count / total_count if total_count > 0 else 0.0
    
    # Overall pass: need at least 75% of checks to pass
    overall_passed = score >= 0.75
    
    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": all_checks
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()