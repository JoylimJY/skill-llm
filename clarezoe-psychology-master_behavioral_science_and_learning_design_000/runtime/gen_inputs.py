import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")

# ── Directory Structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "company_data/hr",
    "company_data/marketing",
    "company_data/product",
    "outputs",
    "archive/2023",
    "archive/2022",
    "internal/drafts",
    "internal/reviews",
]
for d in dirs:
    Path(WORKSPACE, d).mkdir(parents=True, exist_ok=True)

# ── Core SKILL.md scripts (simulate real tools) ──────────────────────────────

learner_assessment = '''\
#!/usr/bin/env python3
"""Learner profile assessment tool."""
import argparse
import json
import sys

def assess(age, skill, context):
    profiles = {
        ("coding", "work"): {
            "developmental_stage": "Early Adulthood (26-64)",
            "prior_knowledge_assumed": "low",
            "recommended_approach": "Efficiency-first with deliberate practice",
            "time_budget_recommendation": "45-60 min/day, 5 days/week",
            "primary_motivation_type": "Extrinsic (career advancement)",
            "key_frameworks": ["Deliberate Practice", "Spaced Repetition", "Project-Based Learning"],
            "risk_factors": ["Context-switching fatigue", "Imposter syndrome", "Time scarcity"],
            "scaffolding_level": "High initial scaffolding, gradual fade",
        }
    }
    key = (skill.lower(), context.lower())
    base = profiles.get(key, {
        "developmental_stage": f"Adult ({age})",
        "prior_knowledge_assumed": "unknown",
        "recommended_approach": "Balanced exploration and practice",
        "time_budget_recommendation": "30-60 min/day",
        "primary_motivation_type": "Mixed",
        "key_frameworks": ["Spaced Repetition", "Active Recall"],
        "risk_factors": ["Inconsistent practice"],
        "scaffolding_level": "Moderate",
    })
    base["age"] = age
    base["skill"] = skill
    base["context"] = context
    return base

parser = argparse.ArgumentParser(description="Learner profile assessment")
parser.add_argument("--age", type=int, required=True)
parser.add_argument("--skill", type=str, required=True)
parser.add_argument("--context", type=str, required=True)
args = parser.parse_args()

result = assess(args.age, args.skill, args.context)
print(json.dumps(result, indent=2))
'''

conversion_audit = '''\
#!/usr/bin/env python3
"""Conversion funnel audit tool."""
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("--funnel", type=str, required=True)
parser.add_argument("--segment", type=str, required=True)
args = parser.parse_args()

result = {
    "funnel": args.funnel,
    "segment": args.segment,
    "drop_off_rate": "68%",
    "primary_friction_points": ["Long form", "Unclear value proposition", "No social proof above fold"],
    "recommended_levers": ["Risk reduction (free trial)", "Social proof", "Progress indicators"],
    "psychological_stage": "Consideration -> Decision",
    "key_jtbd": "Get promoted by demonstrating data skills",
}
print(json.dumps(result, indent=2))
'''

bias_detector = '''\
#!/usr/bin/env python3
"""Bias detection in marketing copy."""
import argparse
import json
import sys

DARK_PATTERNS = [
    ("guaranteed", "Overstatement risk — requires evidence qualification"),
    ("limited time", "Artificial scarcity — verify if genuinely limited"),
    ("everyone is", "Bandwagon fallacy — sweeping generalization"),
    ("you must", "High-pressure language — consider softening"),
    ("don\'t miss out", "FOMO manipulation — ensure offer is genuine"),
    ("risk-free", "Ambiguous promise — define clearly what is risk-free"),
    ("instantly", "Unrealistic expectation — clarify actual timeline"),
    ("only idiots", "Disparagement — remove immediately"),
]

parser = argparse.ArgumentParser()
parser.add_argument("--copy", type=str, required=True)
args = parser.parse_args()

try:
    with open(args.copy, "r") as f:
        text = f.read().lower()
except FileNotFoundError:
    print(json.dumps({"error": f"File not found: {args.copy}"}))
    sys.exit(1)

issues = []
for phrase, note in DARK_PATTERNS:
    if phrase.lower() in text:
        issues.append({"phrase": phrase, "issue": note, "severity": "medium" if "remove" not in note else "high"})

result = {
    "copy_file": args.copy,
    "issues_found": len(issues),
    "ethical_status": "PASS" if len(issues) == 0 else "NEEDS_REVIEW",
    "issues": issues,
    "recommendation": "Revise flagged phrases before publication" if issues else "Copy cleared for use",
}
print(json.dumps(result, indent=2))
'''

search_script = '''\
#!/usr/bin/env python3
"""Search reference files."""
import argparse
import os
import re
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--query", type=str, required=True)
parser.add_argument("--ignore-case", action="store_true")
args = parser.parse_args()

refs_dir = Path(__file__).parent.parent / "references"
flags = re.IGNORECASE if args.ignore_case else 0
results = []
for f in refs_dir.glob("*.md"):
    content = f.read_text()
    if re.search(args.query, content, flags):
        lines = [l for l in content.splitlines() if re.search(args.query, l, flags)]
        results.append({"file": str(f.name), "matches": lines[:3]})

for r in results:
    print(f"[{r[\'file\']}]")
    for m in r[\'matches\']:
        print(f"  {m.strip()}")
'''

scripts = {
    "scripts/learner_assessment.py": learner_assessment,
    "scripts/conversion_audit.py": conversion_audit,
    "scripts/bias_detector.py": bias_detector,
    "scripts/search.py": search_script,
}
for path, content in scripts.items():
    with open(Path(WORKSPACE, path), "w") as f:
        f.write(content)
    os.chmod(Path(WORKSPACE, path), 0o755)

# ── Reference files ──────────────────────────────────────────────────────────
refs = {
    "references/learning-development.md": """\
# Learning Development Reference

## Age Band: 26-64 (Working Adults)
- Efficiency-first: adults prefer learning tied to immediate application
- Constraint-aware: must fit within real-life time budgets
- Transfer learning: connect new skills to existing knowledge
- Metacognition: self-monitoring and reflection essential
- Motivation: predominantly extrinsic (career), can be cultivated intrinsically

## Scaffolding Protocol
1. Provide high structure initially
2. Fade scaffolding as competence grows
3. Use worked examples before problem-solving

## Spaced Repetition Windows
- Day 1, Day 3, Day 7, Day 14, Day 30
""",
    "references/skill-acquisition.md": """\
# Skill Acquisition Reference

## Programming (Adult Learners)
- Start with concrete problems, not abstract syntax
- Project-based learning accelerates retention
- Pair reading with immediate application (< 20 min lag)
- Deliberate practice: identify weakest sub-skills, isolate for drill
- Feedback loop: automated tests provide immediate feedback

## Languages
- Immersion + spaced repetition hybrid most effective
- Emotional engagement accelerates vocabulary retention

## Mathematics
- Conceptual understanding before procedural fluency
""",
    "references/motivation-frameworks.md": """\
# Motivation Frameworks

## Self-Determination Theory (SDT)
- Autonomy: learner controls pace and path
- Competence: frequent small wins build confidence
- Relatedness: peer cohort and social learning

## Goal-Setting (SMART + Implementation Intentions)
- Specific micro-goals beat vague aspirations
- "When X happens, I will do Y" — implementation intentions reduce drop-off

## Habit Formation
- Cue → Routine → Reward loop
- Habit stacking: attach new habit to existing one
- 66-day average formation period for complex habits
""",
    "references/cognitive-systems.md": """\
# Cognitive Systems Reference

## Memory
- Working memory: 4±1 chunks
- Encoding: elaborative interrogation, self-explanation
- Retrieval: testing effect — retrieval > re-reading
- Spacing effect: distributed practice superior to massed

## Attention
- Cognitive load theory: avoid split-attention effect
- Dual-task interference: minimize notifications during learning

## Decision
- Status quo bias: default options drive behavior
- Loss aversion: 2:1 ratio (losses hurt more than gains feel good)
""",
    "references/marketing-psychology.md": """\
# Marketing Psychology Reference

## JTBD (Jobs-to-be-Done)
- Functional job: the task the customer hires the product for
- Emotional job: how they want to feel
- Social job: how they want to be perceived
- Frame messaging around JTBD, not features

## Behavioral Economics
- Anchoring: first number seen sets reference point
- Decoy effect: add inferior option to make target option attractive
- Framing: "90% success rate" beats "10% failure rate"

## Persuasion Science (Cialdini)
- Reciprocity, Commitment/Consistency, Social Proof, Authority, Liking, Scarcity
- All applications must be ethical and truthful
""",
    "references/conversion-optimization.md": """\
# Conversion Optimization Reference

## Funnel Psychology
- Awareness: capture attention with relevance, not interruption
- Consideration: reduce cognitive load, provide comparisons
- Decision: remove friction, add reassurance
- Post-purchase: set expectations, prevent buyer's remorse

## Friction Reduction
- Each form field costs ~5% conversion
- Progress indicators increase completion by 28%
- Social proof near CTA increases conversion 15-35%

## Risk Reduction Tactics
- Free trial (no credit card) removes top objection
- Money-back guarantee reduces loss aversion
- Testimonials from similar personas increase trust
""",
    "references/customer-psychology.md": """\
# Customer Psychology Reference

## Customer Journey Touchpoints
- Pre-awareness: problem recognition
- Awareness: solution discovery
- Evaluation: comparison and trust-building
- Purchase: decision moment
- Onboarding: first-value delivery
- Loyalty: habit and advocacy

## Persona-Based Messaging
- Match language to customer's own vocabulary
- Mirror the emotional state at each touchpoint
- B2B buyers: rational justification wraps emotional decision
""",
    "references/safety-ethics.md": """\
# Safety & Ethics Reference

## Ethical Validation Checklist
- No deception: all claims must be verifiable
- No dark patterns: no hidden costs, forced continuity, or bait-and-switch
- Transparent value exchange: user understands what they give and get
- User empowerment preserved: easy opt-out, no lock-in traps
- Vulnerable populations: extra care with financial or health claims

## Manipulation vs. Persuasion
- Persuasion: presents true information to help rational decision
- Manipulation: exploits cognitive biases against user's own interests
- Test: "Would the user feel tricked if they knew the technique?" → If yes, it's manipulation
""",
    "references/social-psychology.md": "# Social Psychology\n## Social Proof\n- Conformity: people follow group norms\n- Peer influence strongest in uncertainty\n",
    "references/personality-psychology.md": "# Personality Psychology\n## Big Five (OCEAN)\n- Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism\n",
    "references/ux-psychology.md": "# UX Psychology\n## Fitts Law, Hick's Law, Miller's Law applied to interface design\n",
    "references/emotional-intelligence.md": "# Emotional Intelligence\n## Goleman model: self-awareness, self-regulation, empathy, social skills\n",
    "references/neuropsychology-basics.md": "# Neuropsychology Basics\n## Neuroplasticity: brain changes with deliberate practice\n## Sleep consolidation: critical for skill retention\n",
    "references/communication-psychology.md": "# Communication Psychology\n## Active listening, nonverbal cues, feedback models\n",
    "references/negotiation-psychology.md": "# Negotiation Psychology\n## BATNA, anchoring, concession patterns\n",
    "references/color-psychology.md": "# Color Psychology\n## Blue: trust. Red: urgency. Green: go/safety. Orange: energy\n",
    "references/sleep-circadian.md": "# Sleep & Circadian Rhythms\n## Peak cognitive performance: 90-120 min after waking\n## Sleep consolidates procedural and declarative memory\n",
    "references/creativity-psychology.md": "# Creativity Psychology\n## Incubation effect, divergent/convergent thinking, SCAMPER\n",
    "references/stress-resilience.md": "# Stress & Resilience\n## Yerkes-Dodson curve: moderate arousal optimal for learning\n## Chronic stress impairs hippocampal memory consolidation\n",
    "references/organizational-psychology.md": "# Organizational Psychology\n## Psychological safety, growth mindset culture, distributed leadership\n",
}
for path, content in refs.items():
    with open(Path(WORKSPACE, path), "w") as f:
        f.write(content)

# ── The MESSY raw marketing copy (target for bias detection) ─────────────────
marketing_copy = """\
CodeBoost Enterprise — The Only Platform Your Team Will Ever Need

Guaranteed to transform your workforce in 30 days or less.
Don't miss out — this offer expires soon (limited time deal!).
Everyone is switching to data skills — don't let your team fall behind.
Our learners instantly become productive Python developers.
With CodeBoost, you MUST act now before your competitors do.
Risk-free signup — get started today.

Join 10,000+ enterprise teams who trust CodeBoost.
HR leaders who don't invest in upskilling are being left behind.
"""

with open(Path(WORKSPACE, "company_data/marketing/signup_funnel_copy_v3.txt"), "w") as f:
    f.write(marketing_copy)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = {
    "company_data/hr/employee_survey_2023.csv": "employee_id,satisfaction,training_hours\n1001,4.2,12\n1002,3.8,8\n1003,4.5,20\n",
    "company_data/hr/onboarding_checklist.txt": "Day 1: IT setup\nDay 2: Team intro\nDay 3: Product walkthrough\n",
    "company_data/product/feature_roadmap_q4.json": json.dumps({"q4_features": ["AI tutor", "Progress dashboard", "Slack integration"]}),
    "company_data/product/nps_scores.csv": "month,nps\n2024-01,42\n2024-02,45\n2024-03,38\n",
    "archive/2023/old_curriculum_v1.md": "# OLD Curriculum\nThis is outdated. Do not use.\n",
    "archive/2022/budget_proposal.txt": "Training budget 2022: $120,000\n",
    "internal/drafts/q1_okrs_draft.txt": "OKR1: Increase course completion rate to 70%\nOKR2: Reduce churn by 15%\n",
    "internal/reviews/design_review_notes.txt": "UX review: signup form too long, needs A/B test\n",
    "outputs/.gitkeep": "",
}
for path, content in distractors.items():
    full_path = Path(WORKSPACE, path)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Files created in: {WORKSPACE}")