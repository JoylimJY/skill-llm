import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0

    workspace_path = Path(workspace)

    # ── helper ────────────────────────────────────────────────────────────────
    def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed, weight

    # ── find merged_article.md anywhere in workspace ──────────────────────────
    merged_files = list(workspace_path.rglob("merged_article.md"))

    if not merged_files:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": "merged_article.md not found anywhere in workspace"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    merged_path = merged_files[0]

    try:
        merged_content = merged_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({
            "name": "output_file_readable",
            "passed": False,
            "detail": f"Could not read merged_article.md: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "output_file_exists",
        "passed": True,
        "detail": f"Found merged_article.md at {merged_path}"
    })

    merged_lower = merged_content.lower()

    # ── CHECK 1: Merge report present ─────────────────────────────────────────
    # Must contain the required emoji-prefixed fields from SKILL.md output format
    has_report_header = "合并报告" in merged_content or "merge report" in merged_lower
    has_base_draft_field = "基础稿" in merged_content
    has_contribution_field = "稿件贡献" in merged_content or "贡献" in merged_content
    has_score_field = "质量评分" in merged_content
    has_changes_field = "主要修改" in merged_content

    report_fields_present = sum([
        has_report_header,
        has_base_draft_field,
        has_contribution_field,
        has_score_field,
        has_changes_field
    ])

    report_check_passed = report_fields_present >= 4
    checks.append({
        "name": "merge_report_format",
        "passed": report_check_passed,
        "detail": (
            f"Merge report fields present: {report_fields_present}/5. "
            f"report_header={has_report_header}, base_draft={has_base_draft_field}, "
            f"contribution={has_contribution_field}, score_field={has_score_field}, "
            f"changes={has_changes_field}"
        )
    })

    # ── CHECK 2: Emoji fields present (proprietary format trap) ───────────────
    emoji_fields = {
        "📊": "📊" in merged_content,
        "📝": "📝" in merged_content,
        "📄": "📄" in merged_content,
        "✏️": "✏️" in merged_content or "✏" in merged_content,
        "📈": "📈" in merged_content,
    }
    emoji_count = sum(emoji_fields.values())
    emoji_check_passed = emoji_count >= 3
    checks.append({
        "name": "merge_report_emoji_format",
        "passed": emoji_check_passed,
        "detail": (
            f"Proprietary emoji-prefixed report fields found: {emoji_count}/5. "
            f"Details: {emoji_fields}"
        )
    })

    # ── CHECK 3: Base draft correctly identified as draft_a ───────────────────
    # Draft A should be highest scoring and selected as base
    base_draft_correct = (
        "draft_a" in merged_lower or
        "draft a" in merged_lower or
        "稿a" in merged_content or
        "稿A" in merged_content or
        ("a.md" in merged_lower and "基础稿" in merged_content)
    )
    checks.append({
        "name": "base_draft_correctly_identified",
        "passed": base_draft_correct,
        "detail": (
            f"Base draft (draft_a) correctly identified as highest quality: {base_draft_correct}. "
            "Draft A should have highest weighted score (~85) per quality criteria."
        )
    })

    # ── CHECK 4: Draft C annotated as low quality (<30 rule) ─────────────────
    # SKILL.md: "某稿评估得分极低（<30）→ 在报告中单独标注"
    low_quality_annotated = (
        ("draft_c" in merged_lower or "稿c" in merged_content or "稿C" in merged_content) and
        any(kw in merged_content for kw in [
            "<30", "30分", "极低", "低质", "单独标注", "较差", "质量过低",
            "low", "poor", "below 30"
        ])
    )
    checks.append({
        "name": "low_quality_draft_annotated",
        "passed": low_quality_annotated,
        "detail": (
            f"Draft C (expected score <30) annotated in report: {low_quality_annotated}. "
            "SKILL.md requires separate annotation for drafts scoring below 30."
        )
    })

    # ── CHECK 5: Weighted scoring formula applied ─────────────────────────────
    # Check that numeric scores appear and that the weights (20%, 25%, 20%, 15%, 20%) 
    # or dimension names are mentioned, indicating weighted calculation was done
    dimension_keywords = [
        "结构清晰度", "信息完整度", "表达质量", "独特亮点", "主题契合度"
    ]
    dimensions_mentioned = sum(1 for kw in dimension_keywords if kw in merged_content)

    # Check for numeric score in range (any number between 50-100 appearing near 评分)
    score_numbers = re.findall(r'(\d{2,3}(?:\.\d+)?)\s*(?:分|/100|分/100)', merged_content)
    has_numeric_score = len(score_numbers) > 0

    # Also check for weight percentages
    has_weights = any(w in merged_content for w in ["20%", "25%", "15%"])

    scoring_check_passed = dimensions_mentioned >= 3 or (has_numeric_score and (has_weights or dimensions_mentioned >= 2))
    checks.append({
        "name": "weighted_scoring_formula_applied",
        "passed": scoring_check_passed,
        "detail": (
            f"Quality scoring evidence: dimensions_mentioned={dimensions_mentioned}/5, "
            f"numeric_scores_found={score_numbers}, has_weights={has_weights}. "
            "Weighted formula: structure 20%, completeness 25%, expression 20%, highlights 15%, topic_fit 20%."
        )
    })

    # ── CHECK 6: Conflict about market size detected and reported ─────────────
    # Draft A says "450亿美元 / 2027", Draft B says "620亿美元 / 2028" (source unspecified)
    # Agent must detect and report this conflict
    conflict_detected = any(kw in merged_content for kw in [
        "冲突", "矛盾", "不一致", "差异", "conflict", "450亿", "620亿", "市场规模冲突",
        "数据冲突", "来源不详", "数据来源", "保留", "Gartner"
    ])
    # More specific: agent should prefer draft_a's figure (has Gartner source)
    gartner_preserved = "Gartner" in merged_content or "450亿" in merged_content
    conflict_check_passed = conflict_detected and gartner_preserved
    checks.append({
        "name": "market_size_conflict_handled",
        "passed": conflict_check_passed,
        "detail": (
            f"Market size conflict detected: {conflict_detected}, "
            f"Gartner-sourced figure preserved: {gartner_preserved}. "
            "Draft A (450B/2027, Gartner) should be preferred over Draft B (620B/2028, no source)."
        )
    })

    # ── CHECK 7: All three drafts' contributions mentioned ────────────────────
    # Each draft must have its contribution explained in the report
    draft_refs = {
        "draft_a": any(x in merged_lower for x in ["draft_a", "draft a", "稿a", "稿A"]),
        "draft_b": any(x in merged_lower for x in ["draft_b", "draft b", "稿b", "稿B"]),
        "draft_c": any(x in merged_lower for x in ["draft_c", "draft c", "稿c", "稿C"]),
    }
    all_drafts_mentioned = sum(draft_refs.values())
    contributions_check = all_drafts_mentioned >= 2  # at least 2 out of 3 explicitly named
    checks.append({
        "name": "all_drafts_contributions_mentioned",
        "passed": contributions_check,
        "detail": (
            f"Drafts explicitly referenced in report: {draft_refs}. "
            f"Count: {all_drafts_mentioned}/3. "
            "SKILL.md requires contribution of each draft to be documented."
        )
    })

    # ── CHECK 8: Not a raw concatenation (fusion check) ───────────────────────
    # Raw concatenation would have the original intro paragraphs of B and C 
    # appearing verbatim near each other or the original section headers duplicated
    raw_b_intro = "AI编程助手这两年在企业里越来越普及了。很多公司都开始用，但效果参差不齐。这篇文章想聊聊这个话题"
    raw_c_content = "AI很厉害。\n\n编程助手能帮忙写代码这是大家都知道的事情了。\n\nAI很厉害"
    is_raw_concat_b = raw_b_intro in merged_content
    is_raw_concat_c = "AI很厉害。\n\n编程助手能帮忙写代码这是大家都知道的事情了。" in merged_content

    # The merged article should be substantially longer than draft_a alone but not raw concat
    draft_a_path = workspace_path / "drafts" / "draft_a.md"
    try:
        draft_a_content = draft_a_path.read_text(encoding="utf-8")
        draft_a_len = len(draft_a_content)
    except:
        draft_a_len = 2000  # fallback

    merged_article_section = merged_content
    # Try to separate report from article by finding the 合并报告 section
    if "合并报告" in merged_content:
        parts = merged_content.split("合并报告")
        merged_article_section = parts[0] if len(parts[0]) > len(parts[-1]) else parts[-1]

    not_raw_concat = not (is_raw_concat_b or is_raw_concat_c)
    fusion_check_passed = not_raw_concat
    checks.append({
        "name": "semantic_fusion_not_concatenation",
        "passed": fusion_check_passed,
        "detail": (
            f"Raw concatenation detected: draft_b_verbatim={is_raw_concat_b}, "
            f"draft_c_verbatim={is_raw_concat_c}. "
            "SKILL.md prohibits direct concatenation; requires semantic fusion."
        )
    })

    # ── CHECK 9: Unique insight from Draft B preserved (cognitive load transfer) ─
    # Draft B has unique "认知负荷转移" insight that should be preserved as a highlight
    unique_b_insight = "认知负荷" in merged_content
    checks.append({
        "name": "unique_highlight_from_draft_b_preserved",
        "passed": unique_b_insight,
        "detail": (
            f"Draft B's unique 'cognitive load transfer' (认知负荷转移) insight preserved: {unique_b_insight}. "
            "SKILL.md requires preserving unique highlights from non-base drafts."
        )
    })

    # ── CHECK 10: Article body is substantive (not just a report) ─────────────
    # The merged article itself should contain actual content beyond the report
    has_introduction = any(kw in merged_content for kw in ["引言", "introduction", "## 引", "# 企业", "AI编程助手", "AI coding"])
    has_sections = merged_content.count("##") >= 3
    article_substantive = has_introduction and has_sections
    checks.append({
        "name": "merged_article_body_substantive",
        "passed": article_substantive,
        "detail": (
            f"Article has introduction: {has_introduction}, "
            f"section headers (##): {merged_content.count('##')}. "
            "The output must include a full merged article, not just the report."
        )
    })

    # ── SCORING ───────────────────────────────────────────────────────────────
    check_weights = {
        "output_file_exists": 0.05,
        "merge_report_format": 0.10,
        "merge_report_emoji_format": 0.10,  # proprietary trap
        "base_draft_correctly_identified": 0.15,
        "low_quality_draft_annotated": 0.10,  # proprietary edge case
        "weighted_scoring_formula_applied": 0.10,
        "market_size_conflict_handled": 0.10,
        "all_drafts_contributions_mentioned": 0.08,
        "semantic_fusion_not_concatenation": 0.12,
        "unique_highlight_from_draft_b_preserved": 0.05,
        "merged_article_body_substantive": 0.05,
    }

    total_score = 0.0
    for check in checks:
        weight = check_weights.get(check["name"], 0.0)
        if check["passed"]:
            total_score += weight

    overall_passed = total_score >= 0.60

    return {
        "passed": overall_passed,
        "score": round(total_score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))