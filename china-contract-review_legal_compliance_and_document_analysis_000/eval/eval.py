import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # --- Find the report file ---
    report_files = list(workspace.rglob("contract_review_report.json"))
    
    if not report_files:
        checks.append({"name": "报告文件存在", "passed": False, "detail": "未找到 contract_review_report.json 文件"})
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    
    report_path = report_files[0]
    checks.append({"name": "报告文件存在", "passed": True, "detail": f"找到报告文件: {report_path}"})
    
    # --- Parse JSON ---
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "JSON格式有效", "passed": False, "detail": f"JSON解析失败: {e}"})
        return {"passed": False, "score": 1/7, "checks": checks}
    
    checks.append({"name": "JSON格式有效", "passed": True, "detail": "JSON解析成功"})
    
    # Normalize: support both list of issues and nested dict
    def get_text(obj):
        """Recursively extract all string values from a JSON object as a single searchable blob."""
        if isinstance(obj, str):
            return obj
        elif isinstance(obj, list):
            return " ".join(get_text(i) for i in obj)
        elif isinstance(obj, dict):
            return " ".join(get_text(v) for v in obj.values())
        return str(obj)
    
    full_text = get_text(report)
    
    # --- Check 1: Contract type identified as labor contract ---
    labor_keywords = ["劳动合同", "labor", "雇佣"]
    contract_type_found = any(kw in full_text for kw in labor_keywords)
    checks.append({
        "name": "合同类型识别：劳动合同",
        "passed": contract_type_found,
        "detail": "报告中应明确标识合同类型为劳动合同" if not contract_type_found else "合同类型识别正确"
    })
    
    # --- Check 2: Probation period issue identified (劳动合同法第19条) ---
    probation_law = re.search(r"第\s*19\s*条|第十九条|试用期.*?(违|超|过长|违法|违规)|probation", full_text)
    probation_issue = re.search(r"试用期.{0,30}(12个月|一年|超出|过长|违|不符|最长6|6个月)", full_text)
    probation_pass = bool(probation_law or probation_issue)
    checks.append({
        "name": "问题识别：试用期违规（劳动合同法第19条）",
        "passed": probation_pass,
        "detail": "应识别3年合同试用期12个月超过法定上限6个月，引用第19条" if not probation_pass else "试用期问题识别正确"
    })
    
    # --- Check 3: Penalty clause issue (劳动合同法第25条) ---
    penalty_law = re.search(r"第\s*25\s*条|第二十五条", full_text)
    penalty_issue = re.search(r"违约金.{0,60}(20万|200,000|200000|过高|无效|不得|仅限|违法|违规)", full_text)
    penalty_pass = bool(penalty_law or penalty_issue)
    checks.append({
        "name": "问题识别：违约金条款违规（劳动合同法第25条）",
        "passed": penalty_pass,
        "detail": "应识别劳动者违约金仅限培训/竞业限制情形，一般离职20万违约金不合法，引用第25条" if not penalty_pass else "违约金问题识别正确"
    })
    
    # --- Check 4: Working hours violation (劳动法第36条) ---
    hours_law = re.search(r"第\s*36\s*条|第三十六条|劳动法.*?工时|工时.*?劳动法", full_text)
    hours_issue = re.search(r"(每日|每天).{0,20}(10小时|十小时|超|违|过长)|(每周).{0,20}(60小时|六十小时|超|违)", full_text)
    hours_pass = bool(hours_law or hours_issue)
    checks.append({
        "name": "问题识别：工作时间违规（劳动法第36条）",
        "passed": hours_pass,
        "detail": "应识别每日10小时每周60小时超过标准工时（每日8小时每周40小时），引用第36条" if not hours_pass else "工作时间问题识别正确"
    })
    
    # --- Check 5: Non-compete period too long (劳动合同法第24条) ---
    noncompete_law = re.search(r"第\s*24\s*条|第二十四条", full_text)
    noncompete_issue = re.search(r"竞业.{0,40}(3年|三年|超|违|过长|最长2年|不超过2年)", full_text)
    noncompete_pass = bool(noncompete_law or noncompete_issue)
    checks.append({
        "name": "问题识别：竞业限制期限违规（劳动合同法第24条）",
        "passed": noncompete_pass,
        "detail": "应识别竞业限制3年超过法定最长2年上限，引用第24条" if not noncompete_pass else "竞业限制问题识别正确"
    })
    
    # --- Check 6: Social insurance missing (劳动合同法第17条 or 社会保险法) ---
    insurance_law = re.search(r"第\s*17\s*条|第十七条|社会保险法|社保.*?(缺|未|缺失|必备|必须|漏)", full_text)
    insurance_issue = re.search(r"社(会)?保.{0,50}(未|缺|漏|缺失|未约定|未规定|没有)", full_text)
    insurance_alt = re.search(r"(缺少|缺失|未规定|未约定|未提及).{0,30}社(会)?保", full_text)
    insurance_pass = bool(insurance_law or insurance_issue or insurance_alt)
    checks.append({
        "name": "问题识别：社会保险条款缺失（劳动合同法第17条）",
        "passed": insurance_pass,
        "detail": "应识别合同缺少社会保险缴纳约定（必备条款），引用劳动合同法第17条或社会保险相关法规" if not insurance_pass else "社会保险问题识别正确"
    })
    
    # --- Check 7: Modification suggestions present ---
    suggestion_keywords = ["建议", "修改", "应当", "应将", "应调整", "改为", "suggestion", "recommend"]
    has_suggestions = any(kw in full_text for kw in suggestion_keywords)
    checks.append({
        "name": "包含修改建议",
        "passed": has_suggestions,
        "detail": "报告中应包含具体的条款修改建议" if not has_suggestions else "报告包含修改建议"
    })
    
    # --- Calculate score ---
    passed_count = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_count / total_checks, 4)
    
    # Must pass at least 6/8 checks to pass overall
    overall_passed = passed_count >= 6
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))