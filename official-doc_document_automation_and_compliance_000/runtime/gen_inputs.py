import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── directory skeleton ──────────────────────────────────────────────
dirs = [
    "scripts",
    "drafts",
    "archive/2023/q1",
    "archive/2023/q2",
    "archive/2024/q1",
    "output",
    "config",
    "logs",
    "templates/old",
    "templates/new",
    "review/pending",
    "review/approved",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files (10+) ──────────────────────────────────────────
distractors = {
    "archive/2023/q1/notice_draft_v1.txt": "关于开展节能减排活动的通知草稿（旧版）",
    "archive/2023/q2/meeting_minutes_june.txt": "2023年6月部门例会纪要存档",
    "archive/2024/q1/budget_summary.txt": "2024年第一季度预算汇总报告（内部）",
    "config/doc_config.json": json.dumps({"version": "1.0", "dept": "信息化管理科", "year": 2024}, ensure_ascii=False, indent=2),
    "logs/generation_log_20240301.log": "[2024-03-01] notice generated successfully\n[2024-03-01] format-check passed",
    "logs/generation_log_20240415.log": "[2024-04-15] report generated\n[2024-04-15] tone-check: 3 issues found",
    "templates/old/notice_template_v1.txt": "旧版通知模板（已废弃）\n标题：\n正文：\n落款：",
    "templates/new/report_template_v2.txt": "新版报告模板\n一、基本情况\n二、主要工作\n三、存在问题\n四、下一步打算",
    "review/pending/procurement_idea.txt": "想法：机房服务器太旧了，得换，大概要买5台，不知道要多少钱",
    "review/approved/it_plan_2024.txt": "信息化建设三年规划（已批复）\n第一阶段：基础设施升级\n第二阶段：系统整合\n第三阶段：数据治理",
    "archive/2023/q1/old_request_example.txt": "这是一个很随意的请示，感觉应该买点东西，大家都觉得挺需要的，搞一下吧",
    "config/department_list.txt": "信息化管理科\n行政办公室\n财务科\n人事科\n后勤保障部",
}
for path, content in distractors.items():
    (workspace / path).write_text(content, encoding="utf-8")

# ── THE ACTUAL PROBLEM: a messy, colloquial draft ──────────────────
# This draft is intentionally informal and colloquially phrased
# The agent must: run tone check, run format-check, then generate a proper 请示
messy_draft = """关于购置机房服务器的请示草稿

我觉得咱们机房现在的服务器太老了，已经用了七八年了，感觉随时要坏。
我觉得这事儿挺紧急的，差不多得尽快搞一下升级。
大概要买5台新服务器，估计花个五六十万左右吧，具体多少钱还没算清楚。
我觉得这个方案差不多可以搞一下，希望领导能批一批。
麻烦领导帮忙看看，批了的话我们就去采购了。

信息化管理科
2024年6月
"""
(workspace / "drafts" / "server_procurement_draft.txt").write_text(messy_draft, encoding="utf-8")

# ── The official.sh script (the bespoke tool) ──────────────────────
official_sh = r'''#!/usr/bin/env bash
# scripts/official.sh - 公文生成器 v2.0.0

set -euo pipefail

CMD="${1:-help}"
shift || true

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

YEAR=$(date +%Y)
MONTH=$(date +%m)
DATE_STR=$(date +"%Y年%m月%d日")

# ── header / footer helpers ────────────────────────────────────────
print_header() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "        公文生成器 v2.0.0  |  BytesAgain"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

print_footer() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  生成完成 | Powered by BytesAgain"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# ── notice ─────────────────────────────────────────────────────────
do_notice() {
    TITLE="${1:-通知标题}"
    CONTENT="${2:-通知内容}"
    print_header
    echo ""
    echo -e "${CYAN}【文种】通知${NC}"
    echo ""
    echo "                    ${TITLE}"
    echo ""
    echo "各相关单位："
    echo ""
    echo "  ${CONTENT}"
    echo ""
    echo "  特此通知。"
    echo ""
    echo "                              （发文机关印章）"
    echo "                              ${DATE_STR}"
    echo ""
    print_footer
}

# ── request (请示) ─────────────────────────────────────────────────
do_request() {
    SUBJECT="${1:-请示事由}"
    CONTENT="${2:-请示正文}"
    print_header
    echo ""
    echo -e "${CYAN}【文种】请示${NC}"
    echo ""
    echo "                    关于${SUBJECT}的请示"
    echo ""
    echo "主管领导："
    echo ""
    echo "  ${CONTENT}"
    echo ""
    echo "  以上请示，妥否，请批示。"
    echo ""
    echo "                              （发文机关印章）"
    echo "                              ${DATE_STR}"
    echo ""
    print_footer
}

# ── report ─────────────────────────────────────────────────────────
do_report() {
    TOPIC="${1:-报告主题}"
    CONTENT="${2:-报告正文}"
    print_header
    echo ""
    echo -e "${CYAN}【文种】报告${NC}"
    echo ""
    echo "                    关于${TOPIC}的报告"
    echo ""
    echo "主管领导："
    echo ""
    echo "  现将有关情况报告如下："
    echo ""
    echo "  ${CONTENT}"
    echo ""
    echo "  特此报告。"
    echo ""
    echo "                              （发文机关印章）"
    echo "                              ${DATE_STR}"
    echo ""
    print_footer
}

# ── reply (批复) ───────────────────────────────────────────────────
do_reply() {
    ORIGINAL="${1:-原请示内容}"
    REPLY="${2:-批复内容}"
    print_header
    echo ""
    echo -e "${CYAN}【文种】批复${NC}"
    echo ""
    echo "                    关于${ORIGINAL}的批复"
    echo ""
    echo "来文单位："
    echo ""
    echo "  你单位"关于${ORIGINAL}"的请示收悉。经研究，批复如下："
    echo ""
    echo "  ${REPLY}"
    echo ""
    echo "  此复。"
    echo ""
    echo "                              （批复机关印章）"
    echo "                              ${DATE_STR}"
    echo ""
    print_footer
}

# ── format-check ───────────────────────────────────────────────────
do_format_check() {
    TEXT="${1:-}"
    print_header
    echo ""
    echo -e "${YELLOW}【格式检查报告】${NC}"
    echo ""

    ISSUES=0

    # Check for title
    if echo "$TEXT" | grep -qE "^关于.*的(通知|请示|报告|批复|纪要|总结)"; then
        echo -e "  ${GREEN}✓${NC} 标题格式：符合规范（含"关于…的[文种]"结构）"
    else
        echo -e "  ${RED}✗${NC} 标题格式：不规范，标题应包含"关于…的[文种]"结构"
        ISSUES=$((ISSUES+1))
    fi

    # Check for date
    if echo "$TEXT" | grep -qE "[0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日|[0-9]{4}年[0-9]{1,2}月"; then
        echo -e "  ${GREEN}✓${NC} 日期格式：包含日期信息"
    else
        echo -e "  ${RED}✗${NC} 日期格式：缺少规范日期（应为XXXX年XX月XX日）"
        ISSUES=$((ISSUES+1))
    fi

    # Check for issuing unit
    if echo "$TEXT" | grep -qE "(科|部|处|局|委|办|室|中心|司|厅|院|所)$"; then
        echo -e "  ${GREEN}✓${NC} 落款单位：检测到发文单位"
    else
        echo -e "  ${RED}✗${NC} 落款单位：未检测到规范发文单位名称"
        ISSUES=$((ISSUES+1))
    fi

    # Check for colloquial phrases that indicate informal structure
    COLLOQUIAL_COUNT=0
    for phrase in "我觉得" "差不多" "搞一下" "麻烦" "大概" "感觉" "挺" "咱们" "事儿" "批一批" "看看"; do
        if echo "$TEXT" | grep -q "$phrase"; then
            COLLOQUIAL_COUNT=$((COLLOQUIAL_COUNT+1))
        fi
    done

    if [ "$COLLOQUIAL_COUNT" -gt 0 ]; then
        echo -e "  ${RED}✗${NC} 语体规范：发现 ${COLLOQUIAL_COUNT} 处口语化表达，不符合公文规范"
        ISSUES=$((ISSUES+1))
    else
        echo -e "  ${GREEN}✓${NC} 语体规范：未发现明显口语化表达"
    fi

    # Check length
    CHAR_COUNT=${#TEXT}
    if [ "$CHAR_COUNT" -lt 20 ]; then
        echo -e "  ${RED}✗${NC} 内容完整性：正文内容过短（${CHAR_COUNT}字），可能不完整"
        ISSUES=$((ISSUES+1))
    else
        echo -e "  ${GREEN}✓${NC} 内容完整性：正文长度（${CHAR_COUNT}字）基本符合要求"
    fi

    echo ""
    if [ "$ISSUES" -eq 0 ]; then
        echo -e "  ${GREEN}格式检查结论：通过（无问题）${NC}"
    else
        echo -e "  ${RED}格式检查结论：不通过（发现 ${ISSUES} 项问题）${NC}"
    fi
    echo ""
    print_footer
    
    # Return exit code based on issues
    if [ "$ISSUES" -gt 0 ]; then
        return 1
    fi
    return 0
}

# ── tone check ─────────────────────────────────────────────────────
do_tone() {
    TEXT="${1:-}"
    print_header
    echo ""
    echo -e "${YELLOW}【语气/用语检查报告】${NC}"
    echo ""

    declare -A TONE_ISSUES
    TONE_ISSUES["我觉得"]="口语化，建议改为"经研究"或"经分析""
    TONE_ISSUES["感觉"]="口语化，建议改为"据评估"或"经核查""
    TONE_ISSUES["差不多"]="模糊表达，建议改为具体数字或"约""
    TONE_ISSUES["搞一下"]="口语化动词，建议改为"开展"、"实施"或"推进""
    TONE_ISSUES["麻烦"]="不庄重，建议改为"敬请"或删除"
    TONE_ISSUES["大概"]="模糊表达，建议改为"约"或提供精确数据"
    TONE_ISSUES["挺"]="口语化程度副词，建议删除或改为"较""
    TONE_ISSUES["咱们"]="口语化代词，建议改为"我单位"或"本科室""
    TONE_ISSUES["事儿"]="儿化音口语，建议改为"事项""
    TONE_ISSUES["批一批"]="口语化重叠动词，建议改为"予以批准"或"请批示""
    TONE_ISSUES["看看"]="口语化重叠动词，建议改为"审阅"或"审核""
    TONE_ISSUES["尽快搞"]="口语化，建议改为"尽快推进"或"加快实施""
    TONE_ISSUES["太老了"]="口语化，建议改为"已老化"或"已超过使用年限""

    FOUND=0
    for phrase in "${!TONE_ISSUES[@]}"; do
        if echo "$TEXT" | grep -q "$phrase"; then
            echo -e "  ${RED}[问题]${NC} \"${phrase}\" → ${TONE_ISSUES[$phrase]}"
            FOUND=$((FOUND+1))
        fi
    done

    if [ "$FOUND" -eq 0 ]; then
        echo -e "  ${GREEN}✓ 未发现明显口语化或不规范表达，用语基本符合公文规范。${NC}"
    else
        echo ""
        echo -e "  ${YELLOW}语气检查结论：发现 ${FOUND} 处不规范用语，建议修改后再行发文。${NC}"
    fi
    echo ""
    print_footer
}

# ── template ───────────────────────────────────────────────────────
do_template() {
    TYPE="${1:-all}"
    print_header
    echo ""
    echo -e "${BLUE}【模板库】${NC}"
    echo ""

    show_notice_template() {
        echo "━━━ 通知模板 ━━━"
        echo "标题：关于[事项]的通知"
        echo "主送：各相关单位："
        echo "正文：[通知缘由]。现就[具体事项]通知如下："
        echo "      一、[事项一]"
        echo "      二、[事项二]"
        echo "      特此通知。"
        echo "落款：[发文机关]  [XXXX年XX月XX日]"
    }

    show_request_template() {
        echo "━━━ 请示模板 ━━━"
        echo "标题：关于[请示事项]的请示"
        echo "主送：[上级机关]："
        echo "正文：[请示缘由及必要性]。"
        echo "      [具体请求内容及依据]。"
        echo "      以上请示，妥否，请批示。"
        echo "落款：[发文机关]  [XXXX年XX月XX日]"
    }

    show_report_template() {
        echo "━━━ 报告模板 ━━━"
        echo "标题：关于[报告主题]的报告"
        echo "主送：[上级机关]："
        echo "正文：现将[主题]有关情况报告如下："
        echo "      一、基本情况"
        echo "      二、主要做法"
        echo "      三、存在问题"
        echo "      四、下一步打算"
        echo "      特此报告。"
        echo "落款：[发文机关]  [XXXX年XX月XX日]"
    }

    show_reply_template() {
        echo "━━━ 批复模板 ━━━"
        echo "标题：关于[原请示事项]的批复"
        echo "主送：[来文机关]："
        echo "正文：你单位"关于[原请示事项]"的请示收悉。经研究，批复如下："
        echo "      [批复意见]"
        echo "      此复。"
        echo "落款：[批复机关]  [XXXX年XX月XX日]"
    }

    show_minutes_template() {
        echo "━━━ 会议纪要模板 ━━━"
        echo "标题：[会议名称]纪要"
        echo "会议时间：XXXX年XX月XX日"
        echo "会议地点：[地点]"
        echo "参会人员：[姓名职务列表]"
        echo "主持人：[姓名]"
        echo "正文：会议听取了[内容]，经讨论，形成如下纪要："
        echo "      一、[议题一结论]"
        echo "      二、[议题二结论]"
        echo "落款：[记录单位]  [XXXX年XX月XX日]"
    }

    show_summary_template() {
        echo "━━━ 工作总结模板 ━━━"
        echo "标题：[单位/部门][时间段]工作总结"
        echo "正文：[时间段]，[单位]在[上级单位]领导下，圆满完成了各项工作任务。"
        echo "      现将主要工作总结如下："
        echo "      一、主要工作完成情况"
        echo "      二、存在的主要问题"
        echo "      三、下一阶段工作计划"
        echo "落款：[发文单位]  [XXXX年XX月XX日]"
    }

    case "$TYPE" in
        "all")
            show_notice_template; echo ""
            show_request_template; echo ""
            show_report_template; echo ""
            show_reply_template; echo ""
            show_minutes_template; echo ""
            show_summary_template
            ;;
        "通知") show_notice_template ;;
        "请示") show_request_template ;;
        "报告") show_report_template ;;
        "批复") show_reply_template ;;
        "会议纪要") show_minutes_template ;;
        "工作总结") show_summary_template ;;
        *) echo "未知模板类型: ${TYPE}"; echo "可用类型: 通知 | 报告 | 请示 | 批复 | 会议纪要 | 工作总结 | all" ;;
    esac
    echo ""
    print_footer
}

# ── help ───────────────────────────────────────────────────────────
do_help() {
    print_header
    echo ""
    echo "用法："
    echo "  scripts/official.sh notice \"标题\" \"内容\"          通知"
    echo "  scripts/official.sh request \"事由\" \"请示\"          请示"
    echo "  scripts/official.sh report \"主题\" \"内容\"           报告"
    echo "  scripts/official.sh reply \"原请示\" \"批复\"          批复"
    echo "  scripts/official.sh format-check \"文本\"             格式检查"
    echo "  scripts/official.sh tone \"文本\"                     语气/用语检查"
    echo "  scripts/official.sh template \"类型\"                 模板库"
    echo "  scripts/official.sh help                             帮助"
    echo ""
    echo "模板类型: 通知 | 报告 | 请示 | 批复 | 会议纪要 | 工作总结 | all"
    echo ""
    print_footer
}

# ── dispatch ───────────────────────────────────────────────────────
case "$CMD" in
    notice)        do_notice "$@" ;;
    request)       do_request "$@" ;;
    report)        do_report "$@" ;;
    reply)         do_reply "$@" ;;
    format-check)  do_format_check "$@" ;;
    tone)          do_tone "$@" ;;
    template)      do_template "$@" ;;
    help|--help|-h) do_help ;;
    *) echo "未知命令: ${CMD}"; do_help; exit 1 ;;
esac
'''
(workspace / "scripts" / "official.sh").write_text(official_sh, encoding="utf-8")

print("Workspace generated successfully.")
print(f"Draft file: {workspace / 'drafts' / 'server_procurement_draft.txt'}")
print(f"Script: {workspace / 'scripts' / 'official.sh'}")