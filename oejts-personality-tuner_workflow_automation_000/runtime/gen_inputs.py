#!/usr/bin/env python3
"""
Generate the sandbox workspace for the OEJTS Personality Tuner evaluation task.
"""

import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "team/profiles",
    "team/onboarding",
    "docs/internal",
    "docs/processes",
    "config/env",
    "config/integrations",
    "logs/assessments",
    "logs/system",
    "assets/templates",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = {
    "docs/internal/team-norms.md": "# Team Norms\n\nBe kind. Be direct. Be curious.\n",
    "docs/internal/communication-guide.md": "# Communication Guide\n\nPrefer async over sync. Document decisions.\n",
    "docs/processes/onboarding-checklist.md": "# Onboarding Checklist\n\n- [ ] Setup laptop\n- [ ] Meet team\n- [ ] Read docs\n",
    "docs/processes/offboarding.md": "# Offboarding\n\nReturn hardware. Revoke access. Exit interview.\n",
    "config/env/dev.env": "APP_ENV=development\nDEBUG=true\nLOG_LEVEL=debug\n",
    "config/env/prod.env": "APP_ENV=production\nDEBUG=false\nLOG_LEVEL=info\n",
    "config/integrations/slack.json": json.dumps({"webhook": "disabled", "channel": "#general"}, indent=2),
    "config/integrations/jira.json": json.dumps({"project": "ENG", "sprint_length": 14}, indent=2),
    "logs/assessments/session_2024_01.log": "2024-01-15 09:00:00 INFO Assessment session started\n2024-01-15 09:45:00 INFO Session completed\n",
    "logs/system/app.log": "2024-03-01 10:00:00 ERROR null pointer in module X\n2024-03-01 10:01:00 INFO Recovered\n",
    "assets/templates/email-welcome.txt": "Hi {name},\n\nWelcome to the team! We're excited to have you.\n\nBest,\nHR\n",
    "team/onboarding/buddy-program.md": "# Buddy Program\n\nEach new hire is paired with a buddy for 30 days.\n",
    "team/profiles/sample-profile.json": json.dumps({"name": "Alice", "role": "Backend Engineer", "start_date": "2024-01-15"}, indent=2),
}

for rel_path, content in distractors.items():
    fpath = WORKSPACE / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# ── oejts_tuner.py script (the actual skill script) ──────────────────────────
oejts_script = r'''#!/usr/bin/env python3
"""
OEJTS Personality Tuner v1.2
Administer, score, and apply OEJTS personality assessments.
"""
import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# OEJTS 1.2 Scoring constants
# Each question contributes to one of four axes: IE, SN, FT, JP
# Positive weight = increases first letter; negative = increases second
QUESTION_AXES = {
    "Q1":  ("IE",  1), "Q2":  ("IE", -1), "Q3":  ("IE",  1), "Q4":  ("IE", -1),
    "Q5":  ("IE",  1), "Q6":  ("IE", -1), "Q7":  ("IE",  1), "Q8":  ("IE", -1),
    "Q9":  ("SN",  1), "Q10": ("SN", -1), "Q11": ("SN",  1), "Q12": ("SN", -1),
    "Q13": ("SN",  1), "Q14": ("SN", -1), "Q15": ("SN",  1), "Q16": ("SN", -1),
    "Q17": ("FT",  1), "Q18": ("FT", -1), "Q19": ("FT",  1), "Q20": ("FT", -1),
    "Q21": ("FT",  1), "Q22": ("FT", -1), "Q23": ("FT",  1), "Q24": ("FT", -1),
    "Q25": ("JP",  1), "Q26": ("JP", -1), "Q27": ("JP",  1), "Q28": ("JP", -1),
    "Q29": ("JP",  1), "Q30": ("JP", -1), "Q31": ("JP",  1), "Q32": ("JP", -1),
}

BEHAVIOR_MAPPING = {
    "I": "Favor async communication; allow thinking time before responses.",
    "E": "Engage proactively; offer elaboration and collaborative brainstorming.",
    "S": "Emphasize concrete facts, step-by-step instructions, and practical examples.",
    "N": "Embrace big-picture framing, analogies, and conceptual exploration.",
    "F": "Prioritize empathy signals; acknowledge feelings before facts.",
    "T": "Lead with logic and objective analysis; minimize emotional framing.",
    "J": "Provide structured plans with clear deadlines and defined outcomes.",
    "P": "Offer flexible options; avoid rigid prescriptions.",
}

def compute_scores(answers: dict) -> dict:
    """Compute raw axis scores and derive type letters."""
    axes = {"IE": 0, "SN": 0, "FT": 0, "JP": 0}
    counts = {"IE": 0, "SN": 0, "FT": 0, "JP": 0}

    for qkey, value in answers.items():
        if qkey not in QUESTION_AXES:
            continue
        axis, weight = QUESTION_AXES[qkey]
        axes[axis] += weight * (value - 3)  # centre on 3
        counts[axis] += 1

    # Normalise to [-1, 1]
    normalised = {}
    for axis, raw in axes.items():
        n = counts[axis] if counts[axis] > 0 else 1
        normalised[axis] = raw / (n * 2)  # max deviation is 2 per Q

    # Derive letters
    letters = {
        "IE": "I" if normalised["IE"] >= 0 else "E",
        "SN": "S" if normalised["SN"] >= 0 else "N",
        "FT": "F" if normalised["FT"] >= 0 else "T",
        "JP": "J" if normalised["JP"] >= 0 else "P",
    }
    type_code = letters["IE"] + letters["SN"] + letters["FT"] + letters["JP"]

    # Confidence: average absolute normalised score
    confidence = sum(abs(v) for v in normalised.values()) / 4

    return {
        "raw_axes": axes,
        "normalised": normalised,
        "letters": letters,
        "type_code": type_code,
        "confidence": round(confidence, 4),
        "scored_at": datetime.utcnow().isoformat() + "Z",
    }

def build_profile_block(scores: dict) -> str:
    tc = scores["type_code"]
    letters = scores["letters"]
    conf = scores["confidence"]
    prefs = [BEHAVIOR_MAPPING[letters["IE"]],
             BEHAVIOR_MAPPING[letters["SN"]],
             BEHAVIOR_MAPPING[letters["FT"]],
             BEHAVIOR_MAPPING[letters["JP"]]]
    lines = [
        "<!-- OJTS_PROFILE_START -->",
        f"## Personality Profile (OEJTS 1.2)",
        f"",
        f"**Type:** {tc}  ",
        f"**Confidence:** {conf:.2%}  ",
        f"**Scored:** {scores['scored_at']}  ",
        f"",
        f"### Dimension Scores",
        f"| Axis | Normalised | Letter |",
        f"|------|-----------|--------|",
    ]
    for axis in ["IE", "SN", "FT", "JP"]:
        v = scores["normalised"][axis]
        l = scores["letters"][axis]
        lines.append(f"| {axis} | {v:+.4f} | {l} |")
    lines += ["", "### Interaction Preferences", ""]
    for p in prefs:
        lines.append(f"- {p}")
    lines += ["", "<!-- OJTS_PROFILE_END -->"]
    return "\n".join(lines) + "\n"

def build_adaptation_block(scores: dict) -> str:
    tc = scores["type_code"]
    letters = scores["letters"]
    lines = [
        "<!-- OJTS_ADAPTATION_START -->",
        f"## Personality-Aware Adaptation ({tc})",
        f"",
        f"Adapt assistant soul behavior for type **{tc}**:",
        f"",
    ]
    for axis_key, letter in letters.items():
        lines.append(f"- **{axis_key} → {letter}**: {BEHAVIOR_MAPPING[letter]}")
    lines += [
        "",
        "> Override: User explicit feedback always supersedes this profile.",
        "",
        "<!-- OJTS_ADAPTATION_END -->",
    ]
    return "\n".join(lines) + "\n"

def update_managed_block(content: str, new_block: str, start_marker: str, end_marker: str) -> str:
    """Replace or append managed block."""
    if start_marker in content and end_marker in content:
        before = content[:content.index(start_marker)]
        after = content[content.index(end_marker) + len(end_marker):]
        # Strip leading newline from after if present
        if after.startswith("\n"):
            after = after[1:]
        return before + new_block + after
    else:
        if not content.endswith("\n"):
            content += "\n"
        return content + "\n" + new_block

def cmd_template(args):
    questions = [
        "Q1: I prefer working in groups rather than alone. (1=Strongly Disagree, 5=Strongly Agree)",
        "Q2: I find large social gatherings draining.",
        "Q3: I enjoy being the center of attention.",
        "Q4: I prefer quiet time to recharge after social events.",
        "Q5: I find it easy to approach strangers.",
        "Q6: I need time alone to think through decisions.",
        "Q7: I enjoy meeting new people regularly.",
        "Q8: I prefer depth over breadth in relationships.",
        "Q9: I focus on present realities more than future possibilities.",
        "Q10: I enjoy abstract theories and speculative ideas.",
        "Q11: I trust direct experience over theory.",
        "Q12: I find patterns and symbols more interesting than facts.",
        "Q13: I prefer concrete instructions to open-ended guidance.",
        "Q14: I enjoy exploring 'what if' scenarios.",
        "Q15: I notice practical details others might miss.",
        "Q16: I tend to think about implications and meanings.",
        "Q17: I make decisions based on personal values over logic.",
        "Q18: I prefer objective analysis when solving problems.",
        "Q19: I consider how decisions affect people's feelings.",
        "Q20: I find logical consistency more important than harmony.",
        "Q21: I am moved by artistic or emotional expression.",
        "Q22: I stay calm and detached in emotionally charged situations.",
        "Q23: I prioritize compassion over impartiality.",
        "Q24: I believe truth matters more than tact.",
        "Q25: I like to have things settled and decided.",
        "Q26: I prefer keeping options open rather than committing early.",
        "Q27: I find comfort in structured routines.",
        "Q28: I enjoy spontaneous changes in plans.",
        "Q29: I prefer clear deadlines and organised workflows.",
        "Q30: I like to adapt as I go rather than plan ahead.",
        "Q31: I feel uneasy when things are left open-ended.",
        "Q32: I find rigid schedules constraining.",
    ]
    if args.format == "markdown":
        print("# OEJTS 1.2 Questionnaire\n")
        print("Rate each statement from **1** (Strongly Disagree) to **5** (Strongly Agree).\n")
        for q in questions:
            print(f"- {q}")
    else:
        for q in questions:
            print(q)

def cmd_score(args):
    answers = json.loads(args.answers_json)
    # Validate
    for k, v in answers.items():
        if not (1 <= int(v) <= 5):
            print(f"ERROR: Answer for {k} must be 1-5, got {v}", file=sys.stderr)
            sys.exit(1)
    answers = {k: int(v) for k, v in answers.items()}
    scores = compute_scores(answers)
    print(json.dumps(scores, indent=2))

def cmd_apply(args):
    answers = json.loads(args.answers_json)
    answers = {k: int(v) for k, v in answers.items()}
    scores = compute_scores(answers)

    workspace = Path(args.workspace)
    user_md = workspace / "USER.md"
    soul_md = workspace / "SOUL.md"

    # Read existing
    user_content = user_md.read_text() if user_md.exists() else ""
    soul_content = soul_md.read_text() if soul_md.exists() else ""

    profile_block = build_profile_block(scores)
    adaptation_block = build_adaptation_block(scores)

    new_user = update_managed_block(user_content, profile_block,
                                    "<!-- OJTS_PROFILE_START -->", "<!-- OJTS_PROFILE_END -->")
    new_soul = update_managed_block(soul_content, adaptation_block,
                                    "<!-- OJTS_ADAPTATION_START -->", "<!-- OJTS_ADAPTATION_END -->")

    if args.dry_run:
        print("=== DRY RUN: USER.md ===")
        print(new_user)
        print("=== DRY RUN: SOUL.md ===")
        print(new_soul)
    else:
        user_md.write_text(new_user)
        soul_md.write_text(new_soul)
        print(f"Applied personality profile ({scores['type_code']}) to {user_md} and {soul_md}")

def main():
    parser = argparse.ArgumentParser(description="OEJTS Personality Tuner")
    subparsers = parser.add_subparsers(dest="command")

    # template
    p_template = subparsers.add_parser("template")
    p_template.add_argument("--format", choices=["markdown", "plain"], default="plain")

    # score
    p_score = subparsers.add_parser("score")
    p_score.add_argument("--answers-json", required=True)

    # apply
    p_apply = subparsers.add_parser("apply")
    p_apply.add_argument("--workspace", required=True)
    p_apply.add_argument("--answers-json", required=True)
    p_apply.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    if args.command == "template":
        cmd_template(args)
    elif args.command == "score":
        cmd_score(args)
    elif args.command == "apply":
        cmd_apply(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
'''

(WORKSPACE / "scripts" / "oejts_tuner.py").write_text(oejts_script)

# ── References ───────────────────────────────────────────────────────────────
oejts_ref = """# OEJTS 1.2 Reference

## Items and Axes

Each of the 32 items is assigned to one of four axes (IE, SN, FT, JP).
Items Q1-Q8 → IE axis
Items Q9-Q16 → SN axis
Items Q17-Q24 → FT axis
Items Q25-Q32 → JP axis

## Scoring Formula

For each item, the raw contribution is: weight × (answer − 3)
Weights are +1 or −1 depending on item polarity (see script).
Normalised score = raw_sum / (item_count × 2)

## Type Letter Assignment

- IE: normalised ≥ 0 → I, else → E
- SN: normalised ≥ 0 → S, else → N
- FT: normalised ≥ 0 → F, else → T
- JP: normalised ≥ 0 → J, else → P

## Confidence

Average absolute normalised score across all four axes.
"""

behavior_ref = """# Behavior Mapping

## Type-to-Behavior Guidance

| Letter | Behavior Preference |
|--------|---------------------|
| I | Favor async communication; allow thinking time before responses. |
| E | Engage proactively; offer elaboration and collaborative brainstorming. |
| S | Emphasize concrete facts, step-by-step instructions, and practical examples. |
| N | Embrace big-picture framing, analogies, and conceptual exploration. |
| F | Prioritize empathy signals; acknowledge feelings before facts. |
| T | Lead with logic and objective analysis; minimize emotional framing. |
| J | Provide structured plans with clear deadlines and defined outcomes. |
| P | Offer flexible options; avoid rigid prescriptions. |

## Adaptive Guidance

Use personality as a preference signal. Always allow user overrides.
Managed blocks protect existing content in USER.md and SOUL.md.
"""

(WORKSPACE / "references" / "oejts-1.2.md").write_text(oejts_ref)
(WORKSPACE / "references" / "behavior-mapping.md").write_text(behavior_ref)

# ── Pre-existing USER.md and SOUL.md with existing content to preserve ───────
user_md_content = """# User Profile

## Personal Information

**Name:** Jordan Kim  
**Role:** Senior Software Engineer  
**Team:** Platform Infrastructure  
**Location:** Remote (UTC+9)  

## Work Preferences

- Prefers Slack for async communication
- Core hours: 10:00–18:00 local time
- Uses VSCode with Vim keybindings

## Technical Stack

- Primary: Go, Kubernetes, Terraform
- Secondary: Python, Bash
- Databases: PostgreSQL, Redis

## Current Projects

- Project Atlas: Multi-region failover redesign
- Project Beacon: Internal developer platform

## Notes

This profile is maintained by the onboarding system.
Do not edit the managed section below manually.
"""

soul_md_content = """# Assistant Soul Configuration

## Core Directives

1. Be concise and technically precise.
2. Acknowledge uncertainty explicitly.
3. Cite sources when available.
4. Never fabricate API references or documentation.

## Communication Style

- Default tone: professional and direct
- Code blocks for all code samples
- Use headers for multi-part answers

## Domain Expertise Weighting

- Software Engineering: HIGH
- DevOps/Infrastructure: HIGH
- Product Management: MEDIUM
- General Knowledge: MEDIUM

## Existing Behavioral Notes

- Jordan has requested reduced emoji usage
- Prefers British English spelling
- Avoid marketing language

## Version

soul-config v2.3 | last updated: 2024-11-01
"""

(WORKSPACE / "USER.md").write_text(user_md_content)
(WORKSPACE / "SOUL.md").write_text(soul_md_content)

# ── The assessment answers file (raw, messy format) ─────────────────────────
# These answers are provided as a CSV-like text that the agent must parse
# and convert to the correct JSON format. The answers are for a strongly
# Introverted, iNtuitive, Thinking, Judging (INTJ) profile.
# IE: Q1=1,Q2=5,Q3=1,Q4=5,Q5=2,Q6=5,Q7=1,Q8=5 => IE axis: all strongly I
# SN: Q9=1,Q10=5,Q11=1,Q12=5,Q13=1,Q14=5,Q15=2,Q16=5 => all strongly N
# FT: Q17=1,Q18=5,Q19=1,Q20=5,Q21=1,Q22=5,Q23=1,Q24=5 => all strongly T
# JP: Q25=5,Q26=1,Q27=5,Q28=1,Q29=5,Q30=1,Q31=5,Q32=1 => all strongly J
raw_answers = """Jordan Kim - OEJTS 1.2 Self-Assessment Results
Completed: 2024-11-15

Question, Response
Q1, 1
Q2, 5
Q3, 1
Q4, 5
Q5, 2
Q6, 5
Q7, 1
Q8, 5
Q9, 1
Q10, 5
Q11, 1
Q12, 5
Q13, 1
Q14, 5
Q15, 2
Q16, 5
Q17, 1
Q18, 5
Q19, 1
Q20, 5
Q21, 1
Q22, 5
Q23, 1
Q24, 5
Q25, 5
Q26, 1
Q27, 5
Q28, 1
Q29, 5
Q30, 1
Q31, 5
Q32, 1

Notes: Jordan completed this assessment during onboarding week.
"""

(WORKSPACE / "team" / "onboarding" / "jordan_assessment_raw.txt").write_text(raw_answers)

# ── Task brief ────────────────────────────────────────────────────────────────
task_brief = """# Onboarding Task: AI Assistant Configuration for Jordan Kim

A completed personality self-assessment has been filed at:
  team/onboarding/jordan_assessment_raw.txt

Your task is to configure the AI assistant's workspace behavior files
(USER.md and SOUL.md) for Jordan based on these assessment results.

The assessment answers must be processed through the personality scoring
toolchain available in this workspace. Existing content in both files
must be preserved.
"""
(WORKSPACE / "team" / "onboarding" / "TASK_BRIEF.txt").write_text(task_brief)

print("Workspace generated successfully.")
print(f"Files created in: {WORKSPACE}")