import os
import random
import textwrap

random.seed(42)

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "meetings/2024-Q2",
    "meetings/2024-Q3",
    "archive/old_notes",
    "archive/processed",
    "team/engineering",
    "team/design",
    "team/product",
    "exports/csv",
    "exports/reports",
    "config",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "config/settings.yaml": textwrap.dedent("""\
        edition: free
        max_tasks: 50
        output_format: markdown
        timezone: UTC
        auto_assign: false
    """),
    "config/feature_flags.json": '{"premium": false, "integrations": false, "smart_prioritization": false}',
    "team/engineering/members.txt": "Alice Chen\nBob Ramirez\nCarla Singh\nDave Park",
    "team/design/members.txt": "Eva Novak\nFrank Osei",
    "team/product/members.txt": "Grace Lin\nHiro Tanaka",
    "archive/old_notes/2023-kickoff.txt": textwrap.dedent("""\
        Kickoff meeting 2023-01-10
        Discussed roadmap. No decisions recorded.
        Owner: unknown
    """),
    "archive/processed/q1_summary.md": textwrap.dedent("""\
        # Q1 Summary
        Processed. Tasks exported to CSV.
    """),
    "meetings/2024-Q2/planning_notes_raw.txt": textwrap.dedent("""\
        quick sync - may 5
        talked about the mobile redesign maybe? 
        alice mentioned backend api - still blocked
        no clear owner for documentation
        next: review designs
    """),
    "meetings/2024-Q3/retro.txt": textwrap.dedent("""\
        Retrospective July 2024
        Went well: deployment pipeline, test coverage
        Needs work: communication between design and eng
        Action: improve handoff doc - nobody assigned yet
    """),
    "exports/csv/sample_tasks.csv": textwrap.dedent("""\
        task,owner,due_date,status,note
        Update CI pipeline,Bob Ramirez,,done,Completed last sprint
        Write API docs,unassigned,,todo,Blocked on spec review
    """),
    "exports/reports/weekly_digest.md": "# Weekly Digest\nNothing new this week.",
    "meetings/2024-Q3/standup_aug12.txt": "Quick standup. No blockers reported. Dave to check on staging.",
}
for path, content in distractors.items():
    with open(path, "w") as f:
        f.write(content)

# ── references/templates.md ──────────────────────────────────────────────────
templates_md = textwrap.dedent("""\
    # Meeting Recap Templates

    ## Key Points Template

    ```
    ## Key Points
    - **Main Objective:** <objective>
    - **Important Decisions:** <decisions>
    - **Open Questions:** <open_questions>
    - **Risks / Blockers:** <risks>
    - **Notable Follow-up Topics:** <follow_up>
    ```

    ## Summary Template

    ```
    ## Meeting Summary
    **Title:** <title>
    **Date:** <date>
    **Participants:** <participants>

    ### Context
    <context>

    ### Decisions
    <decisions>

    ### Discussion Points
    <discussion_points>

    ### Blockers
    <blockers>

    ### Next Steps
    <next_steps>
    ```

    ## Task List Template

    | task | owner | status | note |
    |------|-------|--------|------|
    | <task> | <owner or unassigned> | todo | <note> |

    ## Output Order

    1. Meeting Context
    2. Concise Summary
    3. Key Points
    4. Task List
    5. Open Questions
""")
with open("references/templates.md", "w") as f:
    f.write(templates_md)

# ── scripts/task_extractor.py ────────────────────────────────────────────────
task_extractor_py = textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"
    task_extractor.py  --  Meeting Notes → Tasks CSV
    
    Usage:
        python scripts/task_extractor.py <input_notes_file> <output_csv_file>

    Reads raw meeting notes from <input_notes_file>.
    Writes a CSV to <output_csv_file> with columns:
        task, owner, status, note

    Rules applied by this script:
    - Parses lines beginning with action keywords (action:, todo:, next:,
      task:, follow-up:, assign:) as tasks.
    - Owner is extracted after 'owner:' or '->' tokens on the same line;
      defaults to 'unassigned' when absent.
    - status is always set to 'todo'.
    - due_date is intentionally omitted from output (free edition).
    - note carries the remainder of the line after owner extraction.
    \"\"\"
    import sys
    import csv
    import re

    ACTION_PREFIXES = re.compile(
        r'^\\s*(?:action|todo|next|task|follow-?up|assign)\\s*[:\\-]\\s*',
        re.IGNORECASE
    )
    OWNER_PATTERN = re.compile(
        r'(?:owner\\s*[:\\-]|->)\\s*([\\w\\s]+?)(?:\\s*[,;\\|]|$)',
        re.IGNORECASE
    )

    def extract_tasks(text):
        tasks = []
        for line in text.splitlines():
            if not ACTION_PREFIXES.search(line):
                continue
            body = ACTION_PREFIXES.sub('', line).strip()
            owner_match = OWNER_PATTERN.search(body)
            if owner_match:
                owner = owner_match.group(1).strip()
                note = (body[:owner_match.start()] + body[owner_match.end():]).strip(' ,;|-')
            else:
                owner = 'unassigned'
                note = body
            tasks.append({
                'task': note,
                'owner': owner,
                'status': 'todo',
                'note': note,
            })
        return tasks

    def main():
        if len(sys.argv) != 3:
            print("Usage: task_extractor.py <input_notes> <output_csv>")
            sys.exit(1)
        input_path, output_path = sys.argv[1], sys.argv[2]
        with open(input_path) as f:
            text = f.read()
        tasks = extract_tasks(text)
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['task', 'owner', 'status', 'note'])
            writer.writeheader()
            writer.writerows(tasks)
        print(f"Extracted {len(tasks)} task(s) → {output_path}")

    if __name__ == '__main__':
        main()
""")
with open("scripts/task_extractor.py", "w") as f:
    f.write(task_extractor_py)

# ── scripts/meeting_summary.py ───────────────────────────────────────────────
meeting_summary_py = textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"
    meeting_summary.py  --  Meeting Notes → Structured Summary

    Usage:
        python scripts/meeting_summary.py <input_notes_file> <output_summary_file>

    Reads raw meeting notes from <input_notes_file>.
    Produces a compact structured Markdown summary in <output_summary_file>.

    Output sections (in order):
        ## Meeting Context
        ## Concise Summary
        ## Key Points
        ## Task List          (inline, not CSV)
        ## Open Questions
    
    Bucketing heuristics:
        - Lines with 'decided', 'agreed', 'approved', 'confirmed'  → Decisions
        - Lines with 'blocked', 'blocker', 'issue', 'risk'         → Blockers
        - Lines with action prefixes (action:, next:, todo:, etc.) → Next Steps
        - Questions (lines ending with '?')                        → Open Questions
        - Remaining content                                        → Discussion Points
    \"\"\"
    import sys
    import re
    from pathlib import Path

    ACTION_RE = re.compile(r'^\\s*(?:action|todo|next|task|follow-?up|assign)\\s*[:\\-]', re.IGNORECASE)
    DECISION_RE = re.compile(r'\\b(decided|agreed|approved|confirmed|decision)\\b', re.IGNORECASE)
    BLOCKER_RE = re.compile(r'\\b(blocked|blocker|blocking|issue|risk|impediment)\\b', re.IGNORECASE)
    QUESTION_RE = re.compile(r'\\?\\s*$')

    def classify(lines):
        buckets = {
            'decisions': [],
            'blockers': [],
            'next_steps': [],
            'open_questions': [],
            'discussion': [],
        }
        for line in lines:
            s = line.strip()
            if not s:
                continue
            if ACTION_RE.search(s):
                buckets['next_steps'].append(s)
            elif DECISION_RE.search(s):
                buckets['decisions'].append(s)
            elif BLOCKER_RE.search(s):
                buckets['blockers'].append(s)
            elif QUESTION_RE.search(s):
                buckets['open_questions'].append(s)
            else:
                buckets['discussion'].append(s)
        return buckets

    def fmt_list(items):
        if not items:
            return '- (none)\\n'
        return ''.join(f'- {i}\\n' for i in items)

    def main():
        if len(sys.argv) != 3:
            print("Usage: meeting_summary.py <input_notes> <output_summary>")
            sys.exit(1)
        input_path, output_path = sys.argv[1], sys.argv[2]
        text = Path(input_path).read_text()
        lines = text.splitlines()

        # best-effort header extraction
        title, date, participants = 'Unknown', 'Unknown', 'Unknown'
        body_lines = []
        for line in lines:
            stripped = line.strip()
            if re.match(r'^(meeting\\s+)?title\\s*[:\\-]', stripped, re.IGNORECASE):
                title = re.sub(r'^(meeting\\s+)?title\\s*[:\\-]\\s*', '', stripped, flags=re.IGNORECASE)
            elif re.match(r'^date\\s*[:\\-]', stripped, re.IGNORECASE):
                date = re.sub(r'^date\\s*[:\\-]\\s*', '', stripped, flags=re.IGNORECASE)
            elif re.match(r'^participants?\\s*[:\\-]', stripped, re.IGNORECASE):
                participants = re.sub(r'^participants?\\s*[:\\-]\\s*', '', stripped, flags=re.IGNORECASE)
            else:
                body_lines.append(stripped)

        buckets = classify(body_lines)
        all_text = ' '.join(body_lines)
        concise = (all_text[:300] + '...') if len(all_text) > 300 else all_text

        out = []
        out.append('## Meeting Context')
        out.append(f'- **Title:** {title}')
        out.append(f'- **Date:** {date}')
        out.append(f'- **Participants:** {participants}')
        out.append('')
        out.append('## Concise Summary')
        out.append(concise)
        out.append('')
        out.append('## Key Points')
        out.append('### Decisions')
        out.append(fmt_list(buckets['decisions']).rstrip())
        out.append('### Blockers')
        out.append(fmt_list(buckets['blockers']).rstrip())
        out.append('### Next Steps')
        out.append(fmt_list(buckets['next_steps']).rstrip())
        out.append('')
        out.append('## Task List')
        if buckets['next_steps']:
            out.append('| task | owner | status | note |')
            out.append('|------|-------|--------|------|')
            for s in buckets['next_steps']:
                out.append(f'| {s} | unassigned | todo |  |')
        else:
            out.append('No tasks extracted.')
        out.append('')
        out.append('## Open Questions')
        out.append(fmt_list(buckets['open_questions']).rstrip())

        Path(output_path).write_text('\\n'.join(out) + '\\n')
        print(f"Summary written → {output_path}")

    if __name__ == '__main__':
        main()
""")
with open("scripts/meeting_summary.py", "w") as f:
    f.write(meeting_summary_py)

# ── THE PROBLEM: raw messy meeting notes ─────────────────────────────────────
raw_notes = textwrap.dedent("""\
    Title: Q3 Feature Scoping – Mobile Checkout
    Date: 2024-08-15
    Participants: Grace Lin, Alice Chen, Eva Novak, Hiro Tanaka, Bob Ramirez

    okay so we kicked off around 2pm, grace started us off... the main thing today
    is to figure out what's going into the mobile checkout v2 scope for Q3.

    grace said we decided the new payment widget will go into the September release.
    hiro confirmed that the analytics dashboard is approved for Q3 too.

    alice raised a concern – the backend API for payment processing is still blocked
    on the security audit from compliance. that's a risk for the timeline.

    eva mentioned there are two design variants for the cart screen, but nobody has
    picked one yet. 

    bob noted the staging environment has a config issue which is a blocker for
    testing the payment flow end-to-end.

    random chat about whether we should migrate to a new logging library –
    nobody really decided, just general discussion.

    actually does anyone know when the compliance review will finish?
    and will the design freeze happen before the September milestone?

    Action: Alice Chen to follow up with compliance team on audit status
    Action: Eva Novak to get stakeholder sign-off on cart design variant by next review
    Next: Bob Ramirez to fix staging config issue
    Todo: update the internal API docs - owner: unassigned
    Action: Grace Lin to send meeting recap to product team

    some extra filler blah blah ignore this repeated text repeated text
    the payment widget is for September we said that already yep confirmed.
""")
with open("meetings/2024-Q3/q3_feature_scoping_raw.txt", "w") as f:
    f.write(raw_notes)

print("Workspace generated successfully.")