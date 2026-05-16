import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def find_file(workspace, filename):
    matches = list(Path(workspace).rglob(filename))
    if not matches:
        return None
    return matches[0]

def score_checks(checks):
    if not checks:
        return 0.0
    return round(sum(1 for c in checks if c["passed"]) / len(checks), 3)

def eval_diagnosis_roadmap(content: str):
    checks = []

    # ── Check 1: Three-Layer Nine-Stage model presence (all 3 layers named) ──
    layers = ["共创生成层", "验证转译层", "放大闭环层"]
    found_layers = [l for l in layers if l in content]
    checks.append(check(
        "三层模型：三层名称均出现",
        len(found_layers) == 3,
        f"找到层名: {found_layers}"
    ))

    # ── Check 2: Stage identification (current stage located) ──
    stage_keywords = ["成果识别", "共创组队", "权责建模", "切入点市场界定",
                      "用户画像", "价值主张", "双十验证", "MVTP", "最小可行转化产品",
                      "三重闭环", "平台化复制"]
    found_stages = [s for s in stage_keywords if s in content]
    checks.append(check(
        "阶段定位：包含至少3个具体阶段名",
        len(found_stages) >= 3,
        f"找到阶段关键词: {found_stages}"
    ))

    # ── Check 3: "最大断点" mentioned (bespoke Step 3 requirement) ──
    has_breakpoint = "最大断点" in content or "断点" in content
    checks.append(check(
        "阶段定位：包含最大断点分析",
        has_breakpoint,
        "搜索'最大断点'或'断点'"
    ))

    # ── Check 4: 五维诊断 — all 5 dimensions present ──
    five_dims = ["技术可转化性", "共创组织成熟度", "价值转译清晰度", "市场验证充分度", "生态与制度支撑度"]
    found_dims = [d for d in five_dims if d in content]
    checks.append(check(
        "五维诊断：5个维度全部出现",
        len(found_dims) == 5,
        f"找到维度: {found_dims}"
    ))

    # ── Check 5: Four core variables mentioned ──
    core_vars = ["共创强度", "转译能力", "验证质量", "生态支撑"]
    found_vars = [v for v in core_vars if v in content]
    checks.append(check(
        "四个核心变量：至少出现3个",
        len(found_vars) >= 3,
        f"找到变量: {found_vars}"
    ))

    # ── Check 6: MVTP mentioned (not just MVP) ──
    has_mvtp = "MVTP" in content or "最小可行转化产品" in content
    checks.append(check(
        "路线图：包含MVTP（最小可行转化产品）概念",
        has_mvtp,
        "搜索'MVTP'或'最小可行转化产品'"
    ))

    # ── Check 7: 双十验证 present ──
    has_shuangshi = "双十验证" in content
    checks.append(check(
        "路线图：包含双十验证",
        has_shuangshi,
        "搜索'双十验证'"
    ))

    # ── Check 8: 权责建模 addressed (team authority issue is a key input) ──
    has_quanze = "权责建模" in content or "权责" in content
    checks.append(check(
        "诊断：涉及权责建模/权责划分问题",
        has_quanze,
        "搜索'权责建模'或'权责'"
    ))

    # ── Check 9: 上一阶段完成情况 or 下一阶段门槛 mentioned ──
    has_gate = any(kw in content for kw in ["上一阶段", "下一阶段", "关键门槛", "门槛"])
    checks.append(check(
        "阶段定位：包含阶段门槛或上/下阶段判断",
        has_gate,
        "搜索'上一阶段'/'下一阶段'/'关键门槛'"
    ))

    # ── Check 10: Actionable recommendations not just generic text ──
    action_indicators = ["行动", "建议", "优先", "路线图", "步骤", "措施"]
    found_actions = [a for a in action_indicators if a in content]
    checks.append(check(
        "交付件：包含具体行动建议或路线图内容",
        len(found_actions) >= 3,
        f"找到行动关键词: {found_actions}"
    ))

    return checks

def eval_pitch_reconstruction(content: str):
    checks = []

    # ── Check 11: This is explicitly a pitch/路演 output type ──
    pitch_indicators = ["路演", "比赛", "挑战杯", "路演框架", "核心论点", "叙事"]
    found = [p for p in pitch_indicators if p in content]
    checks.append(check(
        "路演文件：包含路演/比赛相关关键词",
        len(found) >= 2,
        f"找到路演关键词: {found}"
    ))

    # ── Check 12: Value proposition translated for customer (转译能力) ──
    has_value_prop = any(kw in content for kw in ["价值主张", "客户价值", "转译", "价值语言"])
    checks.append(check(
        "路演：包含价值主张或价值转译内容",
        has_value_prop,
        "搜索'价值主张'/'客户价值'/'转译'"
    ))

    # ── Check 13: Market segmentation addressed (not just 'all autonomous vehicles') ──
    segment_kw = ["细分", "切入点", "市场界定", "目标市场", "细分市场", "AGV", "工业", "仓储", "港口"]
    found_seg = [s for s in segment_kw if s in content]
    checks.append(check(
        "路演：涉及市场细分或切入点选择",
        len(found_seg) >= 2,
        f"找到细分关键词: {found_seg}"
    ))

    # ── Check 14: Structured output (has section headers indicating structural thinking) ──
    header_count = len(re.findall(r'^#{1,4}\s+\S+', content, re.MULTILINE))
    checks.append(check(
        "路演：有结构性小节标题（Markdown headers ≥ 3）",
        header_count >= 3,
        f"找到Markdown标题数: {header_count}"
    ))

    # ── Check 15: Three-layer model referenced or stage positioning done in pitch context ──
    has_framework_ref = any(kw in content for kw in ["共创", "验证", "转化", "师生", "科研成果"])
    checks.append(check(
        "路演：体现科研成果转化/师生共创视角",
        has_framework_ref,
        "搜索'共创'/'验证'/'转化'/'师生'"
    ))

    return checks

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    all_checks = []

    # ── Find diagnosis_roadmap.md ──
    dm_file = find_file(workspace, "diagnosis_roadmap.md")
    if dm_file is None:
        all_checks.append(check("diagnosis_roadmap.md 文件存在", False, "文件未找到"))
    else:
        all_checks.append(check("diagnosis_roadmap.md 文件存在", True, str(dm_file)))
        try:
            dm_content = dm_file.read_text(encoding="utf-8")
            if len(dm_content.strip()) < 200:
                all_checks.append(check("diagnosis_roadmap.md 内容非空", False,
                                        f"内容过短: {len(dm_content)} 字符"))
            else:
                all_checks.append(check("diagnosis_roadmap.md 内容非空", True,
                                        f"内容长度: {len(dm_content)} 字符"))
                all_checks.extend(eval_diagnosis_roadmap(dm_content))
        except Exception as e:
            all_checks.append(check("diagnosis_roadmap.md 读取成功", False, str(e)))

    # ── Find pitch_reconstruction.md ──
    pr_file = find_file(workspace, "pitch_reconstruction.md")
    if pr_file is None:
        all_checks.append(check("pitch_reconstruction.md 文件存在", False, "文件未找到"))
    else:
        all_checks.append(check("pitch_reconstruction.md 文件存在", True, str(pr_file)))
        try:
            pr_content = pr_file.read_text(encoding="utf-8")
            if len(pr_content.strip()) < 100:
                all_checks.append(check("pitch_reconstruction.md 内容非空", False,
                                        f"内容过短: {len(pr_content)} 字符"))
            else:
                all_checks.append(check("pitch_reconstruction.md 内容非空", True,
                                        f"内容长度: {len(pr_content)} 字符"))
                all_checks.extend(eval_pitch_reconstruction(pr_content))
        except Exception as e:
            all_checks.append(check("pitch_reconstruction.md 读取成功", False, str(e)))

    score = score_checks(all_checks)
    passed = score >= 0.70 and all(
        c["passed"] for c in all_checks
        if c["name"] in [
            "diagnosis_roadmap.md 文件存在",
            "pitch_reconstruction.md 文件存在",
            "三层模型：三层名称均出现",
            "五维诊断：5个维度全部出现",
        ]
    )

    result = {
        "passed": passed,
        "score": score,
        "checks": all_checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()