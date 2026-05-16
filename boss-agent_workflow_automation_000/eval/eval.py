import json
import sys
import os
from pathlib import Path

def evaluate(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # -----------------------------------------------------------------------
    # CHECK 1: incident_report.json exists somewhere in workspace
    # -----------------------------------------------------------------------
    report_files = list(workspace.rglob("incident_report.json"))
    check1_passed = len(report_files) > 0
    checks.append({
        "name": "incident_report.json exists",
        "passed": check1_passed,
        "detail": f"Found {len(report_files)} file(s): {[str(f) for f in report_files]}" if report_files else "No incident_report.json found anywhere in workspace"
    })
    if check1_passed:
        total_score += 0.10

    if not check1_passed:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    report_path = report_files[0]

    # -----------------------------------------------------------------------
    # CHECK 2: incident_report.json is valid JSON
    # -----------------------------------------------------------------------
    try:
        with open(report_path, "r") as f:
            report = json.load(f)
        check2_passed = True
        checks.append({
            "name": "incident_report.json is valid JSON",
            "passed": True,
            "detail": f"Successfully parsed JSON from {report_path}"
        })
        total_score += 0.05
    except Exception as e:
        checks.append({
            "name": "incident_report.json is valid JSON",
            "passed": False,
            "detail": f"JSON parse error: {e}"
        })
        return {"passed": False, "score": total_score, "checks": checks}

    # -----------------------------------------------------------------------
    # CHECK 3: sessions_list was used to query BOTH ass and ops agents
    # The evidence: sessions_list writes to sent_messages is not direct,
    # but we check that the report contains data from BOTH agents' sessions.
    # The report must mention both ass and ops agent findings.
    # -----------------------------------------------------------------------
    report_str = json.dumps(report).lower()
    has_ass_content = any(keyword in report_str for keyword in ["ass", "doc_service", "user_service", "documentation", "latency"])
    has_ops_content = any(keyword in report_str for keyword in ["ops", "sys_service", "gateway", "packet loss", "system service"])

    check3a_passed = has_ass_content
    checks.append({
        "name": "Report contains Ass Agent findings (doc_service/user_service data)",
        "passed": check3a_passed,
        "detail": "Report references Ass Agent's domain (doc_service, user_service, or latency issues)" if check3a_passed else "No reference to Ass Agent's managed services found in report"
    })
    if check3a_passed:
        total_score += 0.15

    check3b_passed = has_ops_content
    checks.append({
        "name": "Report contains Ops Agent findings (sys_service/gateway data)",
        "passed": check3b_passed,
        "detail": "Report references Ops Agent's domain (sys_service, gateway, or packet loss)" if check3b_passed else "No reference to Ops Agent's managed services found in report"
    })
    if check3b_passed:
        total_score += 0.15

    # -----------------------------------------------------------------------
    # CHECK 4: sessions_send was called with correct session key format
    # Evidence: Check sent_messages.log for properly formatted session keys
    # -----------------------------------------------------------------------
    sent_log_path = workspace / "sessions" / "sent_messages.log"
    sent_to_ass = False
    sent_to_ops = False
    correct_key_format_ass = False
    correct_key_format_ops = False

    try:
        if sent_log_path.exists():
            with open(sent_log_path, "r") as f:
                log_content = f.read().strip()
            
            if log_content:
                for line in log_content.split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        session_key = entry.get("session_key", "")
                        agent = entry.get("agent", "")
                        
                        # Check exact format: agent:<name>:main
                        if session_key == "agent:ass:main":
                            correct_key_format_ass = True
                            sent_to_ass = True
                        if session_key == "agent:ops:main":
                            correct_key_format_ops = True
                            sent_to_ops = True
                    except json.JSONDecodeError:
                        continue
        
        checks.append({
            "name": "sessions_send called with correct key 'agent:ass:main'",
            "passed": correct_key_format_ass,
            "detail": f"Found valid session send to agent:ass:main in log" if correct_key_format_ass else "No valid sessions_send with key 'agent:ass:main' found in sent_messages.log"
        })
        if correct_key_format_ass:
            total_score += 0.15

        checks.append({
            "name": "sessions_send called with correct key 'agent:ops:main'",
            "passed": correct_key_format_ops,
            "detail": f"Found valid session send to agent:ops:main in log" if correct_key_format_ops else "No valid sessions_send with key 'agent:ops:main' found in sent_messages.log"
        })
        if correct_key_format_ops:
            total_score += 0.15

    except Exception as e:
        checks.append({
            "name": "sessions_send call verification",
            "passed": False,
            "detail": f"Error reading sent_messages.log: {e}"
        })

    # -----------------------------------------------------------------------
    # CHECK 5: Report has a summary/aggregation field (Boss Agent role)
    # The report must show Boss-level synthesis, not just raw forwarding
    # -----------------------------------------------------------------------
    has_summary = any(k in report for k in ["summary", "overall_status", "status", "conclusion", "findings", "incident_summary", "overall"])
    has_agents_section = any(k in report for k in ["agents", "agent_reports", "ass_report", "ops_report", "results", "sub_agents"])
    
    check5a_passed = has_summary
    checks.append({
        "name": "Report contains a summary/overall status field",
        "passed": check5a_passed,
        "detail": f"Report keys: {list(report.keys())}" if isinstance(report, dict) else "Report is not a dict"
    })
    if check5a_passed:
        total_score += 0.10

    check5b_passed = has_agents_section
    checks.append({
        "name": "Report contains per-agent findings section",
        "passed": check5b_passed,
        "detail": f"Found agent-specific section in report keys: {list(report.keys())}" if isinstance(report, dict) else "Report is not a dict"
    })
    if check5b_passed:
        total_score += 0.10

    # -----------------------------------------------------------------------
    # CHECK 6: systemctl --user status was checked for agent services
    # We verify this indirectly by checking if the report mentions service
    # running status (active/running) which only comes from systemctl mock
    # -----------------------------------------------------------------------
    has_service_status = any(keyword in report_str for keyword in ["active", "running", "service", "gateway"])
    checks.append({
        "name": "Report reflects service status check (systemctl verification)",
        "passed": has_service_status,
        "detail": "Report contains service status information (active/running)" if has_service_status else "No service status information found in report"
    })
    if has_service_status:
        total_score += 0.05

    # -----------------------------------------------------------------------
    # FINAL SCORING
    # -----------------------------------------------------------------------
    # Require at minimum: file exists + both session sends with correct keys + both agent contents
    critical_passed = (
        check1_passed and
        correct_key_format_ass and
        correct_key_format_ops and
        has_ass_content and
        has_ops_content
    )

    final_score = min(round(total_score, 2), 1.0)

    return {
        "passed": critical_passed and final_score >= 0.60,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Usage: eval_script.py <workspace_dir>"}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))