import sys
import json
import re
from pathlib import Path

def check_file(workspace: str):
    checks = []
    
    # ── 1. Find the two output files ────────────────────────────────────────
    ws = Path(workspace)
    
    luxun_candidates = list(ws.rglob("luxun_rewrite.md")) + list(ws.rglob("鲁迅风改写.md")) + list(ws.rglob("rewrite_luxun.md"))
    muxin_candidates = list(ws.rglob("muxin_rewrite.md")) + list(ws.rglob("木心风改写.md")) + list(ws.rglob("rewrite_muxin.md"))

    # Also try common naming variants
    all_md = list(ws.rglob("*.md"))
    # Filter out known distractor md files
    distractor_names = {"writing-styles.md", "ai_article_draft.md", "culture_column_draft.md"}
    candidate_md = [f for f in all_md if f.name not in distractor_names]

    luxun_file = None
    muxin_file = None

    # Try strict candidates first
    if luxun_candidates:
        luxun_file = luxun_candidates[0]
    if muxin_candidates:
        muxin_file = muxin_candidates[0]

    # If not found, scan all candidate md files for content signals
    if luxun_file is None or muxin_file is None:
        for f in candidate_md:
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
                if luxun_file is None and ("鲁迅" in text or "luxun" in f.name.lower()):
                    luxun_file = f
                if muxin_file is None and ("木心" in text or "muxin" in f.name.lower()):
                    muxin_file = f
            except Exception:
                pass

    # ── 2. Check 鲁迅 file existence ─────────────────────────────────────────
    if luxun_file is None:
        checks.append({"name": "鲁迅风文件存在", "passed": False, "detail": "未找到鲁迅风改写文件（期望 luxun_rewrite.md 或含鲁迅的md文件）"})
        luxun_text = ""
    else:
        checks.append({"name": "鲁迅风文件存在", "passed": True, "detail": f"找到文件：{luxun_file}"})
        try:
            luxun_text = luxun_file.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            checks.append({"name": "鲁迅风文件可读", "passed": False, "detail": str(e)})
            luxun_text = ""

    # ── 3. Check 木心 file existence ─────────────────────────────────────────
    if muxin_file is None:
        checks.append({"name": "木心风文件存在", "passed": False, "detail": "未找到木心风改写文件（期望 muxin_rewrite.md 或含木心的md文件）"})
        muxin_text = ""
    else:
        checks.append({"name": "木心风文件存在", "passed": True, "detail": f"找到文件：{muxin_file}"})
        try:
            muxin_text = muxin_file.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            checks.append({"name": "木心风文件可读", "passed": False, "detail": str(e)})
            muxin_text = ""

    # ── Helper: check section structure ──────────────────────────────────────
    required_sections = ["## 原文", "## 改写风格", "## 改写后", "## 主要变化"]

    def check_output_format(text: str, style_name: str) -> list:
        results = []
        for section in required_sections:
            present = section in text
            results.append({
                "name": f"{style_name} 包含章节'{section}'",
                "passed": present,
                "detail": f"在文本中{'找到' if present else '未找到'}章节标题 '{section}'"
            })

        # Check 主要变化 has at least 3 bullet points
        if "## 主要变化" in text:
            after_changes = text.split("## 主要变化")[-1]
            bullet_count = len(re.findall(r'^\s*[-\*•]\s+.+', after_changes, re.MULTILINE))
            has_enough_bullets = bullet_count >= 3
            results.append({
                "name": f"{style_name} 主要变化至少3条",
                "passed": has_enough_bullets,
                "detail": f"检测到 {bullet_count} 条改动说明，期望 >= 3"
            })
        else:
            results.append({
                "name": f"{style_name} 主要变化至少3条",
                "passed": False,
                "detail": "未找到'## 主要变化'章节，无法检查条目数"
            })
        return results

    # ── 4. Check format of 鲁迅 output ───────────────────────────────────────
    if luxun_text:
        checks.extend(check_output_format(luxun_text, "鲁迅风"))
    else:
        checks.append({"name": "鲁迅风 格式检查跳过", "passed": False, "detail": "文件内容为空或不可读"})

    # ── 5. Check format of 木心 output ───────────────────────────────────────
    if muxin_text:
        checks.extend(check_output_format(muxin_text, "木心风"))
    else:
        checks.append({"name": "木心风 格式检查跳过", "passed": False, "detail": "文件内容为空或不可读"})

    # ── 6. 鲁迅风 style-specific avoidance rules ──────────────────────────────
    if luxun_text and "## 改写后" in luxun_text:
        rewritten_lu = luxun_text.split("## 改写后")[-1]
        # Remove section after 主要变化 to only check the rewrite body
        if "## 主要变化" in rewritten_lu:
            rewritten_lu = rewritten_lu.split("## 主要变化")[0]

        # Rule: No exclamation marks in rewrite body
        has_exclamation = bool(re.search(r'[！!]', rewritten_lu))
        checks.append({
            "name": "鲁迅风 无感叹号（避坑规则）",
            "passed": not has_exclamation,
            "detail": "改写后内容" + ("含有感叹号，违反鲁迅风避坑规则" if has_exclamation else "未使用感叹号，符合规则")
        })

        # Rule: No direct opinion statements like "我认为" in rewrite body
        has_direct_opinion = bool(re.search(r'我认为|我觉得|大家觉得|我认为', rewritten_lu))
        checks.append({
            "name": "鲁迅风 无直接观点陈述（避坑规则）",
            "passed": not has_direct_opinion,
            "detail": "改写后内容" + ("含有'我认为/我觉得'等直接观点表述，违反避坑规则" if has_direct_opinion else "未出现直接主观陈述，符合规则")
        })

        # Rule: should contain scene/白描 signals (short sentences, no long reasoning paragraphs)
        sentences = [s.strip() for s in re.split(r'[。？]', rewritten_lu) if s.strip()]
        if sentences:
            avg_len = sum(len(s) for s in sentences) / len(sentences)
            is_short_sentence = avg_len < 25
            checks.append({
                "name": "鲁迅风 短句白描特征",
                "passed": is_short_sentence,
                "detail": f"句子平均长度 {avg_len:.1f} 字（期望 < 25，鲁迅风短句特征）"
            })
        else:
            checks.append({"name": "鲁迅风 短句白描特征", "passed": False, "detail": "改写后内容无可分析句子"})

    # ── 7. 木心风 style-specific avoidance rules ──────────────────────────────
    if muxin_text and "## 改写后" in muxin_text:
        rewritten_mu = muxin_text.split("## 改写后")[-1]
        if "## 主要变化" in rewritten_mu:
            rewritten_mu = rewritten_mu.split("## 主要变化")[0]

        # Rule: No exclamation interjections 啊/呀 in rewrite body
        has_exclamation_words = bool(re.search(r'[啊呀哦哎]', rewritten_mu))
        checks.append({
            "name": "木心风 无'啊/呀'感叹词（避坑规则）",
            "passed": not has_exclamation_words,
            "detail": "改写后内容" + ("含有'啊'/'呀'等感叹词，违反木心风避坑规则" if has_exclamation_words else "未使用感叹词，符合规则")
        })

        # Rule: No direct emotion explanations like "他很难过"
        has_emotion_explain = bool(re.search(r'很(难过|孤独|痛苦|绝望|悲伤|高兴|快乐)', rewritten_mu))
        checks.append({
            "name": "木心风 无直接情绪解释（避坑规则）",
            "passed": not has_emotion_explain,
            "detail": "改写后内容" + ("含有直接情绪描述如'很难过'，违反木心风避坑规则" if has_emotion_explain else "未直接解释情绪，符合规则")
        })

        # Rule: Should be short (no more than ~200 chars in rewrite body)
        char_count = len(rewritten_mu.replace('\n', '').replace(' ', ''))
        is_concise = char_count <= 300
        checks.append({
            "name": "木心风 内容简短（避坑规则）",
            "passed": is_concise,
            "detail": f"改写后内容约 {char_count} 字（期望 <= 300，木心风往往短）"
        })

    # ── 8. Source material preservation check ────────────────────────────────
    source_keywords = ["房", "年轻人", "城市", "买房"]
    for style_name, text in [("鲁迅风", luxun_text), ("木心风", muxin_text)]:
        if text:
            found = sum(1 for kw in source_keywords if kw in text)
            checks.append({
                "name": f"{style_name} 保留核心信息",
                "passed": found >= 2,
                "detail": f"在改写内容中检测到 {found}/{len(source_keywords)} 个核心关键词（房/年轻人/城市/买房）"
            })

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 3) if total_checks > 0 else 0.0
    overall_passed = score >= 0.75

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = check_file(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))