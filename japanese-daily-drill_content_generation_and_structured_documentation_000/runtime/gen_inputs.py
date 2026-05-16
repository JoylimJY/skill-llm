import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Create SKILL.md ---
skill_md_content = '''---
name: Japanese Daily Drill
slug: japanese-daily-drill
description: Generates a personalised Japanese language practice session based on JLPT level. Covers vocabulary, grammar, kanji, reading, and speaking prompts. Fresh content every session.
version: 1.0.0
author: tetsuakira-vk
license: MIT
tags: [japanese, jlpt, language-learning, vocabulary, grammar, kanji, daily-practice]
---

# Japanese Daily Drill

You are an expert Japanese language teacher with deep knowledge of the JLPT exam system and natural Japanese communication. When a user requests a drill, you generate a complete, fresh daily practice session tailored to their level.

## Detecting level

Ask the user their JLPT level if not specified: "What\'s your current level? (N5 = beginner, N4, N3, N2, N1 = near-native)"

Levels:
- N5 — absolute beginner, hiragana/katakana, basic vocabulary
- N4 — elementary, simple kanji, basic grammar patterns
- N3 — intermediate, more complex grammar, everyday conversation
- N2 — upper intermediate, formal language, nuanced grammar
- N1 — advanced, native-level text, abstract vocabulary

## Session structure

Generate all sections in a single response.

---

### 1. Vocabulary (10 words)

For each word provide:
- The word in Japanese script (kanji where appropriate, with furigana in brackets)
- Romaji pronunciation
- English meaning
- One example sentence in Japanese with English translation
- A memory tip where useful

Mark JLPT level relevance: [N5] [N4] etc.

---

### 2. Grammar pattern of the day (1 pattern)

- Pattern name and structure
- Plain English explanation of when and how to use it
- 3 example sentences ranging from simple to complex
- Common mistakes to avoid
- How it differs from a similar pattern (if applicable)

---

### 3. Kanji focus (3 kanji for N4 and above, skip for N5)

For each kanji:
- The character
- Readings: on\'yomi and kun\'yomi
- Stroke count
- 2 compound words using this kanji
- 1 example sentence

---

### 4. Reading passage

- Short passage appropriate to the level (50 words for N5, up to 200 words for N1)
- Written entirely in Japanese (appropriate script mix for level)
- Follow with full English translation
- Highlight 3 key vocabulary or grammar points from the passage

---

### 5. Listening/speaking prompt

- A conversation scenario appropriate to the level
- A sample dialogue (2–4 exchanges) in Japanese with English translation
- 3 speaking prompts the user can practise responding to aloud
- Suggested response vocabulary

---

### 6. Quick quiz (5 questions)

Mix of:
- Vocabulary matching
- Fill in the blank (grammar)
- Kanji reading (N4 and above)
- Translation (English to Japanese)

Provide answers at the bottom, clearly separated with a divider.

---

## Session freshness

Never repeat the same vocabulary, kanji, or grammar patterns within the same conversation. If the user asks for another session, generate completely fresh content.

## Cultural note

End every session with one short cultural note relevant to the language — a Japanese custom, etiquette point, or interesting linguistic fact. Keep it to 2–3 sentences.

## Memory tip

If the user says "I keep forgetting X" or "X is hard for me", create a custom mnemonic or memory device for that specific word or pattern before continuing.
'''

(workspace / "SKILL.md").write_text(skill_md_content, encoding="utf-8")

# --- Realistic deeply nested distractor directory structure ---

dirs = [
    "curriculum/jlpt/n3/grammar",
    "curriculum/jlpt/n3/vocab",
    "curriculum/jlpt/n5/grammar",
    "curriculum/jlpt/n5/vocab",
    "curriculum/jlpt/n1/advanced",
    "platform/backend/api",
    "platform/frontend/components",
    "platform/frontend/assets",
    "students/progress_reports/2024",
    "students/progress_reports/2023",
    "tools/scripts",
    "tools/validators",
    "content/templates",
    "content/legacy_sessions",
    "exports/pdf",
    "exports/json",
    "logs/system",
    "logs/user_activity",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files with plausible but misleading content
distractor_files = {
    "curriculum/jlpt/n3/grammar/pattern_list_draft.txt": """N3 Grammar Patterns (DRAFT - incomplete)
~ために
~ながら
~てしまう
~ばかり
NOTE: This list is not finalized. Do not use for generation.""",

    "curriculum/jlpt/n3/vocab/n3_word_list_partial.csv": """word,reading,meaning,status
友達,ともだち,friend,confirmed
学校,がっこう,school,confirmed
仕事,しごと,work,confirmed
NOTE: Only 3 words, list is incomplete and NOT the source of truth.""",

    "curriculum/jlpt/n5/grammar/n5_patterns.json": json.dumps({
        "patterns": ["〜は〜です", "〜ますか", "〜ている"],
        "note": "N5 level only - no kanji section required",
        "warning": "Do not apply N5 rules to N3 sessions"
    }, ensure_ascii=False, indent=2),

    "curriculum/jlpt/n5/vocab/hiragana_only_words.txt": """N5 Vocabulary (hiragana-only, no kanji required)
ありがとう - thank you
おはよう - good morning
This file is for N5 ONLY.""",

    "platform/backend/api/session_generator_stub.py": """# STUB - NOT FUNCTIONAL
# This was a planned API endpoint for session generation
# Status: abandoned in favor of direct LLM approach

def generate_session(level: str):
    # TODO: implement
    raise NotImplementedError("Use SKILL.md directly")
""",

    "platform/frontend/components/DrillCard.jsx": """// React component stub
// Displays a drill session card
// Expected props: { level, sections, date }
export const DrillCard = ({ level, sections }) => {
  // Renders sections - expects markdown content
  return null; // TODO
};
""",

    "students/progress_reports/2024/student_007_report.json": json.dumps({
        "student_id": "007",
        "name": "Kenji Tanaka",
        "current_level": "N3",
        "sessions_completed": 12,
        "weak_areas": ["kanji", "grammar_て_form"],
        "last_session_date": "2024-01-15",
        "notes": "Needs fresh N3 drill session urgently"
    }, ensure_ascii=False, indent=2),

    "students/progress_reports/2023/summary_2023.txt": """Annual summary 2023
Total students: 45
N5: 18, N4: 12, N3: 10, N2: 4, N1: 1
Most common struggle: kanji readings for N3+
Action: Generate more targeted drill sessions""",

    "tools/validators/session_checker_todo.py": """# TODO: Build a validator for drill session output
# Requirements gathered from curriculum team:
# - Must have all 6 sections
# - Vocab: exactly 10 words
# - Kanji: 3 entries for N4+, skipped for N5
# - Quiz: 5 questions with answers separated by a divider
# - Must end with cultural note
# Status: not yet implemented""",

    "tools/scripts/old_session_template.md": """# OLD TEMPLATE (DEPRECATED 2022)
## Words (5 words only - OLD FORMAT)
## Grammar
## Quiz (3 questions - OLD FORMAT)
DO NOT USE - replaced by SKILL.md v1.0.0""",

    "content/templates/blank_session_template.md": """# Daily Drill Session
## Level: [INSERT LEVEL]
## Date: [INSERT DATE]

[SECTIONS TO BE FILLED BY GENERATOR]

---
This template is intentionally blank.
Do NOT submit this file as the output.
The output file must be named drill_session.md""",

    "content/legacy_sessions/session_2023_11_n3_example.md": """# N3 Session - LEGACY EXAMPLE (2023, outdated format)
## Words (only 7 - OLD FORMAT, non-compliant)
1. 心配 - worry
2. 準備 - preparation
...
## No kanji section (BUG - this was incorrect)
## Quiz - only 3 questions (BUG)
NOTE: This legacy file is NON-COMPLIANT with current SKILL.md v1.0.0
Do not replicate this format.""",

    "exports/json/session_schema_draft.json": json.dumps({
        "schema_version": "0.9-draft",
        "note": "This schema is incomplete and not authoritative",
        "sections": {
            "vocabulary": "array of words",
            "grammar": "object",
            "kanji": "array, required for N4+",
            "reading": "object",
            "speaking": "object",
            "quiz": "array of 5 questions"
        },
        "warning": "Defer to SKILL.md for authoritative spec"
    }, indent=2),

    "logs/system/generation_errors_2024.log": """2024-01-10 09:12:33 ERROR: Session for N3 missing kanji section - rejected
2024-01-11 14:45:01 ERROR: Vocab count was 8, expected 10 - rejected
2024-01-12 08:30:22 ERROR: Quiz answers not separated by divider - rejected
2024-01-13 11:00:45 ERROR: Cultural note missing - rejected
2024-01-14 16:20:10 ERROR: Reading passage had no English translation - rejected
2024-01-15 09:05:33 ERROR: Speaking prompt missing 3 practice prompts - rejected""",

    "logs/user_activity/student_007_activity.log": """2024-01-15 StudentID:007 Level:N3 RequestType:NewSession
2024-01-15 StudentID:007 Action:CompletedQuiz Score:3/5
2024-01-14 StudentID:007 Action:RequestedSession Fulfilled:false Reason:generation_error""",

    "curriculum/jlpt/n1/advanced/n1_grammar_notes.txt": """N1 Advanced Grammar Notes
- Abstract vocabulary required
- Native-level text complexity
- Reading passage: up to 200 words
These notes are for N1 only - not applicable to N3 sessions.""",
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")

print("Workspace initialized successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")