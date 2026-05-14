import os
import random
import textwrap

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── references directory (the real content the agent needs) ──────────────────
refs = os.path.join(workspace, "references")
os.makedirs(refs, exist_ok=True)

# The main reference text (al-amr al-mutlaq) – realistic Islamic-ethics article
al_amr_text = textwrap.dedent("""\
# Al-Amr al-Mutlaq (The Absolute Command)

## Introduction

In the science of usul al-fiqh (the foundations of Islamic jurisprudence), one of the most
consequential discussions concerns the nature of a command (al-amr) when it arrives without
any qualifying conditions. Scholars have debated for centuries: when Allah or His Messenger
issues an imperative without a specifying context, what does that command obligate?

## The Core Thesis

The dominant position among Hanafi, Shafi'i, and Hanbali jurists holds that an absolute command
(al-amr al-mutlaq) implies wujub — legal obligation — unless contextual evidence (qarinah)
indicates otherwise. This is grounded in the principle that divine speech carries its weightiest
implication by default.

## Historical Disagreement

A minority of scholars, including some Mu'tazilites and certain later Maliki voices, argued that
an unqualified command implies only nadab (recommendation), not obligation. Their argument rested
on the view that obligation requires additional proof of consequential harm for non-compliance.
Al-Amidi and Ibn al-Hajib documented these positions extensively in their compendia.

## Evidence from the Quran and Sunnah

Several Quranic verses are invoked in this debate:
- "Establish the prayer" (Aqimu al-salah) — taken as an absolute obligating command.
- "And give zakat" — similarly treated.
Scholars note that the Prophet's companions (sahabah) consistently treated unqualified imperatives
as binding obligations, forming a powerful consensus argument (ijma').

## The Role of Qarinah (Contextual Indicator)

The concept of qarinah is pivotal: a surrounding indicator can elevate a command to obligation or
reduce it to mere permissibility. For example, "Eat and drink" is a permissive command, not
obligatory, because the context of personal sustenance provides the qualifying indicator.
Without such indicators, obligation remains the default.

## Implications for Contemporary Ethics

This principle has direct consequences for Islamic bioethics, financial ethics, and social
responsibility. When modern fatwas are issued, the framing of the command — absolute or
conditioned — determines the level of binding force on the Muslim community.

## Conclusion

Al-amr al-mutlaq is not a minor technicality; it is an architectural pillar of Islamic legal
reasoning. Understanding whether a divine or prophetic imperative is absolute or modified shapes
every fatwa, every ethical guideline, and every community standard derived from sacred texts.
""")

with open(os.path.join(refs, "al-amr-al-mutlaq.md"), "w", encoding="utf-8") as f:
    f.write(al_amr_text)

# The templates file (as referenced in SKILL.md)
templates_text = textwrap.dedent("""\
# Content Workbench Templates

## Summary Template
**Summary:**
[5–10 key points as bullet list]

**Key Takeaways:**
1. [Takeaway 1]
2. [Takeaway 2]
3. [Takeaway 3]

---

## Post Variant Templates

### Variant 1 — Hook + 2 Short Paragraphs + Question
[Attention-grabbing hook sentence.]

[Paragraph 1: main idea, 2–4 sentences.]

[Paragraph 2: elaboration or implication, 2–4 sentences.]

[Closing question to the reader?]

---

### Variant 2 — Bullet Points + Closing Question
Key insights:
- [Point 1]
- [Point 2]
- [Point 3]
- [Point 4]

[Closing question to the reader?]

---

### Variant 3 — Short Story/Analogy + Lesson + Question
[A brief story or analogy (3–5 sentences).]

**Lesson:** [One or two sentences summarising the takeaway.]

[Closing question to the reader?]

---

## Archive Entry Template
Title / Angle / Draft / Question / Tags

---

## Discussion Questions Template
1. [Reflective question]
2. [Critical question]
3. [Practical question]
4. [Reflective question]
5. [Critical question]
""")

with open(os.path.join(refs, "templates.md"), "w", encoding="utf-8") as f:
    f.write(templates_text)

# ── Distractor files (realistic messy editorial workspace) ───────────────────

# drafts/ directory with old, irrelevant drafts
drafts_dir = os.path.join(workspace, "drafts")
os.makedirs(drafts_dir, exist_ok=True)

old_drafts = {
    "draft_riba_post_v1.txt": "Riba is prohibited. First draft — needs editing. TODO: add hadith citation.",
    "draft_riba_post_v2.txt": "An updated take on riba prohibition — still missing source checks.",
    "draft_waqf_intro.txt": "Waqf (Islamic endowment) offers an alternative finance model...\n[INCOMPLETE]",
    "zakat_notes_scratch.txt": "Random notes: nisab threshold, lunar year calculation, etc.\nDO NOT PUBLISH",
    "old_summary_attempt.md": "# Old Summary\nThis was a failed attempt at summarising a different article.\n- Point 1\n- Point 2\n[ABANDONED]",
}

for name, content in old_drafts.items():
    with open(os.path.join(drafts_dir, name), "w", encoding="utf-8") as f:
        f.write(content)

# archive/ directory with existing (unrelated) archive entries
archive_dir = os.path.join(workspace, "archive")
os.makedirs(archive_dir, exist_ok=True)

existing_archive = textwrap.dedent("""\
    Riba in Modern Banking / Historical prohibition vs. modern finance / [draft pending] / Is interest ever permissible under necessity? / fiqh, finance, riba
    Waqf Revival / Community endowment model / [draft pending] / How can waqf fund local mosques? / waqf, community, finance
""")
with open(os.path.join(archive_dir, "editorial_calendar.md"), "w", encoding="utf-8") as f:
    f.write(existing_archive)

# notes/ directory with meeting notes and random fragments
notes_dir = os.path.join(workspace, "notes")
os.makedirs(notes_dir, exist_ok=True)

with open(os.path.join(notes_dir, "team_meeting_2024-01-15.txt"), "w") as f:
    f.write("Team meeting notes:\n- Need more content on usul al-fiqh basics\n- Prioritise sourced content\n- Avoid plagiarism\n")

with open(os.path.join(notes_dir, "style_guide_fragments.txt"), "w") as f:
    f.write("Tone: scholarly but accessible.\nAudience: educated Muslim laypeople.\nLength: keep posts concise.\n[INCOMPLETE GUIDE]\n")

with open(os.path.join(notes_dir, "rejected_headlines.txt"), "w") as f:
    f.write("Rejected: 'You MUST do this!' (too clickbait)\nRejected: 'Scholars HATE this trick' (inappropriate)\n")

# research/ directory with tangentially related documents
research_dir = os.path.join(workspace, "research")
os.makedirs(research_dir, exist_ok=True)

with open(os.path.join(research_dir, "usul_al_fiqh_overview.txt"), "w") as f:
    f.write("Usul al-Fiqh — the roots of Islamic jurisprudence — covers sources, legal reasoning, and principles.\nThis is a background document, NOT the main reference text for this task.\n")

with open(os.path.join(research_dir, "ijma_notes.txt"), "w") as f:
    f.write("Ijma = scholarly consensus. One of the four primary sources of Islamic law.\n[Raw research notes, unformatted]\n")

with open(os.path.join(research_dir, "qarinah_examples_raw.txt"), "w") as f:
    f.write("Examples of qarinah from classical texts:\n1. Context of permissive eating commands\n2. Specific hadith contexts\n[Needs verification before use]\n")

# logs/ and tmp/ to add more noise
logs_dir = os.path.join(workspace, "logs")
os.makedirs(logs_dir, exist_ok=True)

with open(os.path.join(logs_dir, "publish_log_2023.txt"), "w") as f:
    f.write("2023-11-01: Published riba article\n2023-11-15: Published tawakkul post\n2023-12-01: Published sadaqah series part 1\n")

tmp_dir = os.path.join(workspace, "tmp")
os.makedirs(tmp_dir, exist_ok=True)

with open(os.path.join(tmp_dir, "clipboard_dump.txt"), "w") as f:
    f.write("Misc paste: 'obligatory prayers are five daily' — needs citation check\nTODO: find original source\n")

with open(os.path.join(tmp_dir, "word_counts.txt"), "w") as f:
    f.write("riba_post_v2: 203 words (too long)\nwaqf_intro: 87 words (too short)\n")

print("Workspace initialised successfully.")
print(f"Directory tree root: {workspace}")