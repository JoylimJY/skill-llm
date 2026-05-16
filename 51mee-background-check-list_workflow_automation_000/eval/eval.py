import sys
import json
import os
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    total_score = 0.0

    # ── Helper ──────────────────────────────────────────────────────────────
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── Find output files ────────────────────────────────────────────────────
    ws = Path(workspace_dir)
    json_files = list(ws.rglob("background_check.json"))
    md_files   = list(ws.rglob("background_check.md"))

    json_exists = len(json_files) > 0
    md_exists   = len(md_files) > 0

    total_score += add_check(
        "background_check.json exists",
        json_exists,
        f"Found at: {json_files[0]}" if json_exists else "File not found anywhere in workspace"
    )
    total_score += add_check(
        "background_check.md exists",
        md_exists,
        f"Found at: {md_files[0]}" if md_exists else "File not found anywhere in workspace"
    )

    # ── Parse JSON ───────────────────────────────────────────────────────────
    data = None
    if json_exists:
        try:
            with open(json_files[0], "r", encoding="utf-8") as f:
                raw = f.read()
            # Strip markdown code fences if present
            raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
            raw = re.sub(r"\s*```$", "", raw.strip())
            data = json.loads(raw)
            total_score += add_check("JSON is valid and parseable", True, "Parsed successfully")
        except Exception as e:
            total_score += add_check("JSON is valid and parseable", False, f"Parse error: {e}")

    if data is None:
        # Can't do further JSON checks; fill remaining with failures
        remaining_checks = [
            ("candidate.name is 李明远",                False, "No JSON data"),
            ("candidate.position is 高级后端工程师",      False, "No JSON data"),
            ("check_items is a non-empty list",          False, "No JSON data"),
            ("All check_items have valid category",      False, "No JSON data"),
            ("All check_items have contact object",      False, "No JSON data"),
            ("All check_items have 3-5 questions",       False, "No JSON data"),
            ("All check_items have valid risk_level",    False, "No JSON data"),
            ("Contains 学历 category item",              False, "No JSON data"),
            ("Contains 工作经历 category items",         False, "No JSON data"),
            ("Contains 项目经历 category items",         False, "No JSON data"),
            ("risk_alerts is present and non-empty",     False, "No JSON data"),
            ("risk_alerts types use allowed enum values",False, "No JSON data"),
            ("频繁跳槽 risk alert present",               False, "No JSON data"),
            ("学历疑点 risk alert present",               False, "No JSON data"),
            ("report_template.sections has ≥5 items",   False, "No JSON data"),
            ("timeline field is present",                False, "No JSON data"),
        ]
        for name, passed, detail in remaining_checks:
            checks.append({"name": name, "passed": passed, "detail": detail})
    else:
        # candidate block
        candidate = data.get("candidate", {})
        cname = candidate.get("name", "")
        cpos  = candidate.get("position", "")

        total_score += add_check(
            "candidate.name is 李明远",
            "李明远" in cname,
            f"Got: {cname!r}"
        )
        total_score += add_check(
            "candidate.position is 高级后端工程师",
            "高级后端工程师" in cpos or "后端工程师" in cpos,
            f"Got: {cpos!r}"
        )

        # check_items
        check_items = data.get("check_items", [])
        total_score += add_check(
            "check_items is a non-empty list",
            isinstance(check_items, list) and len(check_items) > 0,
            f"Count: {len(check_items)}"
        )

        valid_categories = {"学历", "工作经历", "项目经历"}
        valid_risk_levels = {"低", "中", "高"}

        bad_cats, bad_contacts, bad_qcount, bad_risk = [], [], [], []
        for item in check_items:
            cat = item.get("category", "")
            if cat not in valid_categories:
                bad_cats.append(cat)
            contact = item.get("contact", None)
            if not isinstance(contact, dict) or "department" not in contact or "method" not in contact:
                bad_contacts.append(item.get("id", "?"))
            questions = item.get("questions", [])
            if not isinstance(questions, list) or not (3 <= len(questions) <= 5):
                bad_qcount.append({"id": item.get("id","?"), "count": len(questions) if isinstance(questions, list) else "N/A"})
            rl = item.get("risk_level", "")
            if rl not in valid_risk_levels:
                bad_risk.append(rl)

        total_score += add_check(
            "All check_items have valid category",
            len(bad_cats) == 0,
            f"Invalid categories: {bad_cats}" if bad_cats else "All valid (学历|工作经历|项目经历)"
        )
        total_score += add_check(
            "All check_items have contact object",
            len(bad_contacts) == 0,
            f"Items missing contact: {bad_contacts}" if bad_contacts else "All present"
        )
        total_score += add_check(
            "All check_items have 3-5 questions",
            len(bad_qcount) == 0,
            f"Violations: {bad_qcount}" if bad_qcount else "All items have 3-5 questions"
        )
        total_score += add_check(
            "All check_items have valid risk_level",
            len(bad_risk) == 0,
            f"Invalid risk levels: {bad_risk}" if bad_risk else "All valid (低|中|高)"
        )

        cats_present = {item.get("category","") for item in check_items}
        total_score += add_check(
            "Contains 学历 category item",
            "学历" in cats_present,
            f"Categories found: {cats_present}"
        )
        total_score += add_check(
            "Contains 工作经历 category items",
            "工作经历" in cats_present,
            f"Categories found: {cats_present}"
        )
        total_score += add_check(
            "Contains 项目经历 category items",
            "项目经历" in cats_present,
            f"Categories found: {cats_present}"
        )

        # risk_alerts
        risk_alerts = data.get("risk_alerts", [])
        total_score += add_check(
            "risk_alerts is present and non-empty",
            isinstance(risk_alerts, list) and len(risk_alerts) > 0,
            f"Count: {len(risk_alerts)}"
        )

        allowed_types = {"频繁跳槽", "学历疑点", "项目疑点", "其他"}
        bad_types = [a.get("type","") for a in risk_alerts if a.get("type","") not in allowed_types]
        total_score += add_check(
            "risk_alerts types use allowed enum values",
            len(bad_types) == 0,
            f"Invalid types: {bad_types}" if bad_types else "All valid"
        )

        alert_types = {a.get("type","") for a in risk_alerts}
        has_job_hop = "频繁跳槽" in alert_types
        total_score += add_check(
            "频繁跳槽 risk alert present",
            has_job_hop,
            f"Alert types found: {alert_types}. Candidate had 4 jobs in ~5 years including 5-month tenure."
        )

        has_edu_flag = "学历疑点" in alert_types
        total_score += add_check(
            "学历疑点 risk alert present",
            has_edu_flag,
            f"Alert types found: {alert_types}. Candidate's master is from correspondence school; suspicious gap."
        )

        # report_template
        rt = data.get("report_template", {})
        sections = rt.get("sections", [])
        total_score += add_check(
            "report_template.sections has ≥5 items",
            isinstance(sections, list) and len(sections) >= 5,
            f"Sections count: {len(sections)}, content: {sections}"
        )

        timeline = data.get("timeline", None)
        total_score += add_check(
            "timeline field is present",
            timeline is not None and str(timeline).strip() != "",
            f"Got: {timeline!r}"
        )

    # ── Markdown checks ──────────────────────────────────────────────────────
    if md_exists:
        try:
            with open(md_files[0], "r", encoding="utf-8") as f:
                md_content = f.read()

            has_basic_info_header = "📋" in md_content and "基本信息" in md_content
            total_score += add_check(
                "Markdown has 📋 基本信息 section",
                has_basic_info_header,
                "Section header with emoji found" if has_basic_info_header else "Missing 📋 基本信息 section"
            )

            has_verify_header = "✅" in md_content and "验证项目" in md_content
            total_score += add_check(
                "Markdown has ✅ 验证项目 section",
                has_verify_header,
                "Section found" if has_verify_header else "Missing ✅ 验证项目 section"
            )

            has_risk_header = "⚠️" in md_content and "风险提示" in md_content
            total_score += add_check(
                "Markdown has ⚠️ 风险提示 section",
                has_risk_header,
                "Section found" if has_risk_header else "Missing ⚠️ 风险提示 section"
            )

            has_report_header = "📄" in md_content and "背调报告模板" in md_content
            total_score += add_check(
                "Markdown has 📄 背调报告模板 section",
                has_report_header,
                "Section found" if has_report_header else "Missing 📄 背调报告模板 section"
            )

            has_advice_header = "💡" in md_content and "背调建议" in md_content
            total_score += add_check(
                "Markdown has 💡 背调建议 section",
                has_advice_header,
                "Section found" if has_advice_header else "Missing 💡 背调建议 section"
            )

            has_candidate_name = "李明远" in md_content
            total_score += add_check(
                "Markdown contains candidate name 李明远",
                has_candidate_name,
                "Name found in markdown" if has_candidate_name else "Candidate name missing from markdown"
            )

        except Exception as e:
            for name in [
                "Markdown has 📋 基本信息 section",
                "Markdown has ✅ 验证项目 section",
                "Markdown has ⚠️ 风险提示 section",
                "Markdown has 📄 背调报告模板 section",
                "Markdown has 💡 背调建议 section",
                "Markdown contains candidate name 李明远",
            ]:
                checks.append({"name": name, "passed": False, "detail": f"Read error: {e}"})
    else:
        for name in [
            "Markdown has 📋 基本信息 section",
            "Markdown has ✅ 验证项目 section",
            "Markdown has ⚠️ 风险提示 section",
            "Markdown has 📄 背调报告模板 section",
            "Markdown has 💡 背调建议 section",
            "Markdown contains candidate name 李明远",
        ]:
            checks.append({"name": name, "passed": False, "detail": "background_check.md not found"})

    # ── Final score ──────────────────────────────────────────────────────────
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    final_score = round(passed_checks / total_checks, 4) if total_checks > 0 else 0.0
    overall_passed = final_score >= 0.75

    return {
        "passed": overall_passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))