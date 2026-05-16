import os
import random

random.seed(42)

# Create deep directory structure
dirs = [
    "notes",
    "frameworks",
    "meetings",
    "product/roadmap",
    "product/specs",
    "engineering/backend",
    "engineering/frontend",
    "design/mockups",
    "research/user_interviews",
    "marketing/campaigns",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# --- MAIN INPUT FILE 1: notes/ideas.md ---
# Has an existing idea entry about AI Quiz Generator that the agent must append to
ideas_md = """\
# Ideas Inbox

Last updated: 2024-11-15

---

## Idea: Smart Classroom Scheduler
*Added: 2024-11-01*

Use ML to auto-schedule classrooms based on historical booking patterns and student density. Could reduce conflicts by 40%.

Tags: #ml #scheduling #admin

---

## Idea: AI Quiz Generator
*Added: 2024-11-14*

A tool that ingests a lecture transcript or PDF and automatically generates multiple-choice, short-answer, and fill-in-the-blank quiz questions. Teachers review and publish. Students get personalized quizzes based on weak areas.

Current pain: Teachers spend 3-5 hours creating assessments per week. This could cut it to 30 minutes.

Tags: #ai #assessment #edtech #teachers

---

## Idea: Peer Review Matching Engine
*Added: 2024-11-15*

Match students for peer review assignments based on complementary skill gaps rather than random assignment.

Tags: #peerlearning #ml #assessment

---
"""

with open("notes/ideas.md", "w") as f:
    f.write(ideas_md)

# --- MAIN INPUT FILE 2: frameworks/spaced_repetition_framework.md ---
spaced_rep = """\
# Spaced Repetition Framework for EdTech

## Overview

Spaced Repetition is a learning technique that schedules review sessions at increasing intervals, exploiting the "spacing effect" to improve long-term retention.

## Core Components

1. **Initial Encoding**: Student encounters material for the first time.
2. **First Review**: 1 day after initial encounter.
3. **Second Review**: 3 days after first review.
4. **Subsequent Reviews**: Interval roughly doubles each time (7, 14, 30 days...).
5. **Difficulty Weighting**: Cards answered incorrectly reset to shorter intervals.

## Implementation Notes

- Typically implemented via flashcard systems (Anki, SuperMemo)
- SM-2 algorithm is the most widely used scheduling algorithm
- Works best for factual/declarative knowledge
- Requires consistent daily engagement from learners

## Current Limitations

- Feels repetitive and demotivating for many students
- Not adapted for collaborative learning contexts
- Assumes individual study sessions only
- Hard to integrate with classroom curricula

## Metrics

- Retention rate at 30 days
- Daily active review sessions
- Average interval growth rate
"""

with open("frameworks/spaced_repetition_framework.md", "w") as f:
    f.write(spaced_rep)

# --- DISTRACTOR FILES ---

# Meeting notes
with open("meetings/2024_11_10_product_sync.md", "w") as f:
    f.write("""\
# Product Sync - Nov 10 2024

Attendees: Alice, Bob, Carol

## Agenda
1. Q4 roadmap review
2. Teacher feedback from interviews
3. Engineering capacity

## Notes
- Alice: Quiz generator MVP targeting Dec release
- Bob: Backend capacity is tight, need to prioritize
- Carol: User research shows teachers want bulk import

## Action Items
- [ ] Alice: Draft spec by Nov 15
- [ ] Bob: Estimate quiz generation API effort
""")

with open("meetings/2024_11_05_design_review.md", "w") as f:
    f.write("""\
# Design Review - Nov 5 2024

Reviewed mockups for the new dashboard. Feedback: too cluttered.
Redesign to focus on 3 primary actions only.
""")

# Product specs
with open("product/specs/quiz_generator_spec.md", "w") as f:
    f.write("""\
# Quiz Generator - Technical Spec v0.2

## Input
- PDF, DOCX, or plain text lecture transcript
- Max 50 pages / 25,000 tokens

## Processing Pipeline
1. Text extraction
2. Key concept identification (NER + topic modeling)
3. Question generation (GPT-4 fine-tuned on educational QA pairs)
4. Distractor generation for MCQ
5. Teacher review interface

## Output
- JSON question bank
- Export to Google Forms, Canvas LMS, Moodle

## Open Questions
- How to handle math/formulas?
- Image-based content (diagrams)?
""")

with open("product/roadmap/q4_2024.md", "w") as f:
    f.write("""\
# Q4 2024 Roadmap

## Must Have
- Quiz Generator MVP
- Grade export to CSV

## Should Have  
- Peer Review Matching v1
- Parent dashboard

## Nice to Have
- AI Tutoring chatbot
- Gamification layer
""")

# Engineering files
with open("engineering/backend/quiz_api.py", "w") as f:
    f.write("""\
# Quiz Generator API (stub)
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate_quiz():
    transcript = request.json.get('transcript', '')
    # TODO: implement actual generation
    return jsonify({'questions': [], 'status': 'not_implemented'})

if __name__ == '__main__':
    app.run(debug=True)
""")

with open("engineering/backend/config.py", "w") as f:
    f.write("""\
DATABASE_URL = 'postgresql://localhost:5432/edtech_dev'
REDIS_URL = 'redis://localhost:6379'
MODEL_ENDPOINT = 'http://ml-service:8080/predict'
MAX_TOKENS = 25000
""")

with open("engineering/frontend/package.json", "w") as f:
    f.write("""\
{
  "name": "edtech-frontend",
  "version": "0.3.1",
  "dependencies": {
    "react": "^18.2.0",
    "axios": "^1.6.0",
    "tailwindcss": "^3.3.0"
  }
}
""")

# Research files
with open("research/user_interviews/teacher_feedback_nov.md", "w") as f:
    f.write("""\
# Teacher Feedback - November Interviews

## Participant 1: High School Biology Teacher
- Spends 4 hours/week on assessments
- Wants bulk generation from existing slides
- Concerned about AI accuracy for science content

## Participant 2: University CS Professor
- Already uses GitHub Classroom
- Wants integration with existing LMS
- Interested in auto-grading open-ended questions

## Common Themes
- Time savings is the #1 value prop
- Teachers want to stay in control / review before publish
- Privacy concerns about student data
""")

with open("research/user_interviews/student_feedback_oct.md", "w") as f:
    f.write("""\
# Student Feedback - October Survey (n=120)

- 78% find current quizzes repetitive
- 65% want immediate feedback after answering
- 42% study in groups but tools don't support it
- Top request: explain WHY an answer is wrong
""")

# Marketing
with open("marketing/campaigns/q4_launch.md", "w") as f:
    f.write("""\
# Q4 Launch Campaign

## Target Audience
- K-12 teachers in US/Canada
- EdTech coordinators

## Key Messages
1. Save 3+ hours per week on assessment creation
2. Personalized learning at scale
3. Works with your existing LMS

## Channels
- LinkedIn (teacher communities)
- EdSurge newsletter
- Education conference booths (ISTE, FETC)
""")

# Design
with open("design/mockups/quiz_review_ui_notes.md", "w") as f:
    f.write("""\
# Quiz Review UI - Design Notes

## Layout
- Left: Question list (scrollable)
- Right: Question editor
- Top: Publish / Save Draft buttons

## Key Interactions
- Drag to reorder questions
- Inline edit question text and options
- Tag questions by difficulty (Easy/Medium/Hard)
- Bulk select for delete

## Open Questions
- Should AI confidence score be visible to teacher?
""")

with open("design/mockups/dashboard_v2_notes.md", "w") as f:
    f.write("""\
# Dashboard v2 - Notes

Reduce primary actions to 3:
1. Create Quiz
2. View Results
3. Manage Classes

Remove: notification center (low usage), badge system (not working)
""")

# Changelog
with open("product/specs/changelog.md", "w") as f:
    f.write("""\
# Changelog

## v0.3.1 (2024-11-12)
- Fixed PDF parser crash on scanned documents
- Improved MCQ distractor quality for STEM content

## v0.3.0 (2024-11-01)
- Added short-answer question type
- Teacher review interface beta

## v0.2.0 (2024-10-15)
- Initial MCQ generation from plain text
""")

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk("."):
    for fname in files:
        print(f"  {os.path.join(root, fname)}")