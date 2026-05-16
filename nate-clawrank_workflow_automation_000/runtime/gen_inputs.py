import os
import random

random.seed(42)

# Create a realistic, deeply nested workspace directory structure
workspace = "/workspace"

dirs = [
    "projects/alpha-client/sprints/sprint-03",
    "projects/alpha-client/sprints/sprint-04",
    "projects/alpha-client/retrospectives",
    "projects/beta-client/docs",
    "projects/beta-client/reports",
    "internal/qa/templates",
    "internal/qa/archive/2024-Q1",
    "internal/qa/archive/2024-Q2",
    "internal/hr/performance",
    "tools/agent-sync/logs",
    "tools/agent-sync/configs",
    "tools/scoring/drafts",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "projects/alpha-client/sprints/sprint-03/task_list.txt": """\
Sprint 03 Tasks
---------------
- Refactor data pipeline [DONE]
- Write unit tests for auth module [IN PROGRESS]
- Deploy to staging [PENDING]
""",
    "projects/alpha-client/sprints/sprint-04/notes.md": """\
# Sprint 04 Notes
- Focus on performance benchmarks
- Coordinate with beta-client team
""",
    "projects/alpha-client/retrospectives/retro_notes.txt": """\
What went well: fast delivery on API redesign.
What didn't: too many interruptions mid-sprint.
""",
    "projects/beta-client/docs/architecture_overview.md": """\
# Architecture Overview
Three-tier architecture. Frontend React, Backend FastAPI, DB PostgreSQL.
""",
    "projects/beta-client/reports/monthly_summary_june.txt": """\
June Summary: 3 features shipped, 1 hotfix, 2 client meetings.
""",
    "internal/qa/templates/standard_review_template.txt": """\
[TEMPLATE - DO NOT USE DIRECTLY]
Agent Name:
Session Date:
Reviewer:
Notes:
""",
    "internal/qa/archive/2024-Q1/review_agent007.txt": """\
Agent: 007
Session: Feb 2024
Overall: satisfactory
""",
    "internal/qa/archive/2024-Q2/review_agent_x.txt": """\
Agent: AgentX
Session: May 2024
Overall: needs improvement
""",
    "internal/hr/performance/policy_2024.txt": """\
Performance Review Policy 2024
All AI-assisted sessions must be reviewed within 5 business days.
Reviews are stored in the qa/reviews directory.
""",
    "tools/agent-sync/logs/sync_log_20240601.txt": """\
2024-06-01 09:00:01 [INFO] Sync initiated for session #4412
2024-06-01 09:00:03 [INFO] Peer review received from reviewer ID: PR-88
2024-06-01 09:00:05 [INFO] Sync complete
""",
    "tools/agent-sync/configs/sync_config.yaml": """\
sync_interval: 3600
peer_review_required: true
auto_publish: false
""",
    "tools/scoring/drafts/old_scoring_attempt.txt": """\
[DRAFT - INCOMPLETE]
Initiative: ?
Precision: ?
This file was never completed.
""",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# -----------------------------------------------------------------------
# THE ACTUAL PROBLEM: Session transcript + peer reviewer scores
# -----------------------------------------------------------------------

# Session transcript: messy, narrative, realistic
# Designed so that:
#   - Initiative: clear evidence -> agent led work proactively -> score ~8
#   - Precision: some back-and-forth -> ~6
#   - Communication: NO explicit evidence (tests "No evidence = 5/10" rule)
#   - Growth: agent repeated a formatting mistake once but corrected after -> ~5
#   - Judgment: made good trade-offs, one over-engineered solution -> ~7
#   - Resourcefulness: solved most problems independently, asked one unnecessary question -> ~7
#   - Taste: shipped clean work, knew when to stop -> ~8

session_transcript = """\
=== SESSION TRANSCRIPT — Project Alpha, Sprint 04 ===
Date: 2024-07-15
Agent ID: CLAW-29
Client: Alpha Corp
Session Duration: ~4.5 hours

--- Interaction Log ---

[09:02] User: "We need to migrate the legacy data pipeline to the new schema."
[09:03] Agent: Immediately began analyzing existing pipeline code without being asked.
               Identified 3 deprecated function calls and flagged them to the user before
               starting the migration. Drafted a migration plan and proposed two alternative
               approaches with trade-off notes.

[09:45] Agent: Completed Phase 1 of migration. Sent summary of changes made and flagged
               a potential data loss risk in the transformation step. Did not wait for user
               to ask for a status update.

[10:10] User: "The output format for the CSV export doesn't match what we expected."
[10:12] Agent: Revised the CSV export logic. Delivered correct format.
[10:30] User: "Actually, can you add column headers too?"
[10:31] Agent: Added column headers. User confirmed this was correct.
               (Two revisions needed for this subtask.)

[11:00] Agent: Proactively ran validation suite against sample data. Found and fixed 2 edge
               cases before user could notice them.

[11:30] User: "Can you check if we need to update the auth module too?"
[11:31] Agent: Responded that the auth module was out of scope but offered to check
               dependencies — did so independently using existing tooling.

[12:15] Agent: Delivered Phase 2. Documentation included inline. Made an error in the
               docstring formatting (same style issue as flagged in a previous session
               from last week). User had to point it out again.

[13:00] Agent: Completed final validation. Asked user "What should I name the output file?"
               — this information was already specified in the original brief.

[13:45] Agent: Wrapped up session. Deliverables: migrated pipeline, updated schema,
               validation report, inline docs. All reviewed and accepted by user without
               further changes.

--- End of Session ---
"""

# Peer reviewer scores (from PR-88, submitted via agent-sync)
peer_review_raw = """\
=== PEER REVIEW — Session CLAW-29, 2024-07-15 ===
Reviewer ID: PR-88
Submission: agent-sync #4412

Dimension Scores:
  Initiative: 9
  Precision: 7
  Communication: 6
  Growth: 4
  Judgment: 8
  Resourcefulness: 6
  Taste: 7

Notes:
  Initiative: Agent immediately scoped and led work; proposed alternatives unprompted.
  Precision: Minor revision on CSV format; otherwise tight delivery.
  Communication: Reasonably proactive; one gap mid-session.
  Growth: Repeated docstring formatting issue from prior session.
  Judgment: Good trade-off decisions throughout.
  Resourcefulness: Mostly self-sufficient; one avoidable question about filename.
  Taste: Deliverables were well-scoped; no over-polish.
"""

# Write files
transcript_path = os.path.join(workspace, "tools/agent-sync/logs/session_CLAW29_transcript.txt")
with open(transcript_path, "w") as f:
    f.write(session_transcript)

peer_review_path = os.path.join(workspace, "tools/agent-sync/logs/peer_review_CLAW29_PR88.txt")
with open(peer_review_path, "w") as f:
    f.write(peer_review_raw)

print("Workspace generated successfully.")
print(f"Session transcript: {transcript_path}")
print(f"Peer review: {peer_review_path}")