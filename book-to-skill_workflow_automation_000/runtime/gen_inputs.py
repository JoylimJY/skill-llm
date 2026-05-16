import os
import random

random.seed(42)

workspace = "/workspace"

# Create a realistic, deeply nested distractor directory structure
dirs = [
    "library/imported/2024",
    "library/imported/2023",
    "library/processed",
    "library/archive/classics",
    "library/archive/modern",
    "skills/productivity",
    "skills/leadership",
    "skills/communication",
    "skills/drafts",
    "skills/deprecated",
    "tools/parsers",
    "tools/converters",
    "notes/reading_logs",
    "notes/summaries",
    "exports/json",
    "exports/markdown",
    "config",
    "tmp",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files — realistic but irrelevant
distractor_files = {
    "library/imported/2024/atomic_habits_notes.txt": "Chapter 1: Tiny Changes, Remarkable Results\nThe aggregation of marginal gains...\nIdentity-based habits vs outcome-based habits.",
    "library/imported/2023/deep_work_summary.md": "# Deep Work\nRules for Focused Success in a Distracted World\n## Rule 1: Work Deeply\nSchedule deep work blocks.",
    "library/archive/classics/how_to_win_friends.txt": "Part One: Fundamental Techniques in Handling People\n1. Don't criticize, condemn or complain...",
    "library/archive/modern/essentialism_excerpt.txt": "The Disciplined Pursuit of Less\nCore Mindset: Less but better.\nThe Essentialist spends as much time as possible exploring more options.",
    "library/processed/processed_log.csv": "filename,status,date\natomic_habits.pdf,done,2024-01-10\ndeep_work.epub,done,2024-02-05",
    "skills/productivity/gtd-method/SKILL.md": "---\nname: gtd-method\ndescription: Getting Things Done methodology. 用于：当需要管理大量任务和项目时\n---\n# GTD Method\n## 概述\nDavid Allen's productivity framework.",
    "skills/leadership/servant-leadership/SKILL.md": "---\nname: servant-leadership\ndescription: 仆人式领导力。用于：当管理团队需要激发内在动力时\n---\n# Servant Leadership",
    "skills/communication/active-listening/SKILL.md": "---\nname: active-listening\ndescription: 积极倾听技能。用于：当需要建立深度沟通时\n---\n# Active Listening",
    "skills/drafts/unfinished_skill_draft.md": "---\nname: draft-skill\n---\n# Incomplete Draft\nThis skill is not yet ready.",
    "skills/deprecated/old-time-blocking.md": "Deprecated: Use calendar-blocking skill instead.",
    "tools/parsers/epub_parser.py": "# Placeholder for EPUB parsing utility\ndef parse_epub(path):\n    pass",
    "tools/converters/pdf_to_text.py": "# Placeholder for PDF conversion\ndef convert(path):\n    pass",
    "notes/reading_logs/2024_reading_log.txt": "Jan: Atomic Habits - 5/5\nFeb: Deep Work - 4/5\nMar: Essentialism - 5/5\nApr: The Pomodoro Technique - 4/5",
    "notes/summaries/q1_2024_summaries.md": "# Q1 2024 Book Summaries\nSee individual skill files for details.",
    "exports/json/skill_index.json": '{"skills": ["gtd-method", "servant-leadership", "active-listening"]}',
    "config/skill_template_config.yaml": "default_template: methodology\nlanguage: zh-CN\noutput_dir: skills/",
    "tmp/scratch.txt": "temp notes: pomodoro = 25 min work + 5 min break",
    "library/archive/classics/seven_habits_toc.txt": "Habit 1: Be Proactive\nHabit 2: Begin with the End in Mind\nHabit 3: Put First Things First",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# THE MAIN INPUT: A TXT book file about the Pomodoro Technique
# This is the "messy" input book the agent must process
book_content = """The Pomodoro Technique: The Acclaimed Time-Management System That Has Transformed How We Work
By Francesco Cirillo

INTRODUCTION

The Pomodoro Technique was invented in the late 1980s by then university student Francesco Cirillo, who was struggling with his studies and couldn't focus. Feeling overwhelmed, he asked himself to commit to just 10 minutes of focused study time. Encouraged by the challenge, he found a tomato-shaped kitchen timer (pomodoro in Italian), and the Pomodoro Technique was born.

Today, millions of people swear by this simple technique to help them power through distractions, hyper-focus, and get things done in short bursts, while taking frequent breaks to come up for air and relax.

PART ONE: THE BACKGROUND

Chapter 1: A Brief History of Time (and Tomatoes)

Francesco Cirillo named his system "Pomodoro" after the tomato-shaped kitchen timer he used as a university student. The core idea is deceptively simple: break work into intervals, traditionally 25 minutes in length, separated by short breaks.

The fundamental insight is that frequent breaks can improve mental agility. The ticking of the timer externalizes desire — the desire to procrastinate. The mind becomes focused on the work in front of it, not on what comes after.

Chapter 2: The Psychology of Time Boxing

Human brains are not designed for sustained, uninterrupted focus. The ultradian rhythm — natural cycles of alertness and rest — runs approximately 90-120 minutes. The Pomodoro Technique works with these natural rhythms rather than against them.

Key psychological mechanisms:
- Parkinson's Law: Work expands to fill the time available. Fixed time boxes counteract this.
- The Zeigarnik Effect: Unfinished tasks linger in working memory. Completing a pomodoro creates a sense of closure.
- Flow State: Short sprints make it easier to enter and sustain a state of flow.

PART TWO: THE CORE METHOD

Chapter 3: The Five Stages of the Pomodoro Technique

Stage 1: Planning
At the start of each day, create a To-Do Today list. Estimate the number of pomodoros each task will take. This forces you to break large tasks into concrete, manageable pieces.

Stage 2: Tracking
Record each pomodoro as you complete it. Mark interruptions — both internal (your own distracting thoughts) and external (colleagues, phone calls) — with specific symbols.

Stage 3: Recording
At the end of the day, compile your observations into a daily log. Note what you accomplished, how many pomodoros each task took, and how many interruptions occurred.

Stage 4: Processing
Turn raw data into actionable information. Identify patterns: Are certain tasks consistently underestimated? Are interruptions higher at certain times of day?

Stage 5: Visualizing
Create charts or simple tables to visualize your productivity patterns over time. Use this data to continuously improve your estimates and processes.

Chapter 4: The Rules of the Pomodoro Technique

Rule 1: A Pomodoro is Indivisible
Once started, a pomodoro must ring. If you are interrupted, the pomodoro is abandoned and must be restarted. This protects the integrity of focused work time.

Rule 2: If the Pomodoro Rings, the Work is Done
When the timer goes off, stop working — even if you're mid-sentence. This trains the brain to respect boundaries and prevents overwork.

Rule 3: Protect the Pomodoro
Learn to defer and negotiate interruptions. When someone asks for your attention, tell them: "I'll get back to you in X minutes." Then honor that commitment.

Rule 4: The Short Break is Sacred
Take your 5-minute break. Don't use it to check email. Stand up, stretch, walk around. The break is part of the technique, not a reward for finishing.

Rule 5: The Long Break Resets the Cycle
After every 4 pomodoros, take a 15-30 minute break. This allows the brain to consolidate learning and fully recover before the next set.

PART THREE: ADVANCED APPLICATIONS

Chapter 5: Handling Interruptions

Internal interruptions are thoughts that arise while working: "I should check on that email," "I need to remember to buy milk." When this happens, write the thought down on your interruption inventory, mark it with an apostrophe, and return to work immediately. Do not act on the thought.

External interruptions come from others. The strategy is: Inform, Negotiate, Schedule, Call Back.
- Inform: "I'm in the middle of something right now."
- Negotiate: "Can I get back to you in 20 minutes?"
- Schedule: Set a specific time to follow up.
- Call Back: Honor your commitment.

Chapter 6: Estimation and the Pomodoro

A key skill is estimating how many pomodoros a task will take. Begin with your best guess. Over time, your estimates will become more accurate. If a task takes more than 5-7 pomodoros, it should be broken down into smaller sub-tasks.

The Activity Inventory is a master list of all tasks you need to do. Every morning, select from this inventory what you'll work on today and estimate the pomodoros. This is your To-Do Today sheet.

Chapter 7: Team Pomodoro

The Pomodoro Technique can be applied to teams. Synchronize pomodoros across team members. Use a shared timer. During team pomodoros, individual members work on their tasks without interrupting each other. Discuss and coordinate during breaks.

Chapter 8: Common Mistakes and Misconceptions

Mistake 1: Treating the Timer as Optional
Many people start the timer but ignore it when it rings. The timer is not a suggestion. The rule that a pomodoro is indivisible means once you start, you commit to the full 25 minutes.

Mistake 2: Working Through Breaks
The break is not a weakness — it is the mechanism by which the technique works. Skipping breaks defeats the purpose and leads to burnout.

Mistake 3: Using Pomodoros for Everything
The Pomodoro Technique is ideal for tasks requiring sustained cognitive effort. It is not suitable for meetings, phone calls, or tasks that have natural, unpredictable stopping points.

Mistake 4: Forgetting to Record
The tracking and recording stages are what allow continuous improvement. Without data, you can't identify patterns or improve your estimates.

Mistake 5: Obsessing Over the Timer
Some practitioners become anxious about the timer itself. Remember: the goal is focus, not timer management. If the timer causes anxiety, experiment with longer or shorter intervals.

CONCLUSION

The Pomodoro Technique is deceptively simple. It requires no special software or equipment — just a timer and a pen. Its power lies in its consistency and the data it generates over time. By making time visible, tangible, and measurable, it transforms an abstract resource into something you can actively manage.

Start with one pomodoro. Then another. The tomato will take care of the rest.

APPENDIX: QUICK REFERENCE

The Pomodoro Formula:
- 25 minutes focused work = 1 Pomodoro
- 5 minute short break
- After 4 Pomodoros: 15-30 minute long break

The Daily Ritual:
1. Morning: Review Activity Inventory, create To-Do Today list with pomodoro estimates
2. During day: Work in pomodoros, track interruptions, protect each pomodoro
3. Evening: Record results, process data, update Activity Inventory
"""

book_path = os.path.join(workspace, "library/imported/2024/the_pomodoro_technique.txt")
with open(book_path, "w", encoding="utf-8") as f:
    f.write(book_content)

print("Workspace initialized successfully.")
print(f"Book file created at: {book_path}")
print("Distractor files created:", len(distractor_files))