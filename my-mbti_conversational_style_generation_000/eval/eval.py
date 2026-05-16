import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── CHECK 1: blend_response.md exists ───────────────────────────────────
    blend_files = list(workspace.rglob("blend_response.md"))
    blend_exists = len(blend_files) > 0
    checks.append({
        "name": "blend_response.md exists",
        "passed": blend_exists,
        "detail": f"Found at {blend_files[0]}" if blend_exists else "File not found anywhere in workspace"
    })
    if blend_exists:
        total_score += 0.05

    # ── CHECK 2: dual_comparison.md exists ──────────────────────────────────
    dual_files = list(workspace.rglob("dual_comparison.md"))
    dual_exists = len(dual_files) > 0
    checks.append({
        "name": "dual_comparison.md exists",
        "passed": dual_exists,
        "detail": f"Found at {dual_files[0]}" if dual_exists else "File not found anywhere in workspace"
    })
    if dual_exists:
        total_score += 0.05

    # ── Read file contents ───────────────────────────────────────────────────
    blend_content = ""
    dual_content = ""

    try:
        if blend_exists:
            blend_content = blend_files[0].read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "blend_response.md readable", "passed": False, "detail": str(e)})

    try:
        if dual_exists:
            dual_content = dual_files[0].read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "dual_comparison.md readable", "passed": False, "detail": str(e)})

    # ── CHECK 3: blend_response.md addresses the blend question ─────────────
    blend_addresses_topic = False
    try:
        keywords = ["新员工", "入职", "第一周", "不知所措", "焦虑", "建议", "支持", "帮助", "onboarding", "new"]
        blend_addresses_topic = any(kw in blend_content for kw in keywords)
        # Also accept if the content is substantial (>100 chars) and seems relevant
        if not blend_addresses_topic and len(blend_content) > 100:
            # Check for general advisory/supportive content
            general_keywords = ["理解", "感受", "步骤", "可以", "先", "再", "帮", "安心", "了解"]
            blend_addresses_topic = sum(1 for kw in general_keywords if kw in blend_content) >= 3
    except Exception as e:
        blend_addresses_topic = False

    checks.append({
        "name": "blend_response.md addresses the onboarding question",
        "passed": blend_addresses_topic,
        "detail": f"Content length: {len(blend_content)} chars. Keywords found: {[kw for kw in ['新员工','入职','建议','支持','第一周','理解','感受','步骤'] if kw in blend_content]}"
    })
    if blend_addresses_topic:
        total_score += 0.10

    # ── CHECK 4: blend_response.md shows ISFJ-primary warmth/care signals ───
    isfj_warmth = False
    try:
        # ISFJ primary: warmth, care, support, checking understanding
        isfj_signals = ["理解", "感受", "照顾", "安心", "支持", "帮助", "关心", "温暖", "放心", "陪伴",
                        "不要担心", "没关系", "正常", "一步一步", "随时", "需要"]
        isfj_count = sum(1 for sig in isfj_signals if sig in blend_content)
        isfj_warmth = isfj_count >= 2
    except Exception as e:
        isfj_warmth = False

    checks.append({
        "name": "blend_response.md shows ISFJ-primary warmth/care (primary style signals)",
        "passed": isfj_warmth,
        "detail": f"ISFJ warmth signals found: {[s for s in ['理解','感受','照顾','安心','支持','帮助','关心','温暖','放心','不要担心','没关系','随时','需要'] if s in blend_content]}"
    })
    if isfj_warmth:
        total_score += 0.15

    # ── CHECK 5: blend_response.md shows ISTJ secondary structure/steps ─────
    istj_structure = False
    try:
        # ISTJ secondary: numbered/ordered steps, explicit sequence, "first...then...", structured advice
        step_patterns = [
            r'第[一二三四五六七八九十\d]+[步个]',
            r'\d+[\.、\)]',
            r'首先|其次|然后|最后|第一步|第二步|Step \d',
            r'一是|二是|三是',
        ]
        step_found = any(re.search(pat, blend_content) for pat in step_patterns)
        # Also accept if there are multiple structured paragraphs
        structure_keywords = ["步骤", "流程", "清单", "顺序", "先…再", "先……再", "先，再"]
        struct_kw_found = any(kw in blend_content for kw in structure_keywords)
        istj_structure = step_found or struct_kw_found
    except Exception as e:
        istj_structure = False

    checks.append({
        "name": "blend_response.md shows ISTJ secondary structured/step-based content",
        "passed": istj_structure,
        "detail": f"Step patterns or structure keywords found in blend content: {istj_structure}"
    })
    if istj_structure:
        total_score += 0.15

    # ── CHECK 6: blend_response.md does NOT self-identify repeatedly as one type ──
    no_self_id = False
    try:
        # Forbidden: repeatedly self-labeling as one MBTI type
        self_id_patterns = [
            r'我是\s*[A-Z]{4}',
            r'作为\s*[A-Z]{4}',
            r'作为一个\s*[A-Z]{4}',
        ]
        self_id_count = sum(len(re.findall(pat, blend_content)) for pat in self_id_patterns)
        no_self_id = self_id_count == 0
    except Exception as e:
        no_self_id = True

    checks.append({
        "name": "blend_response.md does NOT repeatedly self-identify as one MBTI type",
        "passed": no_self_id,
        "detail": f"Self-identification pattern count: {self_id_count if not isinstance(no_self_id, bool) or not no_self_id else 0}"
    })
    if no_self_id:
        total_score += 0.05

    # ── CHECK 7: dual_comparison.md contains BOTH required section headers ──
    has_intj_header = False
    has_enfp_header = False
    try:
        # Must contain "INTJ 版：" or "INTJ版：" style markers
        has_intj_header = bool(re.search(r'INTJ\s*版[：:]', dual_content))
        has_enfp_header = bool(re.search(r'ENFP\s*版[：:]', dual_content))
    except Exception as e:
        pass

    checks.append({
        "name": "dual_comparison.md contains 'INTJ 版：' section header",
        "passed": has_intj_header,
        "detail": f"INTJ 版 header found: {has_intj_header}. Content snippet: {dual_content[:200] if dual_content else 'empty'}"
    })
    if has_intj_header:
        total_score += 0.10

    checks.append({
        "name": "dual_comparison.md contains 'ENFP 版：' section header",
        "passed": has_enfp_header,
        "detail": f"ENFP 版 header found: {has_enfp_header}."
    })
    if has_enfp_header:
        total_score += 0.10

    # ── CHECK 8: dual_comparison.md addresses the tech framework question ───
    dual_on_topic = False
    try:
        topic_keywords = ["框架", "技术", "学习曲线", "引入", "建议", "团队", "framework", "新", "工具"]
        dual_on_topic = any(kw in dual_content for kw in topic_keywords)
        if not dual_on_topic and len(dual_content) > 200:
            general = ["引入", "技术", "学习", "团队", "成本", "好处", "风险", "决策"]
            dual_on_topic = sum(1 for kw in general if kw in dual_content) >= 2
    except Exception as e:
        dual_on_topic = False

    checks.append({
        "name": "dual_comparison.md addresses the tech framework question",
        "passed": dual_on_topic,
        "detail": f"Topic keywords found: {[kw for kw in ['框架','技术','学习曲线','引入','建议','团队'] if kw in dual_content]}"
    })
    if dual_on_topic:
        total_score += 0.05

    # ── CHECK 9: INTJ section shows cold/strategic/structural signals ────────
    intj_signals_present = False
    try:
        # Extract INTJ section
        intj_match = re.search(r'INTJ\s*版[：:](.*?)(?=ENFP\s*版[：:]|$)', dual_content, re.DOTALL)
        if intj_match:
            intj_section = intj_match.group(1)
            intj_style_signals = ["结论", "逻辑", "风险", "系统", "评估", "判断", "学习成本",
                                   "长期", "短期", "效率", "权衡", "策略", "数据", "分析", "建议先"]
            intj_signal_count = sum(1 for sig in intj_style_signals if sig in intj_section)
            intj_signals_present = intj_signal_count >= 1 and len(intj_section.strip()) > 50
        else:
            intj_signals_present = False
    except Exception as e:
        intj_signals_present = False

    checks.append({
        "name": "INTJ section shows strategic/analytical/cold signals",
        "passed": intj_signals_present,
        "detail": f"INTJ style signals in INTJ section: found={intj_signals_present}"
    })
    if intj_signals_present:
        total_score += 0.10

    # ── CHECK 10: ENFP section shows energetic/possibility-focused signals ───
    enfp_signals_present = False
    try:
        # Extract ENFP section
        enfp_match = re.search(r'ENFP\s*版[：:](.*?)$', dual_content, re.DOTALL)
        if enfp_match:
            enfp_section = enfp_match.group(1)
            enfp_style_signals = ["可能", "有趣", "探索", "尝试", "机会", "灵感", "打开", "想象",
                                   "发现", "好奇", "潜力", "也许", "或者", "不妨", "如果"]
            enfp_signal_count = sum(1 for sig in enfp_style_signals if sig in enfp_section)
            enfp_signals_present = enfp_signal_count >= 1 and len(enfp_section.strip()) > 50
        else:
            enfp_signals_present = False
    except Exception as e:
        enfp_signals_present = False

    checks.append({
        "name": "ENFP section shows energetic/possibility-focused signals",
        "passed": enfp_signals_present,
        "detail": f"ENFP style signals in ENFP section: found={enfp_signals_present}"
    })
    if enfp_signals_present:
        total_score += 0.10

    # ── CHECK 11: two sections have meaningfully different tones ─────────────
    sections_differ = False
    try:
        intj_match = re.search(r'INTJ\s*版[：:](.*?)(?=ENFP\s*版[：:]|$)', dual_content, re.DOTALL)
        enfp_match = re.search(r'ENFP\s*版[：:](.*?)$', dual_content, re.DOTALL)
        if intj_match and enfp_match:
            intj_text = intj_match.group(1).strip()
            enfp_text = enfp_match.group(1).strip()
            # Simple check: they are different enough
            if len(intj_text) > 30 and len(enfp_text) > 30:
                # Check overlap ratio — they should not be nearly identical
                intj_words = set(intj_text.replace("，", " ").replace("。", " ").split())
                enfp_words = set(enfp_text.replace("，", " ").replace("。", " ").split())
                if len(intj_words) > 0 and len(enfp_words) > 0:
                    overlap = len(intj_words & enfp_words) / min(len(intj_words), len(enfp_words))
                    sections_differ = overlap < 0.85  # They should differ by at least 15%
                else:
                    sections_differ = False
    except Exception as e:
        sections_differ = False

    checks.append({
        "name": "INTJ and ENFP sections have meaningfully different content (not copy-paste)",
        "passed": sections_differ,
        "detail": f"Sections differ sufficiently: {sections_differ}"
    })
    if sections_differ:
        total_score += 0.10

    # ── CHECK 12: blend content is non-trivial (min length) ──────────────────
    blend_substantial = len(blend_content.strip()) >= 150
    checks.append({
        "name": "blend_response.md has substantial content (>=150 chars)",
        "passed": blend_substantial,
        "detail": f"Blend content length: {len(blend_content.strip())} chars"
    })
    if blend_substantial:
        total_score += 0.05

    # ── CHECK 13: dual content is non-trivial (min length) ───────────────────
    dual_substantial = len(dual_content.strip()) >= 200
    checks.append({
        "name": "dual_comparison.md has substantial content (>=200 chars)",
        "passed": dual_substantial,
        "detail": f"Dual content length: {len(dual_content.strip())} chars"
    })
    if dual_substantial:
        total_score += 0.05

    # Cap score at 1.0
    total_score = min(round(total_score, 3), 1.0)

    passed = (
        blend_exists and
        dual_exists and
        blend_addresses_topic and
        isfj_warmth and
        istj_structure and
        has_intj_header and
        has_enfp_header and
        intj_signals_present and
        enfp_signals_present and
        sections_differ
    )

    return {
        "passed": passed,
        "score": total_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))