import os
import json
import random

random.seed(42)

# Create deep directory structure with distractor files
dirs = [
    "platform/submissions/batch_2024_01",
    "platform/submissions/batch_2024_02",
    "platform/submissions/archived",
    "platform/templates/old",
    "platform/templates/unused",
    "platform/reports/processed",
    "platform/reports/pending",
    "platform/assets/audio",
    "platform/assets/reading",
    "platform/config",
    "platform/logs",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# --- DISTRACTOR FILES ---

# Old/irrelevant config
with open("platform/config/legacy_config.json", "w") as f:
    json.dump({"version": "0.1", "deprecated": True, "engine": "v1"}, f, indent=2)

# Irrelevant log files
with open("platform/logs/system.log", "w") as f:
    f.write("2024-01-10 INFO: System started\n2024-01-10 WARN: High latency on upload\n2024-01-10 ERROR: Timeout\n")

# Old template (wrong/outdated format, should NOT be used)
with open("platform/templates/old/essay_template_v1.txt", "w") as f:
    f.write("Title:\nContent:\nScore:\nComments:")

# Unused template
with open("platform/templates/unused/feedback_draft.md", "w") as f:
    f.write("# Draft Feedback Form\n\nNOT IN USE. See newer guidelines.\n\nScore: /10\n")

# Archived processed report (distractor)
with open("platform/reports/processed/student_99_old_report.json", "w") as f:
    json.dump({
        "student_id": "S099",
        "note": "archived - old format, do not use as reference",
        "score": 6
    }, f, indent=2)

# Audio asset metadata (distractor)
with open("platform/assets/audio/voa_slow_index.txt", "w") as f:
    f.write("Index of VOA slow-speed audio files\nFile001: news_2024_01_10.mp3\nFile002: news_2024_01_11.mp3\n")

# Reading asset (distractor)
with open("platform/assets/reading/reading_list.csv", "w") as f:
    f.write("level,title,source\nBeginner,News in Levels article 1,newsinlevels.com\nIntermediate,Medium blog post,medium.com\n")

# Archived student (distractor)
with open("platform/submissions/archived/student_archive_summary.txt", "w") as f:
    f.write("Student S001-S010 archived. Data migrated to cold storage.\n")

# Batch 2024-02 placeholder
with open("platform/submissions/batch_2024_02/readme_internal.txt", "w") as f:
    f.write("Batch 2024-02 submissions. Processing scheduled for Feb 2024.\n")

# --- ACTUAL TASK INPUT FILES ---

# Student 1: IELTS Task 2 essay (argumentative) - has problems:
# - Missing hook, weak intro, no clear thesis line, body paragraphs missing topic sentences
# - Under 250 words — agent must flag this
# - Grammar errors present
student1_essay = """IELTS Writing Task 2

Some people think that technology has made our lives more complicated. 
Others believe it made things easier.

Technology is everywhere today. People use phones computers and internet all the time. 
I think technology is good because it help us communicate faster. For example we can send emails in seconds.
Also technology has improve healthcare. Doctors can use machines to find diseases earlier and this save lives.
But there is some problems. Young people spend too much time on social media and ignore their real friends.
Moreover technology make people lazy because they dont need to do hard tasks anymore.

In conclusion technology is double edge sword. It have benefits and disadvantages.
We should use it careful to get best results.
"""

with open("platform/submissions/batch_2024_01/student_101_ielts_task2.txt", "w") as f:
    f.write(student1_essay)

# Student 2: Formal business email (has structure issues, missing fields, grammar errors)
student2_email = """Subject: meeting next week

dear mr johnson

i am writing to asking about the meeting schedule for next week project review. 
i want to know what time is good for you and your team to have this meeting.
our team is available on Tuesday afternoon or Wednesday morning.

please tell me if this work for you.

thanks
li wei
"""

with open("platform/submissions/batch_2024_01/student_102_business_email.txt", "w") as f:
    f.write(student2_email)

# Student 3: Reading passage (agent must apply SQ3R method to this article)
reading_passage = """Title: The Future of Renewable Energy

Section 1: Solar Power Growth
Solar energy has experienced remarkable growth over the past decade. 
According to the International Energy Agency, global solar capacity reached 
over 800 gigawatts in 2022, up from just 40 gigawatts in 2010. 
This twenty-fold increase reflects falling costs and supportive government policies.

Section 2: Wind Energy Challenges  
Wind power, while abundant, faces significant hurdles. Offshore wind farms 
are expensive to build and maintain. Grid integration remains a technical 
challenge because wind is intermittent — it does not blow constantly. 
Energy storage solutions, particularly large-scale batteries, are critical 
to making wind power reliable.

Section 3: Policy and Investment
Government investment has been the primary driver of renewable growth. 
The United States Inflation Reduction Act allocated $369 billion for clean 
energy. The European Union aims to produce 45% of its energy from renewable 
sources by 2030. However, developing nations often lack the capital to 
transition away from coal and oil.

Section 4: The Path Forward
Experts agree that a global energy transition is possible but requires 
coordinated action. Technology improvements, international financing, and 
policy frameworks must align. The next decade will be decisive for whether 
humanity can limit global warming to manageable levels.
"""

with open("platform/assets/reading/renewable_energy_article.txt", "w") as f:
    f.write(reading_passage)

# Task specification file (tells the agent WHAT to produce, but NOT HOW)
task_spec = {
    "task_id": "COACHING_BATCH_2024_01",
    "description": "Process the following student submissions and generate coaching reports for each student, plus a SQ3R analysis of the assigned reading article.",
    "submissions": [
        {
            "student_id": "S101",
            "file": "platform/submissions/batch_2024_01/student_101_ielts_task2.txt",
            "submission_type": "ielts_task2_essay",
            "student_level": "intermediate"
        },
        {
            "student_id": "S102",
            "file": "platform/submissions/batch_2024_01/student_102_business_email.txt",
            "submission_type": "business_email",
            "student_level": "intermediate"
        }
    ],
    "reading_assignment": {
        "article_file": "platform/assets/reading/renewable_energy_article.txt",
        "method": "structured_reading_analysis"
    },
    "output_directory": "platform/reports/pending"
}

with open("platform/config/batch_task_spec.json", "w") as f:
    json.dump(task_spec, f, indent=2)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk("platform"):
    for fname in files:
        print(f"  {os.path.join(root, fname)}")