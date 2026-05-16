import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create deeply nested distractor directory structure
dirs = [
    "project/scripts",
    "project/drafts/chapter_01",
    "project/drafts/chapter_02",
    "project/drafts/chapter_03",
    "project/research/references",
    "project/research/interviews",
    "project/characters/backstory",
    "project/characters/visual_notes",
    "project/notes/misc",
    "project/notes/revisions",
    "project/production/budget",
    "project/production/schedule",
    "archive/old_drafts",
    "archive/feedback",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "project/scripts/scene_12.txt": "INT. HOSPITAL CORRIDOR - NIGHT\nDr. Reyes walks past empty rooms, her footsteps echoing. She pauses at room 7.",
    "project/scripts/scene_13.txt": "EXT. PARKING LOT - DAY\nMarco sits in his car for twenty minutes before going inside.",
    "project/drafts/chapter_01/draft_v1.txt": "The first draft of chapter one, exploring the backstory of the two protagonists.",
    "project/drafts/chapter_01/draft_v2.txt": "Revised chapter one — cutting the flashback sequence as per director's notes.",
    "project/drafts/chapter_02/outline.txt": "Chapter 2 outline: confrontation between Dr. Reyes and Marco at the tribunal.",
    "project/drafts/chapter_03/notes.txt": "Chapter 3 should show Marco's breakdown — but avoid making it melodramatic.",
    "project/research/references/psychology_books.txt": "Bessel van der Kolk - The Body Keeps the Score\nJudith Herman - Trauma and Recovery\nJohn Bowlby - Attachment and Loss\nAaron Beck - Cognitive Therapy",
    "project/research/references/mbti_critique.txt": "Note: MBTI lacks test-retest reliability. Consider using Big Five instead for character depth.",
    "project/research/interviews/cast_interview_notes.txt": "Actor playing Marco wants to understand his character's contradictions. Why does he protect people he resents?",
    "project/research/interviews/director_notes.txt": "Director wants Dr. Reyes to feel 'real' — not a broken victim, not a superhero. Complicated.",
    "project/characters/backstory/reyes_background.txt": "Dr. Elena Reyes, 42. Grew up in a household with an emotionally unavailable father and a high-achieving mother who modeled silence as strength. Became a pediatric surgeon. Lost a patient at 34 — an 8-year-old named Tomás — due to a hospital system failure, not her error, but she testified against her own department chief.",
    "project/characters/backstory/marco_background.txt": "Marco Vitelli, 38. Former paramedic, now works hospital administration. Grew up as the eldest of five siblings; his parents divorced when he was 9. He became the 'fixer' in his family. Has a pattern of entering relationships where his partner is in crisis, then distancing when they stabilize. Two failed marriages.",
    "project/characters/visual_notes/reyes_visual.txt": "Elena: precise, controlled appearance. Always pressed clothes even on night shifts. Small tells: taps her left index finger when lying.",
    "project/characters/visual_notes/marco_visual.txt": "Marco: deliberately casual. Untucked shirt, friendly smile that doesn't reach his eyes when he's under pressure.",
    "project/notes/misc/genre_notes.txt": "Psychological thriller meets medical drama. The tension should come from the INTERNAL conflict, not just external plot.",
    "project/notes/misc/theme_notes.txt": "Central theme: the difference between being needed and being loved. Both characters confuse the two.",
    "project/notes/revisions/feedback_round1.txt": "Beta readers say Marco feels 'thin' — they don't understand why he keeps undermining Elena if he admires her.",
    "project/notes/revisions/feedback_round2.txt": "Elena's reaction to the tribunal scene felt unbelievable. She wouldn't just go cold — there must be something driving the shutdown.",
    "project/production/budget/budget_v2.xlsx": "This is a placeholder for the budget spreadsheet.",
    "project/production/schedule/shoot_schedule.csv": "scene,location,date\n12,hospital_corridor,2024-03-15\n13,parking_lot,2024-03-16",
    "archive/old_drafts/original_concept.txt": "Original concept: two doctors fall in love during a malpractice investigation. Too simple — needs psychological depth.",
    "archive/feedback/editor_notes.txt": "The relationship between Reyes and Marco needs to feel psychologically inevitable. Why THESE two? What wound does each one touch in the other?",
}

for path, content in distractors.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# The main task request file that the agent will read
task_request = """PROJECT: "The Tribunal" — Psychological Character Brief Request
==================================================================

TO: Psychological Consultant
FROM: Narrative Development Team
RE: Character Documentation for Dr. Elena Reyes and Marco Vitelli

We are in pre-production on "The Tribunal," a psychological drama series. We need 
rigorous, academically grounded psychological documentation for our two lead characters 
so that our writing team can maintain consistency across 8 episodes.

THE CHARACTERS:
--------------
Dr. Elena Reyes (42): See project/characters/backstory/reyes_background.txt
Marco Vitelli (38): See project/characters/backstory/marco_background.txt

WHAT WE NEED:
------------
1. A complete psychological profile for EACH character — structured and detailed enough 
   that any writer joining the project mid-season can understand how each character 
   thinks, defends, and breaks down.

2. An analysis of the RELATIONSHIP DYNAMIC between Elena and Marco — specifically what 
   makes their dynamic both compelling and combustible. Our editor (see archive/feedback/editor_notes.txt) 
   asked: "Why THESE two? What wound does each one touch in the other?"

3. Everything must be grounded in actual psychological science, not pop psychology.
   Writers need to know WHICH frameworks you're using and WHY, so they can push back 
   intelligently if something feels wrong for the story.

DELIVERABLE:
-----------
Please produce a single file named: character_psychology_brief.md

This should contain all three pieces of documentation described above. The writing team 
will use this as the canonical psychological reference document for the entire production.

IMPORTANT NOTES FROM DIRECTOR:
- Do NOT flatten these characters into diagnoses or archetypes.
- Marco's behavior of entering relationships when partners are in crisis, then leaving 
  when they stabilize — there must be a specific psychological explanation for this pattern.
- Elena's "going cold" response needs to be explained as a specific mechanism, not just 
  described as "she shuts down."
- Both characters should have ADAPTIVE strengths, not just pathologies.
- The analysis of their relationship should identify the SPECIFIC moments/triggers that 
  would escalate conflict between them.
"""

with open(os.path.join(workspace, "TASK_REQUEST.txt"), "w", encoding="utf-8") as f:
    f.write(task_request)

print("Workspace generated successfully.")
print(f"Files created: {len(distractors) + 1}")