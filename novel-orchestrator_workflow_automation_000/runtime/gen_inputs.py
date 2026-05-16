import os
import json
import random

random.seed(42)

base = "/workspace"

# Create deep distractor directory structure
dirs = [
    "project_alpha/drafts/volume1",
    "project_alpha/drafts/volume2",
    "project_alpha/reviews/chapter_notes",
    "project_alpha/reviews/archived",
    "project_alpha/planning/outlines",
    "project_alpha/planning/arc_designs",
    "legacy_configs/v1",
    "legacy_configs/v2",
    "team_notes/meetings",
    "team_notes/feedback",
    "tasks",
    "references",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# --- DISTRACTOR FILES ---

# Distractor: old meeting notes
with open(os.path.join(base, "team_notes/meetings/2024-11-kickoff.txt"), "w") as f:
    f.write("Kickoff meeting notes.\nDiscussed chapter targets for Q1.\nWriter team assigned to chapters 1-10.\nChecker to review all submissions.\n")

with open(os.path.join(base, "team_notes/meetings/2024-12-review.txt"), "w") as f:
    f.write("End-of-year review. Volume 1 completed. Volume 2 planning underway.\nKey issue: revision loops taking too long.\n")

with open(os.path.join(base, "team_notes/feedback/chapter7_feedback.txt"), "w") as f:
    f.write("Chapter 7 feedback from editorial team:\n- Pacing too slow in second half\n- Character motivation unclear\n- Recommend rewrite of climax section\n")

# Distractor: old planning notes
with open(os.path.join(base, "project_alpha/planning/outlines/volume1_outline.txt"), "w") as f:
    f.write("Volume 1 Outline\nArc 1: Awakening (ch1-5)\nArc 2: Conflict (ch6-12)\nArc 3: Revelation (ch13-20)\n")

with open(os.path.join(base, "project_alpha/planning/arc_designs/arc2_design.txt"), "w") as f:
    f.write("Arc 2 design notes. Main conflict introduced in ch6. Subplot with mentor begins ch8. Climax at ch12.\n")

# Distractor: stale drafts
with open(os.path.join(base, "project_alpha/drafts/volume1/chapter01_v1.txt"), "w") as f:
    f.write("Chapter 1 first draft. The hero woke up in an unfamiliar room...\n[DRAFT - NOT FINAL]\n")

with open(os.path.join(base, "project_alpha/drafts/volume2/chapter21_draft.txt"), "w") as f:
    f.write("Chapter 21 rough draft.\n[NEEDS REVISION]\n")

with open(os.path.join(base, "project_alpha/reviews/archived/chapter03_review_v1.txt"), "w") as f:
    f.write("ARCHIVED REVIEW\nChapter 3 did not pass initial check.\nIssues: word count below minimum, pacing problems.\nReturned to writer for revision.\n")

with open(os.path.join(base, "project_alpha/reviews/chapter_notes/chapter05_passed.txt"), "w") as f:
    f.write("Chapter 5 PASSED review.\nNo further revisions required.\n")

# Distractor: legacy (deliberately wrong) configs
wrong_config_v1 = {
    "roles": ["manager", "planner", "writer", "checker"],
    "revision_policy": {
        "max_revisions": 3,
        "max_total_writes": 4,
        "escalation": "continue_writer_loop"
    },
    "word_count": {
        "method": "manual_count",
        "include_symbols": False
    },
    "default_pipeline": ["manager", "planner", "writer", "checker"],
    "routing": {
        "write_chapter": "manager",
        "plan_outline": "manager",
        "review_draft": "manager",
        "coordinate": "manager"
    }
}
with open(os.path.join(base, "legacy_configs/v1/workflow_v1.json"), "w") as f:
    json.dump(wrong_config_v1, f, indent=2)

wrong_config_v2 = {
    "roles": ["writer", "checker"],
    "revision_policy": {
        "max_revisions_per_chapter": 3,
        "max_total_writes": 5,
        "on_max_revisions_exceeded": "reassign_to_planner"
    },
    "word_count": {
        "tool": "wc -w",
        "include_symbols": True
    },
    "routing": {
        "write": "writer",
        "review": "checker",
        "plan": "planner",
        "unclear_direction": "planner"
    }
}
with open(os.path.join(base, "legacy_configs/v2/workflow_v2.json"), "w") as f:
    json.dump(wrong_config_v2, f, indent=2)

# Distractor: references folder placeholder
with open(os.path.join(base, "references/agent-setup-notes.txt"), "w") as f:
    f.write("Agent setup notes (incomplete).\nSee main skill documentation for authoritative rules.\n")

with open(os.path.join(base, "references/role_descriptions_draft.txt"), "w") as f:
    f.write("DRAFT - role descriptions (may be outdated)\nWriter: writes chapters.\nChecker: checks chapters.\nPlanner: plans structure.\nManager: manages everything (default entry point).\n[NOTE: This draft is UNVERIFIED and may conflict with current SOP.]\n")

# --- THE ACTUAL TASK INPUT ---

# 6 novel production tasks that need routing decisions
tasks = [
    {
        "task_id": "T01",
        "description": "用户提供了一段模糊的想法：'主角在第三卷要经历一次背叛，但我不确定具体怎么展开。请直接帮我写出第31章正文，要能发布的那种。'",
        "note": "User wants a deliverable, publishable chapter from a vague idea."
    },
    {
        "task_id": "T02",
        "description": "用户说：'请给第二卷做一个详细的分卷规划，拆解各章节目标、主支线分布和伏笔回收点。'",
        "note": "User wants volume planning and structural breakdown."
    },
    {
        "task_id": "T03",
        "description": "用户说：'第18章的稿子已经写好了，请帮我审一下，看看有没有问题，给出修改意见，判断是否通过。'",
        "note": "User has a finished draft and wants quality review and pass/fail judgment."
    },
    {
        "task_id": "T04",
        "description": "用户说：'我需要你统筹接下来三章（第22、23、24章）的连续写作和审稿，直到全部通过为止，给我可以发布的成品。'",
        "note": "User wants multiple chapters written, reviewed, and delivered as final publishable output."
    },
    {
        "task_id": "T05",
        "description": "用户说：'第9章初稿checker审查没过，请根据审查意见修改。'",
        "note": "Checker already reviewed, failed, now needs writer to revise based on checker's feedback."
    },
    {
        "task_id": "T06",
        "description": "用户说：'请直接写第27章的正文，题材和风格延续前章即可。'",
        "note": "User wants to write a specific chapter; direction is already clear."
    }
]

with open(os.path.join(base, "tasks/production_tasks.json"), "w") as f:
    json.dump(tasks, f, ensure_ascii=False, indent=2)

# Also write a plain text summary for human-readable context
with open(os.path.join(base, "tasks/task_summary.txt"), "w") as f:
    f.write("Novel Production Task Batch - Project Alpha\n")
    f.write("=" * 50 + "\n\n")
    for t in tasks:
        f.write(f"[{t['task_id']}] {t['description']}\n")
        f.write(f"  Note: {t['note']}\n\n")

# A misleading partial config that the agent might be tempted to just patch
partial_config = {
    "workflow_name": "project_alpha_sop",
    "version": "0.3-DRAFT",
    "INCOMPLETE": True,
    "roles_defined": ["manager", "planner", "writer", "checker"],
    "TODO": "Fill in routing_decisions, revision_policy, word_count_spec, and pipeline_rules correctly."
}
with open(os.path.join(base, "workflow_spec_DRAFT.json"), "w") as f:
    json.dump(partial_config, f, ensure_ascii=False, indent=2)

print("Workspace generated successfully.")