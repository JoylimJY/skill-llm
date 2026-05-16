import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # ── Helper ──────────────────────────────────────────────────────────────
    def add(name, passed, detail=""):
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

    # ── 1. Find the CRM JSON file ────────────────────────────────────────────
    crm_json_candidates = list(workspace.rglob("crm_data.json")) + \
                          list(workspace.rglob("customers.json")) + \
                          list(workspace.rglob("mini_crm*.json")) + \
                          list(workspace.rglob("crm*.json"))
    
    crm_json = None
    crm_data = None
    
    for candidate in crm_json_candidates:
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
            if "customers" in data and isinstance(data["customers"], list):
                crm_json = candidate
                crm_data = data
                break
        except Exception:
            continue
    
    if crm_data is None:
        add("CRM JSON file found with correct schema", False, "No JSON file found with 'customers' array key")
    else:
        add("CRM JSON file found with correct schema", True, f"Found: {crm_json}")
    
    # ── 2. Validate customer count ───────────────────────────────────────────
    if crm_data:
        customers = crm_data.get("customers", [])
        customer_count_ok = len(customers) == 10
        add("Correct number of customers (10)", customer_count_ok, 
            f"Found {len(customers)} customers, expected 10")
    else:
        add("Correct number of customers (10)", False, "No CRM data available")
        customers = []
    
    # ── 3. Validate required JSON fields per customer ───────────────────────
    required_fields = {"id", "name", "company", "wechat", "email", "budget", 
                       "status", "source", "created", "last_contact", "interactions"}
    
    if customers:
        missing_fields_customers = []
        for c in customers:
            missing = required_fields - set(c.keys())
            if missing:
                missing_fields_customers.append(f"{c.get('name','?')}: missing {missing}")
        
        fields_ok = len(missing_fields_customers) == 0
        add("All customers have required JSON fields", fields_ok,
            "; ".join(missing_fields_customers) if missing_fields_customers else "All fields present")
    else:
        add("All customers have required JSON fields", False, "No customers to validate")
    
    # ── 4. Validate status values (must use SKILL.md enum values) ──────────
    valid_statuses = {"negotiating", "closed", "lost", "consulting"}
    if customers:
        invalid_statuses = []
        for c in customers:
            s = c.get("status", "")
            if s not in valid_statuses:
                invalid_statuses.append(f"{c.get('name','?')}: '{s}'")
        
        status_ok = len(invalid_statuses) == 0
        add("Status values use correct SKILL.md enum (negotiating/closed/lost/consulting)", 
            status_ok,
            "; ".join(invalid_statuses) if invalid_statuses else "All statuses valid")
    else:
        add("Status values use correct SKILL.md enum", False, "No customers")
    
    # ── 5. Validate specific customer statuses ───────────────────────────────
    if customers:
        customer_map = {c.get("name", ""): c for c in customers}
        
        # negotiating: 张总, 李经理, 王先生, 吴总
        # closed: 赵总, 钱经理, 孙先生
        # lost: 周女士
        # consulting: 郑经理, 陈小姐
        expected_statuses = {
            "张总": "negotiating",
            "李经理": "negotiating", 
            "王先生": "negotiating",
            "吴总": "negotiating",
            "赵总": "closed",
            "钱经理": "closed",
            "孙先生": "closed",
            "周女士": "lost",
            "郑经理": "consulting",
            "陈小姐": "consulting",
        }
        
        status_errors = []
        for name, expected in expected_statuses.items():
            actual = customer_map.get(name, {}).get("status", "MISSING")
            if actual != expected:
                status_errors.append(f"{name}: expected '{expected}', got '{actual}'")
        
        specific_status_ok = len(status_errors) == 0
        add("Individual customer statuses correctly mapped", specific_status_ok,
            "; ".join(status_errors) if status_errors else "All correct")
    else:
        add("Individual customer statuses correctly mapped", False, "No customers")
    
    # ── 6. Validate budget parsing (numeric, not string) ────────────────────
    if customers:
        budget_errors = []
        expected_budgets = {
            "张总": 50000,
            "李经理": 30000,
            "王先生": 15000,
            "赵总": 40000,
            "钱经理": 30000,
            "孙先生": 20000,
            "周女士": 8000,
            "吴总": 100000,
            "郑经理": 60000,
            "陈小姐": 12000,
        }
        for name, expected_budget in expected_budgets.items():
            actual_budget = customer_map.get(name, {}).get("budget")
            if actual_budget != expected_budget:
                budget_errors.append(f"{name}: expected {expected_budget}, got {actual_budget}")
        
        budget_ok = len(budget_errors) == 0
        add("Budget values correctly parsed as numeric integers", budget_ok,
            "; ".join(budget_errors) if budget_errors else "All budgets correct")
    else:
        add("Budget values correctly parsed as numeric integers", False, "No customers")
    
    # ── 7. Validate interactions array is non-empty for customers with history ──
    if customers:
        interaction_errors = []
        # These customers have at least 1 interaction in the notes
        for c in customers:
            interactions = c.get("interactions", [])
            if not isinstance(interactions, list):
                interaction_errors.append(f"{c.get('name','?')}: interactions not a list")
            elif len(interactions) == 0:
                interaction_errors.append(f"{c.get('name','?')}: empty interactions")
        
        interactions_ok = len(interaction_errors) == 0
        add("All customers have non-empty interactions array", interactions_ok,
            "; ".join(interaction_errors) if interaction_errors else "All have interactions")
    else:
        add("All customers have non-empty interactions array", False, "No customers")
    
    # ── 8. Find the dashboard report file ───────────────────────────────────
    report_candidates = list(workspace.rglob("*report*.txt")) + \
                        list(workspace.rglob("*dashboard*.txt")) + \
                        list(workspace.rglob("*看板*.txt")) + \
                        list(workspace.rglob("*报告*.txt")) + \
                        list(workspace.rglob("monthly_report*")) + \
                        list(workspace.rglob("march*report*")) + \
                        list(workspace.rglob("crm_report*"))
    
    # Exclude old distractor files
    report_candidates = [f for f in report_candidates if "archive" not in str(f) and "template" not in str(f).lower()]
    
    report_file = None
    report_content = None
    
    for candidate in report_candidates:
        try:
            content = candidate.read_text(encoding="utf-8")
            # Must contain dashboard emoji header
            if "📊" in content and ("客户" in content or "CRM" in content):
                report_file = candidate
                report_content = content
                break
        except Exception:
            continue
    
    if report_content is None:
        add("Dashboard report file found with 📊 header", False, 
            "No report file found containing 📊 emoji and customer content")
    else:
        add("Dashboard report file found with 📊 header", True, f"Found: {report_file}")
    
    # ── 9. Report contains required Chinese section headers ─────────────────
    if report_content:
        required_sections = [
            "客户概览",
            "漏斗分析",
            "本月新增",
            "待跟进",
            "本月成交",
            "收入统计",
        ]
        missing_sections = [s for s in required_sections if s not in report_content]
        sections_ok = len(missing_sections) == 0
        add("Report contains all required Chinese section headers", sections_ok,
            f"Missing: {missing_sections}" if missing_sections else "All sections present")
    else:
        add("Report contains all required Chinese section headers", False, "No report content")
    
    # ── 10. Report contains funnel analysis with arrow format ────────────────
    if report_content:
        # Must contain "咨询 → 报价 → 成交" or similar funnel with arrows
        funnel_ok = ("→" in report_content and "成交" in report_content and 
                     ("咨询" in report_content or "报价" in report_content))
        add("Report contains funnel analysis with → arrow format", funnel_ok,
            "Funnel with '→' arrows found" if funnel_ok else "Missing funnel with → arrows")
    else:
        add("Report contains funnel analysis with → arrow format", False, "No report content")
    
    # ── 11. Report correct customer overview counts ──────────────────────────
    if report_content:
        # Total: 10, negotiating: 4, closed: 3, lost: 1, consulting: 2
        total_ok = "10" in report_content
        negotiating_ok = "4" in report_content  # 洽谈中: 4
        closed_ok = "3" in report_content        # 已成交: 3
        lost_ok = "1" in report_content          # 已流失: 1
        
        counts_ok = total_ok and negotiating_ok and closed_ok
        add("Report overview counts correct (10 total, 4 negotiating, 3 closed, 1 lost)", 
            counts_ok,
            f"total_ok={total_ok}, negotiating_ok={negotiating_ok}, closed_ok={closed_ok}, lost_ok={lost_ok}")
    else:
        add("Report overview counts correct", False, "No report content")
    
    # ── 12. Report contains correct monthly revenue ──────────────────────────
    if report_content:
        # 本月成交: 赵总35000 + 钱经理28000 + 孙先生18000 = 81000
        # 本月回款: 25000+28000+12000 = 65000
        # 待收: 10000+0+6000 = 16000
        revenue_ok = "81,000" in report_content or "81000" in report_content or "¥81" in report_content
        payment_ok = "65,000" in report_content or "65000" in report_content or "¥65" in report_content
        outstanding_ok = "16,000" in report_content or "16000" in report_content or "¥16" in report_content
        
        financial_ok = revenue_ok and payment_ok and outstanding_ok
        add("Report financial figures correct (成交¥81k, 回款¥65k, 待收¥16k)", financial_ok,
            f"revenue_ok={revenue_ok}(81000), payment_ok={payment_ok}(65000), outstanding_ok={outstanding_ok}(16000)")
    else:
        add("Report financial figures correct", False, "No report content")
    
    # ── 13. Pending follow-up sorted by days since contact (吴总 first) ─────
    if report_content:
        # Reference date from notes is 2026-03-15
        # 张总: last_contact=2026-03-10 → 5 days ago  
        # 李经理: last_contact=2026-03-13 → 2 days ago
        # 王先生: last_contact=2026-03-14 → 1 day ago
        # 吴总: last_contact=2026-03-12 → 3 days ago
        # Correct order: 张总(5d) > 吴总(3d) > 李经理(2d) > 王先生(1d)
        
        zhang_pos = report_content.find("张总")
        wu_pos = report_content.find("吴总")
        li_pos = report_content.find("李经理")
        wang_pos = report_content.find("王先生")
        
        # Check in context of 待跟进 section
        followup_section_start = report_content.find("待跟进")
        if followup_section_start > 0:
            # Find next section after 待跟进
            next_section = report_content.find("##", followup_section_start + 5)
            if next_section < 0:
                next_section = len(report_content)
            followup_section = report_content[followup_section_start:next_section]
            
            zhang_fo = followup_section.find("张总")
            wu_fo = followup_section.find("吴总")
            li_fo = followup_section.find("李经理")
            wang_fo = followup_section.find("王先生")
            
            # 张总 should appear before 吴总 which should appear before 李经理
            order_ok = (zhang_fo >= 0 and wu_fo >= 0 and 
                        zhang_fo < wu_fo < li_fo)
            add("Pending follow-ups sorted by days-since-contact (张总 first, then 吴总)", order_ok,
                f"In 待跟进 section: 张总@{zhang_fo}, 吴总@{wu_fo}, 李经理@{li_fo}, 王先生@{wang_fo}")
        else:
            add("Pending follow-ups sorted by days-since-contact", False, "待跟进 section not found in report")
    else:
        add("Pending follow-ups sorted by days-since-contact", False, "No report content")
    
    # ── 14. Monthly closed deals listed correctly ────────────────────────────
    if report_content:
        deals_ok = ("赵总" in report_content and "35,000" in report_content or "35000" in report_content) and \
                   ("钱经理" in report_content and "28,000" in report_content or "28000" in report_content) and \
                   ("孙先生" in report_content and "18,000" in report_content or "18000" in report_content)
        
        # Check service types
        service_ok = "网站开发" in report_content and "小程序" in report_content and "APP" in report_content
        
        deals_section_ok = deals_ok and service_ok
        add("Monthly closed deals listed with amounts and service types", deals_section_ok,
            f"deals_ok={deals_ok}, service_types_ok={service_ok}")
    else:
        add("Monthly closed deals listed correctly", False, "No report content")
    
    # ── 15. Source breakdown in 本月新增 section ────────────────────────────
    if report_content:
        new_section_start = report_content.find("本月新增")
        if new_section_start >= 0:
            next_section = report_content.find("##", new_section_start + 5)
            if next_section < 0:
                next_section = len(report_content)
            new_section = report_content[new_section_start:next_section]
            
            # March 2026 new customers: all 10 are new (created in March 2026)
            # Sources: 掘金 (张总,赵总,钱经理,吴总,郑经理=5), 知乎 (李经理,孙先生,陈小姐=3), 朋友推荐 (王先生,周女士=2)
            juejin_ok = "掘金" in new_section and ("5" in new_section or "五" in new_section)
            zhihu_ok = "知乎" in new_section and ("3" in new_section or "三" in new_section)
            referral_ok = "推荐" in new_section and ("2" in new_section or "二" in new_section)
            
            source_ok = juejin_ok and zhihu_ok and referral_ok
            add("Source breakdown correct in 本月新增 (掘金5, 知乎3, 推荐2)", source_ok,
                f"juejin_ok={juejin_ok}, zhihu_ok={zhihu_ok}, referral_ok={referral_ok}")
        else:
            add("Source breakdown in 本月新增 section", False, "本月新增 section not found")
    else:
        add("Source breakdown in 本月新增 section", False, "No report content")
    
    # ── Compute final score ──────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 3)
    passed = score >= 0.75  # Must pass at least 75% of checks
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace_dir)