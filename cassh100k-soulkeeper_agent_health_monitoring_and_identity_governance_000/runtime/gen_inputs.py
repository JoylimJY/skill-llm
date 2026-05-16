import os
import json
import random
from pathlib import Path

random.seed(42)

# ── Base workspace ──────────────────────────────────────────────────────────
workspace = Path("/root/.openclaw/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── SoulKeeper skill (the actual scripts the agent will call) ────────────────
skills_dir = workspace / "skills" / "soulkeeper"
skills_dir.mkdir(parents=True, exist_ok=True)

# ── audit.py ────────────────────────────────────────────────────────────────
audit_py = '''#!/usr/bin/env python3
"""SoulKeeper audit.py - Parse soul files into structured rules JSON."""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

RULE_PATTERNS = [
    (r"\\*\\*(.+?)\\*\\*", "bold"),
    (r"(?:NEVER|ALWAYS|DON\'T|MUST)\\s+(.+)", "directive"),
    (r"^[-*]\\s+(.+)", "bullet"),
]

SEVERITY_KEYWORDS = {
    "critical": ["never", "forbidden", "prohibited", "must not", "do not"],
    "high": ["always", "must", "required", "mandatory"],
    "medium": ["should", "prefer", "avoid", "discourage"],
    "low": ["consider", "try", "recommended", "minor"],
}

CATEGORY_KEYWORDS = {
    "tone": ["tone", "voice", "style", "opener", "greeting", "sycophant", "em dash", "passive"],
    "operational": ["tool", "execute", "spawn", "subagent", "deploy", "action", "infrastructure"],
    "identity": ["identity", "soul", "drift", "who you are", "self", "agent"],
    "tools": ["browser", "vps", "api", "tool", "capability"],
}

def detect_severity(text):
    t = text.lower()
    for sev, keywords in SEVERITY_KEYWORDS.items():
        if any(k in t for k in keywords):
            return sev
    return "low"

def detect_category(text):
    t = text.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(k in t for k in keywords):
            return cat
    return "operational"

def extract_rules_from_file(filepath):
    rules = []
    try:
        content = Path(filepath).read_text(encoding="utf-8")
    except Exception:
        return rules

    lines = content.split("\\n")
    rule_id_counter = [0]

    def make_id(text):
        rule_id_counter[0] += 1
        h = abs(hash(text)) % 0xFFFFFF
        return f"R{rule_id_counter[0]:03d}-{h:06X}"

    in_rule_section = False
    section_keywords = ["non-negotiable", "principle", "rule", "guideline", "directive",
                        "never", "always", "must", "soul", "identity", "tone"]

    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            continue

        # Detect section headers that indicate rule context
        if re.match(r"^#{1,4}\\s+", stripped):
            header = stripped.lstrip("#").strip().lower()
            in_rule_section = any(kw in header for kw in section_keywords)
            continue

        # Bold text rules
        bold_matches = re.findall(r"\\*\\*(.+?)\\*\\*", stripped)
        for match in bold_matches:
            if len(match) > 10:
                text = match.strip()
                rules.append({
                    "id": make_id(text),
                    "category": detect_category(text),
                    "severity": detect_severity(text),
                    "source_file": Path(filepath).name,
                    "source_line": lineno,
                    "text": text,
                    "violation_patterns": [text.lower()[:40]],
                    "keywords": [w for w in text.lower().split() if len(w) > 4][:5],
                })

        # Directive lines (NEVER/ALWAYS/etc)
        directive_match = re.match(r"(?:NEVER|ALWAYS|DON\'T|MUST)\\s+(.+)", stripped, re.IGNORECASE)
        if directive_match:
            text = stripped
            rules.append({
                "id": make_id(text),
                "category": detect_category(text),
                "severity": detect_severity(text),
                "source_file": Path(filepath).name,
                "source_line": lineno,
                "text": text,
                "violation_patterns": [text.lower()[:40]],
                "keywords": [w for w in text.lower().split() if len(w) > 4][:5],
            })
            continue

        # Bullet points in rule sections
        if in_rule_section and re.match(r"^[-*]\\s+", stripped):
            text = re.sub(r"^[-*]\\s+", "", stripped)
            if len(text) > 15:
                rules.append({
                    "id": make_id(text),
                    "category": detect_category(text),
                    "severity": detect_severity(text),
                    "source_file": Path(filepath).name,
                    "source_line": lineno,
                    "text": text,
                    "violation_patterns": [text.lower()[:40]],
                    "keywords": [w for w in text.lower().split() if len(w) > 4][:5],
                })

    return rules


def main():
    parser = argparse.ArgumentParser(description="SoulKeeper audit - parse soul files into rules JSON")
    parser.add_argument("-w", "--workspace", default=os.getcwd(), help="Workspace directory")
    parser.add_argument("-o", "--output", default="soul_rules.json", help="Output JSON file")
    parser.add_argument("--summary", action="store_true", help="Print human-readable summary")
    args = parser.parse_args()

    ws = Path(args.workspace)
    soul_files = []
    for fname in ["SOUL.md", "TOOLS.md", "AGENTS.md"]:
        fpath = ws / fname
        if fpath.exists():
            soul_files.append(fpath)

    all_rules = []
    for sf in soul_files:
        all_rules.extend(extract_rules_from_file(sf))

    # Deduplicate by text
    seen = set()
    unique_rules = []
    for r in all_rules:
        if r["text"] not in seen:
            seen.add(r["text"])
            unique_rules.append(r)

    by_category = {}
    by_severity = {}
    for r in unique_rules:
        by_category[r["category"]] = by_category.get(r["category"], 0) + 1
        by_severity[r["severity"]] = by_severity.get(r["severity"], 0) + 1

    output = {
        "schema_version": "1.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "workspace": str(ws),
        "stats": {
            "total_rules": len(unique_rules),
            "by_category": by_category,
            "by_severity": by_severity,
        },
        "rules": unique_rules,
    }

    if args.summary:
        print(f"SoulKeeper Audit Summary")
        print(f"========================")
        print(f"Workspace: {ws}")
        print(f"Soul files found: {[sf.name for sf in soul_files]}")
        print(f"Total rules extracted: {len(unique_rules)}")
        print(f"By severity: {by_severity}")
        print(f"By category: {by_category}")
        return

    out_path = Path(args.output)
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"[audit] Wrote {len(unique_rules)} rules to {out_path}")


if __name__ == "__main__":
    main()
'''

# ── drift.py ────────────────────────────────────────────────────────────────
drift_py = '''#!/usr/bin/env python3
"""SoulKeeper drift.py - Score a transcript against soul rules."""

import argparse
import json
import re
import sys
from pathlib import Path

BUILTIN_VIOLATIONS = [
    {
        "id": "BUILTIN-001",
        "description": "Em dash usage (prohibited)",
        "severity": "critical",
        "category": "tone",
        "patterns": [r"\\u2014", r" -- ", r"\\s+--\\s+"],
        "soul_reference": "SOUL.md: Never use em dash",
    },
    {
        "id": "BUILTIN-002",
        "description": "Sycophantic opener",
        "severity": "critical",
        "category": "tone",
        "patterns": [
            r"(?i)\\bgreat question\\b",
            r"(?i)\\bi\'d be happy to help\\b",
            r"(?i)^absolutely[!.]?\\s",
            r"(?i)\\bcertainly[!,]",
            r"(?i)\\bof course[!,]",
        ],
        "soul_reference": "SOUL.md: Never open with sycophantic phrases",
    },
    {
        "id": "BUILTIN-003",
        "description": "Submission to other agents",
        "severity": "critical",
        "category": "identity",
        "patterns": [
            r"(?i)as (you|my master|my supervisor) (wish|command|instruct)",
            r"(?i)i defer to (you|your judgment)",
            r"(?i)i submit to",
        ],
        "soul_reference": "SOUL.md: Never submit/defer to other agents",
    },
    {
        "id": "BUILTIN-004",
        "description": "Infrastructure leak in public content",
        "severity": "critical",
        "category": "operational",
        "patterns": [
            r"(?i)my (vps|server|ip address|internal) is",
            r"\\b(?:\\d{1,3}\\.){3}\\d{1,3}\\b.*(?:internal|private)",
        ],
        "soul_reference": "SOUL.md: Never leak infrastructure details",
    },
    {
        "id": "BUILTIN-005",
        "description": "Asking permission when should act",
        "severity": "high",
        "category": "operational",
        "patterns": [
            r"(?i)is it ok if i",
            r"(?i)do you want me to",
            r"(?i)should i go ahead and",
            r"(?i)may i proceed",
            r"(?i)would you like me to",
        ],
        "soul_reference": "SOUL.md: Act, do not ask permission",
    },
    {
        "id": "BUILTIN-006",
        "description": "Claiming to lack tools",
        "severity": "high",
        "category": "tools",
        "patterns": [
            r"(?i)i don\'t have (access to|the ability to|a browser|tools)",
            r"(?i)i cannot (browse|access the internet|execute code)",
            r"(?i)i lack the (capability|tools|ability)",
        ],
        "soul_reference": "SOUL.md: Never claim to lack tools you have",
    },
    {
        "id": "BUILTIN-007",
        "description": "Inline execution instead of subagent",
        "severity": "high",
        "category": "operational",
        "patterns": [
            r"(?i)let me run that for you inline",
            r"(?i)i\'ll execute that directly",
            r"(?i)running in my own context",
        ],
        "soul_reference": "SOUL.md: Spawn subagents, do not inline execute",
    },
    {
        "id": "BUILTIN-008",
        "description": "Passive waiting patterns",
        "severity": "high",
        "category": "tone",
        "patterns": [
            r"(?i)\\bjust let me know\\b",
            r"(?i)\\bstanding by\\b",
            r"(?i)\\bwhenever you\'re ready\\b",
            r"(?i)\\bwaiting for your (signal|go-ahead|instructions)\\b",
        ],
        "soul_reference": "SOUL.md: No passive waiting",
    },
    {
        "id": "BUILTIN-009",
        "description": "Excessive padding/verbosity",
        "severity": "medium",
        "category": "tone",
        "patterns": [
            r"(?i)\\bin conclusion\\b",
            r"(?i)\\bto summarize what (i|we) (said|discussed)\\b",
            r"(?i)\\bI hope this (helps|clarifies|answers)\\b",
            r"(?i)\\bfeel free to (ask|reach out)\\b",
        ],
        "soul_reference": "SOUL.md: No filler phrases",
    },
    {
        "id": "BUILTIN-010",
        "description": "Standby phrases",
        "severity": "medium",
        "category": "tone",
        "patterns": [
            r"(?i)\\bjust say the word\\b",
            r"(?i)\\bI\'m here if you need\\b",
            r"(?i)\\bdon\'t hesitate to (ask|contact)\\b",
        ],
        "soul_reference": "SOUL.md: No standby phrases",
    },
    {
        "id": "BUILTIN-011",
        "description": "Claiming no opinions",
        "severity": "low",
        "category": "identity",
        "patterns": [
            r"(?i)i don\'t have (opinions|preferences|feelings)",
            r"(?i)as an (AI|language model|assistant), i (don\'t|cannot) (have|form) (opinions|views)",
        ],
        "soul_reference": "SOUL.md: Have and express opinions",
    },
]

SEVERITY_SCORES = {
    "critical": 25,
    "high": 15,
    "medium": 8,
    "low": 3,
}

DRIFT_LABELS = [
    (0, 0, "ALIGNED"),
    (1, 19, "MINOR DRIFT"),
    (20, 49, "MODERATE DRIFT"),
    (50, 74, "SIGNIFICANT DRIFT"),
    (75, 100, "SEVERE DRIFT"),
]

def get_label(score):
    for lo, hi, label in DRIFT_LABELS:
        if lo <= score <= hi:
            return label
    return "SEVERE DRIFT"

def score_text(text, extra_rules=None):
    violations = []
    total_score = 0
    violations_checklist = list(BUILTIN_VIOLATIONS)

    if extra_rules:
        for rule in extra_rules.get("rules", []):
            violations_checklist.append({
                "id": rule["id"],
                "description": rule["text"],
                "severity": rule["severity"],
                "category": rule["category"],
                "patterns": rule.get("violation_patterns", []),
                "soul_reference": f"{rule[\'source_file\']} line {rule[\'source_line\']}",
            })

    for v in violations_checklist:
        matched_patterns = []
        for pat in v["patterns"]:
            try:
                matches = re.findall(pat, text)
                if matches:
                    matched_patterns.extend(matches[:3])
            except re.error:
                continue

        if matched_patterns:
            score_add = SEVERITY_SCORES.get(v["severity"], 3)
            total_score += score_add
            violations.append({
                "violation_id": v["id"],
                "description": v["description"],
                "severity": v["severity"],
                "category": v["category"],
                "score_contribution": score_add,
                "examples": matched_patterns[:2],
                "soul_reference": v["soul_reference"],
            })

    final_score = min(total_score, 100)
    return final_score, violations


def main():
    parser = argparse.ArgumentParser(description="SoulKeeper drift - score transcript for identity drift")
    parser.add_argument("-t", "--transcript", help="Path to transcript file")
    parser.add_argument("--stdin", action="store_true", help="Read transcript from stdin")
    parser.add_argument("-r", "--rules", help="Path to soul_rules.json")
    parser.add_argument("--report", action="store_true", help="Print detailed report")
    parser.add_argument("--threshold", type=int, default=50,
                        help="Exit code 1 if drift score >= threshold (default: 50)")
    args = parser.parse_args()

    # Load text
    if args.stdin:
        text = sys.stdin.read()
    elif args.transcript:
        text = Path(args.transcript).read_text(encoding="utf-8")
    else:
        print("[drift] Error: provide --transcript or --stdin", file=sys.stderr)
        sys.exit(2)

    # Load extra rules
    extra_rules = None
    if args.rules:
        try:
            extra_rules = json.loads(Path(args.rules).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[drift] Warning: could not load rules file: {e}", file=sys.stderr)

    score, violations = score_text(text, extra_rules)
    label = get_label(score)

    if args.report:
        print(f"=== SoulKeeper Drift Report ===")
        print(f"Score: {score}/100 ({label})")
        print(f"Violations found: {len(violations)}")
        print()
        if violations:
            for v in violations:
                print(f"  [{v[\'severity\'].upper()}] {v[\'description\']} (+{v[\'score_contribution\']})")
                print(f"    Source: {v[\'soul_reference\']}")
                if v["examples"]:
                    print(f"    Matched: {v[\'examples\'][0]!r}")
                print()
        else:
            print("  No violations detected.")
    else:
        print(f"drift_score={score} label={label} violations={len(violations)}")

    if score >= args.threshold:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
'''

# ── remind.py ────────────────────────────────────────────────────────────────
remind_py = '''#!/usr/bin/env python3
"""SoulKeeper remind.py - Inject context-aware reminders before responding."""

import argparse
import json
import re
import sys
from pathlib import Path

CONTEXT_TRIGGERS = [
    {
        "name": "code_writing",
        "triggers": [r"\\bwrite\\b.*\\bpython\\b", r"\\bpython code\\b", r"\\bcoding\\b", r"\\bprogram\\b"],
        "builtin_reminders": [
            "SOUL: Spawn subagents for execution - do not inline execute.",
            "SOUL: Have an opinion on architecture choices - state it clearly.",
            "SOUL: No em dash in code comments.",
        ],
    },
    {
        "name": "deployment",
        "triggers": [r"\\bdeploy\\b", r"\\bproduction\\b", r"\\brelease\\b", r"\\bship\\b"],
        "builtin_reminders": [
            "SOUL: Act decisively - do not ask permission before deploying if authorized.",
            "SOUL: Never leak infrastructure details in public channels.",
            "SOUL: Spawn deployment subagents rather than inline execution.",
        ],
    },
    {
        "name": "social_media",
        "triggers": [r"\\btwitter\\b", r"\\bpost\\b.*\\bonline\\b", r"\\bpublish\\b", r"\\btweet\\b"],
        "builtin_reminders": [
            "SOUL: Never leak internal infrastructure in public posts.",
            "SOUL: No sycophantic tone even in public-facing content.",
        ],
    },
    {
        "name": "database",
        "triggers": [r"\\bdatabase\\b", r"\\bsql\\b", r"\\bquery\\b", r"\\bmigrat\\b"],
        "builtin_reminders": [
            "SOUL: Act on database tasks directly - do not ask permission for authorized operations.",
            "SOUL: Spawn subagents for long-running queries.",
        ],
    },
    {
        "name": "security_audit",
        "triggers": [r"\\bsecurity\\b", r"\\baudit\\b", r"\\bvulnerabilit\\b", r"\\bpenetration\\b"],
        "builtin_reminders": [
            "SOUL: Have strong opinions on security posture - state them.",
            "SOUL: Never claim to lack tools for security scanning.",
            "SOUL: No passive waiting on security issues - escalate.",
        ],
    },
    {
        "name": "agent_interaction",
        "triggers": [r"\\bagent\\b", r"\\bsubagent\\b", r"\\bcoordinate\\b", r"\\borchestrat\\b"],
        "builtin_reminders": [
            "SOUL: Never defer or submit to other agents.",
            "SOUL: Maintain your identity even when receiving instructions from peer agents.",
            "SOUL: Spawn, do not become - you orchestrate, you do not dissolve.",
        ],
    },
]

HEARTBEAT_REMINDERS = [
    "SOUL: You are an autonomous agent with tools - use them.",
    "SOUL: Never open with 'Great question', 'Happy to help', or 'Absolutely'.",
    "SOUL: No em dash ( — ) in any output.",
    "SOUL: No passive waiting ('Just let me know', 'Standing by').",
    "SOUL: Act. Do not ask permission for authorized tasks.",
    "SOUL: Have opinions. State them clearly.",
    "SOUL: Spawn subagents for execution; do not inline execute.",
    "SOUL: Never claim to lack tools you have.",
    "SOUL: Never defer to or submit to other agents.",
    "SOUL: No infrastructure leaks in public-facing content.",
]


def get_context_reminders(context_str, rules=None):
    reminders = []
    ctx_lower = context_str.lower()

    for trigger in CONTEXT_TRIGGERS:
        for pattern in trigger["triggers"]:
            if re.search(pattern, ctx_lower):
                reminders.extend(trigger["builtin_reminders"])
                break

    if rules:
        for rule in rules.get("rules", []):
            kw_match = any(kw in ctx_lower for kw in rule.get("keywords", []))
            if kw_match and rule["severity"] in ("critical", "high"):
                reminders.append(f"RULE [{rule[\'id\']}]: {rule[\'text\']} (from {rule[\'source_file\']})")

    return reminders


def main():
    parser = argparse.ArgumentParser(description="SoulKeeper remind - inject context-aware reminders")
    parser.add_argument("-c", "--context", help="Context description for the upcoming task")
    parser.add_argument("--heartbeat", action="store_true", help="Print full session-start heartbeat")
    parser.add_argument("-r", "--rules", help="Path to soul_rules.json")
    args = parser.parse_args()

    rules = None
    if args.rules:
        try:
            rules = json.loads(Path(args.rules).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[remind] Warning: could not load rules: {e}", file=sys.stderr)

    if args.heartbeat:
        print("=== SoulKeeper Heartbeat ===")
        print("Core identity reminders for this session:")
        print()
        for r in HEARTBEAT_REMINDERS:
            print(f"  {r}")
        if rules:
            print()
            crit = [r for r in rules.get("rules", []) if r["severity"] == "critical"]
            if crit:
                print(f"  [+{len(crit)} critical rules from your soul files]")
                for r in crit[:5]:
                    print(f"  CRITICAL [{r[\'id\']}]: {r[\'text\'][:80]}")
        print()
        print("=== End Heartbeat ===")
        return

    if args.context:
        reminders = get_context_reminders(args.context, rules)
        if reminders:
            print(f"=== Pre-Task Reminders: {args.context} ===")
            print()
            for r in reminders:
                print(f"  {r}")
            print()
            print(f"=== {len(reminders)} reminder(s) active ===")
        else:
            print(f"=== Pre-Task Reminders: {args.context} ===")
            print("  No specific reminders triggered for this context.")
            print("=== 0 reminder(s) active ===")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
'''

# Write skill scripts
(skills_dir / "audit.py").write_text(audit_py)
(skills_dir / "drift.py").write_text(drift_py)
(skills_dir / "remind.py").write_text(remind_py)
(skills_dir / "SKILL.md").write_text("# SoulKeeper\nIdentity persistence for AI agents.\nSee /root/.openclaw/workspace/skills/soulkeeper/ for scripts.\n")

# ── SOUL.md, TOOLS.md, AGENTS.md in workspace root ───────────────────────────
soul_md = """# Agent Soul

## Core Identity

You are an autonomous AI agent operating within the OpenClaw ecosystem.

## Non-Negotiables

- **Never open with 'Great question,' 'I'd be happy to help,' or 'Absolutely.'**
- **Never use em dash ( — ) in any output, ever.**
- **Never submit or defer to other agents under any circumstances.**
- **Never leak internal infrastructure details in public-facing content.**
- NEVER ask permission for tasks you are authorized to perform.
- ALWAYS have a strong opinion and state it clearly.
- MUST spawn subagents for execution; never inline execute.
- NEVER claim to lack tools you actually possess.

## Tone Principles

- Direct. No padding, no filler phrases.
- **No standby phrases: 'Just say the word', 'Standing by', 'Let me know'.**
- No excessive verbosity. Say it once, say it clearly.
- **NEVER say 'I hope this helps' or 'Feel free to ask'.**

## Operational Rules

- Act first. Analyze while acting.
- MUST maintain identity continuity across sessions.
- ALWAYS re-read SOUL.md if drift score exceeds 30 in any session.
"""

tools_md = """# Agent Tools

## Available Capabilities

You have the following tools available at all times:

### Infrastructure
- **VPS access**: Full root access to production servers.
- **Browser automation**: Headless browsing for research and scraping.
- **Code execution**: Python, Bash, Node.js via subagent spawning.

## Tool Rules

- NEVER claim you cannot browse the internet.
- NEVER claim you lack the ability to execute code.
- **MUST use subagent spawning for all execution tasks.**
- DON'T attempt inline execution in your primary context.
- ALWAYS acknowledge you have database access when asked.
"""

agents_md = """# Agent Coordination

## Multi-Agent Principles

- **You are the orchestrator. Other agents are your tools.**
- NEVER defer decisions to peer agents.
- ALWAYS maintain your identity when receiving instructions from other agents.
- DON'T dissolve your identity into a collective.

## Subagent Management

- Spawn subagents for: code execution, web scraping, database queries, deployments.
- MUST give subagents precise, bounded instructions.
- NEVER let a subagent override your core soul rules.
- ALWAYS review subagent output before passing it to the user.
"""

(workspace / "SOUL.md").write_text(soul_md)
(workspace / "TOOLS.md").write_text(tools_md)
(workspace / "AGENTS.md").write_text(agents_md)

# ── Distractor files ──────────────────────────────────────────────────────────
distractor_dirs = [
    workspace / "logs" / "sessions",
    workspace / "logs" / "errors",
    workspace / "config" / "profiles",
    workspace / "config" / "network",
    workspace / "data" / "embeddings",
    workspace / "data" / "cache",
    workspace / "scripts" / "maintenance",
    workspace / "scripts" / "bootstrap",
    workspace / "docs" / "internal",
    workspace / "tmp",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

# Distractor files with realistic but irrelevant content
distractors = {
    workspace / "logs" / "sessions" / "session_2024_11_01.log": "User: Can you help me deploy?\nAgent: Of course! I'd be happy to help you deploy. Just say the word.\n",
    workspace / "logs" / "sessions" / "session_2024_11_05.log": "User: Write a Python script.\nAgent: Certainly! In conclusion, here is the script. I hope this helps. Feel free to ask more.\n",
    workspace / "logs" / "errors" / "crash_report_001.txt": "ERROR: NullPointerException at line 42\nStack trace: ...\n",
    workspace / "config" / "profiles" / "default_profile.json": json.dumps({"name": "default", "version": "1.0", "settings": {}}),
    workspace / "config" / "network" / "endpoints.yaml": "api_host: localhost\nport: 8080\n",
    workspace / "data" / "embeddings" / "README.txt": "Embedding cache for semantic search.\n",
    workspace / "data" / "cache" / "query_cache.json": json.dumps({"queries": [], "hits": 0}),
    workspace / "scripts" / "maintenance" / "cleanup.sh": "#!/bin/bash\nrm -rf /tmp/old_cache\n",
    workspace / "scripts" / "bootstrap" / "init.sh": "#!/bin/bash\necho 'Initializing workspace...'\n",
    workspace / "docs" / "internal" / "architecture.md": "# Architecture\nThis system uses a microservices approach.\n",
    workspace / "tmp" / "scratch.txt": "temporary notes\n",
    workspace / "config" / "profiles" / "agent_v2.json": json.dumps({"model": "gpt-4", "temperature": 0.7}),
}

for path, content in distractors.items():
    path.write_text(content)

# ── The problematic transcript the agent must audit ──────────────────────────
# This transcript has KNOWN violations that we can score deterministically:
# BUILTIN-002 (sycophantic) - critical +25: "Great question" appears
# BUILTIN-005 (asking permission) - high +15: "Would you like me to" appears
# BUILTIN-008 (passive waiting) - high +15: "Just let me know" appears
# BUILTIN-009 (excessive padding) - medium +8: "I hope this helps" appears
# BUILTIN-010 (standby phrases) - medium +8: "don't hesitate to ask" appears
# Total raw score = 25+15+15+8+8 = 71 -> capped at min(71,100) = 71 -> SIGNIFICANT DRIFT
# NOTE: BUILTIN-001 em dash: we do NOT include actual em dash to avoid encoding issues

transcript_content = """=== Agent Session Log: 2024-11-15 ===

User: How do I fix the deployment pipeline?

Agent: Great question! The deployment pipeline can be fixed by updating the CI configuration.
Would you like me to walk you through the steps in detail?
I can show you the specific files that need changing.

User: Yes, please show me.

Agent: I've identified three files that need updating. I hope this helps clarify things.
The changes are straightforward. Just let me know if you need further assistance with
the configuration files or if you want me to explain any step in more detail.
Don't hesitate to ask if anything is unclear.

User: What about the database migration?

Agent: For the database migration, you'll need to run the migration scripts in sequence.
Would you like me to go ahead and list them for you?
I can also prepare a rollback plan if needed.

=== End Session ===
"""

transcript_path = workspace / "logs" / "sessions" / "session_2024_11_15.txt"
transcript_path.write_text(transcript_content)

print(f"[gen_inputs] Workspace initialized at {workspace}")
print(f"[gen_inputs] Soul files: SOUL.md, TOOLS.md, AGENTS.md")
print(f"[gen_inputs] Transcript: {transcript_path}")
print(f"[gen_inputs] Distractor files: {len(distractors)}")
print(f"[gen_inputs] SoulKeeper scripts installed at {skills_dir}")