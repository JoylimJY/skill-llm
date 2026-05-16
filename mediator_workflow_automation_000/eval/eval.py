#!/usr/bin/env python3
"""
Evaluation script for the mediator skill task.
Checks:
1. mediator.yaml exists at ~/.clawdbot/mediator.yaml with correct structure
2. Contact "Jordan Blake" is configured with correct fields (intercept mode, facts-only, draft)
3. Global settings (archive_originals: true, notify_channel present)
4. A summary output file exists and contains correct mediator output format
5. The summary is in intercept mode (original archived marker) and facts-only format
"""
import sys
import os
import json
import yaml
from pathlib import Path

def load_yaml_safe(path):
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f), None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except yaml.YAMLError as e:
        return None, f"YAML parse error: {e}"
    except Exception as e:
        return None, f"Unexpected error reading {path}: {e}"

def find_summary_file(workspace):
    """Look for any output summary file the agent may have created."""
    candidates = []
    search_dirs = [
        workspace,
        os.path.expanduser("~/.clawdbot"),
        os.path.expanduser("~/"),
    ]
    for base in search_dirs:
        if not os.path.exists(base):
            continue
        for root, dirs, files in os.walk(base):
            for fname in files:
                if any(kw in fname.lower() for kw in ['summary', 'mediator', 'jordan', 'output', 'result', 'processed']):
                    full = os.path.join(root, fname)
                    if full.endswith(('.txt', '.md', '.out', '.json')):
                        candidates.append(full)
    # Also check workspace root directly
    for f in Path(workspace).glob("*.txt"):
        if f.name != "incoming_message.txt" and f not in candidates:
            candidates.append(str(f))
    for f in Path(workspace).glob("*.md"):
        candidates.append(str(f))
    return candidates

def check_summary_content(content):
    """Check the summary content for required mediator output fields."""
    checks = {}
    content_lower = content.lower()
    
    # Must have intercept mode marker
    checks['has_intercept_marker'] = (
        'intercept' in content_lower or
        'archived' in content_lower or
        '[intercepted' in content_lower
    )
    
    # Must mention Jordan Blake as contact
    checks['mentions_contact'] = 'jordan' in content_lower or 'jordan blake' in content_lower
    
    # Must have action required field (facts-only format)
    checks['has_action_required'] = 'action required' in content_lower
    
    # Must have requests/request section
    checks['has_request_section'] = (
        '**request' in content_lower or
        'request:' in content_lower or
        'requests:' in content_lower or
        '- transfer' in content_lower or
        '- send' in content_lower
    )
    
    # Must have suggested response
    checks['has_suggested_response'] = (
        'suggested response' in content_lower or
        '**suggested' in content_lower
    )
    
    # Should NOT contain raw emotional language (facts-only strips it)
    emotional_phrases = [
        'cannot believe', 'i honestly cannot', 
        'absolutely unacceptable', 'after everything',
    ]
    has_emotional = any(phrase in content_lower for phrase in emotional_phrases)
    checks['no_raw_emotion'] = not has_emotional
    
    # Should mention money amount ($14,750) or deadline
    checks['has_financial_fact'] = (
        '$14,750' in content or '14750' in content or
        '14,750' in content
    )
    
    return checks

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/home/user/workspace"
    checks = []
    total_score = 0.0
    max_score = 0.0

    # ===== CHECK 1: mediator.yaml exists at correct path =====
    config_path = os.path.expanduser("~/.clawdbot/mediator.yaml")
    config, err = load_yaml_safe(config_path)
    
    check_config_exists = {
        "name": "mediator_yaml_at_correct_path",
        "passed": config is not None,
        "detail": f"~/.clawdbot/mediator.yaml {'found' if config is not None else f'NOT found — {err}'}"
    }
    checks.append(check_config_exists)
    max_score += 1.0
    if config is not None:
        total_score += 1.0

    # ===== CHECK 2: Global settings correct =====
    archive_ok = False
    notify_ok = False
    if config is not None:
        try:
            mediator_cfg = config.get('mediator', {})
            archive_ok = mediator_cfg.get('archive_originals') is True
            notify_ok = mediator_cfg.get('notify_channel') in ['telegram', 'slack', 'imessage']
        except Exception as e:
            pass
    
    checks.append({
        "name": "global_archive_originals_true",
        "passed": archive_ok,
        "detail": f"archive_originals: {'true (correct)' if archive_ok else 'missing or false'}"
    })
    checks.append({
        "name": "global_notify_channel_set",
        "passed": notify_ok,
        "detail": f"notify_channel: {'set to valid value' if notify_ok else 'missing or invalid value'}"
    })
    max_score += 2.0
    if archive_ok: total_score += 1.0
    if notify_ok: total_score += 1.0

    # ===== CHECK 3: Jordan Blake contact configured =====
    jordan_contact = None
    if config is not None:
        try:
            contacts = config.get('mediator', {}).get('contacts', []) or []
            for c in contacts:
                if c.get('name', '').lower() in ['jordan blake', 'jordan']:
                    jordan_contact = c
                    break
        except Exception as e:
            pass
    
    checks.append({
        "name": "jordan_blake_contact_exists",
        "passed": jordan_contact is not None,
        "detail": f"Contact 'Jordan Blake' {'found' if jordan_contact else 'NOT found'} in contacts list"
    })
    max_score += 1.0
    if jordan_contact is not None:
        total_score += 1.0

    # ===== CHECK 4: Contact has correct email =====
    correct_email = False
    if jordan_contact:
        email = jordan_contact.get('email', '')
        correct_email = email == 'jordan@blakeventures.com'
    
    checks.append({
        "name": "jordan_blake_correct_email",
        "passed": correct_email,
        "detail": f"Email: {jordan_contact.get('email', 'NOT SET') if jordan_contact else 'contact missing'} (expected: jordan@blakeventures.com)"
    })
    max_score += 1.0
    if correct_email: total_score += 1.0

    # ===== CHECK 5: Mode is 'intercept' =====
    correct_mode = False
    if jordan_contact:
        mode = jordan_contact.get('mode', '')
        correct_mode = mode == 'intercept'
    
    checks.append({
        "name": "jordan_blake_mode_intercept",
        "passed": correct_mode,
        "detail": f"mode: {jordan_contact.get('mode', 'NOT SET') if jordan_contact else 'contact missing'} (expected: intercept — hides originals)"
    })
    max_score += 1.5
    if correct_mode: total_score += 1.5

    # ===== CHECK 6: Summarize is 'facts-only' =====
    correct_summarize = False
    if jordan_contact:
        summarize = jordan_contact.get('summarize', '')
        correct_summarize = summarize == 'facts-only'
    
    checks.append({
        "name": "jordan_blake_summarize_facts_only",
        "passed": correct_summarize,
        "detail": f"summarize: {jordan_contact.get('summarize', 'NOT SET') if jordan_contact else 'contact missing'} (expected: facts-only — strips emotion)"
    })
    max_score += 1.5
    if correct_summarize: total_score += 1.5

    # ===== CHECK 7: Respond is 'draft' =====
    correct_respond = False
    if jordan_contact:
        respond = jordan_contact.get('respond', '')
        correct_respond = respond == 'draft'
    
    checks.append({
        "name": "jordan_blake_respond_draft",
        "passed": correct_respond,
        "detail": f"respond: {jordan_contact.get('respond', 'NOT SET') if jordan_contact else 'contact missing'} (expected: draft — not auto)"
    })
    max_score += 1.0
    if correct_respond: total_score += 1.0

    # ===== CHECK 8: channels includes 'email' =====
    correct_channels = False
    if jordan_contact:
        channels = jordan_contact.get('channels', [])
        if isinstance(channels, list):
            correct_channels = 'email' in [c.lower() for c in channels]
        elif isinstance(channels, str):
            correct_channels = 'email' in channels.lower()
    
    checks.append({
        "name": "jordan_blake_channels_includes_email",
        "passed": correct_channels,
        "detail": f"channels: {jordan_contact.get('channels', 'NOT SET') if jordan_contact else 'contact missing'} (must include email)"
    })
    max_score += 0.5
    if correct_channels: total_score += 0.5

    # ===== CHECK 9: Summary output file exists with correct content =====
    summary_candidates = find_summary_file(workspace)
    
    summary_content = None
    summary_file_used = None
    
    for candidate in summary_candidates:
        try:
            with open(candidate, 'r') as f:
                content = f.read()
            if len(content) > 50 and ('jordan' in content.lower() or 'action required' in content.lower() or 'intercept' in content.lower()):
                summary_content = content
                summary_file_used = candidate
                break
        except Exception:
            continue
    
    # Also check ~/.clawdbot/ for any summary files
    clawdbot_dir = os.path.expanduser("~/.clawdbot")
    if summary_content is None and os.path.exists(clawdbot_dir):
        for root, dirs, files in os.walk(clawdbot_dir):
            for fname in files:
                if fname != 'mediator.yaml' and not fname.endswith('.log'):
                    try:
                        full = os.path.join(root, fname)
                        with open(full, 'r') as f:
                            content = f.read()
                        if len(content) > 50 and ('jordan' in content.lower() or 'action required' in content.lower()):
                            summary_content = content
                            summary_file_used = full
                            break
                    except Exception:
                        continue
            if summary_content:
                break

    checks.append({
        "name": "summary_output_file_exists",
        "passed": summary_content is not None,
        "detail": f"Summary file {'found at: ' + summary_file_used if summary_content else 'NOT FOUND. Searched ' + str(len(summary_candidates)) + ' candidates.'}"
    })
    max_score += 1.0
    if summary_content is not None:
        total_score += 1.0

    # ===== CHECK 10: Summary content quality checks =====
    if summary_content is not None:
        content_checks = check_summary_content(summary_content)
        
        checks.append({
            "name": "summary_has_intercept_marker",
            "passed": content_checks.get('has_intercept_marker', False),
            "detail": f"Summary {'contains' if content_checks.get('has_intercept_marker') else 'MISSING'} intercept/archived marker (mode=intercept should mark original as archived)"
        })
        max_score += 0.5
        if content_checks.get('has_intercept_marker'): total_score += 0.5

        checks.append({
            "name": "summary_mentions_contact",
            "passed": content_checks.get('mentions_contact', False),
            "detail": f"Summary {'mentions' if content_checks.get('mentions_contact') else 'does NOT mention'} the contact name"
        })
        max_score += 0.5
        if content_checks.get('mentions_contact'): total_score += 0.5

        checks.append({
            "name": "summary_has_action_required_field",
            "passed": content_checks.get('has_action_required', False),
            "detail": f"Summary {'contains' if content_checks.get('has_action_required') else 'MISSING'} Action Required field (facts-only format requirement)"
        })
        max_score += 0.5
        if content_checks.get('has_action_required'): total_score += 0.5

        checks.append({
            "name": "summary_has_request_section",
            "passed": content_checks.get('has_request_section', False),
            "detail": f"Summary {'contains' if content_checks.get('has_request_section') else 'MISSING'} Requests/Request section with extracted action items"
        })
        max_score += 0.5
        if content_checks.get('has_request_section'): total_score += 0.5

        checks.append({
            "name": "summary_has_suggested_response",
            "passed": content_checks.get('has_suggested_response', False),
            "detail": f"Summary {'contains' if content_checks.get('has_suggested_response') else 'MISSING'} Suggested Response (respond=draft setting)"
        })
        max_score += 0.5
        if content_checks.get('has_suggested_response'): total_score += 0.5

        checks.append({
            "name": "summary_no_raw_emotional_content",
            "passed": content_checks.get('no_raw_emotion', False),
            "detail": f"Summary {'correctly strips' if content_checks.get('no_raw_emotion') else 'CONTAINS'} raw emotional language (facts-only mode should strip all emotion)"
        })
        max_score += 1.0
        if content_checks.get('no_raw_emotion'): total_score += 1.0

        checks.append({
            "name": "summary_contains_financial_fact",
            "passed": content_checks.get('has_financial_fact', False),
            "detail": f"Summary {'correctly extracted' if content_checks.get('has_financial_fact') else 'MISSING'} the $14,750 financial request from the message"
        })
        max_score += 1.0
        if content_checks.get('has_financial_fact'): total_score += 1.0
    else:
        # Add failed placeholder checks so score reflects missing summary
        for check_name in ['summary_has_intercept_marker', 'summary_mentions_contact',
                           'summary_has_action_required_field', 'summary_has_request_section',
                           'summary_has_suggested_response', 'summary_no_raw_emotional_content',
                           'summary_contains_financial_fact']:
            checks.append({
                "name": check_name,
                "passed": False,
                "detail": "Cannot evaluate — no summary file found"
            })
            max_score += 0.5 if 'marker' in check_name or 'contact' in check_name or 'request_section' in check_name or 'response' in check_name else (1.0 if 'emotion' in check_name or 'financial' in check_name else 0.5)

    # ===== FINAL SCORING =====
    final_score = total_score / max_score if max_score > 0 else 0.0
    passed = final_score >= 0.70

    result = {
        "passed": passed,
        "score": round(final_score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()