import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)

    # --- Check 1: Output file exists ---
    output_files = list(workspace.rglob("rewritten_article.txt"))
    if not output_files:
        checks.append({"name": "output_file_exists", "passed": False, "detail": "rewritten_article.txt not found anywhere in workspace."})
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    
    output_file = output_files[0]
    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found at {output_file}"})

    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": f"Cannot read file: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_readable", "passed": True, "detail": f"File read successfully, length={len(content)} chars."})

    # --- Check 2: Genre identification in the opening ---
    # The first sentence/paragraph must identify genre (评论类) and main problem
    first_200 = content[:300]
    genre_keywords = ["评论", "时评", "专栏", "opinion", "commentary"]
    genre_identified = any(kw in first_200 for kw in genre_keywords)
    checks.append({
        "name": "genre_identification_in_opening",
        "passed": genre_identified,
        "detail": f"Opening 300 chars: {first_200[:150]!r}. Expected mention of 评论 genre."
    })

    # --- Check 3: AI banned phrases removed ---
    banned_phrases = ["不可否认", "综合来看", "值得注意的是", "总体而言", "令人深思"]
    banned_found = [p for p in banned_phrases if p in content]
    # Allow at most 1 slip (in case the agent quotes one as an example), but penalize heavily
    banned_check_passed = len(banned_found) <= 1
    checks.append({
        "name": "banned_ai_phrases_removed",
        "passed": banned_check_passed,
        "detail": f"Banned phrases still present: {banned_found}. Allowed max 1 slip."
    })

    # --- Check 4: The "一方面...另一方面...综合来看" structure broken up ---
    # Original had this exact triple structure
    has_yifangmian = "一方面" in content
    has_lingyfangmian = "另一方面" in content
    # Both together with 综合来看 is the AI pattern - it should be broken
    triple_structure_intact = has_yifangmian and has_lingyfangmian and "综合来看" in content
    balance_structure_broken = not triple_structure_intact
    checks.append({
        "name": "balance_structure_broken",
        "passed": balance_structure_broken,
        "detail": f"'一方面' present: {has_yifangmian}, '另一方面' present: {has_lingyfangmian}, '综合来看' present: {'综合来看' in content}. The triple AI structure should be dismantled."
    })

    # --- Check 5: No bullet-point breakdown of changes ---
    # The SKILL.md says: 不要逐条解释改了什么
    # Look for numbered lists or bullet-point explanations of changes
    lines = content.split("\n")
    change_explanation_patterns = [
        r"^\s*[-•]\s+改",
        r"^\s*\d+[.、]\s+改",
        r"^\s*[-•]\s+删",
        r"^\s*\d+[.、]\s+删",
        r"^\s*[-•]\s+将",
        r"^\s*\d+[.、]\s+将",
        r"^\s*改动说明",
        r"^\s*修改说明",
        r"^\s*改写说明",
        r"^\s*以下是.*改.*的地方",
        r"^\s*主要改动",
        r"^\s*改写要点",
    ]
    bullet_change_found = []
    for line in lines:
        for pattern in change_explanation_patterns:
            if re.search(pattern, line):
                bullet_change_found.append(line.strip())
    no_bullet_explanation = len(bullet_change_found) == 0
    checks.append({
        "name": "no_bullet_change_explanation",
        "passed": no_bullet_explanation,
        "detail": f"Found change-explanation bullet lines: {bullet_change_found[:3]}" if bullet_change_found else "No bullet-point change explanations found."
    })

    # --- Check 6: Article body is substantive (not just a meta-response) ---
    # The rewrite should contain substantial Chinese text (>200 chars)
    # and should include the core topic (大模型/企业)
    topic_keywords = ["大模型", "企业", "语言模型", "GPT", "AI"]
    topic_present = any(kw in content for kw in topic_keywords)
    content_substantive = len(content) > 300 and topic_present
    checks.append({
        "name": "substantive_article_body",
        "passed": content_substantive,
        "detail": f"Content length: {len(content)}, topic keywords present: {topic_present}."
    })

    # --- Check 7: Opinionated/emotional language present (评论类 requires偏见) ---
    # Look for direct emotional/opinionated expressions that weren't in the original
    # The original was carefully neutral; the rewrite should show a clear stance
    opinionated_indicators = [
        "说实话", "坦白说", "我觉得", "其实", "明明", "偏偏", "算了", 
        "根本", "压根", "说白了", "不过分吧", "有点", "挺", "真的",
        "吧", "嘛", "呢", "啊", "哦", "？？", "！！",
        "这不就是", "不就是", "扯淡", "荒唐", "离谱", "滑稽",
    ]
    original_article = """大模型进企业：一场被高估的革命？

近年来，以GPT-4、文心一言为代表的大语言模型迅速进入企业市场，引发了广泛的关注与讨论。不可否认，这一技术浪潮正在深刻改变各行各业的工作方式，其影响不容小觑。

一方面，大模型在内容生成、代码辅助、客服自动化等领域展现出了令人瞩目的潜力。多项行业调研数据显示，引入大模型的企业在特定任务上的效率提升幅度达到了20%至40%。值得注意的是，这一数字在不同行业之间存在较大差异，制造业与金融业的表现尤为突出。另一方面，大模型的落地应用也面临诸多现实挑战。数据安全、模型幻觉、私有化部署成本居高不下，都构成了企业大规模应用的掣肘因素。不少企业在引入大模型后，发现实际效果与宣传存在明显落差，投入产出比并不理想。

综合来看，大模型进企业这一趋势是真实的，但泡沫同样存在。总体而言，我们需要以更加理性、审慎的态度来看待这场技术变革，既不应盲目跟风，也不应因噎废食。

值得注意的是，在具体落地路径上，行业内逐渐形成了几种主流模式：一是通过API调用公有云大模型，降低前期投入；二是基于开源模型进行私有化微调，保障数据安全；三是与大模型服务商签订战略合作协议，定制专属解决方案。这三种模式各有利弊，企业需要根据自身规模、数据敏感程度和技术能力做出综合判断。

不可否认，技术本身并无好坏之分，关键在于应用场景的精准匹配与落地策略的持续优化。令人深思的是，那些率先取得成效的企业，往往并非技术实力最强的头部企业，而是在某一垂直场景深耕多年、对业务流程理解最为透彻的中型企业。这一现象值得行业从业者深入思考与借鉴。

总体而言，面对大模型这一新兴技术，企业决策者应保持开放而不失冷静的心态，在跟进技术趋势的同时，牢牢把握自身核心竞争力，方能在这场技术浪潮中立于不败之地。综合来看，未来属于那些既能拥抱变化、又能保持定力的企业。"""
    
    # Check that the rewritten content is meaningfully different from original
    original_lines = set(original_article.split("。"))
    rewritten_lines = set(content.split("。"))
    overlap = len(original_lines & rewritten_lines)
    total_original = len(original_lines)
    similarity_too_high = (overlap / max(total_original, 1)) > 0.6
    
    opinionated_count = sum(1 for ind in opinionated_indicators if ind in content)
    has_opinion = opinionated_count >= 2 or not similarity_too_high
    checks.append({
        "name": "opinionated_voice_present",
        "passed": has_opinion,
        "detail": f"Opinionated indicators found: {opinionated_count}. Sentence overlap with original: {overlap}/{total_original}. Similarity too high: {similarity_too_high}."
    })

    # --- Check 8: No perfect concluding summary (完美结尾 removed) ---
    # Original ended with a smooth "总体而言...综合来看" conclusion
    # The rewrite should NOT end with a clean wrap-up
    last_200 = content[-200:] if len(content) > 200 else content
    clean_ending_patterns = ["立于不败之地", "保持定力", "未来可期", "值得期待", "方能", "相信未来", "前景广阔"]
    clean_ending_found = [p for p in clean_ending_patterns if p in last_200]
    # Having one might be okay if rephrased, but all the original closing phrases together = AI
    perfect_ending_removed = len(clean_ending_found) < 2
    checks.append({
        "name": "perfect_conclusion_avoided",
        "passed": perfect_ending_removed,
        "detail": f"Clean-ending phrases in last 200 chars: {clean_ending_found}."
    })

    # --- Final Score ---
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)
    
    # Must pass the critical checks to be considered overall passing
    critical_checks = ["output_file_exists", "banned_ai_phrases_removed", "balance_structure_broken", "no_bullet_change_explanation"]
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )
    overall_passed = critical_passed and score >= 0.7

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))