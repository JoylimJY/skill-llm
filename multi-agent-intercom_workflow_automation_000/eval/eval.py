import sys
import json
import os
import re
from pathlib import Path

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    
    checks = []
    
    # -----------------------------------------------------------------------
    # CHECK 1: SOP block was appended to agents/alpha/AGENTS.md
    # -----------------------------------------------------------------------
    alpha_agents_md = workspace / "agents/alpha/AGENTS.md"
    sop_in_alpha = False
    alpha_detail = ""
    try:
        content = alpha_agents_md.read_text(encoding="utf-8")
        # Must contain key SOP markers
        has_receiving = "RECEIVING MESSAGES" in content
        has_anti_loop = "Anti-Loop" in content or "anti-loop" in content.lower() or "loop" in content.lower()
        has_from_agent = "[From Agent" in content
        has_protocol_version = "Protocol Version" in content or "1.0.0" in content
        
        sop_in_alpha = has_receiving and has_anti_loop and has_from_agent and has_protocol_version
        alpha_detail = (
            f"has_receiving={has_receiving}, has_anti_loop={has_anti_loop}, "
            f"has_from_agent={has_from_agent}, has_protocol_version={has_protocol_version}"
        )
    except FileNotFoundError:
        alpha_detail = "agents/alpha/AGENTS.md not found"
    except Exception as e:
        alpha_detail = f"Error reading file: {e}"
    
    checks.append({
        "name": "SOP block appended to agents/alpha/AGENTS.md",
        "passed": sop_in_alpha,
        "detail": alpha_detail
    })
    
    # -----------------------------------------------------------------------
    # CHECK 2: A send-queue JSON file was created in data/queue/
    # The file must have target=alpha, sender=beta (correct order)
    # -----------------------------------------------------------------------
    queue_dir = workspace / "data" / "queue"
    sent_files = list(queue_dir.glob("sent_*.json"))
    
    send_executed = False
    correct_target = False
    correct_sender = False
    correct_arg_order = False
    send_detail = ""
    
    # Look through all sent_*.json files
    best_payload = None
    try:
        for f in sorted(sent_files):
            try:
                payload = json.loads(f.read_text(encoding="utf-8"))
                # We need target=alpha, sender=beta
                if payload.get("target", "").lower() == "alpha":
                    best_payload = payload
                    break
            except Exception:
                continue
        
        if best_payload:
            send_executed = True
            correct_target = best_payload.get("target", "").lower() == "alpha"
            correct_sender = best_payload.get("sender", "").lower() == "beta"
            # The formatted message must have [From Agent beta]
            formatted = best_payload.get("formatted", "")
            correct_arg_order = (
                correct_target and 
                correct_sender and
                "[From Agent beta]" in formatted
            )
            send_detail = (
                f"target={best_payload.get('target')}, sender={best_payload.get('sender')}, "
                f"formatted='{formatted[:80]}'"
            )
        else:
            send_detail = f"No sent_*.json file found with target=alpha. Files found: {[f.name for f in sent_files]}"
    except Exception as e:
        send_detail = f"Error scanning queue: {e}"
    
    checks.append({
        "name": "send command executed (queue file created)",
        "passed": send_executed,
        "detail": send_detail
    })
    
    checks.append({
        "name": "correct argument order: target=alpha, sender=beta",
        "passed": correct_arg_order,
        "detail": send_detail
    })
    
    # -----------------------------------------------------------------------
    # CHECK 3: Message content is meaningful (not empty, not a test stub)
    # -----------------------------------------------------------------------
    message_meaningful = False
    message_detail = ""
    try:
        if best_payload:
            msg = best_payload.get("message", "")
            # Must be non-empty and contain some word about documentation/update/review
            # (the task is about telling alpha to update/review something)
            message_meaningful = len(msg.strip()) >= 10
            message_detail = f"message length={len(msg)}, preview='{msg[:100]}'"
        else:
            message_detail = "No valid payload found"
    except Exception as e:
        message_detail = f"Error: {e}"
    
    checks.append({
        "name": "message content is non-trivial (>= 10 chars)",
        "passed": message_meaningful,
        "detail": message_detail
    })
    
    # -----------------------------------------------------------------------
    # CHECK 4: setup subcommand was used (NOT install)
    # We verify indirectly — the SOP block that only `setup` prints must be in AGENTS.md
    # Also check that the agent did NOT try to use an 'install' subcommand that errors
    # We check by looking at the intercom script behavior
    # -----------------------------------------------------------------------
    setup_not_install = False
    setup_detail = ""
    try:
        # The SOP block in alpha's AGENTS.md is only produced by `setup`, not `install`
        # If SOP is present, setup was used correctly
        if sop_in_alpha:
            setup_not_install = True
            setup_detail = "SOP block present in AGENTS.md — confirms 'setup' subcommand was used (not 'install')"
        else:
            setup_detail = "SOP block missing — 'setup' was either not run or wrong subcommand used"
    except Exception as e:
        setup_detail = f"Error: {e}"
    
    checks.append({
        "name": "correct 'setup' subcommand used (not 'install')",
        "passed": setup_not_install,
        "detail": setup_detail
    })
    
    # -----------------------------------------------------------------------
    # CHECK 5: The [From Agent <sender>] formatting convention was applied
    # -----------------------------------------------------------------------
    formatting_correct = False
    formatting_detail = ""
    try:
        if best_payload:
            formatted = best_payload.get("formatted", "")
            # Must follow "[From Agent <sender_id>] <original_message>"
            pattern = r'^\[From Agent \w+\] .+'
            formatting_correct = bool(re.match(pattern, formatted))
            formatting_detail = f"formatted='{formatted[:100]}'"
        else:
            formatting_detail = "No payload available to check formatting"
    except Exception as e:
        formatting_detail = f"Error: {e}"
    
    checks.append({
        "name": "[From Agent <id>] formatting convention applied",
        "passed": formatting_correct,
        "detail": formatting_detail
    })
    
    # -----------------------------------------------------------------------
    # Final score
    # -----------------------------------------------------------------------
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total
    all_passed = passed_count == total
    
    result = {
        "passed": all_passed,
        "score": round(score, 4),
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()