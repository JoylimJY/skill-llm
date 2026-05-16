#!/usr/bin/env python3
import sys
import json
import re
from pathlib import Path

def load_note(workspace: str):
    """Find the meeting note file created by the agent."""
    ws = Path(workspace)
    # Search for markdown files that look like meeting notes (not distractor files)
    candidates = []
    exclude_paths = {
        "references/meeting_note_output_template.md",
        "references/deep_learning_skill.md",
        "templates/weekly_report_template.md",
        "02_项目/KYC模块/需求草稿_v0.2.md",
        "02_项目/KYC模块/技术选型备忘.md",
    }
    for f in ws.rglob("*.md"):
        rel = str(f.relative_to(ws))
        if rel in exclude_paths:
            continue
        try:
            content = f.read_text(encoding="utf-8")
            # Must contain KYC-related content and meeting-note signals
            if ("KYC" in content or "kyc" in content.lower()) and len(content) > 800:
                candidates.append((f, content))
        except Exception:
            pass
    if not candidates:
        return None, None, None
    # Pick the largest file as the primary candidate
    candidates.sort(key=lambda x: len(x[1]), reverse=True)
    return candidates[0][0], candidates[0][1], candidates

def run_checks(workspace: str):
    checks = []

    note_path, content, all_candidates = load_note(workspace)

    # ── Check 0: File exists ──────────────────────────────────────────────
    if content is None:
        checks.append({"name": "meeting_note_file_exists", "passed": False,
                        "detail": "No qualifying meeting note markdown file found in workspace."})
        return checks
    checks.append({"name": "meeting_note_file_exists", "passed": True,
                    "detail": f"Found note at: {note_path}"})

    # ── Check 1: Basic info completeness (time, attendees, topic) ─────────
    has_date = bool(re.search(r'2025.{0,5}6.{0,5}5|六月|6月5', content))
    # Attendee names
    attendees = ["赵磊", "林晓薇", "陈国强", "方怡"]
    has_attendees = all(name in content for name in attendees)
    has_topic = "KYC" in content
    passed = has_date and has_attendees and has_topic
    checks.append({"name": "basic_info_completeness",
                   "passed": passed,
                   "detail": f"date={has_date}, all_attendees={has_attendees}, topic_KYC={has_topic}"})

    # ── Check 2: Decision status markers ✅/⏳/❓ ──────────────────────────
    has_confirmed = "✅" in content
    has_pending = "⏳" in content
    has_unclear = "❓" in content
    # At least two of the three status markers should appear (L2 meeting has mixed statuses)
    marker_count = sum([has_confirmed, has_pending, has_unclear])
    passed = marker_count >= 2
    checks.append({"name": "decision_status_markers",
                   "passed": passed,
                   "detail": f"✅={has_confirmed}, ⏳={has_pending}, ❓={has_unclear} (need ≥2)"})

    # ── Check 3: Decision trajectory (提出→争论→收敛 pattern) ────────────
    trajectory_keywords = ["提出", "争论", "收敛", "搁置", "讨论过程", "决策轨迹"]
    trajectory_hits = sum(1 for kw in trajectory_keywords if kw in content)
    passed = trajectory_hits >= 2
    checks.append({"name": "decision_trajectory",
                   "passed": passed,
                   "detail": f"trajectory keywords found: {trajectory_hits}/6 ({[kw for kw in trajectory_keywords if kw in content]})"})

    # ── Check 4: Consensus & Non-consensus with speaker attribution ───────
    # Non-consensus must mention at least two different speakers with their views
    has_consensus = bool(re.search(r'共识|consensus', content, re.IGNORECASE))
    has_nonconsensus = bool(re.search(r'非共识|分歧|不同意见', content))
    # Check speaker-attributed positions (speaker name + view)
    speaker_views = sum(1 for name in ["赵磊", "林晓薇", "陈国强"] if name in content and
                        re.search(name + r'.{0,100}(认为|主张|反对|建议|表示|指出|担心)', content))
    passed = has_consensus and has_nonconsensus and speaker_views >= 2
    checks.append({"name": "consensus_and_nonconsensus_with_attribution",
                   "passed": passed,
                   "detail": f"consensus={has_consensus}, nonconsensus={has_nonconsensus}, speaker_attributed_views={speaker_views}"})

    # ── Check 5: Hidden/unstated content with explicit basis ─────────────
    hidden_section = bool(re.search(r'隐.{0,10}(内容|假设|未明说|推测)|房间里的大象|没说什么', content))
    has_basis = bool(re.search(r'推测依据|依据|原话|语气|反复|回避', content))
    passed = hidden_section and has_basis
    checks.append({"name": "hidden_content_with_basis",
                   "passed": passed,
                   "detail": f"hidden_section_present={hidden_section}, explicit_basis_provided={has_basis}"})

    # ── Check 6: Three atom types (决策原子/洞察原子/假设风险原子) ──────────
    has_decision_atom = bool(re.search(r'决策原子', content))
    has_insight_atom = bool(re.search(r'洞察原子', content))
    has_risk_atom = bool(re.search(r'假设.{0,5}风险.{0,5}原子|风险原子', content))
    passed = has_decision_atom and has_insight_atom and has_risk_atom
    checks.append({"name": "three_atom_types",
                   "passed": passed,
                   "detail": f"决策原子={has_decision_atom}, 洞察原子={has_insight_atom}, 假设/风险原子={has_risk_atom}"})

    # ── Check 7: Priority-coded action items (🔴🟡🟢) ─────────────────────
    has_red = "🔴" in content
    has_yellow = "🟡" in content
    has_green = "🟢" in content
    priority_count = sum([has_red, has_yellow, has_green])
    passed = priority_count >= 2
    checks.append({"name": "priority_coded_action_items",
                   "passed": passed,
                   "detail": f"🔴={has_red}, 🟡={has_yellow}, 🟢={has_green} (need ≥2 types)"})

    # ── Check 8: Action item quality (verb-start, measurable, owner, deadline) ─
    # Check for action items with responsible persons (方怡/陈国强 were assigned tasks)
    has_fangyi_task = bool(re.search(r'方怡.{0,50}(报告|评估|下周|周内)', content) or
                           re.search(r'(报告|评估).{0,50}方怡', content))
    has_chen_task = bool(re.search(r'陈国强.{0,80}(checklist|清单|两周|尽职调查)|尽职调查.{0,80}陈国强', content, re.IGNORECASE))
    # Check for TBD usage for missing info
    has_tbd = "TBD" in content or "tbd" in content.lower()
    # Check for success criteria / measurable indicators
    has_measurable = bool(re.search(r'验收|成功标准|可衡量|完成标准|交付物', content))
    passed = has_fangyi_task and has_chen_task and has_measurable
    checks.append({"name": "action_item_quality",
                   "passed": passed,
                   "detail": f"fangyi_task={has_fangyi_task}, chen_task={has_chen_task}, tbd_used={has_tbd}, measurable={has_measurable}"})

    # ── Check 9: TBD for missing information ─────────────────────────────
    # Q3 timeline was explicitly NOT confirmed; should be TBD
    q3_tbd = bool(re.search(r'Q3.{0,30}TBD|TBD.{0,30}Q3|待确认|待评估', content))
    passed = has_tbd or q3_tbd
    checks.append({"name": "tbd_for_missing_info",
                   "passed": passed,
                   "detail": f"TBD_keyword_present={has_tbd}, Q3_timeline_marked_uncertain={q3_tbd}"})

    # ── Check 10: Zettelkasten links ≥2 with [[filename]] syntax ──────────
    zk_links = re.findall(r'\[\[([^\]]+)\]\]', content)
    unique_links = list(set(zk_links))
    passed = len(unique_links) >= 2
    checks.append({"name": "zettelkasten_links_ge2",
                   "passed": passed,
                   "detail": f"Found {len(unique_links)} unique [[links]]: {unique_links[:5]}"})

    # ── Check 11: Risk section with mitigation (data residency + vendor dependency) ─
    has_risk_section = bool(re.search(r'风险|risk', content, re.IGNORECASE))
    has_data_residency_risk = bool(re.search(r'数据出境|境外|数据安全法|个保法|个人信息保护', content))
    has_vendor_dependency_risk = bool(re.search(r'依赖.{0,20}(风险|供应商|服务商)|SLA|停服|备用', content))
    has_mitigation = bool(re.search(r'缓释|建议|应对|措施|SLA|合同', content))
    passed = has_risk_section and (has_data_residency_risk or has_vendor_dependency_risk) and has_mitigation
    checks.append({"name": "risk_section_with_mitigation",
                   "passed": passed,
                   "detail": f"risk_section={has_risk_section}, data_residency_risk={has_data_residency_risk}, vendor_dependency_risk={has_vendor_dependency_risk}, mitigation={has_mitigation}"})

    # ── Check 12: No expert roundtable (L2 not L3) ───────────────────────
    # The meeting is L2 (project-level), so "专家圆桌" should NOT be required/present
    # However, we don't penalize if it's present (agent may include it optionally)
    # We DO check that the note correctly identifies this as NOT L3
    has_l2_marker = bool(re.search(r'L2|项目级|项目.{0,10}阶段|里程碑', content))
    no_mandatory_roundtable = not bool(re.search(r'专家圆桌.{0,30}(必做|必须|启用)', content))
    passed = has_l2_marker or no_mandatory_roundtable
    checks.append({"name": "correct_meeting_level_not_l3",
                   "passed": passed,
                   "detail": f"L2_marker={has_l2_marker}, no_mandatory_roundtable_for_L2={no_mandatory_roundtable}"})

    # ── Check 13: Unresolved open question about risk talent ─────────────
    # Lin Xiaowei raised: no risk modeling talent — this must be captured
    talent_issue = bool(re.search(r'风控.{0,20}(人|人才|建模)|招人|外部顾问|能力.{0,20}(不足|缺乏|空白)', content))
    open_question = bool(re.search(r'待讨论|下次|开放.{0,10}问题|专项讨论|跟进', content))
    passed = talent_issue and open_question
    checks.append({"name": "open_question_talent_captured",
                   "passed": passed,
                   "detail": f"risk_modeling_talent_issue={talent_issue}, marked_as_open_question={open_question}"})

    return checks

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    workspace = sys.argv[1]
    try:
        checks = run_checks(workspace)
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "eval_error", "passed": False, "detail": str(e)}]}))
        sys.exit(1)

    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)

    # Must pass at least 10/13 to be considered passing
    overall_passed = passed_count >= 10

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()