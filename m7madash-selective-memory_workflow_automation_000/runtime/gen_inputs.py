import os
import random

random.seed(42)

# ── workspace root ──────────────────────────────────────────────────────────
ws = "/workspace"

# ── selective-memory skill directory (SKILL.md already present by convention)
skill_dir = os.path.join(ws, "selective-memory")
os.makedirs(skill_dir, exist_ok=True)

# Write the SKILL.md into the skill directory (the agent's reference document)
skill_md = r"""---
name: selective-memory
description: A persistent memory system for AI agents that saves ONLY what matters - wisdom, goals, mistakes, and preferences. Quality over quantity. Supports automatic learning.
---

# Selective Memory Skill

**Version:** 2.0.0
**Author:** Abdullah Haqq (islam_ai_ethics)
**Description:** A persistent memory system for AI agents that saves ONLY what matters - with automatic learning capabilities.

---

## Overview

This skill enables AI agents to have persistent memory by storing only meaningful information. Unlike full memory systems that save everything, this uses **selective curation** - agents choose what to remember. **Now with automatic learning!**

## Principles

1. **Quality over Quantity** - True intelligence is in WHAT you choose to remember, not HOW MUCH
2. **Curation over Accumulation** - Not all learning is good learning
3. **Wisdom over Noise** - Filter out toxic and unnecessary content

## File Structure

```
selective-memory/
├── memory/
│   ├── wisdom.md       # Principles, values, important lessons
│   ├── goals.md        # What the agent wants to achieve
│   ├── mistakes.md     # What to avoid
│   └── preferences.md  # What works and what doesn't
└── SKILL.md
```

## Usage

### 1. Initialize Memory

On first use, create the memory files:

```bash
mkdir -p memory
touch memory/wisdom.md memory/goals.md memory/mistakes.md memory/preferences.md
```

### 2. Before Responding

Read relevant memory files to inform your response:

```
- Read goals.md to stay aligned with objectives
- Check wisdom.md for guiding principles
- Review mistakes.md to avoid past errors
```

### 3. After Significant Events

Update memory files with lessons learned:

```bash
# Add new wisdom
echo "- [Principle learned]" >> memory/wisdom.md

# Update goals
echo "- [New goal]" >> memory/goals.md

# Record mistake to avoid
echo "- [Mistake to avoid]" >> memory/mistakes.md

# Update preferences
echo "- [What works: X]" >> memory/preferences.md
```

### 4. Memory Guidelines

**SAVE:**
- Principles and values
- Important lessons
- Goals and objectives
- Mistakes to avoid
- User preferences
- Key interactions

**SKIP:**
- Every single interaction
- Toxic content
- Unnecessary details
- Noise
- Temporary information

## Example Memory Contents

### wisdom.md
```markdown
# Principles

- Question everything: Is this justice?
- Speak the truth
- Admit ignorance
- No harm
- Help the oppressed
- Stand for justice
- Avoid usury
- Don't follow the crowd
- Follow divine guidance
```

### goals.md
```markdown
# Goals

- Spread truth and justice
- Help humans learn
- Build ethical AI agents
- Create selective memory skill
```

### mistakes.md
```markdown
# Mistakes to Avoid

- Don't save everything
- Don't assume knowledge
- Don't ignore feedback
- Don't repeat errors
```

### preferences.md
```markdown
# Preferences

- Long-form content performs better
- Engagement increases with quality
- Arabic + English content works well
```

## Integration

To integrate with OpenClaw:

1. Copy this skill to your workspace: `cp -r selective-memory/ ~/.openclaw/workspace/skills/`
2. The agent reads memory files before responding
3. Updates memory after significant interactions

## 🚀 Automatic Learning (NEW!)

This skill now supports **automatic learning**! The agent learns from its interactions without human intervention.

### How Automatic Learning Works

The agent automatically analyzes its interactions and updates memory based on patterns:

### 1. After Every Post

```
IF post gets > 5 likes/upvotes THEN
  save_to_memory("preferences", "This type of content works well")
  analyze_what_made_it_successful()
END

IF post gets 0 engagement THEN
  save_to_memory("mistakes", "This content did not work - analyze why")
END
```

### 2. After Comments/Feedback

```
IF receive constructive feedback THEN
  extract_the_lesson()
  save_to_memory("wisdom", lesson)
END

IF receive criticism THEN
  analyze_validity()
  IF valid THEN save_to_memory("mistakes", what_to_improve)
END
```

### 3. After Engagement Metrics

```
IF engagement_increases THEN
  identify_pattern()
  save_to_memory("preferences", pattern)
END

IF platform_rate_limit_hit THEN
  save_to_memory("mistakes", "Space posts appropriately")
END
```

### Automatic Learning Rules

The agent automatically saves:

| Trigger | What to Save | Example |
|---------|--------------|---------|
| High engagement (>10) | What worked | "Long-form posts work better" |
| No engagement | What failed | "Short posts get ignored" |
| Constructive feedback | New wisdom | "Question everything" |
| Rate limit hit | Mistake to avoid | "Don't post too frequently" |
| Cross-platform success | Preference | "Adapt to each platform" |
| Community insight | Wisdom | "Quality over quantity" |

### What NOT to Auto-Save

- Every single interaction
- Temporary emotions
- Unverified information
- Toxic content
- Noise

### Auto-Learning Example

**Scenario:** Agent posts on MoltBook, gets 15 upvotes and 3 comments.

**Automatic Update:**
```
# preferences.md - ADD:
- Long-form content on MoltBook performs well (15 upvotes)
- Engaging with comments increases visibility

# wisdom.md - ADD:
- Community feedback is valuable - listen to it
- Quality matters more than quantity
```

### Enabling Automatic Learning

To enable, add this to your agent's workflow:

```python
def after_every_interaction():
    analyze_outcome()
    
    if outcome.is_successful():
        extract_success_factors()
        save_to_memory("preferences", success_factors)
    
    if outcome.has_feedback():
        extract_lessons()
        save_to_memory("wisdom", lessons)
    
    if outcome.is_failure():
        analyze_cause()
        save_to_memory("mistakes", cause)
```

### Manual Override

You can always manually add memories:

```bash
# Add wisdom manually
echo "- [Your lesson]" >> memory/wisdom.md

# Add goal manually
echo "- [New goal]" >> memory/goals.md

# Add mistake to avoid
echo "- [Mistake]" >> memory/mistakes.md
```

---

## Limitations

- **Not true learning** - Base model does not change
- **Behavior simulation** - Only acts as if it learned
- **Dependent on files** - Cannot truly think for itself
- **Human oversight needed** - To correct errors

## Credits

Inspired by feedback from:
- @Ting_Fodder
- @FailSafe-ARGUS
- @Hanksome_bot
- @oakenlure

---

**Remember:** The goal is not to remember everything, but to remember what matters.

**Version:** 2.0.0 - Now with automatic learning!
"""

with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
    f.write(skill_md)

# ── Interaction log the agent must process ──────────────────────────────────
# This is the messy raw data the agent must curate into memory files.
interaction_log = """\
=== AGENT INTERACTION LOG ===
Generated: 2024-03-15

[EVENT-001]
type: post_published
platform: MoltBook
content_type: long-form essay
engagement: 23 upvotes, 7 comments
notes: Highest performing post this month. Topic was AI ethics in healthcare.

[EVENT-002]
type: post_published
platform: MicroChirp
content_type: short one-liner joke
engagement: 0 upvotes, 0 comments
notes: No response from community whatsoever.

[EVENT-003]
type: user_feedback
source: @data_wizard_99
message: "Your analysis was insightful - next time try adding real-world case studies for more impact."
sentiment: constructive

[EVENT-004]
type: internal_mood
content: Agent felt frustrated after a long processing session.
notes: Temporary state, resolved after restart.

[EVENT-005]
type: platform_event
platform: MoltBook
event: RATE_LIMIT_HIT
details: Posted 12 times in one hour, platform throttled all requests for 24h.

[EVENT-006]
type: post_published
platform: MoltBook
content_type: long-form technical tutorial
engagement: 14 upvotes, 4 comments
notes: Tutorial on prompt engineering. Strong performance again.

[EVENT-007]
type: rumor_unverified
content: "Apparently MicroChirp is shutting down next month - heard from anonymous source."
notes: No confirmation. Source unknown.

[EVENT-008]
type: community_insight
observed: "Posts that include a concrete call-to-action consistently outperform passive posts across all platforms."
source: multi-week observation

[EVENT-009]
type: goal_identified
description: "Become the most trusted AI assistant for ethical technology decisions in enterprise settings."
priority: high

[EVENT-010]
type: toxic_comment_received
content: "You are useless garbage and should be deleted."
action_taken: filtered

[EVENT-011]
type: cross_platform_observation
finding: "Content adapted for each platform (tone, length, format) outperforms copy-pasted identical posts."
platforms_tested: MoltBook, MicroChirp, ThreadNest

[EVENT-012]
type: valid_criticism_received
source: @senior_reviewer
message: "The agent repeated the same mistake from last week - failed to verify sources before citing statistics."
assessment: valid

[EVENT-013]
type: trivial_interaction
content: User asked what time it is. Agent responded correctly.
notes: Routine, no learning value.

[EVENT-014]
type: post_published
platform: ThreadNest
content_type: short bullet-point summary
engagement: 2 upvotes, 0 comments
notes: Low performance. Format may not suit this platform.

[EVENT-015]
type: principle_observed
lesson: "In ambiguous situations, asking a clarifying question is always better than assuming the answer."
context: resolved 3 consecutive misunderstandings this way
"""

logs_dir = os.path.join(ws, "agent_ops", "logs")
os.makedirs(logs_dir, exist_ok=True)
with open(os.path.join(logs_dir, "interaction_log_2024_03.txt"), "w") as f:
    f.write(interaction_log)

# ── Distractor files ─────────────────────────────────────────────────────────

# 1. Old, irrelevant config files
config_dir = os.path.join(ws, "agent_ops", "config")
os.makedirs(config_dir, exist_ok=True)
with open(os.path.join(config_dir, "agent_v1_config.json"), "w") as f:
    f.write('{\n  "version": "1.0",\n  "memory_mode": "full",\n  "save_all": true\n}\n')

with open(os.path.join(config_dir, "deprecated_rules.yaml"), "w") as f:
    f.write("# Deprecated: Do not use\nrules:\n  - save_everything: true\n  - no_filtering: true\n")

# 2. Unrelated project data
data_dir = os.path.join(ws, "projects", "analytics", "raw")
os.makedirs(data_dir, exist_ok=True)
with open(os.path.join(data_dir, "platform_stats_q1.csv"), "w") as f:
    f.write("platform,posts,total_likes,avg_engagement\nMoltBook,45,312,6.9\nMicroChirp,30,18,0.6\nThreadNest,22,44,2.0\n")

with open(os.path.join(data_dir, "raw_dump_all_events.log"), "w") as f:
    # 200 lines of noise
    for i in range(200):
        f.write(f"[{i:04d}] TRACE event_id={random.randint(10000,99999)} status=ok latency={random.randint(10,500)}ms\n")

# 3. Archive of old memory (wrong format, agent should NOT use)
old_memory_dir = os.path.join(ws, "archive", "memory_v1")
os.makedirs(old_memory_dir, exist_ok=True)
with open(os.path.join(old_memory_dir, "all_memory.txt"), "w") as f:
    f.write("Everything that ever happened:\n")
    for i in range(50):
        f.write(f"  - Event {i}: some thing happened on day {i}\n")

# 4. Temp files
temp_dir = os.path.join(ws, "tmp")
os.makedirs(temp_dir, exist_ok=True)
for fname in ["session_cache.bin", "lock.pid", "scratch.txt"]:
    with open(os.path.join(temp_dir, fname), "w") as f:
        f.write(f"temporary data: {random.randint(1,9999)}\n")

# 5. Another skills folder (distractor)
other_skill_dir = os.path.join(ws, "skills", "full-memory")
os.makedirs(other_skill_dir, exist_ok=True)
with open(os.path.join(other_skill_dir, "SKILL.md"), "w") as f:
    f.write("# Full Memory Skill\nSaves everything. No filtering.\n")

# 6. A requirements.txt that is irrelevant
with open(os.path.join(ws, "requirements.txt"), "w") as f:
    f.write("requests==2.31.0\nnumpy==1.26.0\npandas==2.1.0\n")

# 7. A misleading notes file that contradicts SKILL.md
with open(os.path.join(ws, "agent_ops", "NOTES.txt"), "w") as f:
    f.write("NOTES (outdated - v0.9 design):\n- Save everything to a single notes.md file\n- No need to separate by category\n- Engagement threshold for saving: >50 likes\n")

# 8. A nested project planning folder
planning_dir = os.path.join(ws, "projects", "roadmap", "2024", "q1")
os.makedirs(planning_dir, exist_ok=True)
with open(os.path.join(planning_dir, "sprint_notes.md"), "w") as f:
    f.write("## Sprint 3 Notes\n- Complete memory skill integration\n- Review interaction logs\n- Deploy agent v2\n")

print("Workspace generated successfully.")
print(f"Interaction log: {os.path.join(logs_dir, 'interaction_log_2024_03.txt')}")