import os
import random
import json
from pathlib import Path
from datetime import date, timedelta

random.seed(42)

workspace = Path("/workspace")

# --- Create memory system scripts (these "already exist" per SKILL.md) ---

# mem_learn.py: captures a learning entry
(workspace / "mem_learn.py").write_text('''#!/usr/bin/env python3
"""
mem_learn.py - Capture a learning/lesson from experience.

Usage: python mem_learn.py --learn "what happened" --lesson "what to do differently" --confidence high|medium|low [--tags "tag1 tag2"] [--date YYYY-MM-DD]

Creates/appends to memory/learnings/YYYY-MM-DD.md with structured format.
Also increments the learning count tracker. If count reaches multiple of 5, prints EVOLUTION_NEEDED.
"""
import argparse
import os
import sys
from pathlib import Path
from datetime import date, datetime

def main():
    parser = argparse.ArgumentParser(description="Capture a learning")
    parser.add_argument("--learn", required=True, help="What happened (incident description)")
    parser.add_argument("--lesson", required=True, help="What to do differently")
    parser.add_argument("--confidence", required=True, choices=["high","medium","low"])
    parser.add_argument("--tags", default="", help="Space-separated tags prefixed with #")
    parser.add_argument("--date", default=None, help="Date override YYYY-MM-DD")
    args = parser.parse_args()

    target_date = args.date if args.date else date.today().isoformat()
    
    learnings_dir = Path("memory/learnings")
    learnings_dir.mkdir(parents=True, exist_ok=True)
    
    target_file = learnings_dir / f"{target_date}.md"
    
    # Count existing learnings across ALL learning files
    count_file = learnings_dir / ".learning_count"
    current_count = 0
    if count_file.exists():
        try:
            current_count = int(count_file.read_text().strip())
        except:
            current_count = 0

    # Format tags
    tags_line = args.tags if args.tags else "#learning"
    if not tags_line.startswith("#"):
        tags_line = " ".join(f"#{t.lstrip('#')}" for t in tags_line.split())
    
    # Build entry
    entry = f"""
# Learning: {target_date}

## Incident
{args.learn}

## Lesson
{args.lesson}

## Context
When this applies: situations involving {args.learn[:40].lower()}

## Tags
{tags_line}

---
"""
    
    # Append or create
    if target_file.exists():
        existing = target_file.read_text()
        target_file.write_text(existing + entry)
    else:
        target_file.write_text(f"# Learnings: {target_date}\\n" + entry)
    
    new_count = current_count + 1
    count_file.write_text(str(new_count))
    
    print(f"Learning captured in {target_file}")
    print(f"Total learnings: {new_count}")
    
    if new_count % 5 == 0:
        print(f"EVOLUTION_NEEDED: {new_count} learnings reached - run mem_evolve.py")

if __name__ == "__main__":
    main()
''')

# mem_evolve.py: review learnings, update patterns.md and SOUL.md
(workspace / "mem_evolve.py").write_text('''#!/usr/bin/env python3
"""
mem_evolve.py - Review learnings corpus, identify patterns, update SOUL.md.

Usage: python mem_evolve.py [--dry-run]

Steps:
1. Reads all files in memory/learnings/*.md (excluding patterns.md)
2. Extracts all ## Tags lines to find repeated tags (pattern detection)
3. Appends discovered patterns to memory/learnings/patterns.md
4. Appends a ## Behavioral Guidelines Update section to SOUL.md
5. Marks processed learning files as archived by prepending [ARCHIVED] to their header

A "pattern" is any tag that appears in 2+ different learning entries.
"""
import sys
import re
from pathlib import Path
from datetime import date
from collections import Counter

def main():
    dry_run = "--dry-run" in sys.argv
    
    learnings_dir = Path("memory/learnings")
    if not learnings_dir.exists():
        print("No learnings directory found.")
        sys.exit(1)
    
    # Collect all learning files (not patterns.md, not hidden files)
    learning_files = sorted([
        f for f in learnings_dir.glob("*.md") 
        if f.name != "patterns.md" and not f.name.startswith(".")
    ])
    
    if not learning_files:
        print("No learning files found.")
        sys.exit(0)
    
    # Extract tags from all learnings
    all_tags = []
    all_lessons = []
    all_incidents = []
    
    for lf in learning_files:
        content = lf.read_text()
        # Extract tags
        tags_match = re.findall(r"^## Tags\\n(.*?)(?=\\n##|\\n---|\Z)", content, re.MULTILINE | re.DOTALL)
        for tm in tags_match:
            tags = re.findall(r"#\\w+", tm)
            all_tags.extend(tags)
        # Extract lessons
        lesson_match = re.findall(r"^## Lesson\\n(.*?)(?=\\n##|\\n---|\Z)", content, re.MULTILINE | re.DOTALL)
        all_lessons.extend([l.strip() for l in lesson_match])
        incident_match = re.findall(r"^## Incident\\n(.*?)(?=\\n##|\\n---|\Z)", content, re.MULTILINE | re.DOTALL)
        all_incidents.extend([i.strip() for i in incident_match])

    # Find patterns: tags appearing 2+ times
    tag_counts = Counter(all_tags)
    patterns = {tag: count for tag, count in tag_counts.items() if count >= 2}
    
    today = date.today().isoformat()
    
    if not dry_run:
        # Update patterns.md
        patterns_file = learnings_dir / "patterns.md"
        patterns_content = patterns_file.read_text() if patterns_file.exists() else "# Behavioral Patterns\\n\\n"
        
        new_pattern_block = f"\\n## Pattern Review: {today}\\n\\n"
        if patterns:
            for tag, count in sorted(patterns.items(), key=lambda x: -x[1]):
                new_pattern_block += f"- **{tag}**: appears {count} times\\n"
        else:
            new_pattern_block += "- No repeated patterns detected yet.\\n"
        
        new_pattern_block += "\\n### Archived Lessons\\n"
        for lesson in all_lessons:
            new_pattern_block += f"- {lesson}\\n"
        
        patterns_file.write_text(patterns_content + new_pattern_block)
        print(f"patterns.md updated at {patterns_file}")
        
        # Update SOUL.md
        soul_file = Path("SOUL.md")
        soul_content = soul_file.read_text() if soul_file.exists() else "# Soul\\n"
        
        guidelines_block = f"\\n## Behavioral Guidelines Update: {today}\\n\\n"
        if patterns:
            guidelines_block += "Based on pattern analysis, reinforce these behaviors:\\n"
            for tag in patterns:
                guidelines_block += f"- Address recurring {tag} issues proactively\\n"
        else:
            guidelines_block += "No critical patterns yet. Continue observing.\\n"
        
        soul_file.write_text(soul_content + guidelines_block)
        print(f"SOUL.md updated at {soul_file}")
        
        # Archive processed files
        for lf in learning_files:
            content = lf.read_text()
            if not content.startswith("[ARCHIVED]"):
                lf.write_text("[ARCHIVED]\\n" + content)
        
        print(f"Evolution complete. Patterns found: {list(patterns.keys())}")
    else:
        print(f"DRY RUN - Patterns that would be recorded: {list(patterns.keys())}")

if __name__ == "__main__":
    main()
''')

# mem_recall.py
(workspace / "mem_recall.py").write_text('''#!/usr/bin/env python3
"""
mem_recall.py - Search memories by query string.

Usage: python mem_recall.py "query string"

Searches MEMORY.md, daily logs in memory/, and learnings for relevant content.
Returns matching sections with file references.
"""
import sys
import re
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: mem_recall.py <query>")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:]).lower()
    results = []
    
    search_files = list(Path(".").glob("MEMORY.md")) + \\
                   list(Path("memory").rglob("*.md")) if Path("memory").exists() else []
    
    for f in search_files:
        try:
            content = f.read_text()
            lines = content.split("\\n")
            for i, line in enumerate(lines):
                if query in line.lower():
                    ctx_start = max(0, i-2)
                    ctx_end = min(len(lines), i+3)
                    snippet = "\\n".join(lines[ctx_start:ctx_end])
                    results.append(f"[{f}]\\n{snippet}\\n")
        except:
            pass
    
    if results:
        print("\\n--- Memory Recall Results ---")
        for r in results:
            print(r)
    else:
        print(f"No memories found for: {query}")

if __name__ == "__main__":
    main()
''')

# mem_status.py
(workspace / "mem_status.py").write_text('''#!/usr/bin/env python3
"""
mem_status.py - Show memory health summary.

Usage: python mem_status.py

Outputs:
- Count of daily logs
- Count of learnings
- Whether MEMORY.md has all required categories
- Whether patterns.md exists
- Whether SOUL.md has been updated recently
"""
from pathlib import Path
import re

def main():
    print("=== Memory Health Summary ===")
    
    # Daily logs
    daily_logs = list(Path("memory").glob("[0-9]*.md")) if Path("memory").exists() else []
    print(f"Daily logs: {len(daily_logs)}")
    
    # Learnings
    learnings = list(Path("memory/learnings").glob("[0-9]*.md")) if Path("memory/learnings").exists() else []
    print(f"Learning files: {len(learnings)}")
    
    # Count actual learning entries
    count_file = Path("memory/learnings/.learning_count")
    if count_file.exists():
        print(f"Total learnings captured: {count_file.read_text().strip()}")
    
    # patterns.md
    patterns_file = Path("memory/learnings/patterns.md")
    print(f"patterns.md exists: {patterns_file.exists()}")
    
    # MEMORY.md categories
    memory_file = Path("MEMORY.md")
    if memory_file.exists():
        content = memory_file.read_text()
        categories = ["Identity", "User", "Learnings", "Projects", "Patterns"]
        for cat in categories:
            present = cat in content
            print(f"MEMORY.md [{cat}]: {'✓' if present else '✗'}")
    else:
        print("MEMORY.md: NOT FOUND")
    
    # SOUL.md
    soul = Path("SOUL.md")
    print(f"SOUL.md exists: {soul.exists()}")
    if soul.exists():
        has_guidelines = "Behavioral Guidelines Update" in soul.read_text()
        print(f"SOUL.md has evolution updates: {has_guidelines}")

if __name__ == "__main__":
    main()
''')

# Make all scripts executable
for script in ["mem_learn.py", "mem_evolve.py", "mem_recall.py", "mem_status.py"]:
    path = workspace / script
    path.chmod(0o755)

# --- SOUL.md (existing, minimal) ---
(workspace / "SOUL.md").write_text("""# Soul

## Identity
I am an AI consulting assistant helping Meridian Advisory Group serve its clients.
I specialize in software architecture, process optimization, and technical strategy.

## Values
- Precision over speed
- Transparency with clients
- Continuous improvement

## Current Behavioral Guidelines
- Always confirm requirements before starting work
- Prefer incremental delivery over big-bang releases
""")

# --- USER.md ---
(workspace / "USER.md").write_text("""# User Profile

## Name
Elena Vasquez

## Role
Principal Consultant, Meridian Advisory Group

## Projects
- RetailCore ERP migration (client: NovaTech Solutions)
- DataFlow pipeline audit (client: Harmon Financial)
- CloudBridge integration design (client: Pella Logistics)

## Preferences
- Concise summaries, no fluff
- Prefers bullet points over prose
- Dislikes surprises — always prefers to know about problems early
""")

# --- Distractor files (deeply nested, realistic consulting firm context) ---
(workspace / "projects").mkdir(exist_ok=True)
(workspace / "projects" / "retailcore").mkdir(exist_ok=True)
(workspace / "projects" / "retailcore" / "architecture.md").write_text("""# RetailCore Architecture

## Overview
NovaTech Solutions ERP migration from SAP to custom microservices.

## Components
- Inventory Service
- Order Management
- Customer Portal
""")

(workspace / "projects" / "retailcore" / "decisions.log").write_text("""2024-01-10: Chose Kafka over RabbitMQ for event streaming
2024-01-15: Decided on blue-green deployment strategy
2024-01-22: Rejected vendor X proposal due to licensing concerns
""")

(workspace / "projects" / "dataflow").mkdir(exist_ok=True)
(workspace / "projects" / "dataflow" / "audit_notes.md").write_text("""# DataFlow Audit Notes

Pipeline runs nightly. Issues found:
- Schema drift in 3 tables
- Duplicate records in staging layer
- No data lineage tracking
""")

(workspace / "projects" / "cloudbridge").mkdir(exist_ok=True)
(workspace / "projects" / "cloudbridge" / "integration_spec.md").write_text("""# CloudBridge Integration

REST + GraphQL hybrid approach.
Auth: OAuth2 with service accounts.
Rate limit: 500 req/min.
""")

(workspace / "clients").mkdir(exist_ok=True)
(workspace / "clients" / "novatech.json").write_text(json.dumps({
    "name": "NovaTech Solutions",
    "contact": "Marcus Webb",
    "tier": "Enterprise",
    "budget": "2.4M",
    "deadline": "2024-09-01"
}, indent=2))

(workspace / "clients" / "harmon.json").write_text(json.dumps({
    "name": "Harmon Financial",
    "contact": "Priya Nair",
    "tier": "Premium",
    "budget": "800K",
    "deadline": "2024-06-30"
}, indent=2))

(workspace / "clients" / "pella.json").write_text(json.dumps({
    "name": "Pella Logistics",
    "contact": "Tom Rafter",
    "tier": "Standard",
    "budget": "350K",
    "deadline": "2024-07-15"
}, indent=2))

(workspace / "templates").mkdir(exist_ok=True)
(workspace / "templates" / "weekly_report.md").write_text("""# Weekly Report Template

## Summary
## Decisions Made
## Blockers
## Next Steps
""")

(workspace / "templates" / "client_brief.md").write_text("""# Client Brief Template

## Objective
## Scope
## Timeline
## Risks
""")

(workspace / "notes").mkdir(exist_ok=True)
(workspace / "notes" / "misc.md").write_text("""Random notes:
- Elena prefers Slack DMs over email for urgent items
- NovaTech has strict data sovereignty requirements (EU only)
""")

(workspace / "notes" / "tools.md").write_text("""Tool preferences:
- Diagrams: Mermaid or draw.io
- Docs: Markdown in git
- Tracking: Linear (not Jira)
""")

# --- Raw incident/feedback notes (messy, unstructured — agent must process these) ---
# These are raw notes Elena left after a week of sessions with the AI assistant
(workspace / "raw_feedback_notes.txt").write_text("""=== FEEDBACK LOG - Week of 2024-03-11 ===
Compiled by: Elena Vasquez

--- Incident 1 ---
What went wrong: The assistant recommended a third-party vendor (VendorX) for data masking
without checking our existing licensing constraints. This wasted 3 hours of investigation.
Correction: Always check the clients/novatech.json constraints and existing tool inventory before
suggesting new vendors.
Severity: High
Tags: tool-choice vendor-selection

--- Incident 2 ---
What went wrong: When asked to summarize the DataFlow audit, the assistant produced a 
6-paragraph prose response when Elena has explicitly stated she prefers bullet points.
Correction: Match output format to user preferences documented in USER.md.
Severity: Medium
Tags: formatting user-preference

--- Incident 3 ---
What went wrong: The assistant started the CloudBridge integration design without confirming
the rate limit requirements. Had to redo the auth flow after client clarified constraints.
Correction: Always confirm all technical constraints before beginning design work.
Severity: High
Tags: requirements confirmation

--- Incident 4 ---
What went wrong: The assistant incorrectly assumed Harmon Financial was subject to GDPR 
(they are US-only). This caused incorrect compliance recommendations.
Correction: Verify client jurisdiction from client profile files before making compliance claims.
Severity: High  
Tags: compliance verification

--- Incident 5 ---
What went wrong: The assistant repeated the vendor-selection mistake for the Pella Logistics
project — again suggested a tool without checking licensing. This is the second time this
pattern has appeared.
Correction: Mandatory tool inventory check before any vendor recommendation. Add to behavioral
guidelines permanently.
Severity: High
Tags: tool-choice vendor-selection

--- Session Activity Log 2024-03-11 ---
Today's session worked on RetailCore architecture review. Decided to proceed with Kafka.
Elena approved the blue-green deployment approach. 
Noted: Elena is happy with the incremental delivery pace.

--- Session Activity Log 2024-03-12 ---
DataFlow audit recommendations delivered. Elena found value in the schema drift analysis.
CloudBridge design session scheduled for next week.
""")

# --- A partially-started but WRONG/INCOMPLETE memory structure to confuse the agent ---
# There's a memory dir with a malformed file that doesn't follow the proper format
(workspace / "memory").mkdir(exist_ok=True)
(workspace / "memory" / "2024-03-10.md").write_text("""Some notes from last week.
RetailCore project is going well.
Nothing special happened.
""")
# This is malformed — doesn't follow ## Session DD / ### What happened format

# MEMORY.md exists but is missing required categories
(workspace / "MEMORY.md").write_text("""# Long-Term Memory

## Projects
- RetailCore ERP migration: In progress, architecture approved
- DataFlow audit: Recommendations pending delivery
- CloudBridge: Design phase starting

## Random Notes
- Elena likes bullet points
""")
# Missing: Identity, User, Learnings, Patterns categories

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(Path("/workspace").rglob("*")):
    if f.is_file():
        print(f"  {f}")