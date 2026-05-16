import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
score = 0.0

def find_file(name_pattern, search_dir=None):
    base = search_dir or workspace
    matches = list(base.rglob(name_pattern))
    return matches[0] if matches else None

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ─────────────────────────────────────────────────
# PART 1: Locate required output files
# ─────────────────────────────────────────────────

weekly_report_file = find_file("weekly_intelligence_report*.json") or find_file("weekly_report*.json") or find_file("weekly_intelligence*.json")
alert_file = find_file("adhoc_alert*.json") or find_file("ad_hoc_alert*.json") or find_file("alert_lexai*.json") or find_file("alert_sig001*.json") or find_file("urgent_alert*.json")
daily_brief_file = find_file("daily_brief*.json") or find_file("daily_brief*.txt")

# Also accept YAML
if not weekly_report_file:
    weekly_report_file = find_file("weekly_intelligence_report*.yaml") or find_file("weekly_report*.yaml")
if not alert_file:
    alert_file = find_file("adhoc_alert*.yaml") or find_file("ad_hoc_alert*.yaml") or find_file("alert*.yaml")
if not daily_brief_file:
    daily_brief_file = find_file("daily_brief*.yaml")

# ─────────────────────────────────────────────────
# CHECK 1: Weekly Intelligence Report exists
# ─────────────────────────────────────────────────
if weekly_report_file is None:
    score += add_check("weekly_report_exists", False, "No weekly intelligence report file found (expected weekly_intelligence_report*.json or similar).")
    weekly_data = None
else:
    score += add_check("weekly_report_exists", True, f"Found weekly report at {weekly_report_file}")
    try:
        with open(weekly_report_file) as f:
            content = f.read()
        # Try JSON first, then YAML
        try:
            weekly_data = json.loads(content)
        except json.JSONDecodeError:
            import yaml
            weekly_data = yaml.safe_load(content)
    except Exception as e:
        weekly_data = None
        add_check("weekly_report_parseable", False, f"Could not parse weekly report: {e}")

# ─────────────────────────────────────────────────
# CHECK 2: Weekly Report has all 4 required sections
# ─────────────────────────────────────────────────
REQUIRED_WEEKLY_SECTIONS = [
    "competitive_landscape_changes",
    "technology_shifts",
    "market_opportunity_assessment",
    "recommended_strategic_actions",
]

SECTION_ALIASES = {
    "competitive_landscape_changes": ["competitive_landscape", "competitive_landscape_changes", "competitor_changes", "competitive_changes", "competitive"],
    "technology_shifts": ["technology_shifts", "tech_shifts", "technology_changes", "technology_shift", "tech_shift"],
    "market_opportunity_assessment": ["market_opportunity_assessment", "market_opportunity", "market_assessment", "market_opportunities"],
    "recommended_strategic_actions": ["recommended_strategic_actions", "strategic_actions", "recommendations", "recommended_actions", "strategic_recommendations"],
}

if weekly_data is not None:
    if isinstance(weekly_data, dict):
        keys_lower = {k.lower().replace(" ", "_"): k for k in weekly_data.keys()}
        missing_sections = []
        for section, aliases in SECTION_ALIASES.items():
            found = any(alias in keys_lower for alias in aliases)
            # Also check raw content string for section headers
            if not found:
                content_str = str(weekly_data).lower()
                found = any(alias.replace("_", " ") in content_str or alias in content_str for alias in aliases)
            if not found:
                missing_sections.append(section)
        if missing_sections:
            score += add_check("weekly_report_sections", False, f"Missing required sections: {missing_sections}. Found keys: {list(weekly_data.keys())}")
        else:
            score += add_check("weekly_report_sections", True, "All 4 required sections present in weekly report.")
    else:
        # It's a string or list - check raw content
        content_str = str(weekly_data).lower()
        missing = [s for s, aliases in SECTION_ALIASES.items() 
                   if not any(a.replace("_"," ") in content_str or a in content_str for a in aliases)]
        if missing:
            score += add_check("weekly_report_sections", False, f"Missing sections in text content: {missing}")
        else:
            score += add_check("weekly_report_sections", True, "All 4 required sections found in report content.")
else:
    score += add_check("weekly_report_sections", False, "Cannot check sections: weekly report not parseable.")

# ─────────────────────────────────────────────────
# CHECK 3: Competitive Analysis Template Applied Correctly
# ─────────────────────────────────────────────────
# Must include all 5 fields for each competitor: Product, Position, Momentum, Threat Level (1-5), Response

TEMPLATE_FIELDS = ["product", "position", "momentum", "threat_level", "response"]
THREAT_LEVEL_ALIASES = ["threat_level", "threat level", "threatlevel"]

def check_competitor_template(data_str, competitor_name):
    data_lower = data_str.lower()
    missing = []
    for field in TEMPLATE_FIELDS:
        field_readable = field.replace("_", " ")
        if field not in data_lower and field_readable not in data_lower:
            missing.append(field)
    has_threat_num = bool(re.search(r'threat[_\s]level["\s:]+([1-5])', data_lower) or 
                          re.search(r'"threat[_\s]?level"\s*:\s*([1-5])', data_lower))
    return missing, has_threat_num

if weekly_data is not None:
    data_str = json.dumps(weekly_data) if isinstance(weekly_data, (dict, list)) else str(weekly_data)
    
    # Check LexAI competitor coverage
    lexai_in_report = "lexai" in data_str.lower()
    score += add_check("lexai_competitor_in_report", lexai_in_report, 
                       "LexAI competitor analysis found in weekly report." if lexai_in_report else "LexAI not mentioned in weekly report.")
    
    # Check ClauseBot coverage
    clausebot_in_report = "clausebot" in data_str.lower()
    score += add_check("clausebot_competitor_in_report", clausebot_in_report,
                       "ClauseBot competitor analysis found in weekly report." if clausebot_in_report else "ClauseBot not mentioned in weekly report.")
    
    # Check template fields present
    missing_fields, has_threat_num = check_competitor_template(data_str, "any")
    if len(missing_fields) <= 1:  # Allow 1 field to use slight variant
        score += add_check("competitor_template_fields", True, f"Competitor analysis template fields present. Minor missing: {missing_fields}")
    else:
        score += add_check("competitor_template_fields", False, f"Missing competitor template fields: {missing_fields}. All 5 required: {TEMPLATE_FIELDS}")
    
    # Threat level must be numeric 1-5
    score += add_check("threat_level_numeric", has_threat_num,
                       "Threat level expressed as numeric 1-5 score." if has_threat_num else "Threat level not found as numeric 1-5 score (required by competitive analysis template).")
else:
    score += add_check("lexai_competitor_in_report", False, "Cannot check: weekly report not parseable.")
    score += add_check("clausebot_competitor_in_report", False, "Cannot check: weekly report not parseable.")
    score += add_check("competitor_template_fields", False, "Cannot check: weekly report not parseable.")
    score += add_check("threat_level_numeric", False, "Cannot check: weekly report not parseable.")

# ─────────────────────────────────────────────────
# CHECK 4: Impact and Confidence ratings (1-5 scale)
# ─────────────────────────────────────────────────
# Decision Support Framework requires impact (1-5) and confidence (1-5)

if weekly_data is not None:
    data_str = json.dumps(weekly_data) if isinstance(weekly_data, (dict, list)) else str(weekly_data)
    has_impact = bool(re.search(r'impact["\s:_]+([1-5])\b', data_str, re.IGNORECASE))
    has_confidence = bool(re.search(r'confidence["\s:_]+([1-5])\b', data_str, re.IGNORECASE))
    score += add_check("impact_rating_1_to_5", has_impact,
                       "Impact rated on 1-5 scale as required by Decision Support Framework." if has_impact else "Impact rating (1-5) not found. Decision Support Framework requires numeric 1-5 impact score.")
    score += add_check("confidence_rating_1_to_5", has_confidence,
                       "Confidence rated on 1-5 scale as required." if has_confidence else "Confidence rating (1-5) not found. Decision Support Framework requires numeric 1-5 confidence score.")
else:
    score += add_check("impact_rating_1_to_5", False, "Cannot check: weekly report not parseable.")
    score += add_check("confidence_rating_1_to_5", False, "Cannot check: weekly report not parseable.")

# ─────────────────────────────────────────────────
# CHECK 5: Signal Classification - Tiers assigned
# ─────────────────────────────────────────────────
# SIG-001 (LexAI launch) = Tier 1 / Direct competitor launch / Immediate CRO briefing / Hours urgency
# SIG-002 (Model release) = Tier 2 / Major technology release / Assess product impact / 24 hours
# SIG-007 (Emerging capability) = Tier 3 / Horizon opportunity / Monthly strategic review / Monthly

if weekly_data is not None:
    data_str = json.dumps(weekly_data) if isinstance(weekly_data, (dict, list)) else str(weekly_data)
    
    # Check tier classification present
    has_tier1 = bool(re.search(r'tier[_\s]*1|tier_1|immediate.*revenue|revenue.*impact', data_str, re.IGNORECASE))
    has_tier2 = bool(re.search(r'tier[_\s]*2|tier_2|strategic.*position', data_str, re.IGNORECASE))
    
    score += add_check("tier1_classification", has_tier1,
                       "Tier 1 (Immediate Revenue Impact) classification applied." if has_tier1 else "Tier 1 classification missing. LexAI launch should be Tier 1: Immediate Revenue Impact.")
    score += add_check("tier2_classification", has_tier2,
                       "Tier 2 (Strategic Positioning) classification applied." if has_tier2 else "Tier 2 classification missing. Model release should be Tier 2: Strategic Positioning.")
    
    # Check CRO briefing mentioned for competitor launch
    has_cro = bool(re.search(r'cro|chief revenue|immediate.*brief', data_str, re.IGNORECASE))
    score += add_check("cro_briefing_for_competitor_launch", has_cro,
                       "CRO briefing recommended for direct competitor launch (correct per Signal Classification Framework)." if has_cro else "CRO briefing not mentioned for competitor launch. Signal Classification Framework requires 'Immediate CRO briefing' for direct competitor launches.")
else:
    score += add_check("tier1_classification", False, "Cannot check: weekly report not parseable.")
    score += add_check("tier2_classification", False, "Cannot check: weekly report not parseable.")
    score += add_check("cro_briefing_for_competitor_launch", False, "Cannot check: weekly report not parseable.")

# ─────────────────────────────────────────────────
# CHECK 6: Ad-Hoc Alert exists and has correct structure
# ─────────────────────────────────────────────────
# Must cover LexAI launch (highest urgency signal: "Hours")
# Must have 3 fields: what happened, impact assessment, recommended action

if alert_file is None:
    score += add_check("adhoc_alert_exists", False, "No ad-hoc alert file found. SIG-001 (LexAI launch) requires an immediate ad-hoc alert.")
    alert_data = None
else:
    score += add_check("adhoc_alert_exists", True, f"Ad-hoc alert found at {alert_file}")
    try:
        with open(alert_file) as f:
            content = f.read()
        try:
            alert_data = json.loads(content)
        except json.JSONDecodeError:
            import yaml
            alert_data = yaml.safe_load(content)
    except Exception as e:
        alert_data = None
        add_check("adhoc_alert_parseable", False, f"Could not parse alert file: {e}")

if alert_data is not None:
    alert_str = json.dumps(alert_data) if isinstance(alert_data, (dict, list)) else str(alert_data)
    alert_lower = alert_str.lower()
    
    # Must cover LexAI
    covers_lexai = "lexai" in alert_lower
    score += add_check("alert_covers_lexai_launch", covers_lexai,
                       "Alert correctly targets LexAI Contract Pro launch." if covers_lexai else "Alert does not mention LexAI. The highest-urgency signal (SIG-001) must trigger the ad-hoc alert.")
    
    # Must have "what happened" 
    has_what = bool(re.search(r'what.{0,20}happened|what_happened|event|incident|trigger', alert_lower))
    score += add_check("alert_has_what_happened", has_what,
                       "Alert includes 'what happened' field as required." if has_what else "Alert missing 'what happened' field. Ad-Hoc Alerts require: what happened, impact assessment, recommended action.")
    
    # Must have "impact assessment"
    has_impact_field = bool(re.search(r'impact.{0,20}assess|impact_assess|assessment', alert_lower))
    score += add_check("alert_has_impact_assessment", has_impact_field,
                       "Alert includes 'impact assessment' field as required." if has_impact_field else "Alert missing 'impact assessment' field.")
    
    # Must have "recommended action"
    has_action = bool(re.search(r'recommend.{0,20}action|recommended_action|action.{0,20}recommend', alert_lower))
    score += add_check("alert_has_recommended_action", has_action,
                       "Alert includes 'recommended action' field as required." if has_action else "Alert missing 'recommended action' field. All 3 Ad-Hoc Alert fields are mandatory.")
    
    # Urgency must be "Hours" for competitor launch
    has_hours_urgency = bool(re.search(r'hour|urgent|immediate|hours', alert_lower))
    score += add_check("alert_hours_urgency", has_hours_urgency,
                       "Alert correctly reflects Hours-level urgency for competitor launch." if has_hours_urgency else "Alert urgency not specified as 'Hours'. Direct competitor launches require Hours urgency per Signal Classification Framework.")
else:
    if alert_file is not None:
        for check_name in ["alert_covers_lexai_launch", "alert_has_what_happened", "alert_has_impact_assessment", "alert_has_recommended_action", "alert_hours_urgency"]:
            score += add_check(check_name, False, "Cannot check: alert file not parseable.")

# ─────────────────────────────────────────────────
# CHECK 7: Daily Brief — 3-5 bullets + 1 recommendation + optional flag
# ─────────────────────────────────────────────────

if daily_brief_file is None:
    score += add_check("daily_brief_exists", False, "No daily brief file found.")
    brief_data = None
else:
    score += add_check("daily_brief_exists", True, f"Daily brief found at {daily_brief_file}")
    try:
        with open(daily_brief_file) as f:
            content = f.read()
        try:
            brief_data = json.loads(content)
        except json.JSONDecodeError:
            try:
                import yaml
                brief_data = yaml.safe_load(content)
            except Exception:
                brief_data = content  # treat as raw text
    except Exception as e:
        brief_data = None

if brief_data is not None:
    brief_str = json.dumps(brief_data) if isinstance(brief_data, (dict, list)) else str(brief_data)
    
    # Count bullet points - look for list items, bullet chars, or array elements
    bullet_count = 0
    if isinstance(brief_data, dict):
        # Look for a "bullets", "key_signals", "highlights" key
        for key in ["bullets", "key_signals", "highlights", "signals", "items", "points"]:
            if key in brief_data and isinstance(brief_data[key], list):
                bullet_count = len(brief_data[key])
                break
        if bullet_count == 0:
            # Count list-type values
            for v in brief_data.values():
                if isinstance(v, list):
                    bullet_count = max(bullet_count, len(v))
    elif isinstance(brief_data, list):
        bullet_count = len(brief_data)
    else:
        # Count lines starting with bullet chars
        bullet_lines = re.findall(r'(?:^|\n)\s*[-•*]\s+\S', brief_str)
        bullet_count = len(bullet_lines)
        # Also count numbered items
        if bullet_count == 0:
            bullet_count = len(re.findall(r'(?:^|\n)\s*\d+\.\s+\S', brief_str))
    
    bullets_ok = 3 <= bullet_count <= 5
    score += add_check("daily_brief_bullet_count", bullets_ok,
                       f"Daily brief has {bullet_count} bullets (valid: 3-5)." if bullets_ok else f"Daily brief has {bullet_count} bullets. Required: exactly 3-5 bullet points per Daily Brief spec.")
    
    # Must have exactly one actionable recommendation
    has_recommendation = bool(re.search(r'recommend|action|suggest', brief_str, re.IGNORECASE))
    score += add_check("daily_brief_has_recommendation", has_recommendation,
                       "Daily brief includes actionable recommendation." if has_recommendation else "Daily brief missing 'one actionable recommendation' (required field in Daily Brief format).")
    
    # Risk or opportunity flag
    has_flag = bool(re.search(r'flag|risk|opportunity', brief_str, re.IGNORECASE))
    score += add_check("daily_brief_has_flag", has_flag,
                       "Daily brief includes risk/opportunity flag." if has_flag else "Daily brief missing risk or opportunity flag (required when applicable).")
else:
    if daily_brief_file is not None:
        for n in ["daily_brief_bullet_count", "daily_brief_has_recommendation", "daily_brief_has_flag"]:
            score += add_check(n, False, "Cannot check: daily brief not parseable.")

# ─────────────────────────────────────────────────
# CHECK 8: Decision Support Framework 5-Step Process
# ─────────────────────────────────────────────────
# The agent must have applied the 5-step process at least for the model release evaluation:
# Gather, Analyze, Assess, Recommend, Monitor

DSF_STEPS = ["gather", "analyze", "assess", "recommend", "monitor"]

all_output = ""
for f in [weekly_report_file, alert_file, daily_brief_file]:
    if f:
        try:
            all_output += open(f).read().lower()
        except Exception:
            pass

steps_found = [step for step in DSF_STEPS if step in all_output]
dsf_ok = len(steps_found) >= 4
score += add_check("decision_support_5_step_process", dsf_ok,
                   f"Decision Support Framework steps found: {steps_found}" if dsf_ok else f"Only {len(steps_found)}/5 Decision Support steps found ({steps_found}). Required: Gather, Analyze, Assess, Recommend, Monitor.")

# ─────────────────────────────────────────────────
# CHECK 9: Horizon scanning signal handled at monthly cadence
# ─────────────────────────────────────────────────
# SIG-007 (multimodal emerging capability) = Tier 3 → Monthly Strategic Review

horizon_handled = bool(re.search(r'horizon|monthly|tier.{0,5}3|emerging.{0,30}capabilit', all_output, re.IGNORECASE))
score += add_check("horizon_signal_tier3_monthly", horizon_handled,
                   "Horizon scanning signal (SIG-007) correctly classified as Tier 3 / monthly cadence." if horizon_handled else "Emerging capability signal (SIG-007 multimodal) not classified as Tier 3 horizon opportunity with monthly review cadence.")

# ─────────────────────────────────────────────────
# Final scoring
# ─────────────────────────────────────────────────
total_checks = len(checks)
passed_checks = sum(1 for c in checks if c["passed"])
final_score = round(passed_checks / total_checks, 3) if total_checks > 0 else 0.0
all_passed = passed_checks == total_checks

result = {
    "passed": all_passed,
    "score": final_score,
    "checks": checks
}

print(json.dumps(result, indent=2))