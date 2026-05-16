import sys
import json
import os
from pathlib import Path

def load_report(workspace: str):
    """Find and load the o2o_diagnostic_report.json file."""
    candidates = list(Path(workspace).rglob("o2o_diagnostic_report.json"))
    if not candidates:
        return None, "File 'o2o_diagnostic_report.json' not found anywhere in workspace."
    # prefer workspace root
    root_candidate = Path(workspace) / "o2o_diagnostic_report.json"
    if root_candidate.exists():
        target = root_candidate
    else:
        target = candidates[0]
    with open(target, "r", encoding="utf-8") as f:
        return json.load(f), str(target)

def check_five_flows(report: dict) -> tuple[bool, str]:
    """五流模型: 人流/商流/物流/资金流/信息流 all 5 must appear."""
    five_flows = ["人流", "商流", "物流", "资金流", "信息流"]
    report_str = json.dumps(report, ensure_ascii=False)
    found = [f for f in five_flows if f in report_str]
    if len(found) == 5:
        return True, f"All 5 flows present: {found}"
    else:
        missing = [f for f in five_flows if f not in report_str]
        return False, f"Missing flows: {missing}. Found: {found}"

def check_o2o_relationship_type(report: dict) -> tuple[bool, str]:
    """4种O2O关系: must identify at least one correct relationship type using exact directional notation or clear equivalent."""
    report_str = json.dumps(report, ensure_ascii=False)
    # Valid patterns from the skill: 线上→线下, 线下→线上, 线下→线上→线下, 线上→线下→线上
    patterns = [
        "线上→线下→线上",
        "线下→线上→线下",
        "线上到线下到线上",
        "线下到线上到线下",
        "线上→线下",
        "线下→线上",
        "线上到线下",
        "线下到线上",
    ]
    found = [p for p in patterns if p in report_str]
    if found:
        return True, f"O2O relationship type(s) identified: {found}"
    else:
        return False, "No valid O2O relationship type notation found (e.g., '线上→线下→线上', '线下→线上')"

def check_three_closedloops(report: dict) -> tuple[bool, str]:
    """3个闭环: 信息闭环/支付闭环/关系闭环 — all 3 must be mentioned."""
    loops = ["信息闭环", "支付闭环", "关系闭环"]
    report_str = json.dumps(report, ensure_ascii=False)
    found = [l for l in loops if l in report_str]
    if len(found) == 3:
        return True, f"All 3 closed loops present: {found}"
    else:
        missing = [l for l in loops if l not in report_str]
        return False, f"Missing closed loops: {missing}. Found: {found}"

def check_entry_points(report: dict) -> tuple[bool, str]:
    """15个入口: must identify at least 3 relevant entry points from the canonical list."""
    canonical_entries = [
        "二维码", "搜索", "电商流量", "即时聊天", "微信",
        "地图导航", "评价信息", "大众点评", "促销", "预约预付",
        "会员卡", "储值卡", "口碑", "数据外呼", "支付入口",
        "广告联盟", "免费Wi-Fi", "Wi-Fi", "上门服务", "美团", "饿了么",
        "小程序", "外卖平台"
    ]
    report_str = json.dumps(report, ensure_ascii=False)
    found = [e for e in canonical_entries if e in report_str]
    # deduplicate by meaning
    unique_found = list(set(found))
    # count distinct meaningful entries (merge synonyms)
    distinct = set()
    if any(x in report_str for x in ["二维码"]): distinct.add("二维码")
    if any(x in report_str for x in ["搜索"]): distinct.add("搜索")
    if any(x in report_str for x in ["电商流量"]): distinct.add("电商流量")
    if any(x in report_str for x in ["即时聊天", "微信", "企业微信"]): distinct.add("即时聊天")
    if any(x in report_str for x in ["地图导航"]): distinct.add("地图导航")
    if any(x in report_str for x in ["评价信息", "大众点评"]): distinct.add("评价信息")
    if any(x in report_str for x in ["促销"]): distinct.add("促销")
    if any(x in report_str for x in ["预约", "预付"]): distinct.add("预约预付")
    if any(x in report_str for x in ["会员卡", "储值卡"]): distinct.add("会员卡储值卡")
    if any(x in report_str for x in ["口碑"]): distinct.add("口碑")
    if any(x in report_str for x in ["数据外呼"]): distinct.add("数据外呼")
    if any(x in report_str for x in ["支付入口", "支付"]): distinct.add("支付入口")
    if any(x in report_str for x in ["广告联盟"]): distinct.add("广告联盟")
    if any(x in report_str for x in ["Wi-Fi", "Wifi", "wifi"]): distinct.add("Wi-Fi")
    if any(x in report_str for x in ["上门服务"]): distinct.add("上门服务")
    if any(x in report_str for x in ["美团", "饿了么", "外卖平台", "本地生活"]): distinct.add("外卖平台")
    if any(x in report_str for x in ["小程序"]): distinct.add("小程序")

    if len(distinct) >= 3:
        return True, f"Found {len(distinct)} distinct entry points: {sorted(distinct)}"
    else:
        return False, f"Only found {len(distinct)} distinct entry points (need ≥3): {sorted(distinct)}"

def check_risks(report: dict) -> tuple[bool, str]:
    """8大风险: must identify at least 2 specific risks from the canonical list."""
    report_str = json.dumps(report, ensure_ascii=False)
    risk_keywords = [
        "高期望", "规划太宏伟", "政策风险", "监管", "渠道风险",
        "利益分配", "盲目扩张", "消费者习惯", "平台风险",
        "过度依赖", "人才风险", "经营风险"
    ]
    found_risks = [k for k in risk_keywords if k in report_str]
    if len(found_risks) >= 2:
        return True, f"Found risk keywords: {found_risks}"
    else:
        return False, f"Insufficient risk analysis. Found keywords: {found_risks} (need at least 2 from 8大风险)"

def check_misconceptions(report: dict) -> tuple[bool, str]:
    """10大误区: must identify at least 2 specific misconceptions relevant to the case."""
    report_str = json.dumps(report, ensure_ascii=False)
    misconception_keywords = [
        "O2O就是销售", "为了销售", "促销", "误区",
        "二维码就是O2O", "移动支付就是O2O", "平台越多越好",
        "托管代运营", "活动不需要系统", "产品用户等于O2O用户",
        "什么都叫O2O", "线上到线下", "数据"
    ]
    # More targeted: look for misconception framing
    misconception_indicators = [
        "误区", "不是", "错误认知", "错误理解", "不等于",
        "不只是", "不仅仅", "不应该", "不能简单"
    ]
    # Check if the report actually addresses misconceptions from case
    # Case mentions: "老板认为O2O就是搞促销" and "把东西搬到网上就算转型"
    case_misconceptions = [
        "O2O就是搞促销", "O2O就是促销", "促销", 
        "搬到网上就算", "线上化就是O2O", "搬上网", "简单搬到线上",
        "O2O就是打折", "销售导向", "体验"
    ]
    found_case = [k for k in case_misconceptions if k in report_str]
    found_indicators = [k for k in misconception_indicators if k in report_str]
    
    # Must show awareness of misconceptions AND address them
    if (len(found_case) >= 1 and len(found_indicators) >= 1) or len(found_case) >= 2:
        return True, f"Misconceptions addressed. Case-specific: {found_case}, Indicators: {found_indicators}"
    else:
        return False, f"Insufficient misconception analysis. Case keywords: {found_case}, Indicators: {found_indicators}"

def check_experience_over_sales(report: dict) -> tuple[bool, str]:
    """Core principle: 体验 must be emphasized as primary over 销售."""
    report_str = json.dumps(report, ensure_ascii=False)
    experience_keywords = ["体验", "客户体验", "消费者体验", "用户体验"]
    found_exp = [k for k in experience_keywords if k in report_str]
    
    # Check that it's framed as primary/core, not just mentioned
    core_framing = ["核心是体验", "以体验", "体验为核心", "体验导向", 
                    "体验至上", "不是销售", "不是以销售", "体验优先",
                    "体验而非", "重点是体验"]
    found_core = [k for k in core_framing if k in report_str]
    
    if found_exp and (found_core or report_str.count("体验") >= 3):
        return True, f"Experience-centric framing detected. Keywords: {found_exp}, Core framing: {found_core}"
    else:
        return False, f"Missing strong 'experience over sales' framing. Found: {found_exp}, Core: {found_core}"

def check_report_structure(report: dict) -> tuple[bool, str]:
    """The report must be a valid JSON with at least 3 meaningful top-level sections."""
    if not isinstance(report, dict):
        return False, "Report is not a JSON object."
    keys = list(report.keys())
    if len(keys) < 3:
        return False, f"Report has fewer than 3 top-level keys: {keys}"
    # Check for meaningful content (not empty/placeholder)
    content_str = json.dumps(report, ensure_ascii=False)
    placeholders = ["TODO", "TBD", "???", "PLACEHOLDER", "待填写"]
    found_placeholders = [p for p in placeholders if p in content_str]
    if found_placeholders:
        return False, f"Report contains placeholders: {found_placeholders}"
    if len(content_str) < 800:
        return False, f"Report content is too thin ({len(content_str)} chars). Expected substantive analysis."
    return True, f"Report structure valid with {len(keys)} top-level keys: {keys}"

def check_company_specific(report: dict) -> tuple[bool, str]:
    """Report must be specific to 蜀香阁 (not generic boilerplate)."""
    report_str = json.dumps(report, ensure_ascii=False)
    specific_references = ["蜀香阁", "川菜", "门店", "纸质会员", "8000", "美团", "饿了么", "抖音", "公众号", "4万"]
    found = [r for r in specific_references if r in report_str]
    if len(found) >= 3:
        return True, f"Company-specific content confirmed: {found}"
    else:
        return False, f"Report appears generic. Only found {len(found)} company-specific references: {found}"

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    total_score = 0.0
    weights = {
        "report_structure": 0.10,
        "company_specific": 0.10,
        "five_flows": 0.15,
        "o2o_relationship": 0.10,
        "three_closedloops": 0.15,
        "entry_points": 0.10,
        "risks": 0.10,
        "misconceptions": 0.10,
        "experience_over_sales": 0.10,
    }

    # Load report
    try:
        report, location = load_report(workspace)
        if report is None:
            result = {
                "passed": False,
                "score": 0.0,
                "checks": [{"name": "file_found", "passed": False, "detail": location}]
            }
            print(json.dumps(result, ensure_ascii=False))
            return
        file_check = {"name": "file_found", "passed": True, "detail": f"Found at: {location}"}
        checks.append(file_check)
    except json.JSONDecodeError as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_found", "passed": False, "detail": f"JSON parse error: {e}"}]
        }
        print(json.dumps(result, ensure_ascii=False))
        return
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_found", "passed": False, "detail": f"Unexpected error: {e}"}]
        }
        print(json.dumps(result, ensure_ascii=False))
        return

    # Run all checks
    check_functions = {
        "report_structure": check_report_structure,
        "company_specific": check_company_specific,
        "five_flows": check_five_flows,
        "o2o_relationship": check_o2o_relationship_type,
        "three_closedloops": check_three_closedloops,
        "entry_points": check_entry_points,
        "risks": check_risks,
        "misconceptions": check_misconceptions,
        "experience_over_sales": check_experience_over_sales,
    }

    for check_name, check_fn in check_functions.items():
        try:
            passed, detail = check_fn(report)
            checks.append({"name": check_name, "passed": passed, "detail": detail})
            if passed:
                total_score += weights[check_name]
        except Exception as e:
            checks.append({"name": check_name, "passed": False, "detail": f"Check error: {e}"})

    # Normalize score to [0,1]
    final_score = round(total_score, 3)
    # Pass threshold: ≥ 0.70
    passed_overall = final_score >= 0.70

    result = {
        "passed": passed_overall,
        "score": final_score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()