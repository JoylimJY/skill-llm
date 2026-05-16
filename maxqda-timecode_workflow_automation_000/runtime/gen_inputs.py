import os
import random

random.seed(42)

workspace = "/workspace"

# --- Directory structure ---
dirs = [
    "research_project/fieldwork_2023/interviews/raw",
    "research_project/fieldwork_2023/interviews/processed",
    "research_project/fieldwork_2023/notes",
    "research_project/fieldwork_2024/interviews/raw",
    "research_project/fieldwork_2024/notes",
    "research_project/literature/sources",
    "research_project/analysis/codes",
    "research_project/analysis/memos",
    "research_project/exports/audio",
    "research_project/exports/video",
    "admin/ethics_forms",
    "admin/consent_forms",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files (non-.txt or irrelevant) ---
distractors = [
    ("research_project/fieldwork_2023/notes/fieldnotes_day1.md", "# Day 1 Fieldnotes\nArrived at site at 09:00. Met with coordinator.\n"),
    ("research_project/fieldwork_2023/notes/fieldnotes_day2.md", "# Day 2 Fieldnotes\nFollow-up session scheduled.\n"),
    ("research_project/literature/sources/bibliography.bib", "@article{smith2020, title={Qualitative Methods}, author={Smith, J.}, year={2020}}\n"),
    ("research_project/analysis/codes/codebook_v1.csv", "code,definition,memo\nTheme_A,First major theme,Emerging pattern\nTheme_B,Secondary theme,Needs review\n"),
    ("research_project/analysis/memos/memo_001.txt", "Memo: Possible connection between Theme_A and Theme_B. Review transcripts.\n"),
    ("research_project/exports/audio/session_01.mp3.placeholder", "AUDIO FILE PLACEHOLDER\n"),
    ("admin/ethics_forms/ethics_approval.pdf.placeholder", "ETHICS APPROVAL PLACEHOLDER\n"),
    ("admin/consent_forms/consent_template.docx.placeholder", "CONSENT FORM PLACEHOLDER\n"),
    ("research_project/fieldwork_2024/notes/observer_notes.md", "# Observer Notes 2024\nParticipant seemed relaxed. Good rapport.\n"),
    ("research_project/analysis/memos/memo_002.txt", "Memo: Consider deviant case analysis for outlier participant.\n"),
    ("research_project/fieldwork_2023/interviews/processed/placeholder.txt", "This directory is for processed transcripts.\n"),
]
for rel_path, content in distractors:
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# --- TARGET FILES: raw interview transcripts needing conversion ---
# File 1: Standard transcript with sub-60-minute timecodes, no BOM
# First line is a title that must be removed
transcript_1 = (
    "Interview Session 1 - Participant A - 2023-09-15\n"
    "提问者 00:02\n"
    "您好，感谢您参与这次访谈。\n"
    "回答者 00:45\n"
    "不客气，很高兴能参与。\n"
    "提问者 01:30\n"
    "请问您在这个领域工作多久了？\n"
    "回答者 02:10\n"
    "大约五年了。\n"
    "提问者 03:55\n"
    "您认为主要挑战是什么？\n"
    "回答者 04:20\n"
    "资源不足和时间压力是最大的挑战。\n"
)

# File 2: Transcript with OVER-60-minute timecodes (hours rollover), no BOM
# First line is a title that must be removed
transcript_2 = (
    "Interview Session 2 - Participant B - 2023-10-02\n"
    "提问者2 00:05\n"
    "我们继续上次的话题。\n"
    "受访者B 00:58\n"
    "好的，没问题。\n"
    "提问者2 59:30\n"
    "我们已经谈了将近一个小时，再问最后几个问题。\n"
    "受访者B 61:15\n"
    "当然可以。\n"
    "提问者2 65:45\n"
    "您对未来的发展有什么期待？\n"
    "受访者B 68:00\n"
    "希望看到更多的合作机会。\n"
    "提问者2 72:33\n"
    "非常感谢您的时间。\n"
    "受访者B 73:50\n"
    "感谢邀请。\n"
)

# File 3: Transcript with UTF-8 BOM, mixed timecodes
# First line is a title that must be removed
bom = b'\xef\xbb\xbf'
transcript_3_text = (
    "Interview Session 3 - Participant C - 2024-03-10\n"
    "Interviewer 00:00\n"
    "Good morning. Thank you for your time today.\n"
    "Participant_C 00:30\n"
    "Good morning. Happy to help.\n"
    "Interviewer 05:00\n"
    "Can you describe your role in the project?\n"
    "Participant_C 05:45\n"
    "I serve as the lead coordinator for the pilot phase.\n"
    "Interviewer 60:10\n"
    "We are now at the one-hour mark. Final question:\n"
    "Participant_C 62:55\n"
    "The most important lesson is stakeholder engagement.\n"
)

# File 4: Another standard transcript in fieldwork_2024, no BOM, normal timecodes
transcript_4 = (
    "Focus Group Alpha - Urban Community - 2024-06-20\n"
    "主持人 00:10\n"
    "欢迎大家参与今天的焦点小组讨论。\n"
    "参与者甲 00:50\n"
    "谢谢邀请我们。\n"
    "参与者乙 01:05\n"
    "很荣幸能参与。\n"
    "主持人 02:30\n"
    "今天我们主要讨论社区参与的问题。\n"
    "参与者甲 03:15\n"
    "我觉得社区参与度近年来有所提高。\n"
    "参与者丙 04:00\n"
    "但资源分配仍然不均衡。\n"
    "主持人 05:10\n"
    "大家有什么具体的建议吗？\n"
    "参与者乙 06:45\n"
    "需要更多基层工作者。\n"
)

# Write the target files
target_files = [
    ("research_project/fieldwork_2023/interviews/raw/session_01_participantA.txt", transcript_1, False),
    ("research_project/fieldwork_2023/interviews/raw/session_02_participantB.txt", transcript_2, False),
    ("research_project/fieldwork_2024/interviews/raw/session_03_participantC.txt", transcript_3_text, True),   # BOM
    ("research_project/fieldwork_2024/interviews/raw/focus_group_alpha.txt",       transcript_4, False),
]

for rel_path, content, has_bom in target_files:
    full_path = os.path.join(workspace, rel_path)
    if has_bom:
        with open(full_path, "wb") as f:
            f.write(bom + content.encode("utf-8"))
    else:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

print("Workspace generated successfully.")
print("Target transcript files:")
for rel_path, _, has_bom in target_files:
    print(f"  {rel_path}{'  [BOM]' if has_bom else ''}")