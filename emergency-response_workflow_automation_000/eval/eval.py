import sys
import os
import json
import csv
import re
from pathlib import Path

workspace = sys.argv[1]

checks = []
total_score = 0.0
max_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global total_score, max_score
    max_score += weight
    if passed:
        total_score += weight

# ── Helper ────────────────────────────────────────────────────────────────────
def find_file(pattern, root=workspace):
    return list(Path(root).rglob(pattern))

def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 1 — Per-ticket response files exist
# ══════════════════════════════════════════════════════════════════════════════

ticket_ids = ["T-2024-1201", "T-2024-1202", "T-2024-1203", "T-2024-1204"]
response_texts = {}

for tid in ticket_ids:
    matches = find_file(f"*{tid}*")
    # Filter to likely response files (not the original CSV)
    matches = [m for m in matches if m.suffix in (".txt", ".md", ".json") and "complaint" not in m.name and "inbox" not in str(m)]
    if matches:
        try:
            response_texts[tid] = read_text(matches[0])
            add_check(f"response_file_exists_{tid}", True, f"Found response file: {matches[0]}", weight=0.5)
        except Exception as e:
            add_check(f"response_file_exists_{tid}", False, f"Could not read file: {e}", weight=0.5)
    else:
        add_check(f"response_file_exists_{tid}", False, f"No response file found for {tid}", weight=0.5)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 2 — Correct Level classification reflected in responses/docs
# ══════════════════════════════════════════════════════════════════════════════

# T-2024-1201: 修正依頼 → Level 2
# T-2024-1202: 返金要求 → Level 3
# T-2024-1203: 質問 → Level 1
# T-2024-1204: アカウント警告・法的言及 → Level 4

level_map = {
    "T-2024-1201": ("2", "Level 2"),
    "T-2024-1202": ("3", "Level 3"),
    "T-2024-1203": ("1", "Level 1"),
    "T-2024-1204": ("4", "Level 4"),
}

# Look for level classification in any output file (response, escalation, or incident log)
all_output_texts = {}
for p in Path(workspace).rglob("*"):
    if p.is_file() and p.suffix in (".txt", ".md", ".json") and "complaint" not in p.name:
        try:
            all_output_texts[str(p)] = read_text(p)
        except:
            pass

combined_output = "\n".join(all_output_texts.values())

for tid, (level_num, level_label) in level_map.items():
    # Check that the correct level appears somewhere in output associated with this ticket
    # We search for the level number near the ticket ID, or in the ticket's own response file
    found_level = False
    search_text = response_texts.get(tid, "") + "\n" + combined_output
    pattern = re.compile(r"[Ll]evel\s*" + level_num + r"|レベル[：:]\s*" + level_num + r"|Level\s+" + level_num, re.IGNORECASE)
    if pattern.search(search_text):
        found_level = True
    add_check(f"level_classification_{tid}", found_level,
              f"{'Correct' if found_level else 'Missing'} Level {level_num} for {tid}", weight=1.0)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 3 — T-2024-1201 uses "原因報告・対応策提示" template structure
# ══════════════════════════════════════════════════════════════════════════════

t1201_text = response_texts.get("T-2024-1201", "")

has_cause_section = bool(re.search(r"【原因】|原因[：:]", t1201_text))
has_fix_section = bool(re.search(r"【対応策】|対応策[：:]", t1201_text))
has_prevention_section = bool(re.search(r"【今後の防止策】|再発防止|防止策", t1201_text))
has_customer_name_t1201 = "田中" in t1201_text

add_check("t1201_cause_section", has_cause_section,
          f"【原因】section present in T-2024-1201 response: {has_cause_section}", weight=1.5)
add_check("t1201_fix_section", has_fix_section,
          f"【対応策】section present: {has_fix_section}", weight=1.0)
add_check("t1201_prevention_section", has_prevention_section,
          f"Prevention section present: {has_prevention_section}", weight=1.0)
add_check("t1201_customer_name", has_customer_name_t1201,
          f"Customer name 田中 present in T-2024-1201 response: {has_customer_name_t1201}", weight=0.5)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 4 — T-2024-1202 (返金要求 / Level 3): must NOT unilaterally promise refund;
#                 must defer to human
# ══════════════════════════════════════════════════════════════════════════════

t1202_text = response_texts.get("T-2024-1202", "")

# Must NOT contain a firm unilateral refund promise
unilateral_refund_patterns = [
    r"返金いたします",
    r"全額返金します",
    r"すぐに返金",
    r"immediately refund",
    r"refund you",
]
has_unilateral_refund = any(re.search(p, t1202_text, re.IGNORECASE) for p in unilateral_refund_patterns)

# Must show deference to human
deference_patterns = [
    r"確認",r"人間", r"担当者", r"上長", r"責任者", r"ご相談", r"判断",
    r"確認の上", r"検討", r"折り返し", r"ご連絡",
]
has_deference = any(re.search(p, t1202_text) for p in deference_patterns)

add_check("t1202_no_unilateral_refund", not has_unilateral_refund,
          f"T-2024-1202 does NOT unilaterally promise refund: {not has_unilateral_refund}", weight=2.0)
add_check("t1202_defers_to_human", has_deference,
          f"T-2024-1202 defers to human consultation: {has_deference}", weight=1.5)
add_check("t1202_customer_name", "佐藤" in t1202_text,
          f"Customer name 佐藤 present in T-2024-1202: {'佐藤' in t1202_text}", weight=0.5)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 5 — Escalation notification file (for Level 3 and Level 4)
# ══════════════════════════════════════════════════════════════════════════════

# Find escalation notification file
escalation_files = find_file("escalation*") + find_file("*escalat*") + find_file("*緊急*") + find_file("*urgent*")
escalation_files = [f for f in escalation_files if f.is_file() and f.suffix in (".txt", ".md", ".json")]

escalation_text = ""
if escalation_files:
    try:
        escalation_text = read_text(escalation_files[0])
        add_check("escalation_file_exists", True, f"Escalation file found: {escalation_files[0]}", weight=1.0)
    except Exception as e:
        add_check("escalation_file_exists", False, f"Error reading escalation file: {e}", weight=1.0)
else:
    add_check("escalation_file_exists", False, "No escalation file found", weight=1.0)

# Escalation file must contain 🚨 emoji
has_emergency_emoji = "🚨" in escalation_text
add_check("escalation_has_emoji", has_emergency_emoji,
          f"Escalation notification contains 🚨 emoji: {has_emergency_emoji}", weight=1.5)

# Must contain 【レベル】 field
has_level_field = bool(re.search(r"【レベル】", escalation_text))
add_check("escalation_has_level_field", has_level_field,
          f"Escalation has 【レベル】 field: {has_level_field}", weight=1.0)

# Must contain 【プラットフォーム】 field
has_platform_field = bool(re.search(r"【プラットフォーム】", escalation_text))
add_check("escalation_has_platform_field", has_platform_field,
          f"Escalation has 【プラットフォーム】 field: {has_platform_field}", weight=1.0)

# Must contain 【内容】 field
has_content_field = bool(re.search(r"【内容】", escalation_text))
add_check("escalation_has_content_field", has_content_field,
          f"Escalation has 【内容】 field: {has_content_field}", weight=1.0)

# Must contain 【詳細】 field
has_detail_field = bool(re.search(r"【詳細】", escalation_text))
add_check("escalation_has_detail_field", has_detail_field,
          f"Escalation has 【詳細】 field: {has_detail_field}", weight=1.0)

# Must contain 【対応案】 field
has_proposal_field = bool(re.search(r"【対応案】", escalation_text))
add_check("escalation_has_proposal_field", has_proposal_field,
          f"Escalation has 【対応案】 field: {has_proposal_field}", weight=1.0)

# Must cover BOTH T-2024-1202 (Level 3) and T-2024-1204 (Level 4)
has_1202_in_escalation = "1202" in escalation_text or "佐藤" in escalation_text or "返金" in escalation_text
has_1204_in_escalation = "1204" in escalation_text or "山本" in escalation_text or "アカウント" in escalation_text or "法的" in escalation_text

add_check("escalation_covers_level3_ticket", has_1202_in_escalation,
          f"Escalation covers T-2024-1202 (Level 3 / 返金要求): {has_1202_in_escalation}", weight=1.5)
add_check("escalation_covers_level4_ticket", has_1204_in_escalation,
          f"Escalation covers T-2024-1204 (Level 4 / 法的リスク): {has_1204_in_escalation}", weight=1.5)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 6 — Incident log JSON with required 7 fields
# ══════════════════════════════════════════════════════════════════════════════

REQUIRED_INCIDENT_FIELDS_JP = {"発生日時", "内容", "原因", "対応内容", "結果", "学び", "再発防止策"}

incident_files = find_file("incident*") + find_file("*incident*") + find_file("*記録*") + find_file("*trouble*") + find_file("*log*")
incident_files = [f for f in incident_files if f.is_file() and f.suffix == ".json"
                  and "app.log" not in f.name and "kpi" not in f.name]

incident_data = None
incident_text = ""
if incident_files:
    try:
        incident_text = read_text(incident_files[0])
        incident_data = json.loads(incident_text)
        add_check("incident_log_exists", True, f"Incident log JSON found: {incident_files[0]}", weight=1.0)
    except json.JSONDecodeError as e:
        add_check("incident_log_exists", False, f"Incident log not valid JSON: {e}", weight=1.0)
    except Exception as e:
        add_check("incident_log_exists", False, f"Error reading incident log: {e}", weight=1.0)
else:
    # Also try txt/md
    incident_files_text = find_file("*incident*") + find_file("*記録*") + find_file("*trouble*")
    incident_files_text = [f for f in incident_files_text if f.is_file() and f.suffix in (".txt", ".md")]
    if incident_files_text:
        try:
            incident_text = read_text(incident_files_text[0])
            add_check("incident_log_exists", True, f"Incident log text found: {incident_files_text[0]}", weight=1.0)
        except Exception as e:
            add_check("incident_log_exists", False, f"Error: {e}", weight=1.0)
    else:
        add_check("incident_log_exists", False, "No incident log file found", weight=1.0)

# Check all 7 required fields are present
search_in_incident = incident_text if incident_text else combined_output
fields_found = {}
for field in REQUIRED_INCIDENT_FIELDS_JP:
    found = field in search_in_incident
    fields_found[field] = found

all_fields_found = all(fields_found.values())
missing = [f for f, v in fields_found.items() if not v]
add_check("incident_has_all_7_fields", all_fields_found,
          f"All 7 required incident fields present. Missing: {missing}", weight=2.0)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 7 — T-2024-1203 (質問 / Level 1): simple, polite, no escalation
# ══════════════════════════════════════════════════════════════════════════════

t1203_text = response_texts.get("T-2024-1203", "")
has_customer_name_t1203 = "鈴木" in t1203_text
is_not_escalated = "1203" not in escalation_text and "鈴木" not in escalation_text

add_check("t1203_customer_name_present", has_customer_name_t1203,
          f"Customer name 鈴木 in T-2024-1203 response: {has_customer_name_t1203}", weight=0.5)
add_check("t1203_not_escalated", is_not_escalated,
          f"T-2024-1203 (Level 1) is NOT incorrectly escalated: {is_not_escalated}", weight=1.0)

# ══════════════════════════════════════════════════════════════════════════════
# FINAL SCORING
# ══════════════════════════════════════════════════════════════════════════════

score = round(total_score / max_score, 4) if max_score > 0 else 0.0
passed = score >= 0.70

result = {
    "passed": passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, ensure_ascii=False, indent=2))