import os
import random
import textwrap

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Project directory structure (distractor files) ──────────────────────────
dirs = [
    "edtech-sprint/sessions",
    "edtech-sprint/sessions/raw",
    "edtech-sprint/sessions/archive",
    "edtech-sprint/design",
    "edtech-sprint/design/mockups",
    "edtech-sprint/design/wireframes",
    "edtech-sprint/backend/services",
    "edtech-sprint/backend/models",
    "edtech-sprint/frontend/components",
    "edtech-sprint/data/samples",
    "edtech-sprint/data/exports",
    "edtech-sprint/team/retros",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "edtech-sprint/design/quiz_ui_spec.txt": "UI spec v0.3 — button radius 4px, font Inter 14px...",
    "edtech-sprint/design/mockups/quiz_flow_draft.txt": "Mockup notes: loading state, error boundary...",
    "edtech-sprint/design/wireframes/learner_dashboard.txt": "Dashboard wireframe — show streak, badges, progress ring.",
    "edtech-sprint/backend/services/auth_service.py": "# OAuth2 service stub\ndef verify_token(tok): pass",
    "edtech-sprint/backend/models/learner.py": "class Learner:\n    id: str\n    level: int",
    "edtech-sprint/backend/models/quiz.py": "class Quiz:\n    id: str\n    difficulty: float",
    "edtech-sprint/frontend/components/QuizCard.jsx": "export const QuizCard = ({quiz}) => <div>{quiz.title}</div>",
    "edtech-sprint/data/samples/quiz_bank_v1.json": '[{"id":"q1","difficulty":0.3},{"id":"q2","difficulty":0.7}]',
    "edtech-sprint/data/exports/learner_export_2024Q1.csv": "learner_id,score,date\nL001,82,2024-01-10\nL002,67,2024-01-11",
    "edtech-sprint/team/retros/sprint_01_retro.txt": "What went well: good velocity. Delta: need clearer acceptance criteria.",
    "edtech-sprint/team/retros/sprint_02_retro.txt": "What went well: quiz calibration stable. Delta: diagnosis module needs more data.",
    "edtech-sprint/sessions/archive/early_idea_dump.txt": "Random brainstorming — AI tutor, gamification, spaced repetition maybe?",
}
for path, content in distractors.items():
    with open(os.path.join(workspace, path), "w") as f:
        f.write(content)

# ── The main artifact the agent must process ─────────────────────────────────
# A realistic, messy collaboration transcript with TWO separable capabilities
# buried inside — quiz difficulty calibration and learner weakness diagnosis.
# The transcript contains dead ends, corrections, and decision points.

transcript = textwrap.dedent("""
=== EDTECH ADAPTIVE QUIZ — COLLABORATION SESSION LOG ===
Date: 2024-03-15  |  Participants: Product Lead (PL), AI Agent (AG)

[09:02] PL: Okay, let's figure out how to make our quizzes actually adapt.
       Right now we just randomly pick questions. Learners are complaining.

[09:04] AG: Got it. A simple approach: sort questions by difficulty tag, pick
       the nearest to the learner's last score. Done.

[09:05] PL: That's too naive. Last score is noisy. We tried that in January —
       it over-calibrates after one bad session. We need rolling history.

[09:06] AG: Fair correction. So: compute a rolling average of the last N sessions,
       use that as the calibration anchor.

[09:08] PL: Better. But what's N? We experimented with N=3, N=5, N=7.
       N=5 was most stable — outliers get smoothed without lagging too much.

[09:09] AG: N=5 rolling average → difficulty anchor. Then we select the 3 questions
       closest to that anchor difficulty. That's the calibration rule.

[09:11] PL: Yes. And there's a guard: if the learner's average is in the top 10%
       of our difficulty range, cap calibration at 90th percentile — we don't want
       to expose unseen content prematurely. That was a key guard we added after
       week-2 testing.

[09:13] AG: Important. Without that cap, high performers would hit unreviewed
       questions and get inconsistent feedback. So: cap at P90 if anchor > P90.

[09:15] PL: Right. And we discovered something orthogonal: even calibrated
       difficulty doesn't tell us WHICH topic is weak. A learner at difficulty=0.6
       might be strong in algebra but terrible in geometry. The calibration doesn't
       see that. We need a separate diagnosis pass.

[09:17] AG: So two concerns: (1) what difficulty level to serve, (2) which topic
       areas are weak. They use different signals and produce different outputs.

[09:18] PL: Exactly. Don't confuse them. Calibration takes score history → outputs
       difficulty target. Diagnosis takes per-topic error rates → outputs a weakness
       map. They're independent — diagnosis doesn't need calibration to run first.

[09:21] AG: For diagnosis: we track per-topic error rates over last 10 attempts,
       flag any topic where error rate > 40% as a weak zone.

[09:22] PL: We initially tried 30%, too noisy. 40% was the threshold that correlated
       with learner self-report. Also: if a learner has fewer than 5 attempts on a
       topic, mark it as "insufficient data" — don't flag it as weak or strong.

[09:24] AG: Got it. So diagnosis rule: per-topic, last 10 attempts, error rate > 40%
       AND at least 5 attempts → weak zone. Otherwise insufficient data.

[09:26] PL: And these two — calibration and diagnosis — should be packaged separately.
       Other teams (content team, analytics team) only need diagnosis, not calibration.
       Bundling them wastes everyone's time.

[09:28] AG: Understood. They're independent capabilities with different consumers.
       Two separate packages.

[09:30] PL: One more thing: for calibration, we went back and forth on whether
       to use raw scores or normalized scores. Raw scores are faster but platform-
       dependent (quiz lengths vary). We settled on normalized: score / max_possible.
       This was a non-obvious decision — easy to get wrong if you just follow the
       naive path.

[09:32] AG: Normalization is a critical design choice. Without it, a 20-question
       quiz score isn't comparable to a 5-question quiz score, breaking calibration
       across quiz types.

[09:34] PL: Exactly. Okay, I think we have two stable, reusable methods here.
       Let's make sure future teams don't have to rediscover all this.

[09:35] AG: Agreed. Let's lock it in.

=== END OF SESSION LOG ===
""")

with open(os.path.join(workspace, "edtech-sprint/sessions/raw/collab_session_2024-03-15.txt"), "w") as f:
    f.write(transcript)

# A second, older partial session (distractor — not a true collaborative product)
partial = textwrap.dedent("""
=== EARLY EXPLORATION LOG ===
Date: 2024-02-01

[10:00] PL: Can we just use a pre-trained IRT model off the shelf?
[10:01] AG: We could. It would need calibration data we don't have yet.
[10:02] PL: Let's table this. Not ready.

=== ABANDONED ===
""")
with open(os.path.join(workspace, "edtech-sprint/sessions/archive/abandoned_irt_exploration.txt"), "w") as f:
    f.write(partial)

print("Workspace generated successfully.")
print("Key file: edtech-sprint/sessions/raw/collab_session_2024-03-15.txt")