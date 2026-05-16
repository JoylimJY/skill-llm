import sys
import json
import re
from pathlib import Path

workspace = sys.argv[1]

checks = []

def find_output_file(workspace, filename):
    matches = list(Path(workspace).rglob(filename))
    return matches[0] if matches else None

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ── Locate the output file ───────────────────────────────────────────────────
output_file = find_output_file(workspace, "daily_ops_package.md")
if output_file is None:
    check("output_file_exists", False, "File 'daily_ops_package.md' not found anywhere in workspace.")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

try:
    content = output_file.read_text(encoding="utf-8")
except Exception as e:
    check("output_file_readable", False, f"Could not read file: {e}")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

check("output_file_exists", True, f"Found at {output_file}")

content_lower = content.lower()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: DAILY BRIEF STRUCTURE
# ══════════════════════════════════════════════════════════════════════════════

# 1a. Must have a "Daily Brief" heading with a date
has_daily_brief_heading = bool(re.search(r'daily brief', content_lower))
check("daily_brief_heading_present",
      has_daily_brief_heading,
      "Must contain a 'Daily Brief' section heading." if not has_daily_brief_heading else "Found.")

# 1b. Top 3 Priorities section
has_top3 = bool(re.search(r'top\s+3\s+priorit', content_lower))
check("top_3_priorities_section",
      has_top3,
      "Must have a 'Top 3 Priorities' section." if not has_top3 else "Found.")

# 1c. Exactly 3 priorities listed (numbered 1. 2. 3. within or near the Top 3 section)
priority_items = re.findall(r'^\s*[1-3]\.\s+\S', content, re.MULTILINE)
has_three_priorities = len(priority_items) >= 3
check("top_3_priorities_count",
      has_three_priorities,
      f"Found {len(priority_items)} numbered priority items (need ≥3)." if not has_three_priorities else f"Found {len(priority_items)} numbered items.")

# 1d. Next 72h deadlines section
has_72h = bool(re.search(r'72h|72\s+h|next\s+72', content_lower))
check("next_72h_deadlines_section",
      has_72h,
      "Must have a '72h' deadlines/reminders section." if not has_72h else "Found.")

# 1e. Automation suggestion section
has_automation = bool(re.search(r'automation', content_lower))
check("automation_suggestion_present",
      has_automation,
      "Must include an 'Automation Suggestion'." if not has_automation else "Found.")

# 1f. Quick Win (<15 min) section
has_quickwin = bool(re.search(r'quick\s+win|<15\s*min|15\s*min', content_lower))
check("quick_win_present",
      has_quickwin,
      "Must include a 'Quick Win (<15 min)' item." if not has_quickwin else "Found.")

# 1g. "Next action I'll take" closing line
has_next_action_closing = bool(re.search(r"next action i['']ll take|next action i will take", content_lower))
check("next_action_ill_take_closing",
      has_next_action_closing,
      "Must end daily brief with 'Next Action I'll Take' statement." if not has_next_action_closing else "Found.")

# 1h. Key real priorities from inbox are represented
has_eventx_sponsor = bool(re.search(r'sponsor', content_lower))
has_venue_payment = bool(re.search(r'eventY|advance payment|wire|venue.*payment|payment.*venue', content, re.IGNORECASE))
has_catering = bool(re.search(r'ahmad|catering|headcount', content_lower))
priority_coverage = sum([has_eventx_sponsor, has_venue_payment, has_catering])
check("priority_content_from_inbox",
      priority_coverage >= 2,
      f"Priorities must reflect inbox items (sponsorship deck, EventY payment, catering). Found {priority_coverage}/3 coverage." if priority_coverage < 2 else f"Covered {priority_coverage}/3 key items.")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: TRIP OPERATIONS — QUOTE STRUCTURE
# ══════════════════════════════════════════════════════════════════════════════

# 2a. Trip/transport section present
has_trip_section = bool(re.search(r'trip|transport|transfer|kl sentral|putrajaya', content_lower))
check("trip_section_present",
      has_trip_section,
      "Must contain a trip/transport planning section." if not has_trip_section else "Found.")

# 2b. All 6 normalized quote fields present (from transport-procurement.md template)
required_fields = {
    "provider": r'\bprovider\b',
    "price_currency": r'price|myr\s*\d|rm\s*\d|\d+\s*myr',
    "inclusions": r'inclus',
    "exclusions": r'exclus',
    "cancellation_terms": r'cancell?ation',
    "pickup_drop_details": r'pickup|pick.up|drop.off|dropoff|terminal|entrance',
    "confidence_risk": r'confidence|risk|estimated|unconfirmed|pending conf',
}
missing_fields = []
for field, pattern in required_fields.items():
    found = bool(re.search(pattern, content_lower))
    if not found:
        missing_fields.append(field)

check("all_6_quote_fields_present",
      len(missing_fields) == 0,
      f"Missing quote fields: {missing_fields}" if missing_fields else "All 6 normalized quote fields found.")

# 2c. Public transport options sourced FIRST (bus/train/shuttle/ERL/KTM before private)
# Check ordering: public transport keywords appear before private/grab keywords
pub_match = re.search(r'ktm|erl|komuter|shuttle|bus|train', content_lower)
priv_match = re.search(r'grab|private transfer|aziz|taxi|rideshare', content_lower)
public_first = (pub_match and priv_match and pub_match.start() < priv_match.start()) or \
               (pub_match and not priv_match)
check("public_transport_sourced_first",
      bool(pub_match) and public_first,
      "Public transport options (KTM/ERL/shuttle) must appear before private transfers." if not (bool(pub_match) and public_first) else "Public transport listed first.")

# 2d. At least 3 distinct transport options quoted
option_count = len(re.findall(r'option\s+[A-Ca-c]|option\s+[1-3]|\bA\b.*provider|\bB\b.*provider', content, re.IGNORECASE))
# More robust: count provider mentions or option labels
providers_found = len(re.findall(r'(ktm|komuter|erl|grab|aziz|private transfer|shuttle)', content_lower))
check("minimum_3_options_quoted",
      providers_found >= 3,
      f"Found only {providers_found} provider references; need ≥3 distinct options." if providers_found < 3 else f"Found {providers_found} provider references.")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: RECOMMENDATION BLOCK (3-category)
# ══════════════════════════════════════════════════════════════════════════════

has_best_value = bool(re.search(r'best\s+value', content_lower))
has_best_convenience = bool(re.search(r'best\s+convenience', content_lower))
has_best_fallback = bool(re.search(r'best\s+fallback|fallback', content_lower))

check("recommendation_best_value", has_best_value,
      "Must include a 'Best Value' recommendation." if not has_best_value else "Found.")
check("recommendation_best_convenience", has_best_convenience,
      "Must include a 'Best Convenience' recommendation." if not has_best_convenience else "Found.")
check("recommendation_best_fallback", has_best_fallback,
      "Must include a 'Best Fallback' recommendation." if not has_best_fallback else "Found.")

# 3b. Trade-offs stated (one line each) — check that each recommendation section has at least one dash or colon line
# Simple heuristic: after "Best Value" there should be a line with content
tradeoff_pattern = re.search(
    r'best\s+value.*?\n[\-\*\•]?\s*\w.+',
    content_lower, re.DOTALL
)
check("tradeoffs_stated_per_recommendation",
      bool(tradeoff_pattern),
      "Each recommendation category must have a one-line trade-off stated." if not tradeoff_pattern else "Trade-off lines found.")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: DECISION HANDOFF
# ══════════════════════════════════════════════════════════════════════════════

# Must ask for explicit Option A/B/C choice
has_option_abc = bool(re.search(r'option\s+a\s*/\s*option\s+b|option\s+[abc].*option\s+[abc]|choose.*option|please\s+choose', content_lower))
check("decision_handoff_option_abc",
      has_option_abc,
      "Must end trip section with explicit Option A/B/C decision handoff question." if not has_option_abc else "Found.")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5: VENDOR FOLLOW-UP / PENDING LIST
# ══════════════════════════════════════════════════════════════════════════════

# 5a. Vendor pending list present
has_pending_list = bool(re.search(r'pending|vendor.*follow|follow.*up|owner|due\s+date', content_lower))
check("vendor_pending_list_present",
      has_pending_list,
      "Must include a vendor follow-up pending list with owner + due date." if not has_pending_list else "Found.")

# 5b. Key outstanding vendor items are tracked
has_lightworks = bool(re.search(r'lightwork|kl light', content_lower))
has_brightshield = bool(re.search(r'brightshield|insurance', content_lower))
has_ahmad = bool(re.search(r'ahmad|catering', content_lower))
vendor_coverage = sum([has_lightworks, has_brightshield, has_ahmad])
check("vendor_pending_items_from_inbox",
      vendor_coverage >= 2,
      f"Vendor pending list must include key outstanding items from inbox (KL Lightworks, BrightShield, Ahmad Catering). Found {vendor_coverage}/3." if vendor_coverage < 2 else f"Covered {vendor_coverage}/3 vendors.")

# 5c. Reminder/escalation rule mentioned
has_reminder_rule = bool(re.search(r'remind|escalat|day.before|buffer|cutoff', content_lower))
check("reminder_escalation_rule_mentioned",
      has_reminder_rule,
      "Must mention reminder timing rule (day-before buffer) or escalation." if not has_reminder_rule else "Found.")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6: OUTPUT STYLE RULES
# ══════════════════════════════════════════════════════════════════════════════

# 6a. Uncertainty flagged for unconfirmed prices (trip notes say "not sure", "heard")
has_uncertainty_flag = bool(re.search(r'estimated|unconfirmed|\(estimated\)|\(unconfirmed\)|not confirmed|uncertain|approx', content_lower))
check("uncertainty_flagged_for_estimates",
      has_uncertainty_flag,
      "Uncertain/unconfirmed prices must be explicitly flagged (e.g., 'estimated', 'unconfirmed')." if not has_uncertainty_flag else "Found uncertainty flags.")

# 6b. Bullet-first format (leading bullets/dashes in substantial sections)
bullet_lines = re.findall(r'^\s*[-\*\•]\s+\S', content, re.MULTILINE)
check("bullet_first_format_used",
      len(bullet_lines) >= 8,
      f"Bullet-first format required; found only {len(bullet_lines)} bullet lines." if len(bullet_lines) < 8 else f"Found {len(bullet_lines)} bullet lines.")

# ══════════════════════════════════════════════════════════════════════════════
# SCORING
# ══════════════════════════════════════════════════════════════════════════════
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4)
all_passed = passed_count == total

print(json.dumps({
    "passed": all_passed,
    "score": score,
    "checks": checks
}, indent=2))