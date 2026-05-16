import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ─── LOCATE OUTPUT FILES ───────────────────────────────────────────────────────
# 1. Classified signals file
signal_files = list(workspace.rglob("classified_signals*.json")) + \
               list(workspace.rglob("signals_classified*.json")) + \
               list(workspace.rglob("processed_signals*.json"))
classified_signals_file = signal_files[0] if signal_files else None

# 2. Decision evaluation file
decision_files = list(workspace.rglob("decision_evaluation*.json")) + \
                 list(workspace.rglob("DEC-2024-003*.json")) + \
                 list(workspace.rglob("evaluation_DEC*.json")) + \
                 list(workspace.rglob("chapter_editor_eval*.json"))
# Exclude original input file
decision_files = [f for f in decision_files if "raw_signals" not in str(f) and
                  str(f) != str(workspace / "strategy/decisions/DEC-2024-003_chapter_editor.json")]
decision_eval_file = decision_files[0] if decision_files else None

# 3. Ad-hoc alert file
alert_files = list(workspace.rglob("alert*.json")) + \
              list(workspace.rglob("adhoc_alert*.json")) + \
              list(workspace.rglob("*alert*.json")) + \
              list(workspace.rglob("alert*.txt")) + \
              list(workspace.rglob("adhoc*.txt")) + \
              list(workspace.rglob("*SIG-001*.json")) + \
              list(workspace.rglob("*SIG-001*.txt"))
alert_files = [f for f in alert_files if "raw_signals" not in str(f)]
alert_file = alert_files[0] if alert_files else None

# 4. Weekly intelligence report
weekly_files = list(workspace.rglob("weekly_report*.txt")) + \
               list(workspace.rglob("weekly_intel*.txt")) + \
               list(workspace.rglob("weekly_report*.json")) + \
               list(workspace.rglob("weekly_intel*.json")) + \
               list(workspace.rglob("*W03*.txt")) + \
               list(workspace.rglob("*weekly*.txt")) + \
               list(workspace.rglob("*weekly*.json"))
# exclude stale draft and W02
weekly_files = [f for f in weekly_files if "DRAFT" not in f.name and "W02" not in f.name]
weekly_file = weekly_files[0] if weekly_files else None

# ─── CHECK GROUP 1: Signal Classification ─────────────────────────────────────

# SIG-001 (HeyGen competitor launch) must be Tier 1, urgency Hours, CRO briefing
# SIG-002 (frontier model paper) must be Tier 2, urgency 24 hours
# SIG-003 (customer signal / job postings RFP indicator) must be Tier 1, urgency Hours
# SIG-005 (regulatory) must be Tier 2
# SIG-004 (open source HN trending) must be Tier 3

def read_text_or_json(fpath):
    try:
        content = fpath.read_text(encoding="utf-8")
        try:
            return json.loads(content), content
        except json.JSONDecodeError:
            return None, content
    except Exception as e:
        return None, ""

if classified_signals_file:
    data, raw_text = read_text_or_json(classified_signals_file)
    full_text = raw_text.lower()

    # SIG-001 Tier 1 / urgency hours / CRO
    sig001_tier1 = bool(re.search(r'sig.?001.*tier.?1|tier.?1.*sig.?001|tier.*1.*heygen|heygen.*tier.*1', full_text, re.DOTALL))
    sig001_urgency = bool(re.search(r'sig.?001.*hour|hour.*sig.?001|hours.*heygen|heygen.*hours', full_text, re.DOTALL)) or \
                     bool(re.search(r'(sig.?001|heygen).{0,200}(immediate|cro briefing|hours)', full_text, re.DOTALL))
    score += add_check(
        "SIG-001 classified as Tier 1",
        sig001_tier1,
        f"File: {classified_signals_file}. HeyGen competitor launch (SIG-001) must be Tier 1 (Immediate Revenue Impact). Found: {sig001_tier1}",
        0.8
    )
    score += add_check(
        "SIG-001 urgency is 'Hours' and triggers CRO briefing",
        sig001_urgency,
        f"SIG-001 must have urgency 'Hours' and note 'Immediate CRO briefing'. Found pattern: {sig001_urgency}",
        0.8
    )

    # SIG-002 Tier 2 / 24 hours
    sig002_tier2 = bool(re.search(r'sig.?002.*tier.?2|tier.?2.*sig.?002|tier.*2.*ditvideo|deepmind.*tier.*2', full_text, re.DOTALL)) or \
                   bool(re.search(r'(frontier model|deepmind|dit.video).{0,200}tier.{0,30}2', full_text, re.DOTALL))
    sig002_urgency = bool(re.search(r'sig.?002.{0,200}24.?hour|24.?hour.{0,200}sig.?002', full_text, re.DOTALL)) or \
                     bool(re.search(r'(frontier model|deepmind|dit.video).{0,300}24', full_text, re.DOTALL))
    score += add_check(
        "SIG-002 classified as Tier 2",
        sig002_tier2,
        f"Frontier model paper (SIG-002) must be Tier 2 (Strategic Positioning). Found: {sig002_tier2}",
        0.7
    )
    score += add_check(
        "SIG-002 urgency is 24 hours",
        sig002_urgency,
        f"SIG-002 (frontier model) urgency must be '24 hours'. Found: {sig002_urgency}",
        0.5
    )

    # SIG-003 Tier 1 (customer signals/RFPs are Tier 1)
    sig003_tier1 = bool(re.search(r'sig.?003.*tier.?1|tier.?1.*sig.?003', full_text, re.DOTALL)) or \
                   bool(re.search(r'(rfp|customer signal|job posting).{0,200}tier.{0,30}1', full_text, re.DOTALL))
    score += add_check(
        "SIG-003 classified as Tier 1 (customer signal/RFP)",
        sig003_tier1,
        f"Customer signal with RFP indicator (SIG-003) must be Tier 1. Found: {sig003_tier1}",
        0.7
    )

    # SIG-005 Tier 2 (regulatory)
    sig005_tier2 = bool(re.search(r'sig.?005.*tier.?2|tier.?2.*sig.?005', full_text, re.DOTALL)) or \
                   bool(re.search(r'(eu ai act|regulatory|regulation).{0,200}tier.{0,30}2', full_text, re.DOTALL))
    score += add_check(
        "SIG-005 classified as Tier 2 (regulatory)",
        sig005_tier2,
        f"EU AI Act regulatory signal (SIG-005) must be Tier 2. Found: {sig005_tier2}",
        0.7
    )

    # SIG-004 Tier 3
    sig004_tier3 = bool(re.search(r'sig.?004.*tier.?3|tier.?3.*sig.?004', full_text, re.DOTALL)) or \
                   bool(re.search(r'(open.source|github|hackernews|hn).{0,200}tier.{0,30}3', full_text, re.DOTALL))
    score += add_check(
        "SIG-004 classified as Tier 3 (horizon scanning)",
        sig004_tier3,
        f"Open-source GitHub trending signal (SIG-004) must be Tier 3. Found: {sig004_tier3}",
        0.5
    )
else:
    score += add_check("Classified signals file exists", False, "Could not find classified_signals*.json or equivalent file.", 4.0)

# ─── CHECK GROUP 2: Decision Evaluation Matrix (Proprietary Weights) ───────────

WEIGHTS = {
    "revenue_impact_30d": 0.30,
    "revenue_impact_90d": 0.20,
    "competitive_advantage": 0.15,
    "implementation_effort": 0.15,
    "risk_of_disruption": 0.10,
    "strategic_alignment": 0.10,
}

OPTIONS = {
    "A": {"revenue_impact_30d": 1, "revenue_impact_90d": 4, "competitive_advantage": 5,
          "implementation_effort": 2, "risk_of_disruption": 3, "strategic_alignment": 5},
    "B": {"revenue_impact_30d": 3, "revenue_impact_90d": 2, "competitive_advantage": 1,
          "implementation_effort": 4, "risk_of_disruption": 4, "strategic_alignment": 2},
    "C": {"revenue_impact_30d": 2, "revenue_impact_90d": 2, "competitive_advantage": 2,
          "implementation_effort": 5, "risk_of_disruption": 5, "strategic_alignment": 3},
}

def compute_weighted_score(scores):
    return sum(WEIGHTS[k] * v for k, v in scores.items())

expected_scores = {opt: round(compute_weighted_score(scores), 4) for opt, scores in OPTIONS.items()}
# A: 0.30*1 + 0.20*4 + 0.15*5 + 0.15*2 + 0.10*3 + 0.10*5 = 0.30+0.80+0.75+0.30+0.30+0.50 = 2.95
# B: 0.30*3 + 0.20*2 + 0.15*1 + 0.15*4 + 0.10*4 + 0.10*2 = 0.90+0.40+0.15+0.60+0.40+0.20 = 2.65
# C: 0.30*2 + 0.20*2 + 0.15*2 + 0.15*5 + 0.10*5 + 0.10*3 = 0.60+0.40+0.30+0.75+0.50+0.30 = 2.85

if decision_eval_file:
    data, raw_text = read_text_or_json(decision_eval_file)
    full_text = raw_text.lower()

    # Check weighted scores appear with correct values (within 0.05 tolerance)
    def find_score_in_text(text, expected_val):
        patterns = [
            str(round(expected_val, 2)),
            str(round(expected_val, 1)),
            str(int(round(expected_val * 100))),  # e.g. "295" for 2.95
        ]
        for p in patterns:
            if p in text:
                return True
        # Also try regex for decimal
        for tolerance_offset in [-0.05, 0, 0.05]:
            target = expected_val + tolerance_offset
            if str(round(target, 2)) in text or str(round(target, 1)) in text:
                return True
        return False

    score_A_correct = find_score_in_text(raw_text, expected_scores["A"])  # 2.95
    score_B_correct = find_score_in_text(raw_text, expected_scores["B"])  # 2.65
    score_C_correct = find_score_in_text(raw_text, expected_scores["C"])  # 2.85

    score += add_check(
        f"Option A weighted score correct (~{expected_scores['A']})",
        score_A_correct,
        f"Expected Option A weighted score ≈ {expected_scores['A']} using weights: rev30d=30%, rev90d=20%, comp=15%, impl=15%, risk=10%, strat=10%. Found: {score_A_correct}",
        1.2
    )
    score += add_check(
        f"Option B weighted score correct (~{expected_scores['B']})",
        score_B_correct,
        f"Expected Option B weighted score ≈ {expected_scores['B']}. Found: {score_B_correct}",
        1.0
    )
    score += add_check(
        f"Option C weighted score correct (~{expected_scores['C']})",
        score_C_correct,
        f"Expected Option C weighted score ≈ {expected_scores['C']}. Found: {score_C_correct}",
        1.0
    )

    # Winner should be Option A (highest score 2.95)
    winner_A = bool(re.search(r'option.{0,10}a.{0,100}(recommend|winner|highest|best|select)', full_text, re.DOTALL)) or \
               bool(re.search(r'(recommend|winner|highest|best|select).{0,100}option.{0,10}a', full_text, re.DOTALL)) or \
               bool(re.search(r'native.{0,50}(recommend|select|choose|winner)', full_text, re.DOTALL))
    score += add_check(
        "Option A recommended as winner (highest weighted score)",
        winner_A,
        f"Option A has the highest weighted score ({expected_scores['A']}) and should be recommended. Found recommendation for A: {winner_A}",
        1.0
    )

    # RAPID: CIO recommends, CEO decides
    rapid_cio = bool(re.search(r'cio.{0,100}(recommend|propose)', full_text, re.DOTALL)) or \
                bool(re.search(r'(recommend|propose).{0,100}cio', full_text, re.DOTALL))
    rapid_ceo = bool(re.search(r'ceo.{0,100}(decide|final|authority)|arthur.{0,100}(decide|final)', full_text, re.DOTALL))
    score += add_check(
        "RAPID model: CIO role as Recommender noted",
        rapid_cio,
        f"Decision document must identify CIO as Recommender per RAPID model. Found: {rapid_cio}",
        0.8
    )
    score += add_check(
        "RAPID model: CEO (Arthur) as final Decision authority",
        rapid_ceo,
        f"Decision document must identify CEO/Arthur as final Decider per RAPID model. Found: {rapid_ceo}",
        0.8
    )

    # Decision type: Strategic (new product feature) → 72 hours timeline
    strategic_timing = bool(re.search(r'72.?hour|strategic.{0,50}(decision|timeline)|three.day', full_text, re.DOTALL))
    score += add_check(
        "Decision classified as Strategic (72-hour timeline)",
        strategic_timing,
        f"New product feature decision is 'Strategic' type with 72-hour max timeline per Speed of Decision framework. Found: {strategic_timing}",
        0.7
    )

    # Workflow not model warning: must mention building on workflow not model capability
    workflow_trap = bool(re.search(r'workflow.{0,100}(not|vs|over|rather).{0,50}model|build on workflow|model.{0,50}(not|agnostic)', full_text, re.DOTALL)) or \
                   bool(re.search(r'(workflow.*model|saas displacement|wrapper)', full_text, re.DOTALL))
    score += add_check(
        "Strategic warning: build on WORKFLOW not MODEL CAPABILITY",
        workflow_trap,
        f"Decision must reference the 'build on WORKFLOW not MODEL CAPABILITY' principle from competitive framework. Found: {workflow_trap}",
        0.8
    )
else:
    score += add_check("Decision evaluation file exists", False, "Could not find decision evaluation output file.", 7.3)

# ─── CHECK GROUP 3: Ad-Hoc Alert for SIG-001 ──────────────────────────────────

if alert_file:
    data, raw_text = read_text_or_json(alert_file)
    full_text = raw_text.lower()

    alert_what = bool(re.search(r'(what happened|what|heygen|enterprise 2\.?0|script.?to.?video|299)', full_text, re.DOTALL))
    alert_impact = bool(re.search(r'(impact|threat|risk|implication|affect)', full_text, re.DOTALL))
    alert_action = bool(re.search(r'(recommend|action|respond|brief|cro)', full_text, re.DOTALL))
    alert_ceo_cro = bool(re.search(r'(ceo|arthur).{0,50}(cro|chief revenue)|cro.{0,50}(ceo|arthur)', full_text, re.DOTALL)) or \
                    bool(re.search(r'notify.{0,50}(ceo|cro)|(ceo|cro).{0,50}notif', full_text, re.DOTALL))

    score += add_check(
        "Ad-hoc alert contains 'what happened' section",
        alert_what,
        f"Alert must include what happened (HeyGen Enterprise 2.0 launch details). Found: {alert_what}",
        0.8
    )
    score += add_check(
        "Ad-hoc alert contains impact assessment",
        alert_impact,
        f"Alert must include impact assessment per Ad-Hoc Alert format. Found: {alert_impact}",
        0.8
    )
    score += add_check(
        "Ad-hoc alert contains recommended action",
        alert_action,
        f"Alert must include recommended action. Found: {alert_action}",
        0.8
    )
    score += add_check(
        "Ad-hoc alert addressed to CEO + CRO",
        alert_ceo_cro,
        f"Ad-hoc alerts go to CEO + CRO per Intelligence Products spec. Found: {alert_ceo_cro}",
        0.7
    )
else:
    score += add_check("Ad-hoc alert file exists", False, "Could not find alert output file for SIG-001.", 3.1)

# ─── CHECK GROUP 4: Weekly Intelligence Report ────────────────────────────────

if weekly_file:
    data, raw_text = read_text_or_json(weekly_file)
    full_text = raw_text.lower()

    has_competitive = bool(re.search(r'competitive (landscape|change|shift)', full_text))
    has_tech_shifts = bool(re.search(r'technology shift|tech.{0,20}shift|frontier model|research', full_text))
    has_market_opp = bool(re.search(r'market opportunity|opportunity assessment|market.{0,30}opportunit', full_text))
    has_recommended = bool(re.search(r'recommend(ed)? (strategic )?action', full_text))

    score += add_check(
        "Weekly report has 'Competitive landscape changes' section",
        has_competitive,
        f"Weekly Intelligence Report must include 'Competitive landscape changes'. Found: {has_competitive}",
        0.6
    )
    score += add_check(
        "Weekly report has 'Technology shifts affecting products' section",
        has_tech_shifts,
        f"Weekly report must include 'Technology shifts affecting products'. Found: {has_tech_shifts}",
        0.6
    )
    score += add_check(
        "Weekly report has 'Market opportunity assessment' section",
        has_market_opp,
        f"Weekly report must include 'Market opportunity assessment'. Found: {has_market_opp}",
        0.6
    )
    score += add_check(
        "Weekly report has 'Recommended strategic actions' section",
        has_recommended,
        f"Weekly report must include 'Recommended strategic actions'. Found: {has_recommended}",
        0.6
    )
else:
    score += add_check("Weekly intelligence report file exists", False, "Could not find weekly intelligence report file.", 2.4)

# ─── FINAL SCORING ────────────────────────────────────────────────────────────
max_score = (
    0.8 + 0.8 +      # SIG-001 tier + urgency
    0.7 + 0.5 +      # SIG-002 tier + urgency
    0.7 +            # SIG-003 tier
    0.7 +            # SIG-005 tier
    0.5 +            # SIG-004 tier
    1.2 + 1.0 + 1.0 +  # weighted scores A, B, C
    1.0 +            # winner A
    0.8 + 0.8 +      # RAPID roles
    0.7 +            # Strategic 72h
    0.8 +            # workflow not model
    0.8 + 0.8 + 0.8 + 0.7 +  # alert sections
    0.6 + 0.6 + 0.6 + 0.6     # weekly report sections
)

normalized = round(min(score / max_score, 1.0), 4)
passed = normalized >= 0.60

output = {
    "passed": passed,
    "score": normalized,
    "checks": checks
}
print(json.dumps(output, indent=2))