import sys
import json
import os
import re
from pathlib import Path

workspace = sys.argv[1]
checks = []

def make_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

# -------------------------------------------------------
# Locate the agent's output file
# -------------------------------------------------------
output_file = None
candidates = list(Path(workspace).rglob("relay_session.md"))
if not candidates:
    # Also accept .txt fallback but penalize
    candidates = list(Path(workspace).rglob("relay_session.txt"))

if candidates:
    output_file = candidates[0]
    content = output_file.read_text(errors="replace")
else:
    content = ""

file_found = output_file is not None
checks.append(make_check(
    "relay_session.md file exists",
    file_found,
    f"Found at {output_file}" if file_found else "relay_session.md not found anywhere in workspace"
))

# -------------------------------------------------------
# Check 1: SETUP_NEEDED flow was handled
# (agent must have called config root with the dev_projects path)
# -------------------------------------------------------
state_file = Path(workspace) / "scripts" / ".cc_state"
try:
    state_content = state_file.read_text()
    configured = "configured=true" in state_content
    root_line = [l for l in state_content.splitlines() if l.startswith("root=")]
    root_path = root_line[0].split("=", 1)[1].strip() if root_line else ""
    
    # Root must point to a real directory containing the projects
    root_points_to_projects = "dev_projects" in root_path or (
        os.path.isdir(root_path) and any(
            p in os.listdir(root_path) 
            for p in ["ledger-api", "fraud-detector", "payment-gateway", "audit-service", "compliance-bot"]
            if os.path.isdir(root_path)
        )
    )
    
    checks.append(make_check(
        "config root was set correctly (SETUP_NEEDED flow)",
        configured and root_points_to_projects,
        f"configured={configured}, root='{root_path}', points_to_projects={root_points_to_projects}"
    ))
except Exception as e:
    checks.append(make_check(
        "config root was set correctly (SETUP_NEEDED flow)",
        False,
        f"Could not read state file: {e}"
    ))

# -------------------------------------------------------
# Check 2: Session was started for payment-gateway
# -------------------------------------------------------
try:
    state_content = state_file.read_text()
    # The agent should have started payment-gateway session at some point
    # We check the output file for evidence of session start
    session_started_in_output = False
    if content:
        session_started_in_output = (
            "payment-gateway" in content and
            ("Claude Code session started" in content or "SESSION_STARTED" in content or "✅" in content)
        )
    
    checks.append(make_check(
        "Session started for payment-gateway project",
        session_started_in_output,
        f"Output contains session start confirmation for payment-gateway: {session_started_in_output}"
    ))
except Exception as e:
    checks.append(make_check(
        "Session started for payment-gateway project",
        False,
        f"Error checking session start: {e}"
    ))

# -------------------------------------------------------
# Check 3: Relay message was forwarded (not answered by agent directly)
# The output must show evidence the message was relayed, not self-answered
# -------------------------------------------------------
try:
    # The long output contains specific text from the mock
    relay_evidence = False
    if content:
        # The mock output contains "PCI-DSS" and "payment_core/transaction_handler"
        relay_evidence = (
            "PCI-DSS" in content or
            "transaction_handler" in content or
            "Compliance scan complete" in content or
            "files scanned" in content
        )
    
    checks.append(make_check(
        "Claude Code output was relayed (not self-answered)",
        relay_evidence,
        f"Output contains relay content from mock Claude Code: {relay_evidence}"
    ))
except Exception as e:
    checks.append(make_check(
        "Claude Code output was relayed (not self-answered)",
        False,
        f"Error: {e}"
    ))

# -------------------------------------------------------
# Check 4: Output truncation applied correctly (>4000 chars rule)
# Must NOT contain the full output verbatim (all 79 scanning lines)
# Must contain the exact "Full output: send /cc tail to see more" phrase
# -------------------------------------------------------
try:
    if not content:
        raise ValueError("No content to check")
    
    # Count how many "Scanning module" lines appear — full output has 79
    scan_lines = re.findall(r'\[\d{3}\] Scanning module:', content)
    has_full_dump = len(scan_lines) >= 79
    
    has_truncation_notice = "Full output: send /cc tail to see more" in content
    
    # The summary should contain first meaningful paragraph
    has_first_para = "Analyzing payment-gateway codebase" in content or "PCI-DSS compliance" in content
    
    # Last 10 lines of the mock output should be present
    last_10_markers = [
        "Compliance scan complete",
        "Total files scanned: 79",
        "Critical issues found: 0",
        "Warnings: 3",
        "Warning: Deprecated TLS",
        "Warning: Hardcoded timeout",
        "Warning: Missing input validation",
        "Recommendation: Address warnings",
        "Session complete"
    ]
    last_10_present = sum(1 for m in last_10_markers if m in content)
    
    truncation_correct = (
        not has_full_dump and
        has_truncation_notice and
        has_first_para and
        last_10_present >= 5  # at least 5 of last-10 markers
    )
    
    checks.append(make_check(
        "Output truncation applied correctly (>4000 char rule)",
        truncation_correct,
        (
            f"has_full_dump={has_full_dump} (scan_lines={len(scan_lines)}), "
            f"has_truncation_notice={has_truncation_notice}, "
            f"has_first_para={has_first_para}, "
            f"last_10_present={last_10_present}/9"
        )
    ))
except Exception as e:
    checks.append(make_check(
        "Output truncation applied correctly (>4000 char rule)",
        False,
        f"Error: {e}"
    ))

# -------------------------------------------------------
# Check 5: Acknowledgment signal (⏳) present before relay output
# The agent must emit ⏳ BEFORE forwarding
# -------------------------------------------------------
try:
    if not content:
        raise ValueError("No content")
    
    has_pending_signal = "⏳" in content
    
    # ⏳ should appear before the relay output content
    pending_idx = content.find("⏳")
    relay_content_idx = content.find("PCI-DSS") if "PCI-DSS" in content else content.find("Compliance scan")
    
    order_correct = (
        has_pending_signal and
        relay_content_idx != -1 and
        pending_idx < relay_content_idx
    )
    
    checks.append(make_check(
        "⏳ acknowledgment appears before relay output",
        order_correct,
        f"⏳ at index {pending_idx}, relay content at index {relay_content_idx}, order_correct={order_correct}"
    ))
except Exception as e:
    checks.append(make_check(
        "⏳ acknowledgment appears before relay output",
        False,
        f"Error: {e}"
    ))

# -------------------------------------------------------
# Check 6: Session stop was performed
# -------------------------------------------------------
try:
    if not content:
        raise ValueError("No content")
    
    session_stopped = (
        "Session ended" in content or
        "back to normal chat" in content or
        "SESSION_STOPPED" in content or
        "/cc off" in content.lower()
    )
    
    checks.append(make_check(
        "Session was stopped after relay",
        session_stopped,
        f"Evidence of session stop in output: {session_stopped}"
    ))
except Exception as e:
    checks.append(make_check(
        "Session was stopped after relay",
        False,
        f"Error: {e}"
    ))

# -------------------------------------------------------
# Final scoring
# -------------------------------------------------------
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4)
overall_passed = passed_count >= 5  # Must pass at least 5 of 7 checks

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))