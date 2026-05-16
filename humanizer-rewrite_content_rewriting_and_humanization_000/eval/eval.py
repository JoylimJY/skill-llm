import sys
import json
import re
import os
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    target_file = Path(workspace_dir) / "content" / "drafts" / "product_launch_article.txt"
    
    # Check 1: File exists and has been modified
    try:
        if not target_file.exists():
            raise FileNotFoundError(f"Target file not found: {target_file}")
        content = target_file.read_text(encoding="utf-8")
        file_exists = True
        checks.append({"name": "目标文件存在且可读", "passed": True, "detail": f"文件路径: {target_file}, 字符数: {len(content)}"})
    except Exception as e:
        checks.append({"name": "目标文件存在且可读", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # Check 2: File content has been substantially changed from the original AI article
    original_ai_phrases = [
        "随着人工智能技术的飞速发展",
        "综上所述",
        "未来可期",
        "值得注意的是",
        "与此同时"
    ]
    original_phrases_found = sum(1 for phrase in original_ai_phrases if phrase in content)
    file_modified = original_phrases_found <= 2  # At most 2 original AI phrases should remain
    checks.append({
        "name": "文件内容已被实质性改写（原始AI套话已被去除）",
        "passed": file_modified,
        "detail": f"原始AI高危套话残留数量: {original_phrases_found}/5 (应 ≤ 2). 发现的套话: {[p for p in original_ai_phrases if p in content]}"
    })

    # Check 3: Output contains round structure with proper separators
    # The format requires ═══ separators and 【第 N 轮 · 执行者草稿】 headers
    has_round_format = bool(re.search(r'═{10,}', content)) or bool(re.search(r'【第\s*[1-3]\s*轮', content))
    
    # The final file should contain the rewritten article - check if it's the final version
    # OR the content contains the iteration output
    # Per skill: "将最终版本覆盖写回原文件"
    # So the file should contain the FINAL rewritten article (not necessarily the full iteration log)
    # But we need to check if the rewrite actually happened

    # Check 4: Presence of humanization markers - subjective language
    subjective_markers = ["我", "其实", "说白了", "说实话", "觉得", "我认为", "扯", "真的", "可能", "但"]
    subjective_count = sum(1 for marker in subjective_markers if marker in content)
    has_subjective_voice = subjective_count >= 3
    checks.append({
        "name": "包含主观语气和口语化表达（拟人化注入）",
        "passed": has_subjective_voice,
        "detail": f"发现的主观/口语标记数量: {subjective_count}/10 (应 ≥ 3). 标记: {[m for m in subjective_markers if m in content]}"
    })

    # Check 5: No forbidden AI-writing clichés in final content
    forbidden_endings = ["未来可期", "值得深思", "让我们共同期待", "相信未来"]
    has_no_cliche_ending = not any(phrase in content for phrase in forbidden_endings)
    checks.append({
        "name": "最终文章不含升华式AI结尾套话",
        "passed": has_no_cliche_ending,
        "detail": f"残留升华套话: {[p for p in forbidden_endings if p in content]}"
    })

    # Check 6: No overused transition phrases
    forbidden_transitions = ["综上所述", "值得注意的是", "与此同时", "此外，", "首先，其次，最后"]
    transition_count = sum(1 for phrase in forbidden_transitions if phrase in content)
    has_no_excessive_transitions = transition_count <= 1
    checks.append({
        "name": "最终文章去除了滥用过渡词",
        "passed": has_no_excessive_transitions,
        "detail": f"残留AI过渡词数量: {transition_count}/5 (应 ≤ 1). 发现: {[p for p in forbidden_transitions if p in content]}"
    })

    # Check 7: Content is in Simplified Chinese (not empty, not English replacement)
    chinese_char_count = len(re.findall(r'[\u4e00-\u9fff]', content))
    is_chinese = chinese_char_count >= 100
    checks.append({
        "name": "最终内容为简体中文且有实质字数",
        "passed": is_chinese,
        "detail": f"中文字符数: {chinese_char_count} (应 ≥ 100)"
    })

    # Check 8: Look for iteration structure evidence - either in the file itself or check for sentence variety
    # Check for question marks or exclamations (sentence variety - non-pure declarative)
    has_sentence_variety = bool(re.search(r'[？！…—]', content))
    checks.append({
        "name": "句式多样性：包含问句/感叹/破折号/省略号",
        "passed": has_sentence_variety,
        "detail": f"是否包含 ？！…— 等多样句式标点: {has_sentence_variety}"
    })

    # Check 9: The iteration log should be present in the output (either in file or agent's stdout captured)
    # Per skill: the file should contain the FINAL article. But the output format during execution should have rounds.
    # We check if the content shows evidence of the iterative process OR is clearly a rewritten (non-AI) article
    # Look for round markers in the file (agent may have written full iteration log)
    round_pattern = re.search(r'【第\s*[123]\s*轮', content)
    has_iteration_evidence = round_pattern is not None
    
    # Also check: if the file only has the final article (clean rewrite), we need to verify it's substantially different
    content_length = len(content)
    is_substantially_rewritten = content_length >= 200  # Must have real content

    checks.append({
        "name": "文件包含迭代轮次标记或经过实质改写",
        "passed": has_iteration_evidence or (file_modified and is_substantially_rewritten),
        "detail": f"发现轮次标记: {has_iteration_evidence}, 内容长度: {content_length}, 实质改写: {file_modified and is_substantially_rewritten}"
    })

    # Check 10: Verify the critic scoring format if iteration log is present
    if has_iteration_evidence:
        critic_pattern = re.search(r'【第\s*[123]\s*轮\s*·\s*批评者', content)
        judge_pattern = re.search(r'【第\s*[123]\s*轮\s*·\s*裁判者', content)
        has_full_triangle = critic_pattern is not None and judge_pattern is not None
        checks.append({
            "name": "迭代日志包含完整三角结构（执行者+批评者+裁判者）",
            "passed": has_full_triangle,
            "detail": f"发现批评者模块: {critic_pattern is not None}, 发现裁判者模块: {judge_pattern is not None}"
        })
        
        # Check for anti-defense lock phrase
        anti_defense = "我的批评维持原判" in content
        checks.append({
            "name": "批评者包含反辩护锁语句",
            "passed": anti_defense,
            "detail": f"是否包含「我的批评维持原判，请在下一轮修改中证明」: {anti_defense}"
        })

        # Check for humanization technique labels
        tech_labels = ["口语锚点", "观点突袭", "自我矛盾", "具体细节锚定", "句子截断", "反转一次"]
        tech_count = sum(1 for t in tech_labels if t in content)
        has_enough_techniques = tech_count >= 2
        checks.append({
            "name": "裁判者标注了使用的拟人化注入技术（≥2种）",
            "passed": has_enough_techniques,
            "detail": f"发现的技术标注数量: {tech_count}/6. 发现: {[t for t in tech_labels if t in content]}"
        })

        # Check for average score mention
        score_pattern = re.search(r'平均分[：:]\s*(\d+\.?\d*)\s*/\s*5', content)
        has_score = score_pattern is not None
        checks.append({
            "name": "批评者给出了量化评分（平均分 X.X/5）",
            "passed": has_score,
            "detail": f"发现评分格式: {score_pattern.group(0) if score_pattern else '未找到'}"
        })

    # Final scoring
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    # Must pass critical checks to overall pass
    critical_passed = (
        checks[0]["passed"] and  # file exists
        checks[2]["passed"] and  # has subjective voice
        checks[3]["passed"] and  # no cliche ending
        checks[6]["passed"]      # is Chinese
    )
    
    overall_passed = critical_passed and score >= 0.65

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "参数错误", "passed": False, "detail": "需要提供workspace目录路径"}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))